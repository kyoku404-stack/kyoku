"""KEEP Phase 4.7 — Memory Relevance Ranking & Context Budgeting.

Implements lexical token-overlap scoring, recency decay weighting, source
confidence calibration, deduplication, and context token budgeting.

Specification: devdocs/p4/p4.7.txt (Sections 4, 7)
Owner: Member 2 (Retrieval, Relevance & Consolidation)
"""

from __future__ import annotations

import datetime
import math
import re

from backend.app.agents.memory.contracts import MemoryRecord

_TOKEN_PATTERN = re.compile(r"\w+")


def tokenize(text: str) -> set[str]:
    """Extracts lowercase word tokens from text."""
    return set(_TOKEN_PATTERN.findall(text.lower()))


class MemoryRanker:
    """Ranks and budgets candidate memories for agent execution context."""

    def __init__(
        self,
        *,
        lexical_weight: float = 0.7,
        recency_weight: float = 0.3,
        half_life_days: float = 30.0,
        min_recency_floor: float = 0.2,
    ) -> None:
        self.lexical_weight = lexical_weight
        self.recency_weight = recency_weight
        self.half_life_days = max(1.0, half_life_days)
        self.min_recency_floor = min_recency_floor

    def compute_lexical_similarity(self, query_tokens: set[str], doc_tokens: set[str]) -> float:
        """Computes Jaccard / token-overlap similarity between query and memory content."""
        if not query_tokens or not doc_tokens:
            return 0.0
        intersection = query_tokens.intersection(doc_tokens)
        union = query_tokens.union(doc_tokens)
        if not union:
            return 0.0
        # Blend intersection ratio over query tokens (coverage) and overall Jaccard
        query_coverage = len(intersection) / len(query_tokens)
        jaccard = len(intersection) / len(union)
        return (0.7 * query_coverage) + (0.3 * jaccard)

    def compute_recency_factor(
        self,
        record: MemoryRecord,
        now: datetime.datetime | None = None,
    ) -> float:
        """Computes exponential recency decay factor e^(-lambda * days)."""
        current_time = now or datetime.datetime.now(datetime.UTC)
        reference_time = record.updated_at or record.created_at

        # Guard against future timestamps
        if reference_time > current_time:
            delta_days = 0.0
        else:
            delta_days = (current_time - reference_time).total_seconds() / 86400.0

        decay_constant = math.log(2) / self.half_life_days
        raw_factor = math.exp(-decay_constant * delta_days)

        # User preferences degrade slower and maintain a higher floor
        if record.scope == "user":
            return max(self.min_recency_floor + 0.3, min(1.0, raw_factor))
        return max(self.min_recency_floor, min(1.0, raw_factor))

    def score(
        self,
        query: str,
        record: MemoryRecord,
        now: datetime.datetime | None = None,
    ) -> float:
        """Calculates a composite score combining relevance, recency, and confidence."""
        query_tokens = tokenize(query)
        doc_tokens = tokenize(record.content)
        # Also include memory_type and scope in tokens
        doc_tokens.add(record.memory_type.lower())
        doc_tokens.add(record.scope.lower())

        lexical_sim = self.compute_lexical_similarity(query_tokens, doc_tokens)
        recency = self.compute_recency_factor(record, now)

        if not query_tokens:
            base_score = recency
        else:
            base_score = (self.lexical_weight * lexical_sim) + (self.recency_weight * recency)

        # Scale by source confidence
        final_score = base_score * max(0.1, record.confidence)
        return round(final_score, 4)

    def rank(
        self,
        query: str,
        memories: list[MemoryRecord],
        *,
        limit: int = 5,
        max_tokens: int = 1000,
        min_confidence: float = 0.0,
        now: datetime.datetime | None = None,
    ) -> list[tuple[MemoryRecord, float]]:
        """Filters, scores, sorts, and applies context token budget to memories."""
        candidates = [m for m in memories if m.is_active and m.confidence >= min_confidence]

        scored: list[tuple[MemoryRecord, float]] = []
        for memory in candidates:
            score_val = self.score(query, memory, now)
            scored.append((memory, score_val))

        # Sort descending by score, then recency
        scored.sort(
            key=lambda item: (item[1], item[0].updated_at or item[0].created_at),
            reverse=True,
        )

        budgeted: list[tuple[MemoryRecord, float]] = []
        cumulative_tokens = 0

        for memory, score_val in scored:
            mem_tokens = memory.estimated_tokens
            if cumulative_tokens + mem_tokens > max_tokens and budgeted:
                # Token budget exceeded for subsequent entries
                continue
            budgeted.append((memory, score_val))
            cumulative_tokens += mem_tokens
            if len(budgeted) >= limit:
                break

        return budgeted


def calculate_jaccard_similarity(text_a: str, text_b: str) -> float:
    """Helper to compute token Jaccard similarity between two texts."""
    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    return len(intersection) / len(union) if union else 0.0
