"""Phase 4.11 — Significant Change Detector.

Compares a new document version with its previous version to surface material
changes in policies, deadlines, figures, or requirements with verified diffs.
"""

from __future__ import annotations

import re
from typing import Any

from backend.app.agents.intelligence.contracts import (
    EvidenceReference,
    IntelligenceCandidate,
)

_NUMBER_OR_DATE_RE = re.compile(r"\b\d+(?:\.\d+)?%?\b")
_POLICY_KEYWORDS = (
    "must",
    "shall",
    "required",
    "prohibited",
    "deadline",
    "retention",
    "days",
    "sla",
    "compliance",
    "approval",
    "encryption",
)


class SignificantChangeDetector:
    """Deterministic document version comparison detector."""

    detector_id: str = "significant_change_detector"
    version: str = "1.0.0"

    async def detect(
        self,
        observation: dict[str, Any],
        security_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if observation.get("kind") not in (None, "document_version", "document_change", "knowledge_update"):
            return []

        previous_text = str(observation.get("previous_content") or "").strip()
        current_text = str(observation.get("current_content") or "").strip()
        if not previous_text or not current_text or previous_text == current_text:
            return []

        doc_id = str(observation.get("document_id") or observation.get("resource_id") or "unknown")
        doc_title = str(observation.get("title") or f"Document {doc_id}")
        prev_ver = str(observation.get("previous_version") or "v1")
        curr_ver = str(observation.get("current_version") or "v2")

        prev_lines = {line.strip() for line in previous_text.splitlines() if line.strip()}
        curr_lines = {line.strip() for line in current_text.splitlines() if line.strip()}
        removed = sorted(prev_lines - curr_lines)
        added = sorted(curr_lines - prev_lines)

        prev_nums = set(_NUMBER_OR_DATE_RE.findall(previous_text))
        curr_nums = set(_NUMBER_OR_DATE_RE.findall(current_text))
        changed_figures = prev_nums.symmetric_difference(curr_nums)

        combined_diff = " ".join(added + removed).lower()
        keyword_hits = [kw for kw in _POLICY_KEYWORDS if kw in combined_diff]

        if not added and not removed:
            return []

        is_material = bool(changed_figures or keyword_hits or len(added) + len(removed) >= 2)
        if not is_material:
            return []

        impact = 0.85 if (changed_figures and keyword_hits) else 0.72 if keyword_hits else 0.60
        urgency = 0.78 if any(k in keyword_hits for k in ("deadline", "sla", "retention", "compliance")) else 0.55

        facts = [
            f"Removed/modified clauses ({prev_ver}): {removed[0][:180]}" if removed else f"Updated from {prev_ver}.",
            f"Added/new clauses ({curr_ver}): {added[0][:180]}" if added else f"Updated to {curr_ver}.",
        ]
        if changed_figures:
            facts.append(f"Changed numeric values/thresholds: {', '.join(sorted(changed_figures)[:5])}.")

        ref_prev = f"doc:{doc_id}:{prev_ver}"
        ref_curr = f"doc:{doc_id}:{curr_ver}"
        cand = IntelligenceCandidate(
            category="significant_change",
            title=f"Material update detected in {doc_title} ({prev_ver} -> {curr_ver})",
            summary=(
                f"{doc_title} changed between {prev_ver} and {curr_ver}"
                + (f" affecting {', '.join(keyword_hits[:3])}." if keyword_hits else ".")
            ),
            observed_facts=facts,
            inferred_explanation=(
                "Policy or numeric threshold updates may impact downstream workflows and team guidance."
            ),
            evidence_refs=[ref_prev, ref_curr],
            evidence_details=[
                EvidenceReference(
                    resource_ref=ref_prev,
                    source_type="document_version",
                    source_version=prev_ver,
                    snippet=removed[0][:240] if removed else previous_text[:240],
                ),
                EvidenceReference(
                    resource_ref=ref_curr,
                    source_type="document_version",
                    source_version=curr_ver,
                    snippet=added[0][:240] if added else current_text[:240],
                ),
            ],
            affected_resource_refs=[f"doc:{doc_id}"],
            impact_score=impact,
            relevance_score=float(observation.get("relevance_score", 0.82)),
            evidence_quality_score=0.92,
            urgency_score=urgency,
            novelty_score=0.88,
            confidence_score=0.90,
            detector_id=self.detector_id,
            detector_version=self.version,
            audience_roles=list(observation.get("audience_roles") or []),
            dedup_hint=f"change:{doc_id}:{prev_ver}:{curr_ver}",
        )
        return [cand.model_dump()]
