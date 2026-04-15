"""
Local HuggingFace embeddings using sentence-transformers.
No API key required — model is downloaded once on first use (~90MB).
Default model: all-MiniLM-L6-v2 → 384 dimensions.
"""

from __future__ import annotations

from typing import List

from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_embeddings_instance: HuggingFaceEmbeddings | None = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Return a cached HuggingFace embeddings instance."""
    global _embeddings_instance
    if _embeddings_instance is None:
        settings = get_settings()
        logger.info(
            "embeddings_loading",
            model=settings.embedding_model,
            note="First load downloads model (~90MB). Subsequent starts are instant.",
        )
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("embeddings_ready", model=settings.embedding_model)
    return _embeddings_instance


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a batch of texts. Runs synchronously in thread pool via caller."""
    emb = get_embeddings()
    return emb.embed_documents(texts)


async def embed_query(text: str) -> List[float]:
    """Embed a single query string."""
    emb = get_embeddings()
    return emb.embed_query(text)
