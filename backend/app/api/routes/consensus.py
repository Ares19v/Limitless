"""
Consensus API route — Contradiction & Evidence Synthesis Engine.

POST /api/v1/consensus
Body: {"question": "Does X support Y?", "document_id": "optional-uuid"}

Returns SSE stream of:
- status updates
- progress (chunks analyzed)
- final result with consensus % and stance-classified evidence
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.consensus import stream_consensus_analysis

router = APIRouter(prefix="/consensus", tags=["consensus"])
logger = get_logger(__name__)


class ConsensusRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=2000,
                          description="The claim or question to analyze evidence for")
    document_id: Optional[UUID] = Field(
        None,
        description="If provided, search only this document. If null, search entire corpus."
    )


@router.post("")
async def analyze_consensus(request: ConsensusRequest):
    """
    Run contradiction/consensus analysis on uploaded documents.

    Retrieves relevant chunks, classifies each as SUPPORTS/CONTRADICTS/NEUTRAL,
    aggregates consensus percentage, and synthesizes a structured evidence report.

    Returns SSE stream with progress updates and final structured JSON result.
    """
    logger.info(
        "consensus_request",
        question_preview=request.question[:80],
        document_id=str(request.document_id) if request.document_id else "global",
    )

    return StreamingResponse(
        stream_consensus_analysis(
            question=request.question,
            document_id=request.document_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
