"""
Pinecone vector store service.
Each document gets its own namespace in the shared Pinecone index,
which provides clean isolation and simple bulk deletion.

Pinecone free tier: 1 index, up to 100K vectors.
Index setup: Dimensions=384, Metric=cosine (matches all-MiniLM-L6-v2).
"""

from __future__ import annotations

import asyncio
from typing import List, Optional
from uuid import UUID

from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import SourceChunk
from app.services.embeddings import embed_query, embed_texts

logger = get_logger(__name__)

_pinecone_client: Pinecone | None = None


def _get_pinecone() -> Pinecone:
    """Return a cached Pinecone client."""
    global _pinecone_client
    if _pinecone_client is None:
        settings = get_settings()
        _pinecone_client = Pinecone(api_key=settings.pinecone_api_key)
        logger.info("pinecone_client_ready")
    return _pinecone_client


def _get_index():
    """Return the Pinecone index handle, auto-creating if necessary."""
    settings = get_settings()
    pc = _get_pinecone()
    index_name = settings.pinecone_index_name

    existing = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing:
        logger.info("pinecone_creating_index", name=index_name, dims=settings.embedding_dimension)
        pc.create_index(
            name=index_name,
            dimension=settings.embedding_dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        logger.info("pinecone_index_created", name=index_name)

    return pc.Index(index_name)


def _document_namespace(document_id: UUID) -> str:
    """Each document gets an isolated namespace: doc-<uuid>"""
    return f"doc-{document_id}"


async def store_embeddings(
    document_id: UUID,
    chunks: List[Document],
) -> int:
    """
    Embed all chunks and upsert them into Pinecone under the document's namespace.
    Returns the number of chunks stored.
    """
    if not chunks:
        return 0

    settings = get_settings()
    texts = [c.page_content for c in chunks]

    logger.info("embedding_chunks", count=len(texts), document_id=str(document_id))

    # Run embedding in thread pool (CPU-bound)
    loop = asyncio.get_event_loop()
    vectors = await loop.run_in_executor(None, lambda: _sync_embed_texts(texts))

    namespace = _document_namespace(document_id)
    index = _get_index()

    # Build Pinecone vector records
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
            },
        })

    # Upsert in batches of 100 (Pinecone limit per batch)
    batch_size = 100
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        index.upsert(vectors=batch, namespace=namespace)
        logger.info(
            "pinecone_upsert_batch",
            batch=i // batch_size + 1,
            count=len(batch),
            document_id=str(document_id),
        )

    logger.info("embeddings_stored", count=len(records), document_id=str(document_id))
    return len(records)


def _sync_embed_texts(texts: List[str]) -> List[List[float]]:
    """Synchronous wrapper for embedding (used in thread pool)."""
    from app.services.embeddings import get_embeddings
    emb = get_embeddings()
    return emb.embed_documents(texts)


async def similarity_search(
    document_id: UUID,
    query: str,
    top_k: Optional[int] = None,
) -> List[SourceChunk]:
    """
    Embed the query and find the most similar chunks in the document's namespace.
    Returns ranked SourceChunk objects with content, page, and similarity score.
    """
    settings = get_settings()
    k = top_k or settings.top_k_results

    # Embed query in thread pool
    loop = asyncio.get_event_loop()
    query_vector = await loop.run_in_executor(
        None,
        lambda: _sync_embed_query(query),
    )

    namespace = _document_namespace(document_id)
    index = _get_index()

    result = index.query(
        vector=query_vector,
        top_k=k,
        namespace=namespace,
        include_metadata=True,
    )

    sources: List[SourceChunk] = []
    for match in result.get("matches", []):
        meta = match.get("metadata", {})
        sources.append(
            SourceChunk(
                content=meta.get("content", ""),
                page=meta.get("page"),
                score=round(float(match.get("score", 0.0)), 4),
            )
        )

    logger.info(
        "similarity_search_done",
        document_id=str(document_id),
        results=len(sources),
    )
    return sources


def _sync_embed_query(text: str) -> List[float]:
    """Synchronous wrapper for query embedding."""
    from app.services.embeddings import get_embeddings
    return get_embeddings().embed_query(text)


async def delete_document_embeddings(document_id: UUID) -> None:
    """
    Delete all vectors in the document's namespace.
    This is instant and clean — no leftover vectors.
    """
    try:
        namespace = _document_namespace(document_id)
        index = _get_index()
        index.delete(delete_all=True, namespace=namespace)
        logger.info("pinecone_namespace_deleted", document_id=str(document_id))
    except Exception as exc:
        logger.warning(
            "pinecone_delete_failed",
            document_id=str(document_id),
            error=str(exc),
        )
