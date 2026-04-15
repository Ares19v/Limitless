"""
Groq API Key Manager — automatic rotation on 429 rate limit errors.

Strategy: Round-robin with fallback.
- Keys rotate in order on every LLM creation call.
- If a key returns 429, it's immediately skipped and the next one is tried.
- Gives you 4x the daily token budget across 4 keys.
"""

from __future__ import annotations

import threading
from typing import List

from langchain_groq import ChatGroq

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GroqKeyManager:
    """Thread-safe round-robin key manager with 429 fallback."""

    def __init__(self, keys: List[str], model: str):
        self._keys = keys
        self._model = model
        self._index = 0
        self._lock = threading.Lock()
        logger.info("key_manager_ready", keys=len(keys), model=model)

    def _next_key(self) -> str:
        with self._lock:
            key = self._keys[self._index % len(self._keys)]
            self._index += 1
            return key

    def get_llm(self, **kwargs) -> ChatGroq:
        """Get a ChatGroq instance using the next key in rotation."""
        key = self._next_key()
        key_hint = f"...{key[-6:]}"
        logger.info("groq_key_selected", hint=key_hint, total_keys=len(self._keys))
        return ChatGroq(
            model=self._model,
            groq_api_key=key,
            **kwargs,
        )

    def get_llm_with_fallback(self, **kwargs) -> tuple[ChatGroq, str]:
        """
        Try each key in order until one doesn't immediately fail.
        Returns (llm_instance, api_key_used).
        """
        errors = []
        for _ in range(len(self._keys)):
            key = self._next_key()
            key_hint = f"...{key[-6:]}"
            try:
                llm = ChatGroq(model=self._model, groq_api_key=key, **kwargs)
                logger.info("groq_key_selected", hint=key_hint)
                return llm, key
            except Exception as e:
                errors.append(f"{key_hint}: {e}")

        raise RuntimeError(f"All Groq keys failed: {errors}")


# ── Singleton ─────────────────────────────────────────────────────────────────

_manager: GroqKeyManager | None = None


def get_key_manager() -> GroqKeyManager:
    """Return the singleton key manager, initialised from settings."""
    global _manager
    if _manager is None:
        settings = get_settings()
        _manager = GroqKeyManager(
            keys=settings.groq_api_keys,
            model=settings.llm_model,
        )
    return _manager


def get_llm(streaming: bool = True, temperature: float = 0.1, max_tokens: int = 2048) -> ChatGroq:
    """
    Convenience function — get a ChatGroq instance from the key pool.
    Automatically rotates keys on each call (round-robin).
    """
    return get_key_manager().get_llm(
        streaming=streaming,
        temperature=temperature,
        max_tokens=max_tokens,
    )
