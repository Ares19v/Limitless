"""
PDF processing service.
Uses pypdf (pure Python, cross-platform) for extraction and
LangChain text splitters for chunking.
"""

from __future__ import annotations

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
