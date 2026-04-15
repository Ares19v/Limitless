"""
SQLite document metadata store (replaces Supabase REST API).
Uses aiosqlite for async access. The database is auto-created on startup.

Schema:
  documents  — filename, status, chunk_count, error_message, timestamps
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import UUID, uuid4

import aiosqlite

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── SQL ───────────────────────────────────────────────────────────────────────
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id            TEXT PRIMARY KEY,
    filename      TEXT NOT NULL,
    file_size     INTEGER,
    status        TEXT NOT NULL DEFAULT 'processing'
                       CHECK(status IN ('processing', 'ready', 'error')),
    chunk_count   INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _db_path() -> Path:
    return get_settings().db_path


async def init_db() -> None:
    """Create the documents table if it doesn't exist."""
    async with aiosqlite.connect(str(_db_path())) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.commit()
    logger.info("sqlite_db_ready", path=str(_db_path()))


async def create_document(
    document_id: UUID,
    filename: str,
    file_size: int,
) -> dict:
    """Insert a new document row with 'processing' status."""
    now = _now()
    row = {
        "id": str(document_id),
        "filename": filename,
        "file_size": file_size,
        "status": "processing",
        "chunk_count": 0,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }
    async with aiosqlite.connect(str(_db_path())) as db:
        await db.execute(
            """INSERT INTO documents
               (id, filename, file_size, status, chunk_count, created_at, updated_at)
               VALUES (:id, :filename, :file_size, :status, :chunk_count, :created_at, :updated_at)""",
            row,
        )
        await db.commit()
    return row


async def update_document_status(
    document_id: UUID,
    status: str,
    chunk_count: int = 0,
    error_message: Optional[str] = None,
) -> None:
    """Update status after RAG processing completes or fails."""
    async with aiosqlite.connect(str(_db_path())) as db:
        await db.execute(
            """UPDATE documents
               SET status=?, chunk_count=?, error_message=?, updated_at=?
               WHERE id=?""",
            (status, chunk_count, error_message, _now(), str(document_id)),
        )
        await db.commit()


async def get_document(document_id: UUID) -> Optional[dict]:
    """Fetch a single document by ID. Returns None if not found."""
    async with aiosqlite.connect(str(_db_path())) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM documents WHERE id = ?", (str(document_id),)
        ) as cursor:
            row = await cursor.fetchone()
    return dict(row) if row else None


async def list_documents(limit: int = 50, offset: int = 0) -> tuple[List[dict], int]:
    """List documents ordered by newest first. Returns (rows, total_count)."""
    async with aiosqlite.connect(str(_db_path())) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT COUNT(*) as cnt FROM documents") as cur:
            total_row = await cur.fetchone()
            total = dict(total_row)["cnt"] if total_row else 0

        async with db.execute(
            "SELECT * FROM documents ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ) as cursor:
            rows = [dict(r) for r in await cursor.fetchall()]

    return rows, total


async def delete_document(document_id: UUID) -> None:
    """Delete document record from SQLite."""
    async with aiosqlite.connect(str(_db_path())) as db:
        await db.execute("DELETE FROM documents WHERE id = ?", (str(document_id),))
        await db.commit()
