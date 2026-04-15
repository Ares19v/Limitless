"""
Tests for the PDF processing service.
Verifies chunking, metadata extraction, and error handling.
Uses pypdf as the PDF reader.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from app.services.pdf_processor import (
    get_pdf_page_count,
    process_pdf,
    split_documents,
    _extract_text_with_metadata,
)


class TestSplitDocuments:
    """Test LangChain text splitter behavior."""

    def test_splits_large_document_into_multiple_chunks(self):
        """A document larger than chunk_size should produce multiple chunks."""
        long_text = "This is a test sentence. " * 200  # ~5000 chars
        docs = [Document(page_content=long_text, metadata={"page": 1})]
        chunks = split_documents(docs, chunk_size=500, chunk_overlap=50)
        assert len(chunks) > 1

    def test_small_document_stays_as_one_chunk(self):
        """A short document should not be split unnecessarily."""
        short_text = "Short document content."
        docs = [Document(page_content=short_text, metadata={"page": 1})]
        chunks = split_documents(docs, chunk_size=1000, chunk_overlap=100)
        assert len(chunks) == 1
        assert chunks[0].page_content == short_text

    def test_metadata_preserved_in_chunks(self):
        """Metadata from parent doc should be preserved in all chunks."""
        text = "Sentence one. Sentence two. " * 100
        docs = [Document(page_content=text, metadata={"page": 5, "source": "test.pdf"})]
        chunks = split_documents(docs, chunk_size=200, chunk_overlap=20)
        for chunk in chunks:
            assert chunk.metadata.get("page") == 5
            assert chunk.metadata.get("source") == "test.pdf"

    def test_empty_document_list_returns_empty(self):
        """Empty input should return empty output."""
        chunks = split_documents([])
        assert chunks == []

    def test_chunk_size_respected(self):
        """No chunk should significantly exceed chunk_size."""
        text = "word " * 1000
        docs = [Document(page_content=text, metadata={})]
        chunks = split_documents(docs, chunk_size=300, chunk_overlap=50)
        for chunk in chunks:
            assert len(chunk.page_content) <= 350


class TestPdfProcessor:
    """Tests for full PDF extraction pipeline."""

    def test_process_pdf_raises_on_nonexistent_file(self, tmp_path: Path):
        """Non-existent path should raise RuntimeError."""
        bad_path = tmp_path / "nonexistent.pdf"
        with pytest.raises(RuntimeError):
            process_pdf(bad_path)

    def test_process_pdf_raises_on_empty_content(self, tmp_path: Path):
        """PDF with no extractable text should raise ValueError."""
        blank_path = tmp_path / "blank.pdf"
        blank_path.write_bytes(b"dummy content")

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "   "  # Only whitespace

        with patch("app.services.pdf_processor.PdfReader") as mock_reader_cls:
            mock_reader = MagicMock()
            mock_reader.pages = [mock_page]
            mock_reader_cls.return_value = mock_reader

            with pytest.raises(ValueError, match="empty"):
                process_pdf(blank_path)

    def test_extract_returns_one_doc_per_page(self, tmp_path: Path):
        """Should return one Document per non-empty page."""
        path = tmp_path / "test.pdf"
        path.write_bytes(b"placeholder")

        mock_pages = []
        for i in range(3):
            p = MagicMock()
            p.extract_text.return_value = f"Content of page {i + 1}."
            mock_pages.append(p)

        with patch("app.services.pdf_processor.PdfReader") as mock_reader_cls:
            mock_reader = MagicMock()
            mock_reader.pages = mock_pages
            mock_reader_cls.return_value = mock_reader

            docs = _extract_text_with_metadata(path)
            assert len(docs) == 3
            for i, doc in enumerate(docs):
                assert doc.metadata["page"] == i + 1
                assert doc.metadata["total_pages"] == 3

    def test_get_pdf_page_count(self, tmp_path: Path):
        """Should return correct page count."""
        path = tmp_path / "test.pdf"
        path.write_bytes(b"placeholder")

        with patch("app.services.pdf_processor.PdfReader") as mock_reader_cls:
            mock_reader = MagicMock()
            mock_reader.pages = [MagicMock()] * 7
            mock_reader_cls.return_value = mock_reader

            count = get_pdf_page_count(path)
            assert count == 7
