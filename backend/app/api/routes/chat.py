"""
Chat route — streams LLM responses via Server-Sent Events (SSE).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.logging import get_logger
from app.models.schemas import ChatRequest
from app.services.rag_chain import stream_rag_response

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)


@router.post("/{document_id}")
async def chat_with_document(
    document_id: UUID,
    request: ChatRequest,
):
    """
    Stream a RAG-powered response about the uploaded document.
    Returns SSE stream (text/event-stream).
    """
    if request.document_id != document_id:
        raise HTTPException(
            status_code=422,
            detail="document_id in path and body must match.",
        )

    logger.info(
        "chat_request",
        document_id=str(document_id),
        message_preview=request.message[:80],
        history_length=len(request.history),
    )

    return StreamingResponse(
        stream_rag_response(
            document_id=document_id,
            user_message=request.message,
            history=request.history,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
