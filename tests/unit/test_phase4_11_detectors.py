"""Unit tests for Phase 4.11 Member 2: Detectors, Evidence Validation & Persistence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.app.agents.intelligence.contracts import (
    IntelligenceCandidate,
    IntelligenceSecurityContext,
)
from backend.app.agents.intelligence.evidence_validation import EvidenceValidator
from backend.app.agents.intelligence_detectors import (
    ContradictionDetector,
    EmergingTrendDetector,
    KnowledgeGapDetector,
    SignificantChangeDetector,
    StalenessDetector,
    build_default_detectors,
    detect_stale_document,
)


@pytest.mark.asyncio
async def test_significant_change_and_contradiction_detectors() -> None:
    change_det = SignificantChangeDetector()
    cands = await change_det.detect(
        {
            "kind": "document_version",
            "document_id": "pol-sec-1",
            "title": "Data Retention Policy",
            "previous_version": "v1",
            "current_version": "v2",
            "previous_content": "Audit logs must be retained for 90 days.",
            "current_content": "Audit logs must be retained for 30 days.",
        },
        {"tenant_id": "org_1"},
    )
    assert len(cands) == 1
    assert cands[0]["category"] == "significant_change"
    assert "doc:pol-sec-1:v1" in cands[0]["evidence_refs"]
    assert "doc:pol-sec-1:v2" in cands[0]["evidence_refs"]

    contra_det = ContradictionDetector()
    contra_cands = await contra_det.detect(
        {
            "topic": "MFA Enforcement",
            "compare_sources": [
                {"resource_ref": "doc:sec-a", "text": "Hardware keys are mandatory for all admins."},
                {"resource_ref": "doc:sec-b", "text": "Hardware keys are prohibited on contractor laptops."},
            ],
        },
        {"tenant_id": "org_1"},
    )
    assert len(contra_cands) == 1
    assert contra_cands[0]["category"] == "contradiction"


@pytest.mark.asyncio
async def test_staleness_knowledge_gap_and_trend_detectors() -> None:
    now = datetime(2026, 11, 25, tzinfo=UTC)
    stale = detect_stale_document(now - timedelta(days=100), 90, now=now)
    assert stale["is_stale"] is True
    assert stale["reason"] == "review_interval_exceeded"

    missing = detect_stale_document(None, 90, now=now)
    assert missing["is_stale"] is True
    assert missing["reason"] == "review_date_missing"

    stale_det = StalenessDetector()
    stale_cands = await stale_det.detect(
        {
            "kind": "staleness_check",
            "document_id": "runbook-1",
            "review_interval_days": 30,
            "last_reviewed_at": (now - timedelta(days=45)).isoformat(),
        },
        {"tenant_id": "org_1"},
    )
    assert len(stale_cands) == 1
    assert stale_cands[0]["category"] == "stale_knowledge"

    gap_det = KnowledgeGapDetector()
    gap_cands = await gap_det.detect(
        {
            "kind": "knowledge_gap",
            "topic": "SOC2 Incident Escalation",
            "unanswered_count": 5,
            "evidence_count": 0,
            "run_id": "r_123",
        },
        {"tenant_id": "org_1"},
    )
    assert len(gap_cands) == 1
    assert gap_cands[0]["category"] == "knowledge_gap"

    trend_det = EmergingTrendDetector()
    trend_cands = await trend_det.detect(
        {
            "kind": "trend_window",
            "topic": "SSO login failures",
            "current_count": 12,
            "baseline_count": 4.0,
            "window_days": 7,
            "evidence_refs": ["doc:inc-1"],
        },
        {"tenant_id": "org_1"},
    )
    assert len(trend_cands) == 1
    assert trend_cands[0]["category"] == "emerging_trend"
    assert len(build_default_detectors()) == 5


@pytest.mark.asyncio
async def test_evidence_validator_blocks_missing_and_unauthorized_refs() -> None:
    validator = EvidenceValidator(resource_exists_fn=lambda _t, ref: ref != "doc:missing")
    ctx = IntelligenceSecurityContext(
        tenant_id="org_1",
        user_id="usr_1",
        roles=["member"],
        accessible_resource_refs=["doc:allowed"],
    )

    cand_unauth = IntelligenceCandidate(
        category="significant_change",
        title="Restricted change",
        summary="Restricted summary",
        evidence_refs=["doc:secret"],
        impact_score=0.8,
        relevance_score=0.8,
    )
    ok, records, lims = await validator.validate(cand_unauth, ctx)
    assert ok is False
    assert records[0].validation_outcome == "unauthorized"
    assert any("lacks access" in lim for lim in lims)

    cand_valid = IntelligenceCandidate(
        category="significant_change",
        title="Allowed change",
        summary="Allowed summary",
        evidence_refs=["doc:allowed"],
        impact_score=0.8,
        relevance_score=0.8,
    )
    ok2, records2, _ = await validator.validate(cand_valid, ctx)
    assert ok2 is True
    assert records2[0].validation_outcome == "valid"
