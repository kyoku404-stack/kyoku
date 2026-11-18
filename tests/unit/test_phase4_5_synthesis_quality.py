"""KEEP Phase 4.5 — Member 3 Unit Tests: Synthesis, Citations & Evidence Quality."""

from __future__ import annotations

import pytest

from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import ResearchCitationValidationError
from backend.app.agents.research.citations import validate_evidence_references
from backend.app.agents.research.contracts import (
    EvidenceItem,
    ResearchFinding,
    ResearchRequest,
    SynthesisDraft,
)
from backend.app.agents.research.quality import ResearchQualityValidator
from backend.app.agents.research.retrieval import KeepResearchRetrievalService
from backend.app.agents.research.synthesis import KeepResearchSynthesisService


def _ctx() -> AgentContext:
    return AgentContext(
        user_id="u_analyst",
        tenant_id="org_alpha",
        roles=["member"],
        permissions={"agent.view", "agent.invoke"},
    )


def _sample_evidence() -> list[EvidenceItem]:
    return [
        EvidenceItem(
            evidence_id="ev_01",
            source_id="doc_payments_postmortem",
            source_title="Payments Gateway v3.4 Postmortem",
            passage="Payment gateway v3.4 retry storm caused 62% of Q4 billing complaints.",
            retrieval_reference="doc_payments_postmortem#chunk:1",
            relevance_score=0.92,
            document_date="2026-01-15",
            metadata={"stance_topic": "q4_root_cause", "stance": "payment_gateway"},
        ),
        EvidenceItem(
            evidence_id="ev_02",
            source_id="doc_support_retro",
            source_title="Support Escalation Retrospective",
            passage="Tier-2 support leads attributed Q4 complaints primarily to understaffed onboarding queues.",
            retrieval_reference="doc_support_retro#chunk:0",
            relevance_score=0.84,
            document_date="2026-01-05",
            metadata={"stance_topic": "q4_root_cause", "stance": "support_understaffing"},
        ),
    ]


def test_validate_evidence_references_rejects_fabricated_and_ungrounded_claims() -> None:
    evidence = _sample_evidence()

    fabricated = [
        ResearchFinding(
            finding_id="f_bad",
            claim="Payment gateway retry storm caused Q4 complaints.",
            claim_type="factual",
            evidence_ids=["ev_does_not_exist"],
            confidence="high",
        )
    ]
    report = validate_evidence_references(fabricated, evidence)
    assert report.is_valid is False
    assert "ev_does_not_exist" in report.invalid_citations
    assert "f_bad" in report.unsupported_findings

    with pytest.raises(ResearchCitationValidationError):
        validate_evidence_references(fabricated, evidence, strict_raise=True)

    # Weakly grounded claim citing a real evidence_id with unrelated topic
    unrelated = [
        ResearchFinding(
            finding_id="f_ungrounded",
            claim="Autonomous lunar rovers reduced satellite latency in orbit.",
            claim_type="factual",
            evidence_ids=["ev_01"],
            confidence="high",
        )
    ]
    weak_report = validate_evidence_references(unrelated, evidence)
    assert weak_report.is_valid is False
    assert "f_ungrounded" in weak_report.weakly_grounded_findings

    # Distinct hypothesis / recommendation without mandatory factual citation passes cleanly
    hypothesis = [
        ResearchFinding(
            finding_id="f_hyp",
            claim="Expanding automated billing telemetry could shorten triage cycles.",
            claim_type="recommendation",
            evidence_ids=["ev_01"],
            confidence="medium",
        )
    ]
    assert validate_evidence_references(hypothesis, evidence).is_valid is True


@pytest.mark.asyncio
async def test_synthesis_surfaces_contradictions_dates_and_valid_citations() -> None:
    retrieval = KeepResearchRetrievalService()
    synthesis = KeepResearchSynthesisService()
    validator = ResearchQualityValidator()

    req = ResearchRequest(
        question="Why did customer complaints increase last quarter and which internal teams were affected?",
        scope="Internal customer feedback and support records",
        required_output="detailed_report",
    )
    out = await retrieval.retrieve_evidence(req, _ctx())
    draft = await synthesis.synthesize(req, out.evidence, _ctx())

    assert draft.findings
    assert any(f.claim_type == "factual" for f in draft.findings)
    assert any(f.claim_type == "recommendation" for f in draft.findings)
    assert len(draft.contradictions) >= 1
    assert any(f.has_contradiction for f in draft.findings)
    assert draft.contradictions[0].source_dates == ["2026-01-05", "2026-01-15"]
    assert draft.unresolved_questions

    quality = validator.validate(req, draft, out.evidence)
    assert quality.is_valid is True
    assert quality.invalid_citations == []
    assert any("2026-01-05" in w and "2026-01-15" in w for w in quality.warnings)


@pytest.mark.asyncio
async def test_quality_validator_catches_hidden_contradiction_and_correction_repairs_it() -> None:
    evidence = _sample_evidence()
    validator = ResearchQualityValidator()
    synthesis = KeepResearchSynthesisService()
    req = ResearchRequest(question="What caused Q4 complaints and what was the budget impact?")

    flawed_draft = SynthesisDraft(
        summary="Incomplete draft hiding contradiction and citing fake ID.",
        findings=[
            ResearchFinding(
                finding_id="f_01",
                claim="Payment gateway v3.4 retry storm caused 62% of Q4 billing complaints.",
                claim_type="factual",
                evidence_ids=["ev_01", "ev_fake_99"],
                confidence="high",
            )
        ],
        contradictions=[],
    )

    first_check = validator.validate(req, flawed_draft, evidence)
    assert first_check.is_valid is False
    assert "ev_fake_99" in first_check.invalid_citations
    assert any("conflicting" in issue.lower() for issue in first_check.issues)
    assert any("budget" in q.lower() for q in first_check.recommended_unresolved_questions)

    repaired = await synthesis.correct_findings(req, flawed_draft, evidence, first_check.issues, _ctx())
    second_check = validator.validate(req, repaired, evidence)
    assert second_check.is_valid is True
    assert repaired.findings[0].evidence_ids == ["ev_01"]
    assert len(repaired.contradictions) == 1
