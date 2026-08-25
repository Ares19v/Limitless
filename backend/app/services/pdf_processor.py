"""
PDF processing service.
Uses pypdf (pure Python, cross-platform) for extraction and
LangChain text splitters for chunking.

v3: Adds contextual chunk enrichment (Anthropic-style) — prepends document-level
context to each chunk before embedding, reducing retrieval failure rate by ~67%.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Optional

from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _extract_text_with_metadata(pdf_path: Path) -> List[Document]:
    """
    Extract text from each page of a PDF using pypdf.
    Returns a list of LangChain Documents, one per page, with metadata.
    """
    docs: List[Document] = []
    try:
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                docs.append(
                    Document(
                        page_content=text,
                        metadata={
                            "page": page_num + 1,
                            "total_pages": total_pages,
                            "source": pdf_path.name,
                        },
                    )
                )
    except Exception as exc:
        logger.error("pdf_extraction_failed", path=str(pdf_path), error=str(exc))
        raise RuntimeError(f"Failed to extract PDF text: {exc}") from exc

    logger.info("pdf_extracted", pages=len(docs), file=pdf_path.name)
    return docs


def split_documents(
    docs: List[Document],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> List[Document]:
    """Split extracted page documents into smaller chunks."""
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.chunk_size,
        chunk_overlap=chunk_overlap or settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    logger.info("pdf_chunked", chunk_count=len(chunks))
    return chunks


def process_pdf(pdf_path: Path) -> List[Document]:
    """
    Full pipeline: extract → split → return chunks.
    This is the main entry point called by the upload service.
    """
    pages = _extract_text_with_metadata(pdf_path)
    if not pages:
        raise ValueError("PDF appears to be empty or contains no extractable text.")
    chunks = split_documents(pages)
    return chunks


def get_pdf_page_count(pdf_path: Path) -> int:
    """Return total page count without full text extraction."""
    try:
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception:
        return 0


async def enrich_chunks_with_context(
    chunks: List[Document],
    document_name: str,
) -> List[Document]:
    """
    Anthropic-style Contextual Retrieval:
    Prepends a ~60-token LLM-generated document-level context prefix to each chunk.
    This dramatically improves retrieval accuracy by giving every chunk awareness
    of where it sits within the broader document.

    Reduces retrieval failure rate by up to 67% (Anthropic, Sept 2024).
    Uses batch LLM calls with rate-limit awareness and graceful fallback.
    """
    from app.services.key_manager import get_llm

    if not chunks:
        return chunks

    # Build a short document overview from the first 3 chunks (≤1500 chars)
    doc_overview = "\n\n".join(c.page_content[:500] for c in chunks[:3])

    enriched: List[Document] = []
    llm = get_llm(streaming=False, max_tokens=80)

    logger.info("contextual_enrichment_start", chunks=len(chunks), doc=document_name)

    # Process in small batches to avoid rate limits
    BATCH_SIZE = 5
    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[batch_start: batch_start + BATCH_SIZE]
        tasks = []
        for chunk in batch:
            prompt = [
                {
                    "role": "system",
                    "content": (
                        "You are a document indexing assistant. Given a document excerpt and the document overview, "
                        "write a single SHORT sentence (max 60 words) that situates this excerpt within the broader document. "
                        "Start with 'This chunk' or 'This section'. Be specific, not generic."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Document: {document_name}\n"
                        f"Document overview:\n{doc_overview[:800]}\n\n"
                        f"Chunk to situate:\n{chunk.page_content[:400]}\n\n"
                        f"Context sentence:"
                    ),
                },
            ]
            tasks.append(llm.ainvoke(prompt))

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for chunk, result in zip(batch, results):
                if isinstance(result, Exception):
                    # Graceful fallback — keep chunk unchanged
                    logger.warning("context_enrichment_failed_chunk", error=str(result))
                    enriched.append(chunk)
                else:
                    context_prefix = result.content.strip()
                    enriched_content = f"[Context: {context_prefix}]\n\n{chunk.page_content}"
                    enriched.append(Document(
                        page_content=enriched_content,
                        metadata={**chunk.metadata, "context_prefix": context_prefix},
                    ))
        except Exception as exc:
            logger.warning("contextual_enrichment_batch_failed", error=str(exc))
            enriched.extend(batch)  # fallback: add unenriched batch

        # Small pause between batches to respect rate limits
        if batch_start + BATCH_SIZE < len(chunks):
            await asyncio.sleep(0.3)

    logger.info("contextual_enrichment_complete", enriched=len(enriched))
    return enriched

