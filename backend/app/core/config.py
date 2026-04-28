"""
Core configuration using pydantic-settings.
All values are read from environment variables / .env file.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # Groq LLM
    groq_api_key: str = Field(..., description="Primary Groq API key")
    groq_api_key_pool: str = Field("", description="Comma-separated Groq API keys for rotation")
    llm_model: str = Field("llama-3.3-70b-versatile", description="Groq LLM model")

    # Pinecone Vector Store
    pinecone_api_key: str = Field(..., description="Pinecone API key")
    pinecone_index_name: str = Field("documind", description="Pinecone index name")

    # HuggingFace Embeddings (local, no API key needed)
    embedding_model: str = Field("all-MiniLM-L6-v2")
    embedding_dimension: int = Field(384, description="Must match the Pinecone index dimension")

    # RAG parameters
    chunk_size: int = Field(1000, ge=100, le=8000)
    chunk_overlap: int = Field(200, ge=0, le=1000)
    top_k_results: int = Field(5, ge=1, le=20)

    # Upload
    max_upload_size_mb: int = Field(50, ge=1, le=500)
    upload_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "uploads"
    )

    # SQLite document metadata store
    db_path: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "data" / "limitless.db"
    )

    # CORS — stored as comma-separated string; use allowed_origins property to get list
    # Note: we use str here so pydantic-settings does NOT attempt json.loads on it
    allowed_origins_raw: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        alias="ALLOWED_ORIGINS",
    )

    # App
    app_name: str = "Limitless API"
    app_version: str = "2.0.0"
    debug: bool = False

    @field_validator("upload_dir", mode="before")
    @classmethod
    def resolve_upload_dir(cls, v) -> Path:
        p = Path(v).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @field_validator("db_path", mode="before")
    @classmethod
    def resolve_db_path(cls, v) -> Path:
        p = Path(v).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def allowed_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins_raw.split(",") if o.strip()]

    @property
    def groq_api_keys(self) -> List[str]:
        """Return all Groq keys from the pool, falling back to primary key."""
        if self.groq_api_key_pool:
            keys = [k.strip() for k in self.groq_api_key_pool.split(",") if k.strip()]
            if keys:
                return keys
        return [self.groq_api_key]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
