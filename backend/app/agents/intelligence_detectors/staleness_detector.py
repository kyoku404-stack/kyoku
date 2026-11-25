"""Phase 4.11 — Staleness Detector.

Detects documents or knowledge records exceeding configured review intervals,
distinguishing missing review dates from confirmed staleness.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from backend.app.agents.intelligence.contracts import (
    EvidenceReference,
    IntelligenceCandidate,
)


def detect_stale_document(
    last_reviewed_at: datetime | None,
    review_interval_days: int,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Deterministic staleness evaluator with strict timezone and policy bounds."""
    current = now or datetime.now(UTC)
    if review_interval_days < 1:
        raise ValueError("review_interval_days must be positive")
    if last_reviewed_at is None:
        return {
            "is_stale": True,
            "reason": "review_date_missing",
        }
    if last_reviewed_at.tzinfo is None:
        raise ValueError("last_reviewed_at must be timezone-aware")

    deadline = last_reviewed_at + timedelta(days=review_interval_days)
    return {
        "is_stale": current >= deadline,
        "reason": "review_interval_exceeded" if current >= deadline else "within_review_interval",
        "review_due_at": deadline.isoformat(),
    }


class StalenessDetector:
    """Detector flagging stale knowledge records based on policy review intervals."""

    detector_id: str = "staleness_detector"
    version: str = "1.0.0"

    async def detect(
        self,
        observation: dict[str, Any],
        security_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if observation.get("kind") not in ("staleness_check", "document_review", None):
            return []
        if "review_interval_days" not in observation:
            return []

        interval_days = int(observation["review_interval_days"])
        raw_reviewed = observation.get("last_reviewed_at")
        reviewed_dt: datetime | None = None
        if isinstance(raw_reviewed, datetime):
            reviewed_dt = raw_reviewed
        elif isinstance(raw_reviewed, str) and raw_reviewed:
            reviewed_dt = datetime.fromisoformat(raw_reviewed)

        outcome = detect_stale_document(reviewed_dt, interval_days)
        if not outcome["is_stale"]:
            return []

        doc_id = str(observation.get("document_id") or observation.get("resource_ref") or "unknown")
        ref = doc_id if ":" in doc_id else f"doc:{doc_id}"
        title = str(observation.get("title") or ref)
        reason_code = outcome["reason"]

        limitations = []
        if reason_code == "review_date_missing":
            limitations.append("Last-reviewed timestamp is missing; staleness is inferred from missing metadata.")

        cand = IntelligenceCandidate(
            category="stale_knowledge",
            title=f"Stale knowledge review needed for {title[:100]}",
            summary=(
                f"Resource '{ref}' triggered staleness check ({reason_code}) "
                f"against {interval_days}-day review policy."
            ),
            observed_facts=[
                f"Review policy interval: {interval_days} days",
                f"Staleness outcome: {reason_code}",
            ],
            inferred_explanation="Outdated operational guidance increases risk of inaccurate answers.",
            evidence_refs=[ref],
            evidence_details=[EvidenceReference(resource_ref=ref, source_type="document")],
            affected_resource_refs=[ref],
            impact_score=0.68 if reason_code == "review_interval_exceeded" else 0.52,
            relevance_score=0.75,
            evidence_quality_score=0.90 if reason_code == "review_interval_exceeded" else 0.65,
            urgency_score=0.65,
            novelty_score=0.70,
            confidence_score=0.92 if reason_code == "review_interval_exceeded" else 0.60,
            limitations=limitations,
            detector_id=self.detector_id,
            detector_version=self.version,
            audience_roles=list(observation.get("audience_roles") or []),
            dedup_hint=f"stale:{ref}:{reason_code}",
        )
        return [cand.model_dump()]
