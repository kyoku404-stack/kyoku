"""Phase 4.10 Member 4 — Event-Driven & Trigger-Based Agents Integration & QA Suite.

Proves all 17 Phase 4.10 Readiness Checklist items (`devdocs/p4/p4.10.txt` Section 12)
and the Recommended First Demo (`knowledge.document.indexed` -> `document_enrichment`
followed by duplicate event replay verification) through KEEP's live FastAPI,
Phase 4.3 Orchestration, Phase 4.9 Autonomy, and SQLAlchemy persistence layers.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app.agents.events.adapters.webhook import (
    WebhookIngestionAdapter,
    WebhookSourceRegistry,
)
from backend.app.agents.events.contracts import (
    EventPublishRequest,
    EventSecurityContext,
    WebhookSourceConfig,
)
from backend.app.agents.events.event_store import InMemoryEventStore, SqlAlchemyEventStore
from backend.app.agents.triggers.models import ScheduleCreateRequest, TriggerCreateRequest
from backend.app.agents.triggers.repository import (
    InMemoryTriggerRepository,
    SqlAlchemyTriggerRepository,
)
from backend.app.agents.triggers.service import TriggerService
from backend.app.agents.workers.event_worker import PermanentDeliveryError
from backend.app.core.constants import UserRole
from backend.app.core.security import create_access_token
from backend.app.db.session import async_session_factory
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
        "X-Request-ID": f"corr-p410-{uuid4().hex[:8]}",
    }


def _reset_trigger_state(*, use_db: bool = True) -> TriggerService:
    ev_store = (
        SqlAlchemyEventStore(session_factory=async_session_factory)
        if use_db
        else InMemoryEventStore()
    )
    trg_repo = (
        SqlAlchemyTriggerRepository(session_factory=async_session_factory)
        if use_db
        else InMemoryTriggerRepository()
    )
    svc = TriggerService(
        event_store=ev_store,
        trigger_repository=trg_repo,
        workflow_registry=getattr(app.state, "workflow_registry", None),
        orchestration_service=getattr(app.state, "orchestration_service", None),
        autonomy_service=getattr(app.state, "autonomy_service", None),
    )
    src_reg = WebhookSourceRegistry()
    app.state.event_store = ev_store
    app.state.trigger_repository = trg_repo
    app.state.trigger_service = svc
    app.state.webhook_source_registry = src_reg
    app.state.webhook_adapter = WebhookIngestionAdapter(svc.ingestion_service, src_reg)
    return svc


class TestPhase410EventDrivenTriggersIntegration:
    """Comprehensive Phase 4.10 API, Reliability, Security & Workflow Dispatch QA Suite."""

    def test_01_auth_rbac_and_tenant_isolation_on_triggers_and_events(self) -> None:
        """Checklist: Tenant-scoped triggers, RBAC enforcement, malformed & cross-tenant rejection."""
        with TestClient(app) as client:
            _reset_trigger_state(use_db=True)

            # Unauthenticated rejected
            assert client.post("/api/v1/triggers", json={}).status_code == 401
            assert client.post("/api/v1/events", json={}).status_code == 401

            # Viewer cannot create triggers or publish events
            viewer_headers = _auth_headers(role=UserRole.VIEWER)
            assert (
                client.post(
                    "/api/v1/triggers",
                    headers=viewer_headers,
                    json={
                        "name": "Unauthorized viewer rule",
                        "event_type": "knowledge.document.indexed",
                        "workflow_id": "document_enrichment",
                    },
                ).status_code
                == 403
            )

            # Tenant A creates trigger; Tenant B cannot read/update/disable it
            org_a = str(uuid4())
            org_b = str(uuid4())
            headers_a = _auth_headers(role=UserRole.ORG_ADMIN, org_id=org_a)
            headers_b = _auth_headers(role=UserRole.ORG_ADMIN, org_id=org_b)

            trg = client.post(
                "/api/v1/triggers",
                headers=headers_a,
                json={
                    "name": "Enrich Org A Docs",
                    "event_type": "knowledge.document.indexed",
                    "workflow_id": "document_enrichment",
                },
            )
            assert trg.status_code == 201
            trg_id = trg.json()["data"]["trigger_id"]

            assert client.get(f"/api/v1/triggers/{trg_id}", headers=headers_b).status_code == 404
            assert (
                client.post(f"/api/v1/triggers/{trg_id}/disable", headers=headers_b).status_code
                == 404
            )

            # Tenant spoofing inside event body blocked
            spoof = client.post(
                "/api/v1/events",
                headers=headers_b,
                json={
                    "event_type": "knowledge.document.indexed",
                    "tenant_id": org_a,
                    "payload": {"document_id": "doc-spoof"},
                },
            )
            assert spoof.status_code == 403

            # Malformed / missing required field rejected
            malformed = client.post(
                "/api/v1/events",
                headers=headers_a,
                json={
                    "event_type": "knowledge.document.indexed",
                    "payload": {},
                },
            )
            assert malformed.status_code == 400

    def test_02_recommended_first_demo_document_indexed_and_replay_dedup(self) -> None:
        """Recommended First Demo + Phase 4.3 orchestration: upload/index triggers document_enrichment once."""
        with TestClient(app) as client:
            _reset_trigger_state(use_db=True)
            org_id = str(uuid4())
            headers = _auth_headers(role=UserRole.ORG_ADMIN, org_id=org_id)

            # 1. Create matching trigger rule for collection-10
            trg_res = client.post(
                "/api/v1/triggers",
                headers=headers,
                json={
                    "name": "Document Indexing Enrichment",
                    "event_type": "knowledge.document.indexed",
                    "workflow_id": "document_enrichment",
                    "execution_mode": "workflow",
                    "conditions": {"collection_id": "collection-10"},
                    "cooldown_seconds": 0,
                    "max_concurrent_runs": 2,
                },
            )
            assert trg_res.status_code == 201, trg_res.text
            trg_id = trg_res.json()["data"]["trigger_id"]

            # 2. Publish valid indexed event matching condition
            ev_res = client.post(
                "/api/v1/events",
                headers=headers,
                json={
                    "event_id": "evt-demo-doc-100",
                    "event_type": "knowledge.document.indexed",
                    "source": "keep.knowledge",
                    "resource_id": "doc-100",
                    "correlation_id": "corr-demo-100",
                    "payload": {"document_id": "doc-100", "collection_id": "collection-10"},
                },
            )
            assert ev_res.status_code == 202, ev_res.text
            ev_data = ev_res.json()["data"]
            assert ev_data["deduplicated"] is False
            assert len(ev_data["dispatches"]) == 1
            first_exec_id = ev_data["dispatches"][0]["workflow_execution_id"]
            assert first_exec_id is not None

            # Verify Phase 4.3 workflow execution exists in orchestration API
            wf_inspect = client.get(f"/api/v1/workflow-executions/{first_exec_id}", headers=headers)
            assert wf_inspect.status_code == 200
            assert wf_inspect.json()["data"]["workflow_id"] == "document_enrichment"

            # 3. Replay identical event -> MUST NOT create a second workflow execution
            replay_res = client.post(
                "/api/v1/events",
                headers=headers,
                json={
                    "event_id": "evt-demo-doc-100",
                    "event_type": "knowledge.document.indexed",
                    "source": "keep.knowledge",
                    "resource_id": "doc-100",
                    "correlation_id": "corr-demo-100",
                    "payload": {"document_id": "doc-100", "collection_id": "collection-10"},
                },
            )
            assert replay_res.status_code == 202
            assert replay_res.json()["data"]["deduplicated"] is True

            # Verify trigger run history has exactly 1 dispatch
            runs_res = client.get(f"/api/triggers/{trg_id}/runs", headers=headers)
            assert runs_res.status_code == 200
            assert len(runs_res.json()["data"]) == 1
            assert runs_res.json()["data"][0]["workflow_execution_id"] == first_exec_id

            # Verify /api/v1/events/{event_id} inspection
            inspect_res = client.get("/api/v1/events/evt-demo-doc-100", headers=headers)
            assert inspect_res.status_code == 200
            assert inspect_res.json()["data"]["event"]["correlation_id"] == "corr-demo-100"

    def test_03_non_matching_conditions_disable_toggle_and_autonomous_dispatch(self) -> None:
        """Checklist: non-matching conditions, disabled trigger suppression, and Phase 4.9 autonomous trigger."""
        with TestClient(app) as client:
            _reset_trigger_state(use_db=True)
            org_id = str(uuid4())
            headers = _auth_headers(role=UserRole.ORG_ADMIN, org_id=org_id)

            trg = client.post(
                "/api/v1/triggers",
                headers=headers,
                json={
                    "name": "Churn Threshold Autonomous Investigation",
                    "event_type": "threshold.metric.breached",
                    "workflow_id": "churn_investigation",
                    "execution_mode": "autonomous_workflow",
                    "conditions": {"metric": "monthly_churn_rate", "value": {"gte": 0.05}},
                },
            ).json()["data"]
            trg_id = trg["trigger_id"]

            # Non-matching event (value below threshold) -> 0 dispatches
            miss = client.post(
                "/api/v1/events",
                headers=headers,
                json={
                    "event_type": "threshold.metric.breached",
                    "payload": {"metric": "monthly_churn_rate", "value": 0.01},
                },
            ).json()["data"]
            assert len(miss["dispatches"]) == 0

            # Matching event launches real Phase 4.9 Autonomous Workflow
            hit = client.post(
                "/api/v1/events",
                headers=headers,
                json={
                    "event_type": "threshold.metric.breached",
                    "resource_id": "churn-q4",
                    "payload": {"metric": "monthly_churn_rate", "value": 0.09},
                },
            ).json()["data"]
            assert len(hit["dispatches"]) == 1
            auto_exec_id = hit["dispatches"][0]["workflow_execution_id"]
            assert auto_exec_id.startswith("auto_wf_")

            # Disable trigger -> subsequent matching event does NOT dispatch
            dis_res = client.post(f"/api/v1/triggers/{trg_id}/disable", headers=headers)
            assert dis_res.status_code == 200 and dis_res.json()["data"]["enabled"] is False

            after_disable = client.post(
                "/api/v1/events",
                headers=headers,
                json={
                    "event_type": "threshold.metric.breached",
                    "resource_id": "churn-q4-2",
                    "payload": {"metric": "monthly_churn_rate", "value": 0.12},
                },
            ).json()["data"]
            assert len(after_disable["dispatches"]) == 0

    def test_04_webhook_hmac_verification_and_replay_protection(self) -> None:
        """Checklist: External webhook signature authentication and timestamp replay protection."""
        with TestClient(app) as client:
            svc = _reset_trigger_state(use_db=True)
            org_id = str(uuid4())
            headers = _auth_headers(role=UserRole.ORG_ADMIN, org_id=org_id)

            client.post(
                "/api/v1/triggers",
                headers=headers,
                json={
                    "name": "External CRM Webhook Trigger",
                    "event_type": "webhook.external.received",
                    "workflow_id": "document_enrichment",
                    "execution_mode": "workflow",
                },
            )

            app.state.webhook_source_registry.register(
                WebhookSourceConfig(
                    source_id="crm_sync",
                    tenant_id=org_id,
                    secret="crm_hmac_secret_key_998877",
                    replay_window_seconds=300,
                )
            )
            now_ts = int(time.time())
            raw_body = json.dumps(
                {"event_id": "wh-crm-001", "resource_id": "acc-42", "payload": {"action": "tier_drop"}}
            ).encode("utf-8")
            sig = app.state.webhook_adapter.compute_signature(
                "crm_hmac_secret_key_998877", str(now_ts), raw_body
            )

            # Invalid signature rejected (401)
            bad = client.post(
                "/api/v1/webhooks/crm_sync",
                content=raw_body,
                headers={"X-KEEP-Signature": "v1=invalid", "X-KEEP-Timestamp": str(now_ts)},
            )
            assert bad.status_code == 401

            # Expired timestamp rejected (409)
            stale_ts = now_ts - 900
            stale_sig = app.state.webhook_adapter.compute_signature(
                "crm_hmac_secret_key_998877", str(stale_ts), raw_body
            )
            stale = client.post(
                "/api/v1/webhooks/crm_sync",
                content=raw_body,
                headers={"X-KEEP-Signature": stale_sig, "X-KEEP-Timestamp": str(stale_ts)},
            )
            assert stale.status_code == 409

            # Valid signed webhook accepted and triggers workflow
            ok = client.post(
                "/api/v1/webhooks/crm_sync",
                content=raw_body,
                headers={"X-KEEP-Signature": sig, "X-KEEP-Timestamp": str(now_ts)},
            )
            assert ok.status_code == 202
            assert ok.json()["data"]["accepted"] is True
            assert len(
                client.get("/api/v1/events/wh-crm-001", headers=headers).json()["data"]["dispatches"]
            ) == 1
            assert svc is not None

    @pytest.mark.asyncio
    async def test_05_dlq_replay_schedule_dispatch_and_restart_recovery(self) -> None:
        """Checklist: DLQ API inspection/replay, schedules, cooldowns, and worker crash recovery."""
        with TestClient(app) as client:
            svc = _reset_trigger_state(use_db=True)
            org_id = str(uuid4())
            headers = _auth_headers(role=UserRole.ORG_ADMIN, org_id=org_id)

            # Schedule attachment endpoint test
            trg = client.post(
                "/api/v1/triggers",
                headers=headers,
                json={
                    "name": "Scheduled Weekly Gap Report",
                    "event_type": "schedule.triggered",
                    "workflow_id": "autonomous_research",
                    "execution_mode": "autonomous_workflow",
                },
            ).json()["data"]
            sch_res = client.post(
                f"/api/v1/triggers/{trg['trigger_id']}/schedules",
                headers=headers,
                json={"interval_seconds": 60, "timezone": "UTC", "missed_run_policy": "coalesce"},
            )
            assert sch_res.status_code == 201

            due_time = datetime.now(UTC) + timedelta(seconds=65)
            emitted = await svc.tick_schedules(now=due_time)
            assert len(emitted) == 1
            runs = client.get(f"/api/v1/triggers/{trg['trigger_id']}/runs", headers=headers).json()["data"]
            assert len(runs) == 1

            # Dead-letter + API replay test
            should_fail = {"flag": True}

            async def dlq_handler(event, delivery):
                if should_fail["flag"]:
                    raise PermanentDeliveryError("Simulated downstream corruption")
                await svc.dispatcher.process_event_matches(event)

            svc.worker.bind_handler(dlq_handler)
            fail_ev = client.post(
                "/api/v1/events",
                headers=headers,
                json={
                    "event_id": "evt-dlq-01",
                    "event_type": "knowledge.document.indexed",
                    "payload": {"document_id": "doc-dlq"},
                },
            ).json()["data"]
            assert fail_ev["status"] == "dead_letter"

            dlq_list = client.get("/api/v1/events/dead-letter", headers=headers).json()["data"]
            assert any(item["delivery_id"] == fail_ev["delivery_id"] for item in dlq_list)

            # Fix downstream and replay safely via REST API
            should_fail["flag"] = False
            replayed = client.post(
                f"/api/v1/events/deliveries/{fail_ev['delivery_id']}/replay",
                headers=headers,
            )
            assert replayed.status_code == 200
            assert replayed.json()["data"]["status"] == "completed"

            # Simulated crash/restart recovery with brand-new TriggerService reading same DB
            svc2 = TriggerService(
                event_store=SqlAlchemyEventStore(session_factory=async_session_factory),
                trigger_repository=SqlAlchemyTriggerRepository(session_factory=async_session_factory),
            )
            ev_rec, d_rec, _ = await svc2.ingestion_service.ingest(
                EventPublishRequest(
                    event_id="evt-restart-01",
                    event_type="knowledge.document.indexed",
                    payload={"document_id": "doc-restart"},
                ),
                EventSecurityContext(
                    tenant_id=org_id,
                    user_id="usr-lead",
                    roles=["admin"],
                    permissions=["agent.invoke", "agent.manage"],
                ),
            )
            assert d_rec.status == "pending"
            recovered_count = await svc2.worker.recover_pending_events()
            assert recovered_count >= 1
            after_rec = await svc2.event_store.get_event(ev_rec.event_id, org_id)
            assert after_rec is not None and after_rec.status == "processed"
            assert TriggerCreateRequest(
                name="Check", event_type="knowledge.document.indexed", workflow_id="document_enrichment"
            ).enabled
            assert ScheduleCreateRequest(interval_seconds=60).interval_seconds == 60
