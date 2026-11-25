"""Phase 4.11 — Feedback Aggregation & Ranking Calibration Support."""

from __future__ import annotations

from backend.app.agents.intelligence.contracts import InsightFeedbackRecord
from backend.app.agents.intelligence.repository import BaseIntelligenceRepository


class InsightFeedbackService:
    """Aggregates feedback signals for ranking calibration and quality review."""

    def __init__(self, repository: BaseIntelligenceRepository) -> None:
        self._repository = repository

    async def summarize_feedback(
        self,
        tenant_id: str,
        insight_id: str | None = None,
    ) -> dict[str, int]:
        records: list[InsightFeedbackRecord] = await self._repository.list_feedback(
            tenant_id=tenant_id,
            insight_id=insight_id,
        )
        counts: dict[str, int] = {
            "useful": 0,
            "irrelevant": 0,
            "already_known": 0,
            "incorrect": 0,
            "needs_more_evidence": 0,
        }
        for rec in records:
            counts[rec.feedback] = counts.get(rec.feedback, 0) + 1
        return counts
