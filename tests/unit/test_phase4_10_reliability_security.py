"""Phase 4.10 Member 3 Unit Tests — Reliability, Queues, DLQ, Scheduler & Security Policies."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.app.agents.errors import (
    EventTenantMismatchError,
    TriggerAccessDeniedError,
    TriggerDisabledError,
    TriggerRateLimitedError,
)
from backend.app.agents.events.contracts import (
    EventPublishRequest,
    EventSecurityContext,
    KeepEvent,
)
from backend.app.agents.events.event_store import InMemoryEventStore
from backend.app.agents.events.ingestion import EventIngestionService
from backend.app.agents.triggers.models import (
    ScheduleCreateRequest,
    TriggerCreateRequest,
)
from backend.app.agents.triggers.policies import TriggerPolicyEngine
from backend.app.agents.triggers.registry import TriggerRegistry
from backend.app.agents.triggers.repository import InMemoryTriggerRepository
from backend.app.agents.triggers.scheduler import TriggerScheduler, compute_next_run
from backend.app.agents.workers.event_worker import (
    EventQueueWorker,
    PermanentDeliveryError,
    RetryableDeliveryError,
)


def _ctx(
    tenant: str = "tenant-rel",
    roles: list[str] | None = None,
    perms: list[str] | None = None,
) -> EventSecurityContext:
    return EventSecurityContext(
        tenant_id=tenant,
        user_id="usr-rel",
        roles=roles if roles is not None else ["admin"],
        permissions=perms if perms is not None else ["agent.manage", "agent.invoke", "agent.read"],
        trusted_source="keep.knowledge",
    )


@pytest.mark.asyncio
async def test_policy_enforces_rbac_tenant_cooldown_and_concurrency():
    ev_store = InMemoryEventStore()
    trg_repo = InMemoryTriggerRepository()
    reg = TriggerRegistry(trg_repo)
    policy = TriggerPolicyEngine(trg_repo, ev_store)

    # RBAC denials
    with pytest.raises(TriggerAccessDeniedError):
        policy.authorize_manage(_ctx(roles=["Viewer"], perms=["agent.read"]))
    with pytest.raises(TriggerAccessDeniedError):
        policy.authorize_manage(_ctx(roles=["revoked"], perms=[]))

    rule = await reg.create_trigger(
        TriggerCreateRequest(
            name="Cooldown test rule",
            event_type="knowledge.document.indexed",
            workflow_id="document_enrichment",
            cooldown_seconds=60,
            max_concurrent_runs=1,
        ),
        _ctx(),
    )
    ev1 = KeepEvent(
        event_id="evt-p1",
        event_type="knowledge.document.indexed",
        source="keep.knowledge",
        tenant_id="tenant-rel",
        resource_id="doc-1",
        correlation_id="corr-1",
        payload={"document_id": "doc-1"},
    )

    # First claim succeeds
    d1, claimed = await trg_repo.claim_dispatch(event_id=ev1.event_id, trigger=rule, resource_key="doc-1")
    assert claimed is True

    # Concurrency/Cooldown triggers suppression
    ev2 = ev1.model_copy(update={"event_id": "evt-p2"})
    with pytest.raises(TriggerRateLimitedError):
        await policy.authorize_trigger(
            event=ev2,
            trigger=rule,
            security_context=_ctx(),
            resource_key="doc-1",
        )

    # Disabled trigger blocked
    await reg.set_enabled(rule.trigger_id, enabled=False, security_context=_ctx())
    disabled_rule = await reg.get_trigger(rule.trigger_id, _ctx())
    with pytest.raises(TriggerDisabledError):
        await policy.authorize_trigger(event=ev2, trigger=disabled_rule, security_context=_ctx())

    # Cross-tenant denied
    with pytest.raises(EventTenantMismatchError):
        policy.authorize_read("tenant-rel", _ctx(tenant="tenant-evil"))


@pytest.mark.asyncio
async def test_event_worker_retry_backoff_dlq_replay_and_crash_recovery():
    ev_store = InMemoryEventStore()
    ingestion = EventIngestionService(ev_store)
    attempts = {"count": 0, "mode": "retryable"}

    async def flaky_handler(event, delivery):
        attempts["count"] += 1
        if attempts["mode"] == "retryable" and attempts["count"] == 1:
            raise RetryableDeliveryError("Transient vector store timeout")
        if attempts["mode"] == "permanent":
            raise PermanentDeliveryError("Invalid schema mapping")

    worker = EventQueueWorker(ev_store, handler=flaky_handler, base_backoff_seconds=1.0)
    ev, deliv, _ = await ingestion.ingest(
        EventPublishRequest(
            event_id="evt-retry-1",
            event_type="knowledge.document.indexed",
            payload={"document_id": "doc-r1"},
        ),
        _ctx(),
    )

    # 1. Transient failure schedules retry with next_retry_at
    r1 = await worker.process_delivery(deliv.delivery_id, "tenant-rel")
    assert r1.status == "retry_scheduled"
    assert r1.next_retry_at is not None

    # 2. Retry after backoff succeeds
    future = r1.next_retry_at + timedelta(seconds=1)
    due = await ev_store.list_due_deliveries(now=future)
    assert len(due) == 1
    r2 = await worker.process_delivery(deliv.delivery_id, "tenant-rel", now=future)
    assert r2.status == "completed"

    # 3. Permanent failure goes directly to dead_letter, and operator replay recovers it
    attempts["mode"] = "permanent"
    _, d_perm, _ = await ingestion.ingest(
        EventPublishRequest(
            event_id="evt-perm-1",
            event_type="knowledge.document.indexed",
            payload={"document_id": "doc-p1"},
        ),
        _ctx(),
    )
    res_dlq = await worker.process_delivery(d_perm.delivery_id, "tenant-rel")
    assert res_dlq.status == "dead_letter"
    assert res_dlq.is_permanent_failure is True

    dlq_list = await ev_store.list_dead_letter_deliveries("tenant-rel")
    assert len(dlq_list) == 1

    # Fix underlying condition and replay safely
    attempts["mode"] = "ok"
    replayed = await worker.replay_dead_letter(d_perm.delivery_id, _ctx(), process_immediately=True)
    assert replayed.status == "completed"

    # 4. Simulated worker crash (expired lease) recovered cleanly
    _, d_crash, _ = await ingestion.ingest(
        EventPublishRequest(
            event_id="evt-crash-1",
            event_type="knowledge.document.indexed",
            payload={"document_id": "doc-c1"},
        ),
        _ctx(),
    )
    past = datetime.now(UTC) - timedelta(seconds=10)
    await ev_store.claim_delivery_lease(d_crash.delivery_id, lease_until=past, now=past - timedelta(seconds=30))
    recovered = await worker.recover_pending_events(now=datetime.now(UTC))
    assert recovered == 1


@pytest.mark.asyncio
async def test_scheduler_cron_interval_missed_runs_and_deduplication():
    ev_store = InMemoryEventStore()
    trg_repo = InMemoryTriggerRepository()
    ingestion = EventIngestionService(ev_store)
    reg = TriggerRegistry(trg_repo)
    scheduler = TriggerScheduler(trg_repo, ingestion)

    rule = await reg.create_trigger(
        TriggerCreateRequest(
            name="Weekly knowledge gap audit",
            event_type="schedule.triggered",
            workflow_id="autonomous_research",
            execution_mode="autonomous_workflow",
        ),
        _ctx(),
    )

    t0 = datetime(2026, 11, 25, 10, 0, tzinfo=UTC)
    sch = await scheduler.create_schedule(
        rule.trigger_id,
        ScheduleCreateRequest(interval_seconds=60, timezone="UTC", missed_run_policy="coalesce"),
        _ctx(),
        now=t0,
    )
    assert sch.next_run_at == t0 + timedelta(seconds=60)

    # Cron next run test in America/New_York
    cron_next = compute_next_run(
        cron_expression="30 9 * * *",
        interval_seconds=None,
        timezone_name="America/New_York",
        after=t0,
    )
    assert cron_next > t0

    # Tick at due time -> emits 1 event, advances next_run_at
    emitted = await scheduler.tick(now=t0 + timedelta(seconds=61))
    assert len(emitted) == 1
    assert emitted[0].event_type == "schedule.triggered"

    # Re-ticking before next_run_at produces 0 duplicates
    emitted_again = await scheduler.tick(now=t0 + timedelta(seconds=62))
    assert len(emitted_again) == 0
