"""
FastAPI application entry point.
v2: Groq LLM + Pinecone vector store + SQLite document metadata.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import chat, documents, upload
from app.api.routes import global_chat, agent_chat, history, consensus, audio
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.models.schemas import ErrorResponse, HealthResponse
from app.services.document_store import init_db

# ── Bootstrap ─────────────────────────────────────────────────────────────────
settings = get_settings()
setup_logging(debug=settings.debug)
logger = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize SQLite DB on startup."""
    logger.info(
        "app_startup",
        name=settings.app_name,
        version=settings.app_version,
        llm=settings.llm_model,
        embedding=settings.embedding_model,
    )
    await init_db()
    logger.info("sqlite_initialized")
    yield
    logger.info("app_shutdown", name=settings.app_name)


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Limitless — PDF RAG API powered by Groq LLM + Pinecone vector store + "
        "HuggingFace embeddings (local, no OpenAI key required)"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(upload.router, prefix="/api/v1")
app.include_router(global_chat.router, prefix="/api/v1")  # MUST be before chat to avoid /chat/global matching /{document_id}
app.include_router(chat.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(agent_chat.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(consensus.router, prefix="/api/v1")    # Feature 3: Contradiction/Consensus Engine
app.include_router(audio.router, prefix="/api/v1")        # Feature 5: Audio Overview Generator


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        timestamp=datetime.now(tz=timezone.utc),
    )


# ── Global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=str(request.url), error=str(exc))
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="An internal error occurred.", code="INTERNAL_ERROR"
        ).model_dump(),
    )
