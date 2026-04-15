"""
PDF upload route — multipart upload with background RAG processing.
Stores metadata in SQLite; vectors go to Pinecone.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import UploadResponse
from app.services.document_store import create_document, update_document_status
from app.services.pdf_processor import process_pdf
from app.services.vector_store import store_embeddings
from app.utils.file_handler import get_upload_path, validate_file

router = APIRouter(prefix="/upload", tags=["upload"])
logger = get_logger(__name__)


async def _process_and_embed(document_id: UUID, file_path: Path) -> None:
    """Background task: parse PDF → chunk → embed → store in Pinecone."""
    try:
        logger.info("processing_start", document_id=str(document_id), file=file_path.name)

        # CPU-bound PDF parsing in thread pool
        loop = asyncio.get_event_loop()
        chunks = await loop.run_in_executor(None, process_pdf, file_path)

        # Embeddings + Pinecone upsert
        count = await store_embeddings(document_id, chunks)

        # Update SQLite status → ready
        await update_document_status(document_id, "ready", chunk_count=count)
        logger.info("processing_complete", document_id=str(document_id), chunks=count)

    except Exception as exc:
        logger.error("processing_failed", document_id=str(document_id), error=str(exc))
        await update_document_status(
            document_id, "error", error_message=str(exc)[:500]
        )


@router.post("", response_model=UploadResponse, status_code=202)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF file to upload (max 50MB)"),
):
    """
    Upload a PDF for RAG processing.
    Returns immediately with document_id; processing runs in the background.
    Poll GET /documents/{id} to check when status becomes 'ready'.
    """
    settings = get_settings()

    # Validate file type
    ok, err = validate_file(file.filename or "", file.content_type)
    if not ok:
        raise HTTPException(status_code=422, detail=err)

    # Read & validate size
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=422, detail="File is empty.")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb}MB.",
        )

    # Save file using cross-platform pathlib
    document_id = uuid4()
    safe_name = file.filename or "document.pdf"
    file_path = get_upload_path(settings.upload_dir, document_id, safe_name)
    file_path.write_bytes(content)

    # Insert document record in SQLite
    await create_document(document_id, safe_name, len(content))

    # Schedule background processing
    background_tasks.add_task(_process_and_embed, document_id, file_path)

    logger.info(
        "upload_accepted",
        document_id=str(document_id),
        filename=safe_name,
        size_kb=round(len(content) / 1024, 1),
    )

    return UploadResponse(
        document_id=document_id,
        filename=safe_name,
        message="File accepted. Processing started — poll /documents/{id} for status.",
    )
