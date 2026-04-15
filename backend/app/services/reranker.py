"""
Cross-encoder re-ranker using sentence-transformers.
After Pinecone + BM25 retrieve many candidates, this selects the best top_k.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2 (~85MB, downloaded once on first call)
"""

from __future__ import annotations

from typing import List

from sentence_transformers.cross_encoder import CrossEncoder

from app.core.logging import get_logger
from app.models.schemas import SourceChunk

logger = get_logger(__name__)

_reranker: CrossEncoder | None = None


def get_reranker() -> CrossEncoder:
    """Lazy-load the cross-encoder (downloads model on first call)."""
    global _reranker
    if _reranker is None:
        logger.info("reranker_loading", model="cross-encoder/ms-marco-MiniLM-L-6-v2")
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        logger.info("reranker_ready")
    return _reranker


def rerank(query: str, chunks: List[SourceChunk], top_k: int = 5) -> List[SourceChunk]:
    """
    Score each (query, chunk) pair with the cross-encoder.
    Returns the top_k highest-scoring chunks.
    """
    if not chunks:
        return chunks

    reranker = get_reranker()
    pairs = [(query, chunk.content) for chunk in chunks]
    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(scores, chunks),
        key=lambda x: float(x[0]),
        reverse=True,
    )

    result = [chunk for _, chunk in ranked[:top_k]]
    logger.info("reranked", input_count=len(chunks), output_count=len(result))
    return result
