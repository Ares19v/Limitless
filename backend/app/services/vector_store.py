"""
Pinecone vector store service + Hybrid Search (BM25 + Vector with RRF fusion).

Each document gets its own namespace in the shared Pinecone index.
Hybrid search combines keyword precision (BM25) with semantic understanding (Pinecone).
Results are merged using Reciprocal Rank Fusion (RRF, k=60).
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional
from uuid import UUID

from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import SourceChunk
from app.services.embeddings import embed_query, embed_texts

logger = get_logger(__name__)

_pinecone_client: Pinecone | None = None
_RRF_K = 60  # RRF constant — standard value


def _get_pinecone() -> Pinecone:
    global _pinecone_client
    if _pinecone_client is None:
        settings = get_settings()
        _pinecone_client = Pinecone(api_key=settings.pinecone_api_key)
        logger.info("pinecone_client_ready")
    return _pinecone_client


def _get_index():
    settings = get_settings()
    pc = _get_pinecone()
    index_name = settings.pinecone_index_name
    existing = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing:
        logger.info("pinecone_creating_index", name=index_name)
        pc.create_index(
            name=index_name,
            dimension=settings.embedding_dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(index_name)


def _document_namespace(document_id: UUID) -> str:
    return f"doc-{document_id}"


async def store_embeddings(document_id: UUID, chunks: List[Document]) -> int:
    """Embed chunks and upsert into Pinecone. Returns chunk count stored."""
    if not chunks:
        return 0

    settings = get_settings()
    texts = [c.page_content for c in chunks]
    logger.info("embedding_chunks", count=len(texts), document_id=str(document_id))

    loop = asyncio.get_event_loop()
    vectors = await loop.run_in_executor(None, lambda: _sync_embed_texts(texts))

    namespace = _document_namespace(document_id)
    index = _get_index()

    records = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        records.append({
            "id": f"{document_id}-{i}",
            "values": vector,
            "metadata": {
                "content": chunk.page_content,
                "page": chunk.metadata.get("page"),
                "source": chunk.metadata.get("source", ""),
                "total_pages": chunk.metadata.get("total_pages"),
                "document_id": str(document_id),
                "chunk_index": i,
                "bbox": chunk.metadata.get("bbox", ""),                       # Feature 6: bounding box
                "context_prefix": chunk.metadata.get("context_prefix", ""),   # Feature 1: contextual retrieval
            },
        })

    for i in range(0, len(records), 100):
        batch = records[i: i + 100]
        index.upsert(vectors=batch, namespace=namespace)
        logger.info("pinecone_upsert_batch", batch=i // 100 + 1, count=len(batch))

    logger.info("embeddings_stored", count=len(records), document_id=str(document_id))
    return len(records)


def _sync_embed_texts(texts: List[str]) -> List[List[float]]:
    from app.services.embeddings import get_embeddings
    return get_embeddings().embed_documents(texts)


def _sync_embed_query(text: str) -> List[float]:
    from app.services.embeddings import get_embeddings
    return get_embeddings().embed_query(text)


async def similarity_search(
    document_id: UUID, query: str, top_k: Optional[int] = None,
) -> List[SourceChunk]:
    """Pure Pinecone vector similarity search (used internally)."""
    settings = get_settings()
    k = top_k or settings.top_k_results

    loop = asyncio.get_event_loop()
    query_vector = await loop.run_in_executor(None, lambda: _sync_embed_query(query))

    namespace = _document_namespace(document_id)
    index = _get_index()

    result = index.query(
        vector=query_vector, top_k=k, namespace=namespace, include_metadata=True,
    )

    sources: List[SourceChunk] = []
    for match in result.get("matches", []):
        meta = match.get("metadata", {})
        sources.append(SourceChunk(
            content=meta.get("content", ""),
            page=meta.get("page"),
            score=round(float(match.get("score", 0.0)), 4),
            bbox=meta.get("bbox") or None,
            context_prefix=meta.get("context_prefix") or None,
        ))

    logger.info("similarity_search_done", document_id=str(document_id), results=len(sources))
    return sources


def _rrf_fuse(
    vector_results: List[SourceChunk],
    bm25_results: List[SourceChunk],
    k: int = _RRF_K,
) -> List[SourceChunk]:
    """
    Reciprocal Rank Fusion — merges two ranked lists into one.
    Score = sum(1 / (k + rank)) for each result appearance.
    """
    scores: Dict[str, float] = {}
    chunk_map: Dict[str, SourceChunk] = {}

    for rank, chunk in enumerate(vector_results):
        key = chunk.content[:100]  # Use content prefix as dedup key
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
        chunk_map[key] = chunk

    for rank, chunk in enumerate(bm25_results):
        key = chunk.content[:100]
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
        chunk_map[key] = chunk

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [chunk_map[key] for key, _ in ranked]


async def hybrid_similarity_search(
    document_id: UUID, query: str, top_k: int = 15,
) -> List[SourceChunk]:
    """
    Hybrid search: BM25 keyword + Pinecone vector, fused with RRF.
    Returns top_k candidates for downstream re-ranking.
    """
    from app.services.bm25_store import bm25_search

    # Run both searches in parallel
    vector_task = similarity_search(document_id, query, top_k=top_k)
    loop = asyncio.get_event_loop()
    bm25_task = loop.run_in_executor(
        None, lambda: bm25_search(str(document_id), query, top_k=top_k)
    )

    vector_results, bm25_results = await asyncio.gather(vector_task, bm25_task)

    fused = _rrf_fuse(vector_results, list(bm25_results))
    logger.info(
        "hybrid_search_done",
        document_id=str(document_id),
        vector=len(vector_results),
        bm25=len(bm25_results),
        fused=len(fused),
    )
    return fused[:top_k]


async def global_similarity_search(query: str, top_k: int = 15) -> List[SourceChunk]:
    """
    Search across ALL documents (no namespace filter).
    Returns chunks tagged with their document_id in content.
    """
    loop = asyncio.get_event_loop()
    query_vector = await loop.run_in_executor(None, lambda: _sync_embed_query(query))

    index = _get_index()
    result = index.query(
        vector=query_vector, top_k=top_k, include_metadata=True,
    )

    sources: List[SourceChunk] = []
    for match in result.get("matches", []):
        meta = match.get("metadata", {})
        doc_id = meta.get("document_id", "unknown")
        sources.append(SourceChunk(
            content=f"[Doc: {doc_id[:8]}...]\n{meta.get('content', '')}",
            page=meta.get("page"),
            score=round(float(match.get("score", 0.0)), 4),
        ))

    logger.info("global_search_done", results=len(sources))
    return sources


async def delete_document_embeddings(document_id: UUID) -> None:
    """Delete all vectors in the document's Pinecone namespace."""
    try:
        namespace = _document_namespace(document_id)
        index = _get_index()
        index.delete(delete_all=True, namespace=namespace)
        logger.info("pinecone_namespace_deleted", document_id=str(document_id))
    except Exception as exc:
        logger.warning("pinecone_delete_failed", document_id=str(document_id), error=str(exc))
