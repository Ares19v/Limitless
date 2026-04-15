"""
Document management routes — CRUD backed by SQLite.
No Supabase dependency.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.core.logging import get_logger
from app.models.schemas import DocumentListResponse, DocumentResponse
from app.services.document_store import (
    delete_document as db_delete,
    get_document,
    list_documents,
)
from app.services.vector_store import delete_document_embeddings

router = APIRouter(prefix="/documents", tags=["documents"])
logger = get_logger(__name__)


@router.get("", response_model=DocumentListResponse)
async def list_docs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List all documents with their processing status."""
    rows, total = await list_documents(limit=limit, offset=offset)
    return DocumentListResponse(
        documents=[DocumentResponse(**r) for r in rows],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_doc(document_id: UUID):
    """Get a single document by ID (used for polling processing status)."""
    row = await get_document(document_id)
    if not row:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentResponse(**row)


@router.delete("/{document_id}", status_code=204)
async def delete_doc(document_id: UUID):
    """
    Delete a document:
    1. Remove all Pinecone vectors in the document's namespace
    2. Remove the SQLite metadata row
    """
    row = await get_document(document_id)
    if not row:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 1. Delete Pinecone namespace (all vectors for this doc)
    await delete_document_embeddings(document_id)

    # 2. Delete SQLite record
    await db_delete(document_id)

    logger.info("document_deleted", document_id=str(document_id))
