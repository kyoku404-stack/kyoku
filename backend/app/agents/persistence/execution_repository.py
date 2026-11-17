"""KEEP Phase 4.2 — Durable Agent Execution Repositories (SQLAlchemy & InMemory).

Enforces atomic compare-and-set lifecycle transitions at the persistence layer,
scoped `(tenant_id, requested_by, idempotency_key)` uniqueness, tenant-isolated
retrieval, and stale RUNNING crash recovery queries.

Owner: Member 2 (Execution State, Persistence & Result Management)
Specification: devdocs/p4/p4.2.txt (Sections 3, 4, 6, 13)
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from backend.app.agents.errors import (
    ExecutionNotFoundError,
    IdempotencyConflictError,
    InvalidExecutionTransitionError,
    sanitize_error_message,
)
from backend.app.agents.runtime.lifecycle import (
    ExecutionRecord,
    ExecutionStatus,
    assert_valid_transition,
)
from backend.app.models.agent_execution import AgentExecution
from sqlalchemy import and_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _compute_ms(start: datetime | None, end: datetime | None) -> int | None:
    if start is None or end is None:
        return None
    s_utc = _ensure_utc(start)
    e_utc = _ensure_utc(end)
    if s_utc is None or e_utc is None:
        return None
    return max(0, int((e_utc - s_utc).total_seconds() * 1000))


def _orm_to_record(row: AgentExecution) -> ExecutionRecord:
    return ExecutionRecord(
        execution_id=row.execution_id,
        task_id=row.task_id,
        agent_id=row.agent_id,
        agent_version=row.agent_version,
        tenant_id=row.tenant_id,
        requested_by=row.requested_by,
        status=ExecutionStatus(row.status),
        mode=row.mode,  # type: ignore[arg-type]
        goal=row.goal,
        input_payload=dict(row.input_json or {}),
        input_ref=row.input_ref,
        result_payload=dict(row.result_json) if row.result_json is not None else None,
        result_ref=row.result_ref,
        error_code=row.error_code,
        error_message=row.error_message,
        correlation_id=row.correlation_id,
        attempt_number=row.attempt_number,
        parent_execution_id=row.parent_execution_id,
        idempotency_key=row.idempotency_key,
        request_fingerprint=row.request_fingerprint,
        cancel_requested=bool(row.cancel_requested),
        cancel_requested_at=_ensure_utc(row.cancel_requested_at),
        created_at=_ensure_utc(row.created_at) or datetime.now(UTC),
        started_at=_ensure_utc(row.started_at),
        completed_at=_ensure_utc(row.completed_at),
        deadline_at=_ensure_utc(row.deadline_at),
        duration_ms=row.duration_ms,
        queue_wait_ms=row.queue_wait_ms,
        checkpoint_thread_id=row.checkpoint_thread_id,
    )


class InMemoryExecutionRepository:
    """Asyncio-lock-protected atomic in-memory repository for unit testing."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._records: dict[str, ExecutionRecord] = {}
        self._idempotency_index: dict[tuple[str, str, str], str] = {}

    async def create(self, record: ExecutionRecord) -> ExecutionRecord:
        async with self._lock:
            if record.idempotency_key:
                key = (record.tenant_id, record.requested_by, record.idempotency_key)
                if key in self._idempotency_index:
                    raise IdempotencyConflictError(record.idempotency_key)
                self._idempotency_index[key] = record.execution_id
            stored = record.model_copy(deep=True)
            self._records[record.execution_id] = stored
            return stored.model_copy(deep=True)

    async def get(self, execution_id: str, *, tenant_id: str | None = None) -> ExecutionRecord | None:
        async with self._lock:
            rec = self._records.get(execution_id)
            if rec is None:
                return None
            if tenant_id is not None and rec.tenant_id != tenant_id:
                return None
            return rec.model_copy(deep=True)

    async def find_by_idempotency_key(
        self,
        *,
        tenant_id: str,
        requested_by: str,
        idempotency_key: str,
    ) -> ExecutionRecord | None:
        async with self._lock:
            exec_id = self._idempotency_index.get((tenant_id, requested_by, idempotency_key))
            if exec_id is None:
                return None
            rec = self._records.get(exec_id)
            return rec.model_copy(deep=True) if rec else None

    async def list_executions(
        self,
        *,
        tenant_id: str,
        agent_id: str | None = None,
        status: ExecutionStatus | None = None,
        limit: int = 50,
    ) -> list[ExecutionRecord]:
        async with self._lock:
            items = [r.model_copy(deep=True) for r in self._records.values() if r.tenant_id == tenant_id]
            if agent_id:
                items = [r for r in items if r.agent_id == agent_id.strip().lower()]
            if status is not None:
                items = [r for r in items if r.status == status]
            items.sort(key=lambda r: r.created_at, reverse=True)
            return items[: max(1, min(limit, 200))]

    async def mark_running(
        self,
        execution_id: str,
        *,
        started_at: datetime | None = None,
    ) -> ExecutionRecord:
        async with self._lock:
            rec = self._records.get(execution_id)
            if rec is None:
                raise ExecutionNotFoundError(execution_id)
            assert_valid_transition(execution_id, rec.status, ExecutionStatus.RUNNING)
            now = started_at or datetime.now(UTC)
            rec.status = ExecutionStatus.RUNNING
            rec.started_at = now
            rec.queue_wait_ms = _compute_ms(rec.created_at, now)
            return rec.model_copy(deep=True)

    async def mark_succeeded(
        self,
        execution_id: str,
        *,
        result_payload: dict[str, Any],
        completed_at: datetime | None = None,
    ) -> ExecutionRecord:
        async with self._lock:
            rec = self._records.get(execution_id)
            if rec is None:
                raise ExecutionNotFoundError(execution_id)
            assert_valid_transition(execution_id, rec.status, ExecutionStatus.SUCCEEDED)
            now = completed_at or datetime.now(UTC)
            rec.status = ExecutionStatus.SUCCEEDED
            rec.result_payload = dict(result_payload)
            rec.error_code = None
            rec.error_message = None
            rec.completed_at = now
            rec.duration_ms = _compute_ms(rec.started_at or rec.created_at, now)
            return rec.model_copy(deep=True)

    async def mark_failed(
        self,
        execution_id: str,
        *,
        error_code: str,
        error_message: str,
        result_payload: dict[str, Any] | None = None,
        completed_at: datetime | None = None,
    ) -> ExecutionRecord:
        async with self._lock:
            rec = self._records.get(execution_id)
            if rec is None:
                raise ExecutionNotFoundError(execution_id)
            assert_valid_transition(execution_id, rec.status, ExecutionStatus.FAILED)
            now = completed_at or datetime.now(UTC)
            rec.status = ExecutionStatus.FAILED
            rec.error_code = error_code
            rec.error_message = sanitize_error_message(error_message)
            if result_payload is not None:
                rec.result_payload = dict(result_payload)
            rec.completed_at = now
            rec.duration_ms = _compute_ms(rec.started_at or rec.created_at, now)
            return rec.model_copy(deep=True)

    async def mark_timed_out(
        self,
        execution_id: str,
        *,
        error_code: str,
        error_message: str,
        completed_at: datetime | None = None,
    ) -> ExecutionRecord:
        async with self._lock:
            rec = self._records.get(execution_id)
            if rec is None:
                raise ExecutionNotFoundError(execution_id)
            assert_valid_transition(execution_id, rec.status, ExecutionStatus.TIMED_OUT)
            now = completed_at or datetime.now(UTC)
            rec.status = ExecutionStatus.TIMED_OUT
            rec.error_code = error_code
            rec.error_message = sanitize_error_message(error_message)
            rec.completed_at = now
            rec.duration_ms = _compute_ms(rec.started_at or rec.created_at, now)
            return rec.model_copy(deep=True)

    async def request_cancel(
        self,
        execution_id: str,
        *,
        tenant_id: str,
    ) -> ExecutionRecord:
        async with self._lock:
            rec = self._records.get(execution_id)
            if rec is None or rec.tenant_id != tenant_id:
                raise ExecutionNotFoundError(execution_id)
            if rec.is_terminal:
                raise InvalidExecutionTransitionError(
                    execution_id, rec.status.value, ExecutionStatus.CANCELLED.value
                )
            now = datetime.now(UTC)
            rec.cancel_requested = True
            rec.cancel_requested_at = now
            if rec.status == ExecutionStatus.PENDING:
                rec.status = ExecutionStatus.CANCELLED
                rec.error_code = "EXECUTION_CANCELLED"
                rec.error_message = "Execution cancelled before starting."
                rec.completed_at = now
                rec.duration_ms = 0
            return rec.model_copy(deep=True)

    async def mark_cancelled(
        self,
        execution_id: str,
        *,
        reason: str = "Execution cancelled by request.",
        completed_at: datetime | None = None,
    ) -> ExecutionRecord:
        async with self._lock:
            rec = self._records.get(execution_id)
            if rec is None:
                raise ExecutionNotFoundError(execution_id)
            assert_valid_transition(execution_id, rec.status, ExecutionStatus.CANCELLED)
            now = completed_at or datetime.now(UTC)
            rec.status = ExecutionStatus.CANCELLED
            rec.cancel_requested = True
            rec.cancel_requested_at = rec.cancel_requested_at or now
            rec.error_code = "EXECUTION_CANCELLED"
            rec.error_message = sanitize_error_message(reason)
            rec.completed_at = now
            rec.duration_ms = _compute_ms(rec.started_at or rec.created_at, now)
            return rec.model_copy(deep=True)

    async def find_stale_running(self, *, stale_before: datetime) -> list[ExecutionRecord]:
        cutoff = _ensure_utc(stale_before) or datetime.now(UTC)
        async with self._lock:
            results: list[ExecutionRecord] = []
            for rec in self._records.values():
                ref = _ensure_utc(rec.started_at or rec.created_at)
                if rec.status == ExecutionStatus.RUNNING and ref is not None and ref < cutoff:
                    results.append(rec.model_copy(deep=True))
            return results


