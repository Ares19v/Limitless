"""
Consensus & Contradiction Engine — Elicit/Consensus-AI style claim analysis.

Given a question, retrieves relevant chunks across the document corpus,
runs stance classification per chunk (SUPPORTS / CONTRADICTS / NEUTRAL),
and returns a structured consensus analysis with percentage agreement.

Endpoint: POST /api/v1/consensus
"""

from __future__ import annotations

import json
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from app.core.logging import get_logger
from app.models.schemas import SourceChunk
from app.services.key_manager import get_llm
from app.services.vector_store import global_similarity_search, hybrid_similarity_search

logger = get_logger(__name__)


async def _classify_stance(llm, question: str, chunk_content: str) -> dict:
    """
    Zero-shot stance classification for a single chunk against the question/claim.
    Returns: {stance, confidence, key_finding, verbatim_snippet}
    """
    prompt = [
        {
            "role": "system",
            "content": (
                "You are a scientific evidence classifier. Given a question/claim and a document excerpt, "
                "classify whether the excerpt SUPPORTS, CONTRADICTS, or is NEUTRAL to the claim. "
                "Respond ONLY with a JSON object in this exact format:\n"
                '{"stance": "SUPPORTS"|"CONTRADICTS"|"NEUTRAL", '
                '"confidence": 0.0-1.0, '
                '"key_finding": "one sentence summary of this excerpt\'s position", '
                '"verbatim_snippet": "most relevant verbatim quote (max 120 chars)"}'
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question/Claim: {question}\n\n"
                f"Document Excerpt:\n{chunk_content[:600]}\n\n"
                f"Classify this excerpt's stance:"
            ),
        },
    ]
    try:
        response = await llm.ainvoke(prompt)
        text = response.content.strip()
        # Extract JSON from response (handle markdown code blocks)
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        return json.loads(text)
    except Exception as exc:
        logger.warning("stance_classification_failed", error=str(exc))
        return {
            "stance": "NEUTRAL",
            "confidence": 0.3,
            "key_finding": chunk_content[:100],
            "verbatim_snippet": chunk_content[:80],
        }


async def stream_consensus_analysis(
    question: str,
    document_id: Optional[UUID] = None,
) -> AsyncGenerator[str, None]:
    """
    Full consensus analysis pipeline:
    1. Retrieve top-K relevant chunks (single doc or global)
    2. Run parallel stance classification on each chunk
    3. Aggregate consensus statistics
    4. Stream structured SSE results
    """
    import asyncio

    yield f"data: {json.dumps({'type': 'status', 'message': 'Retrieving relevant evidence...'})}\n\n"

    # Step 1: Retrieve relevant chunks
    try:
        if document_id:
            chunks = await hybrid_similarity_search(document_id, question, top_k=12)
        else:
            chunks = await global_similarity_search(question, top_k=12)
    except Exception as exc:
        yield f"data: {json.dumps({'type': 'error', 'message': f'Retrieval failed: {exc}'})}\n\n"
        yield "event: done\ndata: [DONE]\n\n"
        return

    if not chunks:
        yield f"data: {json.dumps({'type': 'error', 'message': 'No relevant evidence found in documents.'})}\n\n"
        yield "event: done\ndata: [DONE]\n\n"
        return

    yield f"data: {json.dumps({'type': 'status', 'message': f'Analyzing {len(chunks)} evidence chunks...'})}\n\n"

    # Step 2: Parallel stance classification
    llm = get_llm(streaming=False, max_tokens=200)

    # Use asyncio.gather with small batches to avoid rate limiting
    BATCH_SIZE = 4
    all_results = []

    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[batch_start: batch_start + BATCH_SIZE]
        tasks = [_classify_stance(llm, question, chunk.content) for chunk in batch]
        try:
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            for chunk, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.warning("stance_failed_chunk", error=str(result))
                    result = {"stance": "NEUTRAL", "confidence": 0.3,
                              "key_finding": chunk.content[:100], "verbatim_snippet": ""}
                all_results.append({
                    "chunk_index": len(all_results),
                    "page": chunk.page,
                    "score": chunk.score,
                    **result,
                })
            # Stream partial progress
            yield f"data: {json.dumps({'type': 'progress', 'analyzed': len(all_results), 'total': len(chunks)})}\n\n"
        except Exception as exc:
            logger.warning("stance_batch_failed", error=str(exc))
        if batch_start + BATCH_SIZE < len(chunks):
            await asyncio.sleep(0.2)

    # Step 3: Aggregate statistics
    supports = [r for r in all_results if r["stance"] == "SUPPORTS"]
    contradicts = [r for r in all_results if r["stance"] == "CONTRADICTS"]
    neutral = [r for r in all_results if r["stance"] == "NEUTRAL"]

    total = len(all_results)
    consensus_pct = round((len(supports) / total) * 100, 1) if total > 0 else 0.0
    contradiction_pct = round((len(contradicts) / total) * 100, 1) if total > 0 else 0.0

    # Step 4: Generate synthesis with LLM
    evidence_summary = "\n".join([
        f"- [{r['stance']}] {r['key_finding']}" for r in all_results[:8]
    ])

    synthesis_prompt = [
        {
            "role": "system",
            "content": (
                "You are an evidence synthesis expert. Given a question and classified evidence, "
                "write a concise 2-3 sentence synthesis of what the evidence collectively says. "
                "Be objective. Mention if evidence is mixed or one-sided. Do not make up facts."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"Evidence ({len(supports)} supporting, {len(contradicts)} contradicting, {len(neutral)} neutral):\n"
                f"{evidence_summary}\n\n"
                f"Synthesis:"
            ),
        },
    ]

    synthesis = ""
    try:
        synth_llm = get_llm(streaming=False, max_tokens=250)
        response = await synth_llm.ainvoke(synthesis_prompt)
        synthesis = response.content.strip()
    except Exception as exc:
        logger.warning("synthesis_failed", error=str(exc))
        synthesis = f"Evidence analysis complete. {len(supports)} chunks support, {len(contradicts)} chunks contradict the claim."

    # Step 5: Stream final result
    final_result = {
        "type": "result",
        "question": question,
        "consensus_pct": consensus_pct,
        "contradiction_pct": contradiction_pct,
        "neutral_pct": round(100 - consensus_pct - contradiction_pct, 1),
        "total_chunks_analyzed": total,
        "synthesis": synthesis,
        "supports": supports[:5],  # Top 5 supporting evidence
        "contradicts": contradicts[:3],  # Top 3 contradicting evidence
        "neutral": neutral[:2],
    }

    yield f"data: {json.dumps(final_result)}\n\n"
    yield "event: done\ndata: [DONE]\n\n"

    logger.info(
        "consensus_analysis_complete",
        question_preview=question[:60],
        total=total,
        supports=len(supports),
        contradicts=len(contradicts),
        consensus_pct=consensus_pct,
    )
