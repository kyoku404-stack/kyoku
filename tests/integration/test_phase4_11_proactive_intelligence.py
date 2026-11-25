"""Phase 4.11 Member 4 — Proactive Enterprise Intelligence Integration & QA Suite.

Proves all 18 Phase 4.11 Readiness Checklist items (`devdocs/p4/p4.11.txt` Section 12)
and the Recommended First Demonstration (Policy Document v2 change + conflict detection,
evidence verification, ranked feed, feedback, dismissal, investigation workflow launch,
restart durability, and tenant/RBAC isolation).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app.agents.intelligence.contracts import IntelligenceSecurityContext
from backend.app.api.v1.intelligence import handle_proactive_event
from backend.app.core.constants import UserRole
from backend.app.core.security import create_access_token
from backend.app.main import app


def _auth_headers(
    role: UserRole = UserRole.ORG_ADMIN,
    *,
    org_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, str]:
    uid = user_id or str(uuid4())
    oid = org_id or str(uuid4())
    token = create_access_token(
        data={
            "sub": uid,
            "org_id": oid,
            "role": role.value,
            "email": f"{role.value.lower()}@keep.corp",
        }
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Request-ID": f"corr-p411-{uuid4().hex[:8]}",
    }


class TestPhase411ProactiveIntelligenceIntegration:
    def test_01_rbac_and_tenant_isolation(self, client: TestClient) -> None:
        org_a = str(uuid4())
        org_b = str(uuid4())
        admin_a = _auth_headers(UserRole.ORG_ADMIN, org_id=org_a)
        viewer_a = _auth_headers(UserRole.VIEWER, org_id=org_a)
        admin_b = _auth_headers(UserRole.ORG_ADMIN, org_id=org_b)

        scan_payload = {
            "observations": [
                {
                    "kind": "document_version",
                    "document_id": "pol-rbac",
                    "title": "Access Control Policy",
                    "previous_version": "v1",
                    "current_version": "v2",
                    "previous_content": "MFA must be rotated every 90 days.",
                    "current_content": "MFA must be rotated every 30 days.",
                }
            ]
        }

        # Viewer forbidden from launching scans
        r_forbid = client.post("/api/v1/intelligence/scans", json=scan_payload, headers=viewer_a)
        assert r_forbid.status_code == 403

        # Org A admin launches scan
        r_scan = client.post("/api/v1/intelligence/scans", json=scan_payload, headers=admin_a)
        assert r_scan.status_code == 201, r_scan.text
        run_id = r_scan.json()["data"]["run_id"]

        r_feed = client.get("/api/v1/intelligence/insights", headers=admin_a)
        assert r_feed.status_code == 200
        insights = r_feed.json()["data"]
        assert len(insights) >= 1
        insight_id = insights[0]["insight_id"]

        # Cross-tenant isolation: Org B cannot read Org A's run, insight, or evidence
        assert client.get(f"/api/v1/intelligence/runs/{run_id}", headers=admin_b).status_code == 404
        assert client.get(f"/api/v1/intelligence/insights/{insight_id}", headers=admin_b).status_code == 404
        assert client.get(f"/api/v1/intelligence/insights/{insight_id}/evidence", headers=admin_b).status_code == 404

    def test_02_recommended_first_demo_policy_change_conflict_evidence_and_investigation(
        self,
        client: TestClient,
    ) -> None:
        org_id = str(uuid4())
        admin_headers = _auth_headers(UserRole.ORG_ADMIN, org_id=org_id)

        # Policy v2 update introduces a material change AND conflicts with an existing standard
        scan_payload = {
            "observations": [
                {
                    "kind": "document_version",
                    "document_id": "policy-retention-01",
                    "title": "Enterprise Data Retention Policy",
                    "previous_version": "v1",
                    "current_version": "v2",
                    "previous_content": "Customer audit logs must be retained for 90 days.",
                    "current_content": "Customer audit logs must be retained for 30 days.",
                    "compare_sources": [
                        {
                            "resource_ref": "doc:policy-retention-01:v2",
                            "version": "v2",
                            "text": "Customer audit logs must be retained for 30 days.",
                        },
                        {
                            "resource_ref": "doc:soc2-baseline:v1",
                            "version": "v1",
                            "text": "Customer audit logs must be retained for 365 days.",
                        },
                    ],
                }
            ],
            "suppress_window_seconds": 3600,
        }

        r_scan = client.post("/api/v1/intelligence/scans", json=scan_payload, headers=admin_headers)
        assert r_scan.status_code == 201, r_scan.text
        run_data = r_scan.json()["data"]
        assert run_data["insights_published"] == 2
        assert run_data["status"] == "completed"

        # Inspect feed (ranked deterministically by priority_score DESC)
        r_feed = client.get("/api/v1/intelligence/insights", headers=admin_headers)
        assert r_feed.status_code == 200
        feed = r_feed.json()["data"]
        assert len(feed) == 2
        assert feed[0]["priority_score"] >= feed[1]["priority_score"]
        categories = {i["category"] for i in feed}
        assert categories == {"significant_change", "contradiction"}

        primary_id = feed[0]["insight_id"]
        secondary_id = feed[1]["insight_id"]

        # Inspect detail & evidence endpoints
        r_detail = client.get(f"/api/v1/intelligence/insights/{primary_id}", headers=admin_headers)
        assert r_detail.status_code == 200
        assert len(r_detail.json()["data"]["observed_facts"]) >= 1

        r_ev = client.get(f"/api/v1/intelligence/insights/{primary_id}/evidence", headers=admin_headers)
        assert r_ev.status_code == 200
        assert len(r_ev.json()["data"]) >= 2

        # Submit feedback
        r_fb = client.post(
            f"/api/v1/intelligence/insights/{primary_id}/feedback",
            json={"feedback": "useful", "comment": "Caught conflicting retention window"},
            headers=admin_headers,
        )
        assert r_fb.status_code == 201
        assert r_fb.json()["data"]["feedback"] == "useful"

        # Request approved workflow investigation (Phase 4.3 orchestration bridge)
        r_inv = client.post(
            f"/api/v1/intelligence/insights/{primary_id}/investigate",
            json={"workflow_id": "knowledge_analysis", "notes": "Verify SOC2 impact"},
            headers=admin_headers,
        )
        assert r_inv.status_code == 200, r_inv.text
        assert r_inv.json()["data"]["status"] == "investigating"
        assert r_inv.json()["data"]["workflow_execution_id"] is not None

        # Dismiss secondary insight for user feed, then resolve primary
        r_dis = client.post(
            f"/api/v1/intelligence/insights/{secondary_id}/dismiss",
            json={"scope": "user", "reason": "Reviewed with legal"},
            headers=admin_headers,
        )
        assert r_dis.status_code == 200

        r_res = client.post(
            f"/api/v1/intelligence/insights/{primary_id}/resolve",
            json={"resolution_note": "Policy aligned to 365 days"},
            headers=admin_headers,
        )
        assert r_res.status_code == 200
        assert r_res.json()["data"]["status"] == "resolved"

    def test_03_deduplication_metrics_and_restart_persistence(self, client: TestClient) -> None:
        org_id = str(uuid4())
        admin_headers = _auth_headers(UserRole.ORG_ADMIN, org_id=org_id)
        now = datetime.now(UTC)

        payload = {
            "observations": [
                {
                    "kind": "staleness_check",
                    "document_id": f"runbook-{uuid4().hex[:6]}",
                    "title": "Incident Response Runbook",
                    "review_interval_days": 30,
                    "last_reviewed_at": (now - timedelta(days=90)).isoformat(),
                }
            ],
            "suppress_window_seconds": 3600,
        }

        # First scan publishes
        r1 = client.post("/api/v1/intelligence/scans", json=payload, headers=admin_headers)
        assert r1.status_code == 201
        assert r1.json()["data"]["insights_published"] == 1

        # Simulate process restart by clearing app.state.intelligence_service
        app.state.intelligence_service = None

        # Second scan after restart deduplicates against SQLAlchemy-persisted suppression
        r2 = client.post("/api/v1/intelligence/scans", json=payload, headers=admin_headers)
        assert r2.status_code == 201
        assert r2.json()["data"]["insights_published"] == 0
        assert r2.json()["data"]["insights_suppressed"] == 1

        r_metrics = client.get("/api/v1/intelligence/metrics", headers=admin_headers)
        assert r_metrics.status_code == 200
        m = r_metrics.json()["data"]
        assert m["total_runs"] == 2
        assert m["published_insights"] == 1
        assert m["suppressed_insights"] == 1
        assert m["duplicate_suppression_rate"] > 0.0

    @pytest.mark.asyncio
    async def test_04_phase4_10_event_bridge_triggers_proactive_scan(self, client: TestClient) -> None:
        from backend.app.agents.intelligence.service import IntelligenceService
        from backend.app.agents.intelligence_detectors import build_default_detectors

        svc = IntelligenceService(detectors=build_default_detectors())
        ctx = IntelligenceSecurityContext(
            tenant_id=f"org_{uuid4().hex[:8]}",
            user_id="system_event_worker",
            roles=["admin"],
            permissions=["agent.invoke", "agent.read"],
        )
        run = await handle_proactive_event(
            svc,
            {
                "kind": "knowledge_gap",
                "topic": "Disaster Recovery Failover",
                "unanswered_count": 4,
                "evidence_count": 0,
                "run_id": "res_run_99",
            },
            ctx,
            source_event_id="evt_p410_123",
        )
        assert run.trigger_source == "event"
        assert run.source_event_id == "evt_p410_123"
        assert run.insights_published == 1
