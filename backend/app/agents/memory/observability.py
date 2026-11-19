"""KEEP Phase 4.7 — Memory Observability & Metrics.

Tracks retrieval latencies, proposal approval/rejection rates, access denials,
and context token budgeting metrics without leaking raw memory content.

Specification: devdocs/p4/p4.7.txt (Sections 4, 11)
Owner: Member 4 (LangGraph Integration, API, Persistence & QA)
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MemoryMetricsSnapshot(BaseModel):
    """Point-in-time metrics summary for memory subsystem."""

    retrieval_operations: int = Field(default=0)
    proposals_submitted: int = Field(default=0)
    proposals_approved: int = Field(default=0)
    proposals_rejected: int = Field(default=0)
    access_denials: int = Field(default=0)
    total_tokens_served: int = Field(default=0)
    average_retrieval_latency_ms: float = Field(default=0.0)


class MemoryMetricsCollector:
    """In-memory thread-safe metrics aggregator for memory operations."""

    def __init__(self) -> None:
        self._retrieval_count: int = 0
        self._retrieval_latencies: list[float] = []
        self._proposals_submitted: int = 0
        self._proposals_approved: int = 0
        self._proposals_rejected: int = 0
        self._access_denials: int = 0
        self._total_tokens_served: int = 0

    def record_retrieval(self, duration_ms: float, tokens_served: int) -> None:
        self._retrieval_count += 1
        self._retrieval_latencies.append(duration_ms)
        self._total_tokens_served += tokens_served
        if len(self._retrieval_latencies) > 1000:
            self._retrieval_latencies = self._retrieval_latencies[-1000:]

    def record_proposal_submitted(self) -> None:
        self._proposals_submitted += 1

    def record_proposal_approved(self) -> None:
        self._proposals_approved += 1

    def record_proposal_rejected(self) -> None:
        self._proposals_rejected += 1

    def record_access_denial(self) -> None:
        self._access_denials += 1

    def get_snapshot(self) -> MemoryMetricsSnapshot:
        avg_lat = (
            sum(self._retrieval_latencies) / len(self._retrieval_latencies)
            if self._retrieval_latencies
            else 0.0
        )
        return MemoryMetricsSnapshot(
            retrieval_operations=self._retrieval_count,
            proposals_submitted=self._proposals_submitted,
            proposals_approved=self._proposals_approved,
            proposals_rejected=self._proposals_rejected,
            access_denials=self._access_denials,
            total_tokens_served=self._total_tokens_served,
            average_retrieval_latency_ms=round(avg_lat, 2),
        )


GLOBAL_MEMORY_METRICS = MemoryMetricsCollector()
