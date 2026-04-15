"""
Global chat route — searches across ALL uploaded documents simultaneously.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.logging import get_logger
from app.models.schemas import SourceChunk
from app.services.rag_chain import stream_global_rag_response

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)


from pydantic import BaseModel, Field

class GlobalChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


@router.post("/global")
async def chat_global(request: GlobalChatRequest):
    """
    Stream a RAG-powered response searching ACROSS all uploaded documents.
    Useful for asking questions when you're not sure which document has the answer.
    """
    logger.info("global_chat_request", message_preview=request.message[:80])

    return StreamingResponse(
        stream_global_rag_response(user_message=request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
