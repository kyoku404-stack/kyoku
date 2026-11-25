"""Unit & security tests for Phase 4.11 Member 3: Governance, Policies, Feedback & Evaluation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.app.agents.errors import IntelligenceAccessDeniedError
from backend.app.agents.intelligence.contracts import (
    InsightDismissRequest,
    InsightFeedbackRequest,
    IntelligenceSecurityContext,
    ScanRequest,
)
from backend.app.agents.intelligence.evaluation import LabelledObservation, evaluate_detector_set
from backend.app.agents.intelligence.feedback import InsightFeedbackService
from backend.app.agents.intelligence.policies import IntelligencePolicyEngine
from backend.app.agents.intelligence.service import IntelligenceService
from backend.app.agents.intelligence_detectors import build_default_detectors


@pytest.mark.asyncio
async def test_policy_engine_enforces_rbac_source_recheck_and_redaction() -> None:
    policy = IntelligencePolicyEngine()
    sanitized = policy.sanitize_summary("Leaked api_key=secret_abc123456789 in doc")
    assert "secret_abc123456789" not in sanitized
    assert "[REDACTED]" in sanitized

    viewer_ctx = IntelligenceSecurityContext(
        tenant_id="org_1",
        user_id="usr_viewer",
        roles=["Viewer"],
        permissions=["agent.read"],
    )
    with pytest.raises(IntelligenceAccessDeniedError):
        policy.authorize_scan(viewer_ctx)

    svc = IntelligenceService(
        detectors=build_default_detectors(),
        policy_engine=policy,
    )
    admin_ctx = IntelligenceSecurityContext(
        tenant_id="org_1",
        user_id="usr_admin",
        roles=["admin"],
        permissions=["agent.invoke", "agent.read", "agent.manage"],
    )
    await svc.run_scan(
        ScanRequest(
            observations=[
                {
                    "kind": "document_version",
                    "document_id": "hr-pol",
                    "title": "HR Access Policy",
                    "previous_version": "v1",
                    "current_version": "v2",
                    "previous_content": "Employees must rotate tokens every 90 days.",
                    "current_content": "Employees must rotate tokens every 30 days.",
                    "audience_roles": ["admin", "hr_lead"],
                }
            ]
        ),
        admin_ctx,
    )

    # Viewer lacks audience role and source access
    viewer_feed = await svc.list_insights(viewer_ctx)
    assert viewer_feed == []

    # User with matching role but revoked source access is denied on live re-check
    revoked_ctx = IntelligenceSecurityContext(
        tenant_id="org_1",
        user_id="usr_hr",
        roles=["hr_lead"],
        permissions=["agent.read"],
        accessible_resource_refs=["doc:other"],
    )
    assert await svc.list_insights(revoked_ctx) == []


@pytest.mark.asyncio
async def test_per_user_dismissal_does_not_hide_org_insight_for_others_and_captures_feedback() -> None:
    svc = IntelligenceService(detectors=build_default_detectors())
    user_a = IntelligenceSecurityContext(
        tenant_id="org_1",
        user_id="usr_a",
        roles=["admin"],
        permissions=["agent.invoke", "agent.read", "agent.manage"],
    )
    user_b = IntelligenceSecurityContext(
        tenant_id="org_1",
        user_id="usr_b",
        roles=["member"],
        permissions=["agent.read"],
    )
    await svc.run_scan(
        ScanRequest(
            observations=[
                {
                    "kind": "document_version",
                    "document_id": "sec-1",
                    "title": "Security Standard",
                    "previous_version": "v1",
                    "current_version": "v2",
                    "previous_content": "Backups must run every 14 days.",
                    "current_content": "Backups must run every 7 days.",
                }
            ]
        ),
        user_a,
    )
    feed_a = await svc.list_insights(user_a)
    assert len(feed_a) == 1
    insight_id = feed_a[0].insight_id

    await svc.submit_feedback(
        insight_id,
        InsightFeedbackRequest(feedback="useful", comment="Clear change diff"),
        user_a,
    )
    fb_svc = InsightFeedbackService(svc.repository)
    summary = await fb_svc.summarize_feedback("org_1", insight_id)
    assert summary["useful"] == 1

    # Personal dismissal hides only for user_a, not user_b
    await svc.dismiss_insight(insight_id, InsightDismissRequest(scope="user", reason="Already seen"), user_a)
    assert await svc.list_insights(user_a) == []
    assert len(await svc.list_insights(user_b)) == 1


@pytest.mark.asyncio
async def test_labelled_detector_evaluation_measures_precision_and_recall() -> None:
    now = datetime(2026, 11, 25, tzinfo=UTC)
    dataset = [
        LabelledObservation(
            case_id="c1",
            observation={
                "kind": "document_version",
                "document_id": "d1",
                "previous_version": "v1",
                "current_version": "v2",
                "previous_content": "SLA must be 48 hours.",
                "current_content": "SLA must be 24 hours.",
            },
            expected_categories={"significant_change"},
        ),
        LabelledObservation(
            case_id="c2",
            observation={
                "kind": "staleness_check",
                "document_id": "d2",
                "review_interval_days": 30,
                "last_reviewed_at": (now - timedelta(days=60)).isoformat(),
            },
            expected_categories={"stale_knowledge"},
        ),
        LabelledObservation(
            case_id="c3",
            observation={
                "kind": "staleness_check",
                "document_id": "d3",
                "review_interval_days": 30,
                "last_reviewed_at": (now - timedelta(days=5)).isoformat(),
            },
            expected_categories=set(),
        ),
    ]
    res = await evaluate_detector_set(build_default_detectors(), dataset)
    assert res.total_cases == 3
    assert res.precision == 1.0
    assert res.recall == 1.0
    assert res.f1_score == 1.0
