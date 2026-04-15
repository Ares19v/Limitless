"""
RAG chain using Groq LLM with streaming via SSE.
Retrieves chunks from Pinecone and streams Groq response token-by-token.
"""

from __future__ import annotations

import json
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from langchain_groq import ChatGroq

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import ChatMessage, SourceChunk
from app.services.vector_store import similarity_search

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are DocuMind, an expert AI assistant specialized in answering questions
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
    """Build a readable context block from retrieved Pinecone chunks."""
    parts = []
    for i, src in enumerate(sources, 1):
        page_info = f" (Page {src.page})" if src.page else ""
        parts.append(f"--- Excerpt {i}{page_info} ---\n{src.content}\n")
    return "\n".join(parts)


def _build_messages(
    context: str,
    user_message: str,
    history: List[ChatMessage],
) -> List[dict]:
    """Assemble the full message list for the Groq LLM."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add last 10 turns of conversation history
    for msg in history[-10:]:
        messages.append({"role": msg.role, "content": msg.content})

    # Append user message with injected context
    messages.append({
        "role": "user",
        "content": f"Context from the document:\n{context}\n\nUser question: {user_message}",
    })
    return messages


async def stream_rag_response(
    document_id: UUID,
    user_message: str,
    history: Optional[List[ChatMessage]] = None,
) -> AsyncGenerator[str, None]:
    """
    Full RAG pipeline with streaming:
    1. Embed query → Pinecone similarity search
    2. Build context prompt
    3. Stream Groq LLM response token-by-token via SSE
    """
    settings = get_settings()
    history = history or []

    # Step 1: Retrieve similar chunks from Pinecone
    sources = await similarity_search(document_id, user_message, top_k=settings.top_k_results)

    if not sources:
        yield "data: I could not find any relevant information in the document for your question.\n\n"
        yield "event: sources\ndata: []\n\n"
        yield "event: done\ndata: [DONE]\n\n"
        return

    # Step 2: Build prompt
    context = _build_context_prompt(sources)
    messages = _build_messages(context, user_message, history)

    # Step 3: Stream from Groq
    llm = ChatGroq(
        model=settings.llm_model,
        groq_api_key=settings.groq_api_key,
        streaming=True,
        temperature=0.1,
        max_tokens=2048,
    )

    logger.info(
        "rag_stream_start",
        document_id=str(document_id),
        sources_found=len(sources),
        model=settings.llm_model,
    )

    try:
        async for chunk in llm.astream(messages):
            token = chunk.content
            if token:
                yield f"data: {token}\n\n"

    except Exception as exc:
        logger.error("rag_stream_error", error=str(exc))
        yield f"data: ❌ An error occurred: {str(exc)}\n\n"

    finally:
        # Send source citations as a special SSE event
        sources_data = [
            {"content": s.content[:200], "page": s.page, "score": s.score}
            for s in sources
        ]
        yield f"event: sources\ndata: {json.dumps(sources_data)}\n\n"
        yield "event: done\ndata: [DONE]\n\n"
        logger.info("rag_stream_complete", document_id=str(document_id))
