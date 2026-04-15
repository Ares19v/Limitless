"""
RAG chain using Groq LLM with streaming via SSE.
v2: Hybrid search (BM25 + Pinecone) → Cross-encoder re-ranking → Groq streaming.
"""

from __future__ import annotations

import json
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from langchain_groq import ChatGroq

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import ChatMessage, SourceChunk
from app.services.key_manager import get_llm as get_groq_llm
from app.services.reranker import rerank
from app.services.vector_store import global_similarity_search, hybrid_similarity_search

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are Limitless, an expert AI assistant specialized in answering questions
about documents. You have been provided with relevant excerpts from a PDF document.

Guidelines:
- Answer questions accurately based ONLY on the provided document context.
- If the answer cannot be found in the context, clearly state that.
- Cite the page numbers when mentioning specific information (e.g., "According to page 3...").
- Format your response with clear markdown: use **bold** for key terms, bullet lists for multiple items.
- Be concise but thorough. Avoid unnecessary padding.
- If code or technical content is present, use code blocks.
"""


def _build_context_prompt(sources: List[SourceChunk]) -> str:
    parts = []
    for i, src in enumerate(sources, 1):
        page_info = f" (Page {src.page})" if src.page else ""
        parts.append(f"--- Excerpt {i}{page_info} ---\n{src.content}\n")
    return "\n".join(parts)


def _build_messages(context: str, user_message: str, history: List[ChatMessage]) -> List[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history[-10:]:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({
        "role": "user",
        "content": f"Context from the document:\n{context}\n\nUser question: {user_message}",
    })
    return messages



async def generate_summary(chunks: List[SourceChunk]) -> str:
    """Auto-summarize a document using the first few chunks."""
    sample_text = "\n\n".join(c.content for c in chunks[:5])

    llm = get_groq_llm(streaming=False, max_tokens=300)

    summary_prompt = [
        {"role": "system", "content": "You are a document summarizer. Be concise."},
        {
            "role": "user",
            "content": (
                f"Summarize this document excerpt in exactly 3 short bullet points "
                f"(each starting with •). Focus on the key topic and purpose.\n\n{sample_text}"
            ),
        },
    ]

    try:
        response = await llm.ainvoke(summary_prompt)
        return response.content.strip()
    except Exception as exc:
        logger.warning("summary_failed", error=str(exc))
        return ""


async def stream_rag_response(
    document_id: UUID,
    user_message: str,
    history: Optional[List[ChatMessage]] = None,
) -> AsyncGenerator[str, None]:
    """
    Full v2 RAG pipeline:
    1. Hybrid search (BM25 + Pinecone) → 15 candidates
    2. Cross-encoder re-ranking → top 5
    3. Stream Groq LLM response via SSE
    4. Persist messages to SQLite
    """
    settings = get_settings()
    history = history or []

    # Step 1: Hybrid retrieval
    candidates = await hybrid_similarity_search(document_id, user_message, top_k=15)

    if not candidates:
        yield "data: I could not find any relevant information in the document for your question.\n\n"
        yield "event: sources\ndata: []\n\n"
        yield "event: done\ndata: [DONE]\n\n"
        return

    # Step 2: Re-rank candidates to top 5
    sources = rerank(user_message, candidates, top_k=5)

    # Step 3: Build prompt and stream
    context = _build_context_prompt(sources)
    messages = _build_messages(context, user_message, history)

    llm = get_groq_llm(streaming=True)
    logger.info(
        "rag_stream_start",
        document_id=str(document_id),
        candidates=len(candidates),
        reranked=len(sources),
    )

    full_answer = ""
    try:
        async for chunk in llm.astream(messages):
            token = chunk.content
            if token:
                full_answer += token
                yield f"data: {token}\n\n"
    except Exception as exc:
        logger.error("rag_stream_error", error=str(exc))
        yield f"data: ❌ An error occurred: {str(exc)}\n\n"
    finally:
        # Persist to conversation history
        try:
            from app.services.document_store import save_message
            await save_message(document_id, "user", user_message)
            if full_answer:
                await save_message(document_id, "assistant", full_answer)
        except Exception as exc:
            logger.warning("history_save_failed", error=str(exc))

        sources_data = [
            {"content": s.content[:200], "page": s.page, "score": s.score}
            for s in sources
        ]
        yield f"event: sources\ndata: {json.dumps(sources_data)}\n\n"
        yield "event: done\ndata: [DONE]\n\n"
        logger.info("rag_stream_complete", document_id=str(document_id))


async def stream_global_rag_response(
    user_message: str,
) -> AsyncGenerator[str, None]:
    """
    Cross-document RAG: searches all documents, no namespace filter.
    Identified by document_id prefix in chunk content.
    """
    settings = get_settings()

    sources = await global_similarity_search(user_message, top_k=10)

    if not sources:
        yield "data: No relevant information found across any of your documents.\n\n"
        yield "event: done\ndata: [DONE]\n\n"
        return

    context = _build_context_prompt(sources)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\nNote: Excerpts may come from multiple documents."},
        {"role": "user", "content": f"Context from documents:\n{context}\n\nQuestion: {user_message}"},
    ]

    llm = get_groq_llm(streaming=True)
    logger.info("global_rag_start", sources=len(sources))

    try:
        async for chunk in llm.astream(messages):
            token = chunk.content
            if token:
                yield f"data: {token}\n\n"
    except Exception as exc:
        logger.error("global_rag_error", error=str(exc))
        yield f"data: ❌ An error occurred: {str(exc)}\n\n"
    finally:
        sources_data = [{"content": s.content[:200], "page": s.page, "score": s.score} for s in sources]
        yield f"event: sources\ndata: {json.dumps(sources_data)}\n\n"
        yield "event: done\ndata: [DONE]\n\n"
