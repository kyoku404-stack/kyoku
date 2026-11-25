"""Phase 4.11 — Knowledge-Gap Detector.

Identifies recurring unanswered questions, low-evidence research runs,
or topics lacking authorized documentation.
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.intelligence.contracts import (
    EvidenceReference,
    IntelligenceCandidate,
)


class KnowledgeGapDetector:
    """Deterministic knowledge-gap detector from unanswered queries or low-evidence runs."""

    detector_id: str = "knowledge_gap_detector"
    version: str = "1.0.0"

    async def detect(
        self,
        observation: dict[str, Any],
        security_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if observation.get("kind") not in ("knowledge_gap", "unanswered_queries", "research_run"):
            return []

        topic = str(observation.get("topic") or observation.get("query") or "").strip()
        if not topic:
            return []

        unanswered_count = int(observation.get("unanswered_count", 0))
        evidence_count = int(observation.get("evidence_count", 0))
        min_threshold = int(observation.get("min_unanswered_threshold", 3))

        if unanswered_count < min_threshold and evidence_count > 0:
            return []

        refs = [str(r) for r in (observation.get("evidence_refs") or []) if r]
        if not refs and observation.get("run_id"):
            refs = [f"run:{observation['run_id']}"]

        limitations = [
            "Missing authoritative documentation prevents verified answers; human authoring is recommended."
        ]
        if not refs:
            limitations.append("Observation flagged a gap without specific source document pointers.")

        cand = IntelligenceCandidate(
            category="knowledge_gap",
            title=f"Knowledge gap identified for '{topic[:120]}'",
            summary=(
                f"Detected {unanswered_count} unanswered/low-evidence inquiries on '{topic}' "
                f"with {evidence_count} authorized supporting documents."
            ),
            observed_facts=[
                f"Unanswered query count: {unanswered_count}",
                f"Supporting authorized sources found: {evidence_count}",
            ],
            inferred_explanation=(
                "Users are repeatedly asking about a topic not adequately covered in current documentation."
            ),
            evidence_refs=refs,
            evidence_details=[
                EvidenceReference(resource_ref=r, source_type="research_run") for r in refs
            ],
            affected_resource_refs=[f"topic:{topic.lower().replace(' ', '_')[:64]}"],
            impact_score=min(1.0, 0.50 + 0.08 * min(unanswered_count, 5)),
            relevance_score=0.80,
            evidence_quality_score=0.75 if refs else 0.45,
            urgency_score=0.60,
            novelty_score=0.75,
            confidence_score=0.82 if refs else 0.60,
            limitations=limitations,
            detector_id=self.detector_id,
            detector_version=self.version,
            allow_evidence_free=True,
            audience_roles=list(observation.get("audience_roles") or []),
            dedup_hint=f"gap:{topic.lower().strip()}",
        )
        return [cand.model_dump()]
