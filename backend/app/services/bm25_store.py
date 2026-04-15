"""
Local BM25 keyword index (per document).
Stored as pickle files in backend/data/bm25/.
Used alongside Pinecone vector search for hybrid retrieval with RRF fusion.
"""

from __future__ import annotations

import asyncio
import pickle
from pathlib import Path
from typing import List

from rank_bm25 import BM25Okapi

from app.core.logging import get_logger
from app.models.schemas import SourceChunk

logger = get_logger(__name__)


def _bm25_dir() -> Path:
    p = Path(__file__).resolve().parents[2] / "data" / "bm25"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _index_path(document_id: str) -> Path:
    return _bm25_dir() / f"{document_id}.pkl"


def _tokenize(text: str) -> List[str]:
    return text.lower().split()


async def build_bm25_index(document_id: str, chunks: List[SourceChunk]) -> None:
    """Build and persist a BM25 index for a document's chunks."""
    corpus = [_tokenize(c.content) for c in chunks]
    index = BM25Okapi(corpus)
    data = {"index": index, "chunks": chunks}

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: _index_path(str(document_id)).write_bytes(pickle.dumps(data)),
    )
    logger.info("bm25_index_built", document_id=str(document_id), chunks=len(chunks))


def bm25_search(document_id: str, query: str, top_k: int = 20) -> List[SourceChunk]:
    """Run BM25 keyword search. Returns empty list if no index exists."""
    path = _index_path(str(document_id))
    if not path.exists():
        return []

    data = pickle.loads(path.read_bytes())
    index: BM25Okapi = data["index"]
    chunks: List[SourceChunk] = data["chunks"]

    tokens = _tokenize(query)
    scores = index.get_scores(tokens)

    ranked = sorted(
        zip(scores, chunks),
        key=lambda x: x[0],
        reverse=True,
    )
    return [chunk for score, chunk in ranked[:top_k] if score > 0]


def delete_bm25_index(document_id: str) -> None:
    """Remove the BM25 index file when a document is deleted."""
    path = _index_path(str(document_id))
    if path.exists():
        path.unlink()
        logger.info("bm25_index_deleted", document_id=str(document_id))
