"""
RAG chain using Groq LLM with streaming via SSE.
v2: Hybrid search (BM25 + Pinecone) → Cross-encoder re-ranking → Groq streaming.
v3: Adaptive Query Router (SIMPLE/MODERATE/COMPLEX) + Contextual Retrieval support.
"""

from __future__ import annotations

import json
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from langchain_groq import ChatGroq

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import ChatMessage, SourceChunk
from app.services.key_manager import get_fallback_llm, get_llm as get_groq_llm
from app.services.query_router import QueryComplexity, classify_query, get_retrieval_config
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


def _deduplicate_chunks(chunks: List[SourceChunk], max_chunks: int = 5) -> List[SourceChunk]:
    """Remove near-duplicate chunks using first-80-char fingerprint to prevent Groq loop detection."""
    seen: set[str] = set()
    unique: List[SourceChunk] = []
    for chunk in chunks:
        # Use first 80 chars as a fingerprint — catches overlapping chunks
        fingerprint = chunk.content[:80].strip().lower()
        if fingerprint not in seen:
            seen.add(fingerprint)
            unique.append(chunk)
        if len(unique) >= max_chunks:
            break
    return unique


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
    Full v3 RAG pipeline:
    1. Adaptive Query Router → classify complexity (SIMPLE/MODERATE/COMPLEX)
    2. Hybrid search (BM25 + Pinecone) → variable candidates based on complexity
    3. Cross-encoder re-ranking → top N (complexity-dependent)
    4. Stream Groq LLM response via SSE
    5. Persist messages to SQLite
    """
    settings = get_settings()
    history = history or []

    # Step 0: Classify query complexity and get retrieval config
    complexity, reason = classify_query(user_message)
    retrieval_cfg = get_retrieval_config(complexity)
    top_k_candidates = retrieval_cfg["top_k_candidates"]
    top_k_reranked = retrieval_cfg["top_k_reranked"]

    logger.info(
        "rag_query_routed",
        complexity=complexity.value,
        reason=reason,
        top_k_candidates=top_k_candidates,
        top_k_reranked=top_k_reranked,
    )

    # Step 1: Hybrid retrieval (depth based on complexity)
    candidates = await hybrid_similarity_search(document_id, user_message, top_k=top_k_candidates)

    if not candidates:
        yield "data: I could not find any relevant information in the document for your question.\n\n"
        yield "event: sources\ndata: []\n\n"
        yield "event: done\ndata: [DONE]\n\n"
        return

    # Step 2: Re-rank candidates (depth adaptive), then deduplicate
    sources = rerank(user_message, candidates, top_k=top_k_reranked)
    sources = _deduplicate_chunks(sources, max_chunks=top_k_reranked)

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
    current_model = get_settings().llm_model
    max_retries = 3  # primary + 2 fallbacks

    for attempt in range(max_retries):
        if attempt == 0:
            llm = get_groq_llm(streaming=True)
        else:
            try:
                llm = get_fallback_llm(failed_model=current_model, streaming=True)
                current_model = llm.model_name
                logger.warning("rag_retry_with_fallback", attempt=attempt, model=current_model)
            except RuntimeError:
                yield "data: ❌ All AI models are rate-limited. Please wait a few minutes and try again.\n\n"
                break

        try:
            async for chunk in llm.astream(messages):
                token = chunk.content
                if token:
                    full_answer += token
                    yield f"data: {token}\n\n"
            break  # success — exit retry loop
        except Exception as exc:
            err = str(exc)
            if "429" in err or "rate_limit" in err:
                logger.warning("rag_rate_limited", attempt=attempt, model=current_model)
                full_answer = ""  # reset for retry
                continue  # try next model
            elif "looping" in err.lower() or "loop detection" in err.lower():
                # Groq flagged the context as repetitive — retry with fewer, shorter chunks
                logger.warning("rag_loop_detected", attempt=attempt)
                if attempt == 0 and len(sources) > 3:
                    sources = sources[:3]  # reduce to 3 chunks and retry
                    context = _build_context_prompt(sources)
                    messages = _build_messages(context, user_message, history)
                    full_answer = ""
                    continue
                else:
                    yield "data: ⚠️ The document has highly repetitive content that prevented a clean response. Try asking a more specific question.\n\n"
                    break
            else:
                logger.error("rag_stream_error", error=err)
                yield f"data: ❌ An error occurred: {err}\n\n"
                break
    # Persist and finalize regardless of which model answered
    try:
        from app.services.document_store import save_message
        await save_message(document_id, "user", user_message)
        if full_answer:
            await save_message(document_id, "assistant", full_answer)
    except Exception as exc:
        logger.warning("history_save_failed", error=str(exc))

    sources_data = [
        {
            "content": s.content[:250],
            "page": s.page,
            "score": s.score,
            "bbox": getattr(s, "bbox", None),
            "context_prefix": getattr(s, "context_prefix", None),
        }
        for s in sources
    ]
    # Emit query metadata event (allows frontend to show routing info)
    meta = {
        "query_complexity": complexity.value,
        "candidates_retrieved": len(candidates),
        "sources_used": len(sources),
        "retrieval_description": retrieval_cfg.get("description", ""),
    }
    yield f"event: meta\ndata: {json.dumps(meta)}\n\n"
    yield f"event: sources\ndata: {json.dumps(sources_data)}\n\n"
    yield "event: done\ndata: [DONE]\n\n"
    logger.info("rag_stream_complete", document_id=str(document_id), complexity=complexity.value)


async def stream_global_rag_response(
    user_message: str,
) -> AsyncGenerator[str, None]:
    """
    Cross-document RAG: searches all documents, no namespace filter.
    Identified by document_id prefix in chunk content.
    """
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
