"""
RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval)
ICLR 2024 — Stanford NLP.

Builds a hierarchical summary tree over document chunks:
  Level 0: Original leaf chunks (raw extracted text)
  Level 1: Cluster summaries (groups of 5-8 similar leaf chunks)
  Level 2: Root summary (summary of all Level 1 summaries)

At retrieval time, searches ALL levels simultaneously — enabling both:
  - Precise leaf-level fact retrieval (specific details)
  - High-level conceptual synthesis (corpus-wide understanding)

Architecture:
  1. Embed all chunks
  2. Cluster using K-Means (sklearn) — faster than GMM for production use
  3. Summarize each cluster with Groq LLM
  4. Store summaries back into Pinecone with raptor_level=1 metadata
  5. Summarize all cluster summaries → store as raptor_level=2 root

This fixes the fundamental limitation of naive RAG for questions like:
  "Summarize the entire paper" or "What is the main argument across all sections?"
"""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import UUID

import numpy as np
from langchain_core.documents import Document

from app.core.logging import get_logger
from app.models.schemas import SourceChunk

logger = get_logger(__name__)

# RAPTOR tree configuration
RAPTOR_LEAF_CLUSTER_SIZE = 6   # Chunks per Level-1 cluster
RAPTOR_MAX_LEVEL1_NODES = 20   # Max Level-1 summary nodes
RAPTOR_SUMMARY_MAX_TOKENS = 250


