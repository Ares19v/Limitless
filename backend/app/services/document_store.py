"""
SQLite document metadata store + conversation history.
Auto-creates all tables on startup via init_db().

Tables:
  documents   — filename, status, chunk_count, summary, timestamps
  messages    — per-document conversation history
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import UUID

import aiosqlite

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import ChatMessage

logger = get_logger(__name__)

CREATE_DOCUMENTS_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id            TEXT PRIMARY KEY,
    filename      TEXT NOT NULL,
    file_size     INTEGER,
    status        TEXT NOT NULL DEFAULT 'processing'
                       CHECK(status IN ('processing', 'ready', 'error')),
    chunk_count   INTEGER NOT NULL DEFAULT 0,
    summary       TEXT,
    error_message TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
"""

CREATE_MESSAGES_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    role        TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
"""

ADD_SUMMARY_COLUMN_SQL = """
ALTER TABLE documents ADD COLUMN summary TEXT;
"""


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _db_path() -> Path:
    return get_settings().db_path


async def init_db() -> None:
    """Create all tables if they don't exist."""
    async with aiosqlite.connect(str(_db_path())) as db:
        await db.execute(CREATE_DOCUMENTS_SQL)
        await db.execute(CREATE_MESSAGES_SQL)
        # Add summary column if it doesn't exist (migration for existing DBs)
        try:
            await db.execute(ADD_SUMMARY_COLUMN_SQL)
        except Exception:
            pass  # Column already exists
        await db.commit()
    logger.info("sqlite_db_ready", path=str(_db_path()))


# ── Documents ─────────────────────────────────────────────────────────────────

async def create_document(document_id: UUID, filename: str, file_size: int) -> dict:
    now = _now()
    row = {
        "id": str(document_id), "filename": filename, "file_size": file_size,
        "status": "processing", "chunk_count": 0, "summary": None,
        "error_message": None, "created_at": now, "updated_at": now,
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
    summary: Optional[str] = None,
) -> None:
    async with aiosqlite.connect(str(_db_path())) as db:
        await db.execute(
            """UPDATE documents
               SET status=?, chunk_count=?, error_message=?, summary=?, updated_at=?
               WHERE id=?""",
            (status, chunk_count, error_message, summary, _now(), str(document_id)),
        )
        await db.commit()


async def get_document(document_id: UUID) -> Optional[dict]:
    async with aiosqlite.connect(str(_db_path())) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM documents WHERE id = ?", (str(document_id),)
        ) as cursor:
            row = await cursor.fetchone()
    return dict(row) if row else None


async def list_documents(limit: int = 50, offset: int = 0) -> tuple[List[dict], int]:
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
    async with aiosqlite.connect(str(_db_path())) as db:
        await db.execute("DELETE FROM documents WHERE id = ?", (str(document_id),))
        await db.commit()


# ── Conversation History ───────────────────────────────────────────────────────

async def save_message(document_id: UUID, role: str, content: str) -> None:
    """Persist a single chat message."""
    async with aiosqlite.connect(str(_db_path())) as db:
        await db.execute(
            "INSERT INTO messages (document_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (str(document_id), role, content, _now()),
        )
        await db.commit()


async def get_history(document_id: UUID, limit: int = 40) -> List[ChatMessage]:
    """Load the last `limit` messages for a document (oldest first)."""
    async with aiosqlite.connect(str(_db_path())) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT role, content FROM messages
               WHERE document_id = ?
               ORDER BY created_at ASC
               LIMIT ?""",
            (str(document_id), limit),
        ) as cursor:
            rows = await cursor.fetchall()
    return [ChatMessage(role=r["role"], content=r["content"]) for r in rows]


async def delete_history(document_id: UUID) -> None:
    """Wipe all messages for a document."""
    async with aiosqlite.connect(str(_db_path())) as db:
        await db.execute("DELETE FROM messages WHERE document_id = ?", (str(document_id),))
        await db.commit()
