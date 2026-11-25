"""Phase 4.11 — Emerging Trend Detector.

Detects repeated patterns across a defined time window relative to a measurable baseline,
always attaching caveats against reporting-volume bias.
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.intelligence.contracts import (
    EvidenceReference,
    IntelligenceCandidate,
)


class EmergingTrendDetector:
    """Deterministic time-window trend detector relative to baseline counts."""

    detector_id: str = "emerging_trend_detector"
    version: str = "1.0.0"

    async def detect(
        self,
        observation: dict[str, Any],
        security_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if observation.get("kind") != "trend_window":
            return []

        topic = str(observation.get("topic") or "").strip()
        current_count = int(observation.get("current_count", 0))
        baseline_count = float(observation.get("baseline_count", 0.0))
        window_days = int(observation.get("window_days", 7))
        min_ratio = float(observation.get("min_growth_ratio", 1.5))

        if not topic or baseline_count <= 0 or current_count < 3:
            return []

        ratio = current_count / baseline_count
        if ratio < min_ratio:
            return []

        refs = [str(r) for r in (observation.get("evidence_refs") or []) if r]
        cand = IntelligenceCandidate(
            category="emerging_trend",
            title=f"Emerging trend: '{topic[:100]}' up {ratio:.1f}x over {window_days}d",
            summary=(
                f"Observed {current_count} occurrences for '{topic}' in {window_days} days "
                f"compared to baseline {baseline_count:.1f}."
            ),
            observed_facts=[
                f"Current {window_days}-day count: {current_count}",
                f"Comparison baseline: {baseline_count:.1f} ({ratio:.2f}x)",
            ],
            inferred_explanation="Increased activity may indicate an emerging operational theme.",
            evidence_refs=refs,
            evidence_details=[EvidenceReference(resource_ref=r, source_type="knowledge_record") for r in refs],
            affected_resource_refs=[f"topic:{topic.lower().replace(' ', '_')[:64]}"],
            impact_score=min(1.0, 0.55 + 0.1 * min(ratio, 4.0)),
            relevance_score=0.78,
            evidence_quality_score=0.80 if refs else 0.50,
            urgency_score=0.60,
            novelty_score=0.85,
            confidence_score=0.78,
            limitations=[
                "Higher document/event volume may reflect improved reporting rather than underlying incidence growth."
            ],
            detector_id=self.detector_id,
            detector_version=self.version,
            allow_evidence_free=not bool(refs),
            audience_roles=list(observation.get("audience_roles") or []),
            dedup_hint=f"trend:{topic.lower()}:{window_days}",
        )
        return [cand.model_dump()]
