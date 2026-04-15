"""Cross-platform file handling utilities using pathlib."""

from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path
from typing import Tuple
from uuid import UUID

ALLOWED_MIME_TYPES = {"application/pdf"}
ALLOWED_EXTENSIONS = {".pdf"}


def validate_file(filename: str, content_type: str | None) -> Tuple[bool, str]:
    """Validate file extension and MIME type."""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return False, f"File type '{suffix}' not allowed. Only PDF files are accepted."

    if content_type and content_type.split(";")[0].strip() not in ALLOWED_MIME_TYPES:
        return False, f"MIME type '{content_type}' not allowed."

    return True, ""


def safe_filename(filename: str) -> str:
    """Sanitize filename for cross-platform safety (removes path separators)."""
    name = Path(filename).name
    # Replace any potentially problematic characters
    safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
    return safe


def get_upload_path(upload_dir: Path, document_id: UUID, filename: str) -> Path:
    """
    Build the upload file path using pathlib for cross-platform compat.
    Returns: upload_dir / <document_id> / <safe_filename>
    """
    doc_dir = upload_dir / str(document_id)
    doc_dir.mkdir(parents=True, exist_ok=True)
    return doc_dir / safe_filename(filename)


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file for deduplication."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def cleanup_upload(file_path: Path) -> None:
    """Remove an uploaded file and its parent directory if empty."""
    try:
        if file_path.exists():
            file_path.unlink()
        parent = file_path.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
    except OSError:
        pass
