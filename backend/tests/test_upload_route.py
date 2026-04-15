"""Tests for upload route — mocks Pinecone and SQLite interactions."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


class TestUploadRoute:
    """Integration tests for /api/v1/upload."""

    def test_rejects_non_pdf(self, client: TestClient):
        """Returns 422 for non-PDF files."""
        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 422

    def test_rejects_empty_file(self, client: TestClient):
        """Returns 422 for empty files."""
        response = client.post(
            "/api/v1/upload",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert response.status_code == 422

    def test_accepts_valid_pdf(self, client: TestClient, sample_pdf_bytes: bytes):
        """Valid PDF is accepted with 202 and returns a document_id."""
        with (
            patch("app.api.routes.upload.create_document", new_callable=AsyncMock),
            patch("app.api.routes.upload._process_and_embed", new_callable=AsyncMock),
        ):
            response = client.post(
                "/api/v1/upload",
                files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
            )

        assert response.status_code == 202
        data = response.json()
        assert "document_id" in data
        assert data["filename"] == "test.pdf"

    def test_health_endpoint(self, client: TestClient):
        """Health check returns 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"
