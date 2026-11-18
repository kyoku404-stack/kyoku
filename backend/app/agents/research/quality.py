"""KEEP Phase 4.5 — Evidence Quality, Contradiction & Coverage Validator.

Implements `ResearchQualityInterface` to inspect synthesized research drafts for:
1. Citation integrity & claim-support grounding (`validate_evidence_references`)
2. Contradiction transparency (conflicting stances in evidence must be surfaced)
3. Temporal awareness (conflicting dated documents carry clear temporal warnings)
4. Coverage gap detection (identifying unanswered sub-parts as `unresolved_questions`)

Owner: Member 3 (Cross-Source Synthesis, Citations & Evidence Quality)
Specification: devdocs/p4/p4.5.txt (Sections 4.3, 5, 6, 7)
"""

from __future__ import annotations

from collections import defaultdict

from backend.app.agents.research.citations import validate_evidence_references
from backend.app.agents.research.contracts import (
    EvidenceItem,
    QualityCheckResult,
    ResearchRequest,
    SynthesisDraft,
)


def detect_evidence_stance_conflicts(
    evidence: list[EvidenceItem],
) -> dict[str, list[EvidenceItem]]:
    """Groups evidence items that express conflicting stances on the same topic."""
    by_topic: dict[str, list[EvidenceItem]] = defaultdict(list)
    for item in evidence:
        topic = item.metadata.get("stance_topic")
        stance = item.metadata.get("stance")
        if isinstance(topic, str) and topic.strip() and isinstance(stance, str) and stance.strip():
            by_topic[topic.strip()].append(item)

    conflicts: dict[str, list[EvidenceItem]] = {}
    for topic, items in by_topic.items():
        distinct_stances = {str(i.metadata.get("stance")) for i in items}
        if len(distinct_stances) >= 2:
            conflicts[topic] = items
    return conflicts


class ResearchQualityValidator:
    """Evaluates citation integrity, contradiction visibility, temporality, and coverage."""

    def validate(
        self,
        request: ResearchRequest,
        draft: SynthesisDraft,
        evidence: list[EvidenceItem],
    ) -> QualityCheckResult:
        citation_report = validate_evidence_references(draft.findings, evidence)
        issues = list(citation_report.issues)
        warnings: list[str] = []
        recommended_unresolved: list[str] = []

        # 1. Verify conflicting evidence stances are surfaced transparently
        stance_conflicts = detect_evidence_stance_conflicts(evidence)
        if stance_conflicts and not draft.contradictions:
            issues.append(
                "Retrieved evidence contains conflicting root-cause assessments that were not "
                "explicitly surfaced in `contradictions`."
            )

        # 2. Temporal awareness check for dated conflicting evidence
        if stance_conflicts:
            dated_items = [
                item for group in stance_conflicts.values() for item in group if item.document_date
            ]
            unique_dates = sorted({item.document_date for item in dated_items if item.document_date})
            if len(unique_dates) >= 2:
                warnings.append(
                    f"Conflicting sources span multiple dates ({', '.join(unique_dates)}); "
                    "newer postmortem records may supersede earlier retrospectives."
                )

        # 3. Single-source coverage caveat
        unique_sources = {item.source_id for item in evidence}
        if len(unique_sources) == 1:
            warnings.append(
                "Only one unique internal source matched this investigation; cross-source corroboration is limited."
            )
            recommended_unresolved.append(
                "Additional independent internal sources are needed to corroborate the single-source evidence."
            )

        # 4. Check for explicit sub-questions not addressed in evidence
        q_lower = request.question.lower()
        combined_text = " ".join(f"{e.source_title} {e.passage}" for e in evidence).lower()
        if "budget" in q_lower and "budget" not in combined_text and "$" not in combined_text:
            recommended_unresolved.append(
                "No authorized internal evidence documented financial or budget impact for this question."
            )
        if "forecast" in q_lower and "forecast" not in combined_text:
            recommended_unresolved.append(
                "Retrieved internal records do not contain forward-looking forecast figures."
            )

        return QualityCheckResult(
            is_valid=len(issues) == 0,
            invalid_citations=citation_report.invalid_citations,
            unsupported_findings=citation_report.unsupported_findings
            + citation_report.weakly_grounded_findings,
            issues=issues,
            warnings=warnings,
            recommended_unresolved_questions=recommended_unresolved,
        )
