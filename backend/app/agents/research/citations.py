"""KEEP Phase 4.5 — Citation Integrity & Claim-Support Grounding Validation.

Enforces ADR-080 ("Evidence Before Conclusions"):
1. Every `evidence_id` cited by any finding MUST exist in the current run's
   authorized `EvidenceItem` set — fabricated or unknown IDs are rejected.
2. Every `factual` claim MUST cite at least one valid `evidence_id`.
3. Cited `factual` claims MUST exhibit meaningful lexical support overlap with
   their cited passage(s) so unsupported claims cannot masquerade as grounded.
4. `hypothesis` and `recommendation` claims are explicitly distinguished.

Owner: Member 3 (Cross-Source Synthesis, Citations & Evidence Quality)
Specification: devdocs/p4/p4.5.txt (Sections 4.3, 5, 6, 7)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from backend.app.agents.errors import ResearchCitationValidationError
from backend.app.agents.research.contracts import EvidenceItem, ResearchFinding

_WORD_RE = re.compile(r"[a-z0-9]{3,}")
_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "were",
        "was",
        "are",
        "have",
        "has",
        "had",
        "been",
        "into",
        "about",
        "their",
        "there",
        "which",
        "while",
        "after",
        "before",
        "during",
        "across",
        "based",
        "shows",
        "show",
        "reported",
        "report",
        "evidence",
        "source",
        "sources",
        "internal",
    }
)


def _content_tokens(text: str) -> set[str]:
    return {tok for tok in _WORD_RE.findall(text.lower()) if tok not in _STOPWORDS}


@dataclass(frozen=True)
class CitationValidationReport:
    """Structured result of verifying finding citations against collected evidence."""

    is_valid: bool
    invalid_citations: list[str] = field(default_factory=list)
    unsupported_findings: list[str] = field(default_factory=list)
    weakly_grounded_findings: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


def validate_evidence_references(
    findings: list[ResearchFinding],
    evidence: list[EvidenceItem],
    *,
    strict_raise: bool = False,
    min_grounding_overlap: int = 2,
) -> CitationValidationReport:
    """Verifies that all citations resolve to collected evidence and support factual claims."""
    evidence_by_id: dict[str, EvidenceItem] = {item.evidence_id: item for item in evidence}

    invalid_citations: list[str] = []
    unsupported_findings: list[str] = []
    weakly_grounded_findings: list[str] = []
    issues: list[str] = []

    for finding in findings:
        valid_items: list[EvidenceItem] = []
        for eid in finding.evidence_ids:
            if eid not in evidence_by_id:
                invalid_citations.append(eid)
                issues.append(
                    f"Finding '{finding.finding_id}' cites unknown or fabricated evidence_id '{eid}'."
                )
            else:
                valid_items.append(evidence_by_id[eid])

        if finding.claim_type == "factual":
            if not valid_items:
                unsupported_findings.append(finding.finding_id)
                issues.append(
                    f"Factual finding '{finding.finding_id}' lacks any valid supporting evidence_id."
                )
            else:
                claim_tokens = _content_tokens(finding.claim)
                cited_tokens: set[str] = set()
                for item in valid_items:
                    cited_tokens |= _content_tokens(f"{item.source_title} {item.passage}")
                overlap = claim_tokens & cited_tokens
                required = min(min_grounding_overlap, max(1, len(claim_tokens)))
                if len(overlap) < required:
                    weakly_grounded_findings.append(finding.finding_id)
                    issues.append(
                        f"Factual finding '{finding.finding_id}' is not sufficiently grounded in "
                        f"its cited evidence ({', '.join(finding.evidence_ids)})."
                    )

    report = CitationValidationReport(
        is_valid=len(issues) == 0,
        invalid_citations=list(dict.fromkeys(invalid_citations)),
        unsupported_findings=list(dict.fromkeys(unsupported_findings)),
        weakly_grounded_findings=list(dict.fromkeys(weakly_grounded_findings)),
        issues=issues,
    )
    if strict_raise and not report.is_valid:
        raise ResearchCitationValidationError(
            "; ".join(report.issues),
            details={
                "invalid_citations": report.invalid_citations,
                "unsupported_findings": report.unsupported_findings,
                "weakly_grounded_findings": report.weakly_grounded_findings,
            },
        )
    return report