class SQLAlchemyExecutionRepository:
    """Durable async SQLAlchemy repository enforcing atomic CAS status transitions."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, record: ExecutionRecord) -> ExecutionRecord:
        row = AgentExecution(
            execution_id=record.execution_id,
            task_id=record.task_id,
            agent_id=record.agent_id,
            agent_version=record.agent_version,
            tenant_id=record.tenant_id,
            requested_by=record.requested_by,
            status=record.status.value,
            mode=record.mode,
            goal=record.goal,
            input_json=dict(record.input_payload),
            input_ref=record.input_ref,
            result_json=dict(record.result_payload) if record.result_payload is not None else None,
            result_ref=record.result_ref,
            error_code=record.error_code,
            error_message=record.error_message,
            correlation_id=record.correlation_id,
            attempt_number=record.attempt_number,
            parent_execution_id=record.parent_execution_id,
            idempotency_key=record.idempotency_key,
            request_fingerprint=record.request_fingerprint,
            cancel_requested=record.cancel_requested,
            cancel_requested_at=record.cancel_requested_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
            deadline_at=record.deadline_at,
            duration_ms=record.duration_ms,
            queue_wait_ms=record.queue_wait_ms,
            checkpoint_thread_id=record.checkpoint_thread_id,
        )
        async with self._session_factory() as session:
            session.add(row)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                if record.idempotency_key:
                    raise IdempotencyConflictError(record.idempotency_key) from exc
                raise
            await session.refresh(row)
            return _orm_to_record(row)

    async def get(self, execution_id: str, *, tenant_id: str | None = None) -> ExecutionRecord | None:
        async with self._session_factory() as session:
            stmt = select(AgentExecution).where(AgentExecution.execution_id == execution_id)
            if tenant_id is not None:
                stmt = stmt.where(AgentExecution.tenant_id == tenant_id)
            res = await session.execute(stmt)
            row = res.scalar_one_or_none()
            return _orm_to_record(row) if row is not None else None

    async def find_by_idempotency_key(
        self,
        *,
        tenant_id: str,
        requested_by: str,
        idempotency_key: str,
    ) -> ExecutionRecord | None:
        async with self._session_factory() as session:
            stmt = select(AgentExecution).where(
                and_(
                    AgentExecution.tenant_id == tenant_id,
                    AgentExecution.requested_by == requested_by,
                    AgentExecution.idempotency_key == idempotency_key,
                )
            )
            res = await session.execute(stmt)
            row = res.scalar_one_or_none()
            return _orm_to_record(row) if row is not None else None

    async def list_executions(
        self,
        *,
        tenant_id: str,
        agent_id: str | None = None,
        status: ExecutionStatus | None = None,
        limit: int = 50,
    ) -> list[ExecutionRecord]:
        async with self._session_factory() as session:
            stmt = select(AgentExecution).where(AgentExecution.tenant_id == tenant_id)
            if agent_id:
                stmt = stmt.where(AgentExecution.agent_id == agent_id.strip().lower())
            if status is not None:
                stmt = stmt.where(AgentExecution.status == status.value)
            stmt = stmt.order_by(AgentExecution.created_at.desc()).limit(max(1, min(limit, 200)))
            res = await session.execute(stmt)
            return [_orm_to_record(row) for row in res.scalars().all()]

    async def _atomic_cas_transition(
        self,
        execution_id: str,
        *,
        expected_statuses: tuple[ExecutionStatus, ...],
        target_status: ExecutionStatus,
        values: dict[str, Any],
    ) -> ExecutionRecord:
        """Executes an atomic SQL compare-and-set transition guarded by `status IN expected_statuses`."""
        expected_values = [s.value for s in expected_statuses]
        async with self._session_factory() as session:
            # 1. Perform atomic guarded UPDATE
            stmt = (
                update(AgentExecution)
                .where(
                    and_(
                        AgentExecution.execution_id == execution_id,
                        AgentExecution.status.in_(expected_values),
                    )
                )
                .values(status=target_status.value, **values)
            )
            result = await session.execute(stmt)
            await session.commit()

            # 2. Reload authoritative row
            row_res = await session.execute(
                select(AgentExecution).where(AgentExecution.execution_id == execution_id)
            )
            row = row_res.scalar_one_or_none()
            if row is None:
                raise ExecutionNotFoundError(execution_id)
            if (result.rowcount or 0) == 0:
                raise InvalidExecutionTransitionError(
                    execution_id,
                    row.status,
                    target_status.value,
                )
            return _orm_to_record(row)

    async def mark_running(
        self,
        execution_id: str,
        *,
        started_at: datetime | None = None,
    ) -> ExecutionRecord:
        existing = await self.get(execution_id)
        if existing is None:
            raise ExecutionNotFoundError(execution_id)
        now = started_at or datetime.now(UTC)
        return await self._atomic_cas_transition(
            execution_id,
            expected_statuses=(ExecutionStatus.PENDING,),
            target_status=ExecutionStatus.RUNNING,
            values={
                "started_at": now,
                "queue_wait_ms": _compute_ms(existing.created_at, now),
            },
        )

    async def mark_succeeded(
        self,
        execution_id: str,
        *,
        result_payload: dict[str, Any],
        completed_at: datetime | None = None,
    ) -> ExecutionRecord:
        existing = await self.get(execution_id)
        if existing is None:
            raise ExecutionNotFoundError(execution_id)
        now = completed_at or datetime.now(UTC)
        return await self._atomic_cas_transition(
            execution_id,
            expected_statuses=(ExecutionStatus.RUNNING,),
            target_status=ExecutionStatus.SUCCEEDED,
            values={
                "result_json": dict(result_payload),
                "error_code": None,
                "error_message": None,
                "completed_at": now,
                "duration_ms": _compute_ms(existing.started_at or existing.created_at, now),
            },
        )

    async def mark_failed(
        self,
        execution_id: str,
        *,
        error_code: str,
        error_message: str,
        result_payload: dict[str, Any] | None = None,
        completed_at: datetime | None = None,
    ) -> ExecutionRecord:
        existing = await self.get(execution_id)
        if existing is None:
            raise ExecutionNotFoundError(execution_id)
        now = completed_at or datetime.now(UTC)
        values: dict[str, Any] = {
            "error_code": error_code,
            "error_message": sanitize_error_message(error_message),
            "completed_at": now,
            "duration_ms": _compute_ms(existing.started_at or existing.created_at, now),
        }
        if result_payload is not None:
            values["result_json"] = dict(result_payload)
        return await self._atomic_cas_transition(
            execution_id,
            expected_statuses=(ExecutionStatus.PENDING, ExecutionStatus.RUNNING),
            target_status=ExecutionStatus.FAILED,
            values=values,
        )

    async def mark_timed_out(
        self,
        execution_id: str,
        *,
        error_code: str,
        error_message: str,
        completed_at: datetime | None = None,
    ) -> ExecutionRecord:
        existing = await self.get(execution_id)
        if existing is None:
            raise ExecutionNotFoundError(execution_id)
        now = completed_at or datetime.now(UTC)
        return await self._atomic_cas_transition(
            execution_id,
            expected_statuses=(ExecutionStatus.RUNNING,),
            target_status=ExecutionStatus.TIMED_OUT,
            values={
                "error_code": error_code,
                "error_message": sanitize_error_message(error_message),
                "completed_at": now,
                "duration_ms": _compute_ms(existing.started_at or existing.created_at, now),
            },
        )

    async def request_cancel(
        self,
        execution_id: str,
        *,
        tenant_id: str,
    ) -> ExecutionRecord:
        existing = await self.get(execution_id, tenant_id=tenant_id)
        if existing is None:
            raise ExecutionNotFoundError(execution_id)
        if existing.is_terminal:
            raise InvalidExecutionTransitionError(
                execution_id,
                existing.status.value,
                ExecutionStatus.CANCELLED.value,
            )

        now = datetime.now(UTC)
        if existing.status == ExecutionStatus.PENDING:
            try:
                return await self._atomic_cas_transition(
                    execution_id,
                    expected_statuses=(ExecutionStatus.PENDING,),
                    target_status=ExecutionStatus.CANCELLED,
                    values={
                        "cancel_requested": True,
                        "cancel_requested_at": now,
                        "error_code": "EXECUTION_CANCELLED",
                        "error_message": "Execution cancelled before starting.",
                        "completed_at": now,
                        "duration_ms": 0,
                    },
                )
            except InvalidExecutionTransitionError:
                # Execution may have just transitioned to RUNNING; fall through to flag cancel
                existing = await self.get(execution_id, tenant_id=tenant_id)
                if existing is None:
                    raise ExecutionNotFoundError(execution_id) from None
                if existing.is_terminal:
                    raise

        async with self._session_factory() as session:
            stmt = (
                update(AgentExecution)
                .where(
                    and_(
                        AgentExecution.execution_id == execution_id,
                        AgentExecution.tenant_id == tenant_id,
                        AgentExecution.status == ExecutionStatus.RUNNING.value,
                    )
                )
                .values(cancel_requested=True, cancel_requested_at=now)
            )
            res = await session.execute(stmt)
            await session.commit()
            row_res = await session.execute(
                select(AgentExecution).where(AgentExecution.execution_id == execution_id)
            )
            row = row_res.scalar_one_or_none()
            if row is None:
                raise ExecutionNotFoundError(execution_id)
            if (res.rowcount or 0) == 0 and row.status != ExecutionStatus.RUNNING.value:
                raise InvalidExecutionTransitionError(
                    execution_id, row.status, ExecutionStatus.CANCELLED.value
                )
            return _orm_to_record(row)

    async def mark_cancelled(
        self,
        execution_id: str,
        *,
        reason: str = "Execution cancelled by request.",
        completed_at: datetime | None = None,
    ) -> ExecutionRecord:
        existing = await self.get(execution_id)
        if existing is None:
            raise ExecutionNotFoundError(execution_id)
        now = completed_at or datetime.now(UTC)
        return await self._atomic_cas_transition(
            execution_id,
            expected_statuses=(ExecutionStatus.PENDING, ExecutionStatus.RUNNING),
            target_status=ExecutionStatus.CANCELLED,
            values={
                "cancel_requested": True,
                "cancel_requested_at": existing.cancel_requested_at or now,
                "error_code": "EXECUTION_CANCELLED",
                "error_message": sanitize_error_message(reason),
                "completed_at": now,
                "duration_ms": _compute_ms(existing.started_at or existing.created_at, now),
            },
        )

    async def find_stale_running(self, *, stale_before: datetime) -> list[ExecutionRecord]:
        cutoff = _ensure_utc(stale_before) or datetime.now(UTC)
        async with self._session_factory() as session:
            stmt = select(AgentExecution).where(
                and_(
                    AgentExecution.status == ExecutionStatus.RUNNING.value,
                    AgentExecution.started_at.is_not(None),
                    AgentExecution.started_at < cutoff,
                )
            )
            res = await session.execute(stmt)
            return [_orm_to_record(row) for row in res.scalars().all()]
