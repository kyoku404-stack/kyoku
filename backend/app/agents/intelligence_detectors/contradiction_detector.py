"""Phase 4.11 — Contradiction Detector.

Identifies incompatible statements across policies, documents, or versions
using deterministic numeric/polarity/directive conflict checks.
"""

from __future__ import annotations

import re
from typing import Any

from backend.app.agents.intelligence.contracts import (
    EvidenceReference,
    IntelligenceCandidate,
)

_NEGATION_WORDS = ("never", "prohibited", "forbidden", "must not", "cannot", "disabled")
_AFFIRMATION_WORDS = ("required", "mandatory", "must", "always", "enabled")


class ContradictionDetector:
    """Deterministic cross-document and cross-policy contradiction detector."""

    detector_id: str = "contradiction_detector"
    version: str = "1.0.0"

    async def detect(
        self,
        observation: dict[str, Any],
        security_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        sources = observation.get("compare_sources") or []
        if len(sources) < 2:
            return []

        results: list[dict[str, Any]] = []
        primary = sources[0]
        p_ref = str(primary.get("resource_ref") or "doc:primary")
        p_text = str(primary.get("text") or "").lower()
        p_nums = re.findall(r"\b(\d+)\s*(days?|hours?|months?|years?|%)\b", p_text)

        for other in sources[1:]:
            o_ref = str(other.get("resource_ref") or "doc:secondary")
            o_text = str(other.get("text") or "").lower()
            o_nums = re.findall(r"\b(\d+)\s*(days?|hours?|months?|years?|%)\b", o_text)

            conflict_reason: str | None = None
            p_neg = any(w in p_text for w in _NEGATION_WORDS)
            o_aff = any(w in o_text for w in _AFFIRMATION_WORDS)
            p_aff = any(w in p_text for w in _AFFIRMATION_WORDS)
            o_neg = any(w in o_text for w in _NEGATION_WORDS)

            if (p_neg and o_aff) or (p_aff and o_neg):
                conflict_reason = "Opposite normative directives detected (prohibition vs requirement)."
            elif p_nums and o_nums:
                p_by_unit = {u.rstrip("s"): n for n, u in p_nums}
                o_by_unit = {u.rstrip("s"): n for n, u in o_nums}
                for unit, p_val in p_by_unit.items():
                    if unit in o_by_unit and o_by_unit[unit] != p_val:
                        conflict_reason = (
                            f"Incompatible numeric thresholds: {p_val} {unit}(s) vs {o_by_unit[unit]} {unit}(s)."
                        )
                        break

            if not conflict_reason:
                continue

            topic = str(observation.get("title") or observation.get("topic") or "Policy Guidance")
            cand = IntelligenceCandidate(
                category="contradiction",
                title=f"Conflicting guidance detected on {topic[:100]}",
                summary=f"{conflict_reason} Sources '{p_ref}' and '{o_ref}' disagree.",
                observed_facts=[
                    f"Source A ({p_ref}): {str(primary.get('text', ''))[:160]}",
                    f"Source B ({o_ref}): {str(other.get('text', ''))[:160]}",
                ],
                inferred_explanation="Conflicting operational policies may cause inconsistent compliance behavior.",
                evidence_refs=[p_ref, o_ref],
                evidence_details=[
                    EvidenceReference(
                        resource_ref=p_ref,
                        source_type="document",
                        source_version=primary.get("version"),
                        snippet=str(primary.get("text", ""))[:240],
                    ),
                    EvidenceReference(
                        resource_ref=o_ref,
                        source_type="document",
                        source_version=other.get("version"),
                        snippet=str(other.get("text", ""))[:240],
                    ),
                ],
                affected_resource_refs=[p_ref, o_ref],
                impact_score=0.90,
                relevance_score=0.85,
                evidence_quality_score=0.90,
                urgency_score=0.82,
                novelty_score=0.85,
                confidence_score=0.86,
                limitations=["Automated comparison flags structural disagreement; human policy owner review advised."],
                detector_id=self.detector_id,
                detector_version=self.version,
                audience_roles=list(observation.get("audience_roles") or []),
                dedup_hint=f"contradiction:{min(p_ref, o_ref)}:{max(p_ref, o_ref)}",
            )
            results.append(cand.model_dump())

        return results
