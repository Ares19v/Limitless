"""
Conversation history routes.
GET  /api/v1/history/{document_id}  — load all past messages for a document
DELETE /api/v1/history/{document_id} — wipe chat history for a document
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.models.schemas import ChatMessage
from app.services.document_store import delete_history, get_history

router = APIRouter(prefix="/history", tags=["history"])
logger = get_logger(__name__)


@router.get("/{document_id}", response_model=List[ChatMessage])
async def get_chat_history(document_id: UUID):
    """Return all persisted messages for a document (oldest first)."""
    messages = await get_history(document_id)
    return messages


@router.delete("/{document_id}", status_code=204)
async def clear_chat_history(document_id: UUID):
    """Delete all persisted chat messages for a document."""
    await delete_history(document_id)
    logger.info("history_cleared", document_id=str(document_id))
