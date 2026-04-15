"""Pytest configuration and shared fixtures for Groq + Pinecone + SQLite stack."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ── Patch env vars before any app import ─────────────────────────────────────
os.environ.setdefault("GROQ_API_KEY", "test-groq-key-xxxxxxxxxxxx")
os.environ.setdefault("PINECONE_API_KEY", "test-pinecone-key")
os.environ.setdefault("PINECONE_INDEX_NAME", "limitless-test")

from app.main import app


@pytest.fixture(scope="session")
def sample_pdf_bytes() -> bytes:
    """Minimal valid PDF for testing (contains extractable text)."""
    return b"""%PDF-1.4
1 0 obj<</Type /Catalog /Pages 2 0 R>>endobj
2 0 obj<</Type /Pages /Kids[3 0 R] /Count 1>>endobj
3 0 obj<</Type /Page /MediaBox[0 0 612 792] /Parent 2 0 R /Resources<</Font<</F1 4 0 R>>>>>>endobj
4 0 obj<</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>endobj
5 0 obj<</Length 44>>
stream
BT /F1 12 Tf 100 700 Td (Hello Limitless Test) Tj ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000347 00000 n
trailer<</Size 6 /Root 1 0 R>>
startxref
443
%%EOF"""


@pytest.fixture
def sample_pdf_path(tmp_path: Path, sample_pdf_bytes: bytes) -> Path:
    path = tmp_path / "test_document.pdf"
    path.write_bytes(sample_pdf_bytes)
    return path


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
