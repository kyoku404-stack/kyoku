"""Phase 4.10 Member 2 Unit Tests — Trigger Registry, Conditions, ORM & Migrations."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.app.agents.errors import (
    EventValidationError,
    TriggerWorkflowNotAllowedError,
)
from backend.app.agents.events.contracts import EventSecurityContext, KeepEvent
from backend.app.agents.events.event_store import SqlAlchemyEventStore
from backend.app.agents.triggers.conditions import evaluate_conditions, validate_condition_spec
from backend.app.agents.triggers.models import (
    ScheduleCreateRequest,
    TriggerCreateRequest,
    TriggerUpdateRequest,
)
from backend.app.agents.triggers.registry import TriggerRegistry
from backend.app.agents.triggers.repository import (
    InMemoryTriggerRepository,
    SqlAlchemyTriggerRepository,
)
from backend.app.agents.triggers.rule_engine import TriggerRuleEngine
from backend.app.db.base import Base
from backend.app.models import agent_triggers  # noqa: F401


def _ctx(tenant: str = "tenant-trg") -> EventSecurityContext:
    return EventSecurityContext(
        tenant_id=tenant,
        user_id="usr-lead",
        roles=["admin"],
        permissions=["agent.invoke", "agent.manage", "agent.read"],
    )


def test_declarative_condition_evaluation_and_operator_allowlist():
    ev = KeepEvent(
        event_id="evt-c1",
        event_type="knowledge.document.indexed",
        source="keep.knowledge",
        tenant_id="tenant-trg",
        resource_id="doc-5",
        correlation_id="corr-5",
        payload={
            "document_id": "doc-5",
            "collection_id": "col-10",
            "tags": ["finance", "q4"],
            "score": 0.92,
        },
    )

    ok1, _ = evaluate_conditions(
        ev, {"collection_id": "col-10", "score": {"gte": 0.9}, "tags": {"contains": "q4"}}
    )
    assert ok1 is True

    ok2, _ = evaluate_conditions(ev, {"collection_id": {"in": ["col-1", "col-2"]}})
    assert ok2 is False

    # Disallowed operator / eval-style attempt rejected
    with pytest.raises(EventValidationError):
        validate_condition_spec({"score": {"$where": "1==1"}})


def test_schedule_create_validation_enforces_exclusive_mode():
    with pytest.raises(ValueError):
        ScheduleCreateRequest(cron_expression=None, interval_seconds=None)

    with pytest.raises(ValueError):
        ScheduleCreateRequest(cron_expression="0 9 * * *", interval_seconds=60)

    valid = ScheduleCreateRequest(interval_seconds=300)
    assert valid.interval_seconds == 300


@pytest.mark.asyncio
async def test_trigger_registry_matching_versioning_and_enable_disable():
    repo = InMemoryTriggerRepository()
    registry = TriggerRegistry(repo)
    engine = TriggerRuleEngine(repo)

    # Disallowed workflow rejected
    with pytest.raises(TriggerWorkflowNotAllowedError):
        await registry.create_trigger(
            TriggerCreateRequest(
                name="Bad trigger",
                event_type="knowledge.document.indexed",
                workflow_id="arbitrary_rogue_workflow",
            ),
            _ctx(),
        )

    rule = await registry.create_trigger(
        TriggerCreateRequest(
            name="Enrich finance docs",
            event_type="knowledge.document.indexed",
            workflow_id="document_enrichment",
            conditions={"collection_id": "collection-10"},
        ),
        _ctx(),
    )
    assert rule.version == 1

    ev_match = KeepEvent(
        event_id="evt-m1",
        event_type="knowledge.document.indexed",
        source="keep.knowledge",
        tenant_id="tenant-trg",
        resource_id="doc-10",
        correlation_id="corr-10",
        payload={"document_id": "doc-10", "collection_id": "collection-10"},
    )
    ev_miss = ev_match.model_copy(
        update={"event_id": "evt-m2", "payload": {"document_id": "doc-11", "collection_id": "other"}}
    )

    matches = await engine.evaluate_event(ev_match)
    assert len(matches) == 1 and matches[0].matched is True

    misses = await engine.evaluate_event(ev_miss)
    assert len(misses) == 1 and misses[0].matched is False

    # Disabled triggers never match
    await registry.set_enabled(rule.trigger_id, enabled=False, security_context=_ctx())
    disabled_eval = await engine.evaluate_event(ev_match)
    assert disabled_eval[0].matched is False
    assert "disabled" in disabled_eval[0].reason.lower()

    # Re-enable + update bumps version
    await registry.set_enabled(rule.trigger_id, enabled=True, security_context=_ctx())
    updated = await registry.update_trigger(
        rule.trigger_id,
        TriggerUpdateRequest(cooldown_seconds=120),
        _ctx(),
    )
    assert updated.version == 2


@pytest.mark.asyncio
async def test_sqlalchemy_event_and_trigger_atomic_dispatch_claim(tmp_path):
    db_file = tmp_path / "triggers_stage2.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    ev_store = SqlAlchemyEventStore(session_factory=session_factory)
    trg_repo = SqlAlchemyTriggerRepository(session_factory=session_factory)

    event = KeepEvent(
        event_id="evt-db-01",
        event_type="knowledge.document.indexed",
        source="keep.knowledge",
        tenant_id="tenant-db",
        resource_id="doc-db-1",
        correlation_id="corr-db",
        occurred_at=datetime.now(UTC),
        payload={"document_id": "doc-db-1"},
    )
    saved_ev, created = await ev_store.save_event_if_absent(event)
    assert created is True
    _, created_dup = await ev_store.save_event_if_absent(event)
    assert created_dup is False

    reg = TriggerRegistry(trg_repo)
    rule = await reg.create_trigger(
        TriggerCreateRequest(
            name="DB enrichment rule",
            event_type="knowledge.document.indexed",
            workflow_id="document_enrichment",
        ),
        _ctx("tenant-db"),
    )

    d1, claimed1 = await trg_repo.claim_dispatch(
        event_id=saved_ev.event_id,
        trigger=rule,
        resource_key="doc-db-1",
    )
    d2, claimed2 = await trg_repo.claim_dispatch(
        event_id=saved_ev.event_id,
        trigger=rule,
        resource_key="doc-db-1",
    )
    assert claimed1 is True
    assert claimed2 is False
    assert d1.dispatch_id == d2.dispatch_id

    # Tenant isolation
    assert await trg_repo.get_trigger(rule.trigger_id, "tenant-other") is None
    await engine.dispose()
