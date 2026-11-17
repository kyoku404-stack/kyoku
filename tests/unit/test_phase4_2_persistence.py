"""Phase 4.2 Member 2 — Execution Persistence, Atomic CAS, Idempotency & Checkpoints Unit Tests.

Verifies:
- Durable SQLAlchemy persistence surviving new repository/session instances (restart simulation).
- Atomic compare-and-set transitions preventing concurrent overwrites and terminal mutation.
- Scoped `(tenant_id, requested_by, idempotency_key)` uniqueness & conflict handling.
- Strict tenant isolation on execution retrieval and checkpoint loading.
- Stale RUNNING execution discovery for crash recovery.

Specification: devdocs/p4/p4.2.txt (Sections 4, 6, 8, 13)
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import IdempotencyConflictError, InvalidExecutionTransitionError
from backend.app.agents.persistence.checkpoints import KeepCheckpointStore
from backend.app.agents.persistence.execution_repository import (
    InMemoryExecutionRepository,
    SQLAlchemyExecutionRepository,
)
from backend.app.agents.runtime.lifecycle import ExecutionRecord, ExecutionStatus
from backend.app.models.agent_execution import AgentCheckpoint, AgentExecution


async def _build_sqlite_session_factory() -> tuple[async_sessionmaker[AsyncSession], object]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: AgentExecution.__table__.create(sync_conn, checkfirst=True)
        )
        await conn.run_sync(
            lambda sync_conn: AgentCheckpoint.__table__.create(sync_conn, checkfirst=True)
        )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return factory, engine


def _sample_record(
    *,
    tenant_id: str = "org-acme",
    requested_by: str = "user-1",
    idempotency_key: str | None = None,
    fingerprint: str | None = "fp-abc",
) -> ExecutionRecord:
    return ExecutionRecord(
        task_id=f"task-{uuid4().hex[:8]}",
        agent_id="reference",
        agent_version="1.0.0",
        tenant_id=tenant_id,
        requested_by=requested_by,
        goal="Persist durable execution",
        input_payload={"k": "v"},
        correlation_id=f"corr-{uuid4().hex[:8]}",
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
    )


class TestSQLAlchemyExecutionPersistence:
    @pytest.mark.asyncio
    async def test_execution_survives_fresh_repository_instance_and_enforces_tenant_scope(self) -> None:
        factory, engine = await _build_sqlite_session_factory()
        try:
            repo1 = SQLAlchemyExecutionRepository(factory)
            rec = await repo1.create(_sample_record(tenant_id="org-acme"))
            await repo1.mark_running(rec.execution_id)
            done = await repo1.mark_succeeded(
                rec.execution_id,
                result_payload={"status": "succeeded", "output": {"answer": 42}},
            )
            assert done.status == ExecutionStatus.SUCCEEDED
            assert done.duration_ms is not None

            # Simulate restart by instantiating a brand new repository instance
            repo2 = SQLAlchemyExecutionRepository(factory)
            reloaded = await repo2.get(rec.execution_id, tenant_id="org-acme")
            assert reloaded is not None
            assert reloaded.status == ExecutionStatus.SUCCEEDED
            assert reloaded.result_payload == {"status": "succeeded", "output": {"answer": 42}}

            # Foreign tenant cannot see the execution
            assert await repo2.get(rec.execution_id, tenant_id="org-globex") is None
        finally:
            await engine.dispose()  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_atomic_cas_blocks_concurrent_mark_running_and_terminal_overwrite(self) -> None:
        factory, engine = await _build_sqlite_session_factory()
        try:
            repo = SQLAlchemyExecutionRepository(factory)
            rec = await repo.create(_sample_record())

            # Two concurrent workers race to claim PENDING -> RUNNING
            results = await asyncio.gather(
                repo.mark_running(rec.execution_id),
                repo.mark_running(rec.execution_id),
                return_exceptions=True,
            )
            successes = [r for r in results if isinstance(r, ExecutionRecord)]
            conflicts = [r for r in results if isinstance(r, InvalidExecutionTransitionError)]
            assert len(successes) == 1
            assert len(conflicts) == 1

            # Complete execution -> terminal SUCCEEDED cannot be overwritten by CANCELLED or FAILED
            await repo.mark_succeeded(rec.execution_id, result_payload={"status": "succeeded", "output": {}})
            with pytest.raises(InvalidExecutionTransitionError):
                await repo.mark_cancelled(rec.execution_id)
            with pytest.raises(InvalidExecutionTransitionError):
                await repo.mark_failed(rec.execution_id, error_code="ERR", error_message="late fail")
        finally:
            await engine.dispose()  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_idempotency_uniqueness_and_stale_running_discovery(self) -> None:
        factory, engine = await _build_sqlite_session_factory()
        try:
            repo = SQLAlchemyExecutionRepository(factory)
            first = await repo.create(
                _sample_record(tenant_id="org-acme", requested_by="u1", idempotency_key="key-123")
            )
            found = await repo.find_by_idempotency_key(
                tenant_id="org-acme", requested_by="u1", idempotency_key="key-123"
            )
            assert found is not None and found.execution_id == first.execution_id

            # Duplicate insert with same tenant + user + key raises IdempotencyConflictError
            with pytest.raises(IdempotencyConflictError):
                await repo.create(
                    _sample_record(tenant_id="org-acme", requested_by="u1", idempotency_key="key-123")
                )

            # Same key under a DIFFERENT tenant is permitted (scoped uniqueness)
            other = await repo.create(
                _sample_record(tenant_id="org-globex", requested_by="u1", idempotency_key="key-123")
            )
            assert other.tenant_id == "org-globex"

            # Stale running lookup
            old_time = datetime.now(UTC) - timedelta(minutes=20)
            await repo.mark_running(first.execution_id, started_at=old_time)
            stale = await repo.find_stale_running(stale_before=datetime.now(UTC) - timedelta(minutes=5))
            assert [s.execution_id for s in stale] == [first.execution_id]
        finally:
            await engine.dispose()  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_checkpoint_store_persists_and_isolates_tenants(self) -> None:
        factory, engine = await _build_sqlite_session_factory()
        try:
            store = KeepCheckpointStore(session_factory=factory)
            acme_ctx = AgentContext(user_id="u1", tenant_id="org-acme", correlation_id="c1")
            globex_ctx = AgentContext(user_id="u2", tenant_id="org-globex", correlation_id="c2")

            await store.save_checkpoint(
                execution_id="exec-chk-1",
                thread_id="thr-1",
                step_name="retrieve",
                step_number=1,
                state={"hits": 3},
                context=acme_ctx,
            )
            await store.save_checkpoint(
                execution_id="exec-chk-1",
                thread_id="thr-1",
                step_name="analyze",
                step_number=2,
                state={"summary": "ok"},
                context=acme_ctx,
            )

            acme_list = await store.list_checkpoints(execution_id="exec-chk-1", context=acme_ctx)
            assert [c.step_name for c in acme_list] == ["retrieve", "analyze"]
            latest = await store.get_latest_checkpoint(thread_id="thr-1", context=acme_ctx)
            assert latest is not None and latest.step_number == 2

            # Foreign tenant cannot read Acme's checkpoints
            assert await store.list_checkpoints(execution_id="exec-chk-1", context=globex_ctx) == []
            assert await store.get_latest_checkpoint(thread_id="thr-1", context=globex_ctx) is None
        finally:
            await engine.dispose()  # type: ignore[attr-defined]


class TestInMemoryExecutionRepository:
    @pytest.mark.asyncio
    async def test_in_memory_atomic_pending_cancel_and_listing(self) -> None:
        repo = InMemoryExecutionRepository()
        rec = await repo.create(_sample_record(tenant_id="org-acme"))
        cancelled = await repo.request_cancel(rec.execution_id, tenant_id="org-acme")
        assert cancelled.status == ExecutionStatus.CANCELLED
        assert len(await repo.list_executions(tenant_id="org-acme", status=ExecutionStatus.CANCELLED)) == 1
