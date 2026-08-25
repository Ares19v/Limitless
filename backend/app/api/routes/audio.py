"""
Audio Overview API route.

POST /api/v1/audio/{document_id}
Returns: audio/mpeg binary — a 2-host podcast overview of the document.

Generation takes 20-40 seconds depending on document length.
The response is streamed as binary audio once complete.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.core.logging import get_logger
from app.services.document_store import get_document
from app.services.audio_overview import generate_audio_overview

router = APIRouter(prefix="/audio", tags=["audio"])
logger = get_logger(__name__)


@router.post("/{document_id}", response_class=Response)
async def create_audio_overview(document_id: UUID):
    """
    Generate a NotebookLM-style 2-host podcast audio overview for a document.

    Retrieves key content, generates a conversational dialogue script between
    Host A (curious) and Host B (expert), synthesizes each turn with distinct
    voices, and returns a stitched MP3 audio file.

    Generation time: ~20-60 seconds depending on document length.
    Returns: audio/mpeg binary response.
    """
    # Verify document exists and is ready
    doc = await get_document(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.status != "ready":
        raise HTTPException(
            status_code=409,
            detail=f"Document is not ready yet (status: {doc.status}). Wait for processing to complete."
        )

    logger.info("audio_overview_request", document_id=str(document_id), filename=doc.filename)

    try:
        audio_bytes = await generate_audio_overview(
            document_id=document_id,
            document_name=doc.filename,
        )
    except ImportError as exc:
        raise HTTPException(
            status_code=501,
            detail="Audio generation requires gTTS: pip install gtts. Install and restart the server."
        )
    except Exception as exc:
        logger.error("audio_generation_failed", document_id=str(document_id), error=str(exc))
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(exc)[:200]}")

    safe_name = doc.filename.replace(".pdf", "").replace(" ", "_")
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}_overview.mp3"',
            "Content-Length": str(len(audio_bytes)),
        },
    )
