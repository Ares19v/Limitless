"""
PDF upload route — multipart upload with background RAG processing.
v2: Also builds BM25 index and generates AI summary after embedding.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import SourceChunk, UploadResponse
from app.services.bm25_store import build_bm25_index
from app.services.document_store import create_document, update_document_status
from app.services.pdf_processor import process_pdf
from app.services.rag_chain import generate_summary
from app.services.vector_store import store_embeddings
from app.utils.file_handler import get_upload_path, validate_file

router = APIRouter(prefix="/upload", tags=["upload"])
logger = get_logger(__name__)


async def _process_and_embed(document_id: UUID, file_path: Path) -> None:
    """
    Background task:
    1. Parse PDF → chunks
    2. Store embeddings in Pinecone
    3. Build local BM25 index for hybrid search
    4. Generate AI summary and store in SQLite
    """
    try:
        logger.info("processing_start", document_id=str(document_id), file=file_path.name)

        # Step 1: CPU-bound PDF parsing
        loop = asyncio.get_event_loop()
        langchain_chunks = await loop.run_in_executor(None, process_pdf, file_path)

        # Step 2: Pinecone vector storage
        count = await store_embeddings(document_id, langchain_chunks)

        # Step 3: Build BM25 index for hybrid search
        bm25_chunks = [
            SourceChunk(
                content=c.page_content,
                page=c.metadata.get("page"),
                score=0.0,
            )
            for c in langchain_chunks
        ]
        await build_bm25_index(str(document_id), bm25_chunks)

        # Step 4: Generate 3-bullet AI summary from first few chunks
        summary = await generate_summary(bm25_chunks)

        # Step 5: Update SQLite → ready with summary
        await update_document_status(
            document_id, "ready", chunk_count=count, summary=summary
        )
        logger.info(
            "processing_complete",
            document_id=str(document_id),
            chunks=count,
            has_summary=bool(summary),
        )

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

    ok, err = validate_file(file.filename or "", file.content_type)
    if not ok:
        raise HTTPException(status_code=422, detail=err)

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=422, detail="File is empty.")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb}MB.",
        )

    document_id = uuid4()
    safe_name = file.filename or "document.pdf"
    file_path = get_upload_path(settings.upload_dir, document_id, safe_name)
    file_path.write_bytes(content)

    await create_document(document_id, safe_name, len(content))
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
