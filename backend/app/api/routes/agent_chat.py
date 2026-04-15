"""
Agent chat route — SSE endpoint for LangChain ReAct agent mode.
Streams tool calls and final answer in real time.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.agent import stream_agent_response

router = APIRouter(prefix="/agent", tags=["agent"])
logger = get_logger(__name__)


class AgentRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


@router.post("/{document_id}")
async def agent_chat(document_id: UUID, request: AgentRequest):
    """
    Run the ReAct agent on a document.
    Streams intermediate tool calls (search, web, calculator) then final answer.
    """
    logger.info("agent_request", document_id=str(document_id), message=request.message[:80])

    return StreamingResponse(
        stream_agent_response(document_id=document_id, user_message=request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
