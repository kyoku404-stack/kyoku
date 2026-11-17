"""KEEP Phase 4.3 — Durable Workflow Execution & Step Linkage Repositories.

Provides both `InMemoryWorkflowRepository` (unit testing / fast local dev) and
`SQLAlchemyWorkflowRepository` (PostgreSQL / async SQLAlchemy persistence with atomic
compare-and-set state transitions, scoped idempotency uniqueness, and strict tenant isolation).

Owner: Member 4 (FastAPI Integration, Persistence & End-to-End QA)
Specification: devdocs/p4/p4.3.txt (Sections 8, 13)
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from backend.app.agents.errors import (
    InvalidWorkflowTransitionError,
    WorkflowExecutionNotFoundError,
    WorkflowIdempotencyConflictError,
)
from backend.app.agents.orchestration.workflow_contracts import (
    TERMINAL_WORKFLOW_STATUSES,
    WorkflowExecutionRecord,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStepLink,
    is_valid_workflow_transition,
)
from backend.app.models.agent_workflow import AgentWorkflowExecution, AgentWorkflowStep
from sqlalchemy import and_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class InMemoryWorkflowRepository:
    """Thread/task-safe in-memory workflow repository implementing WorkflowRepositoryInterface."""

    def __init__(self) -> None:
        self._records: dict[str, WorkflowExecutionRecord] = {}
        self._steps: dict[str, list[WorkflowStepLink]] = {}
        self._idem_index: dict[tuple[str, str, str], str] = {}
        self._lock = asyncio.Lock()

    async def create(self, record: WorkflowExecutionRecord) -> WorkflowExecutionRecord:
        async with self._lock:
            if record.idempotency_key:
                idem_key = (record.tenant_id, record.requested_by, record.idempotency_key)
                if idem_key in self._idem_index:
                    existing = self._records[self._idem_index[idem_key]]
                    if existing.request_fingerprint != record.request_fingerprint:
                        raise WorkflowIdempotencyConflictError(record.idempotency_key)
                    return existing.model_copy(deep=True)
                self._idem_index[idem_key] = record.workflow_execution_id

            stored = record.model_copy(deep=True)
            self._records[stored.workflow_execution_id] = stored
            self._steps.setdefault(stored.workflow_execution_id, [])
            return stored.model_copy(deep=True)

    async def get(
        self, workflow_execution_id: str, tenant_id: str
    ) -> WorkflowExecutionRecord | None:
        async with self._lock:
            rec = self._records.get(workflow_execution_id)
            if rec is None or rec.tenant_id != tenant_id:
                return None
            copy = rec.model_copy(deep=True)
            copy.steps = list(self._steps.get(workflow_execution_id, []))
            return copy

    async def get_by_idempotency_key(
        self, tenant_id: str, requested_by: str, idempotency_key: str
    ) -> WorkflowExecutionRecord | None:
        async with self._lock:
            wf_id = self._idem_index.get((tenant_id, requested_by, idempotency_key))
            if wf_id is None:
                return None
            rec = self._records.get(wf_id)
            return rec.model_copy(deep=True) if rec is not None else None

    async def list_executions(
        self,
        tenant_id: str,
        *,
        workflow_id: str | None = None,
        status: WorkflowStatus | None = None,
        limit: int = 50,
    ) -> list[WorkflowExecutionRecord]:
        async with self._lock:
            items = [r.model_copy(deep=True) for r in self._records.values() if r.tenant_id == tenant_id]
            if workflow_id:
                items = [r for r in items if r.workflow_id == workflow_id]
            if status is not None:
                items = [r for r in items if r.status == status]
            items.sort(key=lambda r: r.created_at, reverse=True)
            return items[: max(1, min(limit, 200))]

    async def mark_running(
        self,
        workflow_execution_id: str,
        tenant_id: str,
        *,
        started_at: datetime,
        deadline_at: datetime | None = None,
        allow_from_recoverable: bool = False,
    ) -> WorkflowExecutionRecord:
        async with self._lock:
            rec = self._records.get(workflow_execution_id)
            if rec is None or rec.tenant_id != tenant_id:
                raise WorkflowExecutionNotFoundError(workflow_execution_id)
            if not allow_from_recoverable and not is_valid_workflow_transition(
                rec.status, WorkflowStatus.RUNNING
            ):
                raise InvalidWorkflowTransitionError(
                    workflow_execution_id, rec.status.value, WorkflowStatus.RUNNING.value
                )
            rec.status = WorkflowStatus.RUNNING
            rec.started_at = started_at
            if deadline_at is not None:
                rec.deadline_at = deadline_at
            rec.error_code = None
            rec.error_message = None
            return rec.model_copy(deep=True)

    async def append_step(
        self, workflow_execution_id: str, tenant_id: str, step: WorkflowStepLink
    ) -> None:
        async with self._lock:
            rec = self._records.get(workflow_execution_id)
            if rec is None or rec.tenant_id != tenant_id:
                raise WorkflowExecutionNotFoundError(workflow_execution_id)
            self._steps.setdefault(workflow_execution_id, []).append(step.model_copy(deep=True))
            if step.agent_execution_id not in rec.execution_ids:
                rec.execution_ids.append(step.agent_execution_id)

    async def update_checkpoint_ref(
        self, workflow_execution_id: str, tenant_id: str, checkpoint_ref: str
    ) -> None:
        async with self._lock:
            rec = self._records.get(workflow_execution_id)
            if rec is not None and rec.tenant_id == tenant_id:
                rec.checkpoint_ref = checkpoint_ref

    async def mark_completed(
        self,
        workflow_execution_id: str,
        tenant_id: str,
        *,
        status: WorkflowStatus,
        result: WorkflowResult | None,
        completed_at: datetime,
        duration_ms: int,
        error_code: str | None = None,
        error_message: str | None = None,
        warnings: list[str] | None = None,
    ) -> WorkflowExecutionRecord:
        async with self._lock:
            rec = self._records.get(workflow_execution_id)
            if rec is None or rec.tenant_id != tenant_id:
                raise WorkflowExecutionNotFoundError(workflow_execution_id)
            rec.status = status
            rec.result = result
            rec.completed_at = completed_at
            rec.duration_ms = duration_ms
            rec.error_code = error_code
            rec.error_message = error_message
            if warnings is not None:
                rec.warnings = list(warnings)
            return rec.model_copy(deep=True)

    async def request_cancel(
        self, workflow_execution_id: str, tenant_id: str, *, cancelled_at: datetime
    ) -> WorkflowExecutionRecord:
        async with self._lock:
            rec = self._records.get(workflow_execution_id)
            if rec is None or rec.tenant_id != tenant_id:
                raise WorkflowExecutionNotFoundError(workflow_execution_id)
            if rec.status in TERMINAL_WORKFLOW_STATUSES:
                raise InvalidWorkflowTransitionError(
                    workflow_execution_id, rec.status.value, WorkflowStatus.CANCELLED.value
                )
            rec.cancel_requested = True
            if rec.status == WorkflowStatus.PENDING:
                rec.status = WorkflowStatus.CANCELLED
                rec.completed_at = cancelled_at
            return rec.model_copy(deep=True)

    async def list_steps(
        self, workflow_execution_id: str, tenant_id: str
    ) -> list[WorkflowStepLink]:
        async with self._lock:
            rec = self._records.get(workflow_execution_id)
            if rec is None or rec.tenant_id != tenant_id:
                return []
            return [s.model_copy(deep=True) for s in self._steps.get(workflow_execution_id, [])]

    async def list_stale_running(self, now: datetime) -> list[WorkflowExecutionRecord]:
        async with self._lock:
            return [
                r.model_copy(deep=True)
                for r in self._records.values()
                if r.status == WorkflowStatus.RUNNING
                and r.deadline_at is not None
                and r.deadline_at < now
            ]


class SQLAlchemyWorkflowRepository:
    """Durable async SQLAlchemy repository for `agent_workflow_executions` and `agent_workflow_steps`."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _ensure_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

    @classmethod
    def _row_to_step(cls, row: AgentWorkflowStep) -> WorkflowStepLink:
        return WorkflowStepLink(
            step_id=row.step_id,
            workflow_execution_id=row.workflow_execution_id,
            tenant_id=row.tenant_id,
            node_name=row.node_name,
            agent_id=row.agent_id,
            agent_execution_id=row.agent_execution_id,
            role=row.role,  # type: ignore[arg-type]
            status=row.status,
            attempt_number=row.attempt_number,
            duration_ms=row.duration_ms,
            error_code=row.error_code,
            is_side_effecting=row.is_side_effecting,
            started_at=cls._ensure_utc(row.started_at or row.created_at) or datetime.now(UTC),
            completed_at=cls._ensure_utc(row.completed_at),
        )

    @classmethod
    def _row_to_record(
        cls,
        row: AgentWorkflowExecution,
        steps: list[WorkflowStepLink] | None = None,
    ) -> WorkflowExecutionRecord:
        step_list = steps or []
        result_obj = WorkflowResult.model_validate(row.result_json) if row.result_json else None
        exec_ids = [s.agent_execution_id for s in step_list]
        if result_obj and not exec_ids:
            exec_ids = list(result_obj.execution_ids)
        return WorkflowExecutionRecord(
            workflow_execution_id=row.workflow_execution_id,
            workflow_id=row.workflow_id,
            workflow_version=row.workflow_version,
            tenant_id=row.tenant_id,
            requested_by=row.requested_by,
            status=WorkflowStatus(row.status),
            mode=row.mode,  # type: ignore[arg-type]
            goal=row.goal,
            input=dict(row.input_json or {}),
            correlation_id=row.correlation_id,
            idempotency_key=row.idempotency_key,
            request_fingerprint=row.request_fingerprint,
            execution_ids=exec_ids,
            steps=step_list,
            result=result_obj,
            result_ref=row.result_ref,
            warnings=list(row.warnings_json or []),
            error_code=row.error_code,
            error_message=row.error_message,
            checkpoint_ref=row.checkpoint_ref,
            cancel_requested=row.cancel_requested,
            created_at=cls._ensure_utc(row.created_at) or datetime.now(UTC),
            started_at=cls._ensure_utc(row.started_at),
            completed_at=cls._ensure_utc(row.completed_at),
            deadline_at=cls._ensure_utc(row.deadline_at),
            duration_ms=row.duration_ms,
        )

    async def create(self, record: WorkflowExecutionRecord) -> WorkflowExecutionRecord:
        async with self._session_factory() as session:
            row = AgentWorkflowExecution(
                workflow_execution_id=record.workflow_execution_id,
                workflow_id=record.workflow_id,
                workflow_version=record.workflow_version,
                tenant_id=record.tenant_id,
                requested_by=record.requested_by,
                status=record.status.value,
                mode=record.mode,
                goal=record.goal,
                input_json=dict(record.input),
                result_json=record.result.model_dump(mode="json") if record.result else None,
                result_ref=record.result_ref,
                warnings_json=list(record.warnings),
                error_code=record.error_code,
                error_message=record.error_message,
                correlation_id=record.correlation_id,
                idempotency_key=record.idempotency_key,
                request_fingerprint=record.request_fingerprint,
                checkpoint_ref=record.checkpoint_ref,
                cancel_requested=record.cancel_requested,
                started_at=record.started_at,
                completed_at=record.completed_at,
                deadline_at=record.deadline_at,
                duration_ms=record.duration_ms,
            )
            session.add(row)
            try:
                await session.commit()
                await session.refresh(row)
                return self._row_to_record(row)
            except IntegrityError as exc:
                await session.rollback()
                if record.idempotency_key:
                    existing = await self.get_by_idempotency_key(
                        record.tenant_id, record.requested_by, record.idempotency_key
                    )
                    if existing is not None:
                        if existing.request_fingerprint != record.request_fingerprint:
                            raise WorkflowIdempotencyConflictError(record.idempotency_key) from exc
                        return existing
                raise

    async def get(
        self, workflow_execution_id: str, tenant_id: str
    ) -> WorkflowExecutionRecord | None:
        async with self._session_factory() as session:
            stmt = select(AgentWorkflowExecution).where(
                and_(
                    AgentWorkflowExecution.workflow_execution_id == workflow_execution_id,
                    AgentWorkflowExecution.tenant_id == tenant_id,
                )
            )
            res = await session.execute(stmt)
            row = res.scalar_one_or_none()
            if row is None:
                return None

            steps_stmt = (
                select(AgentWorkflowStep)
                .where(
                    and_(
                        AgentWorkflowStep.workflow_execution_id == workflow_execution_id,
                        AgentWorkflowStep.tenant_id == tenant_id,
                    )
                )
                .order_by(AgentWorkflowStep.created_at.asc())
            )
            step_rows = (await session.execute(steps_stmt)).scalars().all()
            return self._row_to_record(row, [self._row_to_step(s) for s in step_rows])

    async def get_by_idempotency_key(
        self, tenant_id: str, requested_by: str, idempotency_key: str
    ) -> WorkflowExecutionRecord | None:
        async with self._session_factory() as session:
            stmt = select(AgentWorkflowExecution).where(
                and_(
                    AgentWorkflowExecution.tenant_id == tenant_id,
                    AgentWorkflowExecution.requested_by == requested_by,
                    AgentWorkflowExecution.idempotency_key == idempotency_key,
                )
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return self._row_to_record(row) if row is not None else None

    async def list_executions(
        self,
        tenant_id: str,
        *,
        workflow_id: str | None = None,
        status: WorkflowStatus | None = None,
        limit: int = 50,
    ) -> list[WorkflowExecutionRecord]:
        async with self._session_factory() as session:
            conditions = [AgentWorkflowExecution.tenant_id == tenant_id]
            if workflow_id:
                conditions.append(AgentWorkflowExecution.workflow_id == workflow_id)
            if status is not None:
                conditions.append(AgentWorkflowExecution.status == status.value)

            stmt = (
                select(AgentWorkflowExecution)
                .where(and_(*conditions))
                .order_by(AgentWorkflowExecution.created_at.desc())
                .limit(max(1, min(limit, 200)))
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [self._row_to_record(r) for r in rows]

    async def mark_running(
        self,
        workflow_execution_id: str,
        tenant_id: str,
        *,
        started_at: datetime,
        deadline_at: datetime | None = None,
        allow_from_recoverable: bool = False,
    ) -> WorkflowExecutionRecord:
        allowed_from = (
            [WorkflowStatus.PENDING.value, WorkflowStatus.FAILED.value, WorkflowStatus.TIMED_OUT.value, WorkflowStatus.RUNNING.value]
            if allow_from_recoverable
            else [WorkflowStatus.PENDING.value]
        )
        async with self._session_factory() as session:
            values = {
                "status": WorkflowStatus.RUNNING.value,
                "started_at": started_at,
                "error_code": None,
                "error_message": None,
            }
            if deadline_at is not None:
                values["deadline_at"] = deadline_at

            stmt = (
                update(AgentWorkflowExecution)
                .where(
                    and_(
                        AgentWorkflowExecution.workflow_execution_id == workflow_execution_id,
                        AgentWorkflowExecution.tenant_id == tenant_id,
                        AgentWorkflowExecution.status.in_(allowed_from),
                    )
                )
                .values(**values)
            )
            res = await session.execute(stmt)
            await session.commit()

            current = await self.get(workflow_execution_id, tenant_id)
            if current is None:
                raise WorkflowExecutionNotFoundError(workflow_execution_id)
            if res.rowcount == 0:
                raise InvalidWorkflowTransitionError(
                    workflow_execution_id, current.status.value, WorkflowStatus.RUNNING.value
                )
            return current

    async def append_step(
        self, workflow_execution_id: str, tenant_id: str, step: WorkflowStepLink
    ) -> None:
        async with self._session_factory() as session:
            row = AgentWorkflowStep(
                step_id=step.step_id,
                workflow_execution_id=workflow_execution_id,
                tenant_id=tenant_id,
                node_name=step.node_name,
                agent_id=step.agent_id,
                agent_execution_id=step.agent_execution_id,
                role=step.role,
                status=step.status,
                attempt_number=step.attempt_number,
                duration_ms=step.duration_ms,
                error_code=step.error_code,
                is_side_effecting=step.is_side_effecting,
                started_at=step.started_at,
                completed_at=step.completed_at,
            )
            session.add(row)
            await session.commit()

    async def update_checkpoint_ref(
        self, workflow_execution_id: str, tenant_id: str, checkpoint_ref: str
    ) -> None:
        async with self._session_factory() as session:
            stmt = (
                update(AgentWorkflowExecution)
                .where(
                    and_(
                        AgentWorkflowExecution.workflow_execution_id == workflow_execution_id,
                        AgentWorkflowExecution.tenant_id == tenant_id,
                    )
                )
                .values(checkpoint_ref=checkpoint_ref)
            )
            await session.execute(stmt)
            await session.commit()

    async def mark_completed(
        self,
        workflow_execution_id: str,
        tenant_id: str,
        *,
        status: WorkflowStatus,
        result: WorkflowResult | None,
        completed_at: datetime,
        duration_ms: int,
        error_code: str | None = None,
        error_message: str | None = None,
        warnings: list[str] | None = None,
    ) -> WorkflowExecutionRecord:
        async with self._session_factory() as session:
            values = {
                "status": status.value,
                "result_json": result.model_dump(mode="json") if result else None,
                "completed_at": completed_at,
                "duration_ms": duration_ms,
                "error_code": error_code,
                "error_message": error_message,
            }
            if warnings is not None:
                values["warnings_json"] = list(warnings)

            stmt = (
                update(AgentWorkflowExecution)
                .where(
                    and_(
                        AgentWorkflowExecution.workflow_execution_id == workflow_execution_id,
                        AgentWorkflowExecution.tenant_id == tenant_id,
                    )
                )
                .values(**values)
            )
            await session.execute(stmt)
            await session.commit()

        updated = await self.get(workflow_execution_id, tenant_id)
        if updated is None:
            raise WorkflowExecutionNotFoundError(workflow_execution_id)
        return updated

    async def request_cancel(
        self, workflow_execution_id: str, tenant_id: str, *, cancelled_at: datetime
    ) -> WorkflowExecutionRecord:
        current = await self.get(workflow_execution_id, tenant_id)
        if current is None:
            raise WorkflowExecutionNotFoundError(workflow_execution_id)
        if current.status in TERMINAL_WORKFLOW_STATUSES:
            raise InvalidWorkflowTransitionError(
                workflow_execution_id, current.status.value, WorkflowStatus.CANCELLED.value
            )

        async with self._session_factory() as session:
            values: dict = {"cancel_requested": True}
            if current.status == WorkflowStatus.PENDING:
                values["status"] = WorkflowStatus.CANCELLED.value
                values["completed_at"] = cancelled_at
            stmt = (
                update(AgentWorkflowExecution)
                .where(
                    and_(
                        AgentWorkflowExecution.workflow_execution_id == workflow_execution_id,
                        AgentWorkflowExecution.tenant_id == tenant_id,
                    )
                )
                .values(**values)
            )
            await session.execute(stmt)
            await session.commit()

        refreshed = await self.get(workflow_execution_id, tenant_id)
        assert refreshed is not None
        return refreshed

    async def list_steps(
        self, workflow_execution_id: str, tenant_id: str
    ) -> list[WorkflowStepLink]:
        async with self._session_factory() as session:
            stmt = (
                select(AgentWorkflowStep)
                .where(
                    and_(
                        AgentWorkflowStep.workflow_execution_id == workflow_execution_id,
                        AgentWorkflowStep.tenant_id == tenant_id,
                    )
                )
                .order_by(AgentWorkflowStep.created_at.asc())
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [self._row_to_step(r) for r in rows]

    async def list_stale_running(self, now: datetime) -> list[WorkflowExecutionRecord]:
        check_time = now or datetime.now(UTC)
        async with self._session_factory() as session:
            stmt = select(AgentWorkflowExecution).where(
                and_(
                    AgentWorkflowExecution.status == WorkflowStatus.RUNNING.value,
                    AgentWorkflowExecution.deadline_at.is_not(None),
                    AgentWorkflowExecution.deadline_at < check_time,
                )
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [self._row_to_record(r) for r in rows]
