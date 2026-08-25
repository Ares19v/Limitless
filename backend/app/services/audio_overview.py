"""
Audio Overview Generator — NotebookLM-style 2-host podcast synthesis.

Pipeline:
1. Retrieve top document chunks (RAPTOR L2 root + best leaf chunks)
2. LLM generates a structured Host A / Host B dialogue script (JSON)
3. Each turn synthesized to audio via gTTS (free, no API key needed)
   with different speeds/pitches to differentiate hosts
4. Audio segments stitched with silence gaps → final MP3

Endpoint: POST /api/v1/audio/{document_id}
Returns: audio/mpeg binary stream
"""

from __future__ import annotations

import asyncio
import io
import json
import tempfile
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from app.core.logging import get_logger
from app.models.schemas import SourceChunk

logger = get_logger(__name__)

# Dialogue turn type
DIALOGUE_SCHEMA = """
Return a JSON array of dialogue turns. Each turn:
{"speaker": "HOST_A" | "HOST_B", "text": "what they say (max 80 words per turn)"}

HOST_A: Curious, asks probing questions, reacts with wonder ("Wait, so you're saying...")
HOST_B: Expert, analytical, gives confident explanations ("Exactly, and what's fascinating is...")

Total script: 8-12 turns. Natural conversational flow. Start with HOST_A introducing the document.
"""


async def _generate_dialogue_script(llm, context: str, document_name: str) -> List[dict]:
    """Generate a structured 2-host dialogue script about the document."""
    prompt = [
        {
            "role": "system",
            "content": (
                "You are a podcast script writer. Create a natural, engaging 2-host discussion "
                "about the provided document. Make it educational but conversational.\n\n"
                f"Script format:{DIALOGUE_SCHEMA}"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Create a podcast script discussing: '{document_name}'\n\n"
                f"Key content from the document:\n{context[:3000]}\n\n"
                f"Generate the JSON dialogue script:"
            ),
        },
    ]
    try:
        response = await llm.ainvoke(prompt)
        text = response.content.strip()
        # Clean up markdown code blocks if present
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        # Find the JSON array
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return json.loads(text)
    except Exception as exc:
        logger.warning("dialogue_script_failed", error=str(exc))
        # Fallback minimal script
        return [
            {"speaker": "HOST_A", "text": f"Welcome! Today we're discussing {document_name}."},
            {"speaker": "HOST_B", "text": "Let me walk you through the key ideas in this document."},
            {"speaker": "HOST_A", "text": context[:200]},
        ]


def _synthesize_turn_gtts(text: str, speaker: str) -> bytes:
    """
    Synthesize a dialogue turn to audio using gTTS.
    HOST_A: slightly slower (tld='com.au') — curious tone
    HOST_B: standard speed (tld='com') — confident expert tone
    Returns raw MP3 bytes.
    """
    try:
        from gtts import gTTS
        tld = "com.au" if speaker == "HOST_A" else "com"
        tts = gTTS(text=text, lang="en", tld=tld, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception as exc:
        logger.warning("gtts_synthesis_failed", speaker=speaker, error=str(exc))
        return b""


def _stitch_audio_segments(segments: List[bytes], silence_ms: int = 400) -> bytes:
    """
    Concatenate MP3 audio segments with silence gaps between turns.
    Uses pydub if available, otherwise raw concatenation.
    """
    try:
        from pydub import AudioSegment

        combined = AudioSegment.empty()
        silence = AudioSegment.silent(duration=silence_ms)

        for i, seg_bytes in enumerate(segments):
            if not seg_bytes:
                continue
            try:
                seg = AudioSegment.from_mp3(io.BytesIO(seg_bytes))
                if i > 0:
                    combined += silence
                combined += seg
            except Exception as exc:
                logger.warning("segment_concat_failed", segment=i, error=str(exc))

        if len(combined) == 0:
            return b"".join(segments)

        output = io.BytesIO()
        combined.export(output, format="mp3", bitrate="128k")
        output.seek(0)
        return output.read()

    except ImportError:
        # pydub not available — raw concatenation (works but no silence gaps)
        logger.warning("pydub_not_available", message="Using raw MP3 concatenation")
        return b"".join(s for s in segments if s)


async def generate_audio_overview(
    document_id: UUID,
    document_name: str,
) -> bytes:
    """
    Full audio overview generation pipeline.
    Returns MP3 audio bytes of the 2-host podcast.
    """
    from app.services.key_manager import get_llm
    from app.services.vector_store import hybrid_similarity_search, _get_index, _document_namespace

    logger.info("audio_overview_start", doc_id=str(document_id))

    # Step 1: Retrieve rich context (prefer RAPTOR L2 root if available)
    index = _get_index()
    namespace = _document_namespace(document_id)

    # Try to get RAPTOR root summary first
    raptor_content = ""
    try:
        raptor_vec_result = index.fetch(
            ids=[f"{document_id}-raptor-l2-root"],
            namespace=namespace,
        )
        if raptor_vec_result.get("vectors"):
            for vec_id, vec_data in raptor_vec_result["vectors"].items():
                raptor_content = vec_data.get("metadata", {}).get("content", "")
                break
    except Exception as exc:
        logger.warning("raptor_root_fetch_failed", error=str(exc))

    # Get top leaf chunks for detail
    try:
        chunks = await hybrid_similarity_search(document_id, "main topic purpose overview", top_k=8)
        leaf_content = "\n\n".join(c.content[:400] for c in chunks[:6])
    except Exception as exc:
        logger.warning("audio_retrieval_failed", error=str(exc))
        leaf_content = ""

    context = (raptor_content + "\n\n---\n\n" + leaf_content).strip() or "No content available."

    # Step 2: Generate dialogue script
    llm = get_llm(streaming=False, max_tokens=900)
    script = await _generate_dialogue_script(llm, context, document_name)
    logger.info("dialogue_script_generated", turns=len(script))

    # Step 3: Synthesize each turn to audio (run in thread pool to avoid blocking)
    loop = asyncio.get_event_loop()
    audio_segments: List[bytes] = []

    for turn in script:
        speaker = turn.get("speaker", "HOST_A")
        text = turn.get("text", "").strip()
        if not text:
            continue
        seg = await loop.run_in_executor(
            None, _synthesize_turn_gtts, text, speaker
        )
        audio_segments.append(seg)
        await asyncio.sleep(0.1)  # Brief pause between synthesis calls

    if not audio_segments:
        raise RuntimeError("Audio synthesis produced no segments")

    # Step 4: Stitch all segments together
    final_audio = await loop.run_in_executor(
        None, _stitch_audio_segments, audio_segments
    )

    logger.info(
        "audio_overview_complete",
        doc_id=str(document_id),
        turns=len(audio_segments),
        size_kb=round(len(final_audio) / 1024, 1),
    )
    return final_audio