def _cluster_chunks_kmeans(
    chunks: List[Document],
    embeddings: List[List[float]],
    n_clusters: Optional[int] = None,
) -> List[List[int]]:
    """
    Cluster chunk embeddings using K-Means.
    Returns a list of cluster index groups (list of chunk indices per cluster).
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import normalize

    n = len(chunks)
    if n == 0:
        return []

    # Auto-determine cluster count: sqrt of chunk count, capped at MAX_LEVEL1_NODES
    if n_clusters is None:
        n_clusters = min(max(2, math.isqrt(n)), RAPTOR_MAX_LEVEL1_NODES)

    if n < n_clusters:
        # Too few chunks — group everything into one cluster
        return [list(range(n))]

    vectors = np.array(embeddings, dtype=np.float32)
    normalized = normalize(vectors, norm="l2")

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = kmeans.fit_predict(normalized)

    # Group chunk indices by cluster
    clusters: dict[int, List[int]] = {}
    for idx, label in enumerate(labels):
        clusters.setdefault(int(label), []).append(idx)

    return list(clusters.values())


async def _summarize_cluster(llm, cluster_text: str, level: int) -> str:
    """Generate an abstractive summary for a cluster of chunks."""
    prompt = [
        {
            "role": "system",
            "content": (
                "You are a precise document summarizer. "
                "Write a dense, factual summary that captures ALL key information from the provided text. "
                "Do not add any information not present in the text. "
                f"This is a Level-{level} RAPTOR tree node."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Summarize the following document sections into a single coherent paragraph "
                f"(max {RAPTOR_SUMMARY_MAX_TOKENS} words). Preserve all key facts, numbers, and concepts:\n\n"
                f"{cluster_text[:3000]}"
            ),
        },
    ]
    try:
        response = await llm.ainvoke(prompt)
        return response.content.strip()
    except Exception as exc:
        logger.warning("raptor_summary_failed", level=level, error=str(exc))
        return cluster_text[:500]  # Fallback: use truncated original text


async def build_raptor_tree(document_id: UUID, chunks: List[Document]) -> dict:
    """
    Build the RAPTOR hierarchical summary tree for a document.

    Returns metadata about the tree structure:
    {level1_nodes: int, level2_nodes: int, total_raptor_chunks: int}

    Tree nodes are stored in Pinecone alongside regular chunks
    with raptor_level=1 or raptor_level=2 metadata.
    """
    from app.services.embeddings import get_embeddings
    from app.services.vector_store import _get_index, _document_namespace

    if len(chunks) < 4:
        logger.info("raptor_skipped_too_few_chunks", doc_id=str(document_id), chunks=len(chunks))
        return {"level1_nodes": 0, "level2_nodes": 0, "total_raptor_chunks": 0}

    logger.info("raptor_build_start", doc_id=str(document_id), leaf_chunks=len(chunks))

    # Get LLM for summarization
    from app.services.key_manager import get_llm
    llm = get_llm(streaming=False, max_tokens=RAPTOR_SUMMARY_MAX_TOKENS)

    # Step 1: Embed all leaf chunks
    loop = asyncio.get_event_loop()
    texts = [c.page_content[:1200] for c in chunks]

    try:
        embeddings = await loop.run_in_executor(None, lambda: get_embeddings().embed_documents(texts))
    except Exception as exc:
        logger.error("raptor_embedding_failed", error=str(exc))
        return {"level1_nodes": 0, "level2_nodes": 0, "total_raptor_chunks": 0}

    # Step 2: Cluster chunks
    cluster_groups = _cluster_chunks_kmeans(chunks, embeddings)
    logger.info("raptor_clusters_formed", n_clusters=len(cluster_groups))

    # Step 3: Summarize each cluster (Level 1)
    index = _get_index()
    namespace = _document_namespace(document_id)
    level1_summaries: List[str] = []
    level1_records = []

    SUMMARY_BATCH = 3
    for cluster_idx, chunk_indices in enumerate(cluster_groups):
        cluster_texts = "\n\n---\n\n".join(
            chunks[i].page_content[:800] for i in chunk_indices if i < len(chunks)
        )
        summary = await _summarize_cluster(llm, cluster_texts, level=1)
        level1_summaries.append(summary)

        # Embed the summary
        try:
            summary_vec = await loop.run_in_executor(
                None, lambda s=summary: get_embeddings().embed_query(s)
            )
            pages = [chunks[i].metadata.get("page") for i in chunk_indices if i < len(chunks)]
            pages = [p for p in pages if p is not None]

            level1_records.append({
                "id": f"{document_id}-raptor-l1-{cluster_idx}",
                "values": summary_vec,
                "metadata": {
                    "content": f"[RAPTOR-L1 Summary, Cluster {cluster_idx}]\n{summary}",
                    "page": min(pages) if pages else None,
                    "raptor_level": 1,
                    "cluster_idx": cluster_idx,
                    "source_chunk_count": len(chunk_indices),
                    "document_id": str(document_id),
                },
            })
        except Exception as exc:
            logger.warning("raptor_l1_embed_failed", cluster=cluster_idx, error=str(exc))

        # Small delay to respect rate limits
        if cluster_idx % SUMMARY_BATCH == SUMMARY_BATCH - 1:
            await asyncio.sleep(0.5)

    # Step 4: Upsert Level-1 nodes to Pinecone
    if level1_records:
        for i in range(0, len(level1_records), 50):
            index.upsert(vectors=level1_records[i:i+50], namespace=namespace)
        logger.info("raptor_l1_upserted", count=len(level1_records))

    # Step 5: Build Level-2 root summary (summary of all L1 summaries)
    level2_records = []
    if len(level1_summaries) >= 2:
        all_l1_text = "\n\n---\n\n".join(level1_summaries)
        root_summary = await _summarize_cluster(llm, all_l1_text, level=2)

        try:
            root_vec = await loop.run_in_executor(
                None, lambda: get_embeddings().embed_query(root_summary)
            )
            level2_records.append({
                "id": f"{document_id}-raptor-l2-root",
                "values": root_vec,
                "metadata": {
                    "content": f"[RAPTOR-L2 Root Summary — Full Document]\n{root_summary}",
                    "page": 1,
                    "raptor_level": 2,
                    "cluster_idx": -1,
                    "source_chunk_count": len(chunks),
                    "document_id": str(document_id),
                },
            })
            index.upsert(vectors=level2_records, namespace=namespace)
            logger.info("raptor_l2_root_upserted")
        except Exception as exc:
            logger.warning("raptor_l2_embed_failed", error=str(exc))

    total_raptor = len(level1_records) + len(level2_records)
    result = {
        "level1_nodes": len(level1_records),
        "level2_nodes": len(level2_records),
        "total_raptor_chunks": total_raptor,
    }
    logger.info("raptor_build_complete", doc_id=str(document_id), **result)
    return result
