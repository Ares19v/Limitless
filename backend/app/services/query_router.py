"""
Adaptive Query Router — classifies query complexity and routes accordingly.

SIMPLE   → Direct LLM answer (no retrieval needed for basic facts)
MODERATE → Standard hybrid RAG (BM25 + Vector + Reranker, top_k=5)
COMPLEX  → Enhanced RAG (top_k=20, multi-step, expanded context)

This reduces token cost on simple queries and improves quality on complex ones.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)


class QueryComplexity(str, Enum):
    SIMPLE = "simple"      # Basic factual, one-hop, definitional
    MODERATE = "moderate"  # Multi-aspect, comparison, explanatory
    COMPLEX = "complex"    # Synthesis, multi-hop, cross-document, analytical


# ── Heuristic signals ──────────────────────────────────────────────────────────

_SIMPLE_PATTERNS = [
    r"^what is\b",
    r"^who (is|wrote|created|invented|authored)\b",
    r"^when (was|did|is)\b",
    r"^where (is|was|did)\b",
    r"^define\b",
    r"^what does .{1,30} (mean|stand for)\b",
    r"^how many\b",
    r"^list (the )?(key |main |top )?\d*\s*(points|topics|authors|dates)\b",
]

_COMPLEX_PATTERNS = [
    r"\bcompare\b",
    r"\bcontrast\b",
    r"\banalyze\b",
    r"\bcritically\b",
    r"\bimplications?\b",
    r"\btrade-?offs?\b",
    r"\beverything\b",
    r"\ball\b.{0,20}\b(mechanisms?|aspects?|components?|factors?)\b",
    r"\bsummarize (the )?(entire|whole|full|complete)\b",
    r"\bhow (do|does|did) .{5,} (interact|relate|connect|affect|influence)\b",
    r"\bwhy did\b.{5,}\band\b",
    r"\bacross (all|multiple|different) (documents?|files?|sources?)\b",
    r"\bcomprehensive\b",
    r"\bin depth\b",
    r"\bend.to.end\b",
]

_MODERATE_BOOST_PATTERNS = [
    r"\bhow (does|do|did)\b",
    r"\bexplain\b",
    r"\bdescribe\b",
    r"\bwhat (are|were) the (main|key|primary|core)\b",
    r"\bwhat (caused?|led to|resulted in)\b",
    r"\bwhy\b",
]


def _count_pattern_hits(text: str, patterns: list[str]) -> int:
    text_lower = text.lower()
    return sum(1 for p in patterns if re.search(p, text_lower))


def classify_query(query: str) -> Tuple[QueryComplexity, str]:
    """
    Classify query complexity using fast heuristics.
    Returns (complexity, reason) tuple.

    Heuristic scoring:
    - Word count
    - Presence of complex vs simple patterns
    - Conjunction density (and/or/but/while)
    - Question depth signals
    """
    query_stripped = query.strip()
    words = query_stripped.split()
    word_count = len(words)

    # Count conjunction density — more conjunctions = more complex intent
    conjunctions = len(re.findall(r"\b(and|or|but|while|whereas|however|also|additionally|furthermore)\b",
                                   query_stripped.lower()))

    simple_hits = _count_pattern_hits(query_stripped, _SIMPLE_PATTERNS)
    complex_hits = _count_pattern_hits(query_stripped, _COMPLEX_PATTERNS)
    moderate_hits = _count_pattern_hits(query_stripped, _MODERATE_BOOST_PATTERNS)

    # ── Decision logic ──────────────────────────────────────────────────────
    # COMPLEX signals:
    if complex_hits >= 1 or word_count >= 25 or conjunctions >= 3:
        complexity = QueryComplexity.COMPLEX
        reason = f"complex_hits={complex_hits}, words={word_count}, conjunctions={conjunctions}"

    # SIMPLE signals:
    elif simple_hits >= 1 and word_count <= 12 and conjunctions == 0 and moderate_hits == 0:
        complexity = QueryComplexity.SIMPLE
        reason = f"simple_hits={simple_hits}, words={word_count}"

    # MODERATE (default middle ground):
    else:
        complexity = QueryComplexity.MODERATE
        reason = f"moderate_hits={moderate_hits}, words={word_count}, conjunctions={conjunctions}"

    logger.info(
        "query_classified",
        complexity=complexity.value,
        reason=reason,
        preview=query_stripped[:60],
    )
    return complexity, reason


def get_retrieval_config(complexity: QueryComplexity) -> dict:
    """
    Returns retrieval hyperparameters based on query complexity.
    """
    configs = {
        QueryComplexity.SIMPLE: {
            "top_k_candidates": 5,
            "top_k_reranked": 2,
            "max_tokens": 300,
            "description": "Fast path: minimal retrieval for simple factual queries",
        },
        QueryComplexity.MODERATE: {
            "top_k_candidates": 12,
            "top_k_reranked": 5,
            "max_tokens": 800,
            "description": "Standard RAG: balanced retrieval + reranking",
        },
        QueryComplexity.COMPLEX: {
            "top_k_candidates": 15,   # was 25 — cross-encoder bottleneck at >20
            "top_k_reranked": 6,
            "max_tokens": 1500,
            "description": "Deep RAG: expanded retrieval with maximum context for complex synthesis",
        },
    }
    return configs[complexity]
