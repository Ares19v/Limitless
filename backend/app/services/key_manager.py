"""
Groq Key + Model Manager — automatic fallback on 429 rate limit errors.

Strategy: Try primary model → fallback models → raise.
- llama-3.3-70b-versatile  (100K TPD — main model)
- llama-3.1-8b-instant     (separate 100K TPD quota — fast fallback)
- gemma2-9b-it             (separate 100K TPD quota — backup fallback)

Each model has its own independent daily token budget on Groq,
even on the same account. This gives ~300K effective tokens/day.
"""

from __future__ import annotations

import threading
from typing import List

from langchain_groq import ChatGroq

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

FALLBACK_MODELS = [
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
]


class GroqKeyManager:
    """
    Thread-safe LLM factory with automatic model fallback on 429.

    On each get_llm() call it uses the configured primary model.
    If that call returns a 429 during streaming, rag_chain catches it
    and calls get_llm_fallback() to get the next model in line.
    """

    def __init__(self, keys: List[str], primary_model: str):
        self._keys = keys
        self._primary_model = primary_model
        self._index = 0
        self._lock = threading.Lock()
        logger.info(
            "key_manager_ready",
            keys=len(keys),
            primary_model=primary_model,
            fallback_models=FALLBACK_MODELS,
        )

    def _next_key(self) -> str:
        with self._lock:
            key = self._keys[self._index % len(self._keys)]
            self._index += 1
            return key

    def _make_llm(self, model: str, **kwargs) -> ChatGroq:
        key = self._next_key()
        logger.info("groq_key_selected", hint=f"...{key[-6:]}", model=model)
        return ChatGroq(model=model, groq_api_key=key, **kwargs)

    def get_llm(self, **kwargs) -> ChatGroq:
        """Primary model LLM."""
        return self._make_llm(self._primary_model, **kwargs)

    def get_fallback_llm(self, failed_model: str, **kwargs) -> ChatGroq:
        """
        Return the next model after the one that just failed.
        Cycles through FALLBACK_MODELS in order.
        """
        try:
            idx = ([self._primary_model] + FALLBACK_MODELS).index(failed_model)
        except ValueError:
            idx = 0

        all_models = [self._primary_model] + FALLBACK_MODELS
        for i in range(idx + 1, len(all_models)):
            next_model = all_models[i]
            logger.warning(
                "groq_model_fallback",
                failed=failed_model,
                trying=next_model,
            )
            return self._make_llm(next_model, **kwargs)

        raise RuntimeError(f"All Groq models exhausted after failing on '{failed_model}'")


# ── Singleton ─────────────────────────────────────────────────────────────────

_manager: GroqKeyManager | None = None


def get_key_manager() -> GroqKeyManager:
    global _manager
    if _manager is None:
        settings = get_settings()
        _manager = GroqKeyManager(
            keys=settings.groq_api_keys,
            primary_model=settings.llm_model,
        )
    return _manager


def get_llm(streaming: bool = True, temperature: float = 0.1, max_tokens: int = 2048) -> ChatGroq:
    """Get a ChatGroq instance from the primary model."""
    return get_key_manager().get_llm(
        streaming=streaming,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_fallback_llm(
    failed_model: str,
    streaming: bool = True,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> ChatGroq:
    """Get a ChatGroq instance from the next fallback model."""
    return get_key_manager().get_fallback_llm(
        failed_model=failed_model,
        streaming=streaming,
        temperature=temperature,
        max_tokens=max_tokens,
    )
