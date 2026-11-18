"""KEEP Phase 4.4 — Durable Plan, Immutable Revision, Task & Event Repositories.

Provides `InMemoryPlanRepository` and `SQLAlchemyPlanRepository` persisting plans,
immutable revisions, resolved tasks, and audit events strictly scoped by `tenant_id`.

Owner: Member 4 (FastAPI, Persistence & Integration Testing)
Specification: devdocs/p4/p4.4.txt (Section 10)
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from backend.app.agents.errors import PlanNotFoundError
from backend.app.agents.planning.contracts import (
    ExecutionPlan,
    GoalSpec,
    PlanEventRecord,
    PlannedTask,
    PlanRevisionSnapshot,
    PlanStatus,
    ValidationFinding,
)
from backend.app.models.agent_plan import (
    AgentPlan,
    AgentPlanEvent,
    AgentPlanRevision,
    AgentPlanTask,
)
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class InMemoryPlanRepository:
    """In-memory tenant-scoped repository implementing PlanRepositoryInterface."""

    def __init__(self) -> None:
        self._plans: dict[str, ExecutionPlan] = {}
        self._revisions: dict[str, list[PlanRevisionSnapshot]] = {}
        self._events: dict[str, list[PlanEventRecord]] = {}
        self._lock = asyncio.Lock()

    async def save_plan(
        self,
        plan: ExecutionPlan,
        *,
        revision_reason: str,
    ) -> ExecutionPlan:
        async with self._lock:
            now = datetime.now(UTC)
            stored = plan.model_copy(
                deep=True,
                update={"revision_reason": revision_reason, "updated_at": now},
            )
            self._plans[stored.plan_id] = stored
            rev = PlanRevisionSnapshot(
                plan_id=stored.plan_id,
                version=stored.version,
                tenant_id=stored.tenant_id,
                status=stored.status,
                revision_reason=revision_reason,
                policy_version=stored.policy_version,
                snapshot=stored.model_dump(mode="json"),
                validation_findings=list(stored.validation_findings),
                created_at=now,
            )
            self._revisions.setdefault(stored.plan_id, []).append(rev)
            return stored.model_copy(deep=True)

    async def get_plan(self, plan_id: str, tenant_id: str) -> ExecutionPlan | None:
        async with self._lock:
            plan = self._plans.get(plan_id)
            if plan is None or plan.tenant_id != tenant_id:
                return None
            return plan.model_copy(deep=True)

    async def list_plans(
        self,
        tenant_id: str,
        *,
        status: PlanStatus | None = None,
        limit: int = 50,
    ) -> list[ExecutionPlan]:
        async with self._lock:
            items = [
                p.model_copy(deep=True)
                for p in self._plans.values()
                if p.tenant_id == tenant_id and (status is None or p.status == status)
            ]
            items.sort(key=lambda p: p.created_at, reverse=True)
            return items[: max(1, min(limit, 200))]

    async def list_revisions(
        self, plan_id: str, tenant_id: str
    ) -> list[PlanRevisionSnapshot]:
        async with self._lock:
            return [
                r.model_copy(deep=True)
                for r in self._revisions.get(plan_id, [])
                if r.tenant_id == tenant_id
            ]

    async def append_event(self, event: PlanEventRecord) -> None:
        async with self._lock:
            self._events.setdefault(event.plan_id, []).append(event.model_copy(deep=True))

    async def list_events(self, plan_id: str, tenant_id: str) -> list[PlanEventRecord]:
        async with self._lock:
            return [
                e.model_copy(deep=True)
                for e in self._events.get(plan_id, [])
                if e.tenant_id == tenant_id
            ]

    async def mark_submitted(
        self,
        plan_id: str,
        tenant_id: str,
        *,
        workflow_execution_id: str,
    ) -> ExecutionPlan:
        async with self._lock:
            plan = self._plans.get(plan_id)
            if plan is None or plan.tenant_id != tenant_id:
                raise PlanNotFoundError(plan_id)
            updated = plan.model_copy(
                deep=True,
                update={
                    "status": PlanStatus.SUBMITTED,
                    "workflow_execution_id": workflow_execution_id,
                    "updated_at": datetime.now(UTC),
                },
            )
            self._plans[plan_id] = updated
            return updated.model_copy(deep=True)


class SQLAlchemyPlanRepository:
    """Durable async SQLAlchemy repository for Phase 4.4 planning tables."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _ensure_utc(dt: datetime | None) -> datetime:
        if dt is None:
            return datetime.now(UTC)
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

    @classmethod
    def _rows_to_plan(
        cls,
        row: AgentPlan,
        task_rows: list[AgentPlanTask],
    ) -> ExecutionPlan:
        tasks = [
            PlannedTask(
                task_id=t.task_id,
                description=t.description,
                required_capabilities=list(t.required_capabilities_json or []),
                depends_on=list(t.depends_on_json or []),
                input_refs=list(t.input_refs_json or []),
                output_key=t.output_key,
                required=t.required,
                requires_evidence=t.requires_evidence,
                is_side_effecting=t.is_side_effecting,
                estimated_tokens=t.estimated_tokens,
                parallel_group=t.parallel_group,
                resolved_agent_id=t.resolved_agent_id,
                resolved_agent_version=t.resolved_agent_version,
            )
            for t in task_rows
        ]
        findings = [
            ValidationFinding.model_validate(f) for f in (row.validation_findings_json or [])
        ]
        return ExecutionPlan(
            plan_id=row.plan_id,
            version=row.current_version,
            goal=GoalSpec.model_validate(row.goal_json),
            tasks=tasks,
            execution_layers=list(row.execution_layers_json or []),
            max_steps=row.max_steps,
            max_replans=row.max_replans,
            replan_count=row.replan_count,
            status=PlanStatus(row.status),
            input=dict(row.input_json or {}),
            tenant_id=row.tenant_id,
            requested_by=row.requested_by,
            correlation_id=row.correlation_id,
            source_request_id=row.source_request_id,
            policy_version=row.policy_version,
            validation_findings=findings,
            approval_required=row.approval_required,
            approval_reasons=list(row.approval_reasons_json or []),
            clarification_questions=list(row.clarification_questions_json or []),
            workflow_execution_id=row.workflow_execution_id,
            revision_reason=row.revision_reason,
            created_at=cls._ensure_utc(row.created_at),
            updated_at=cls._ensure_utc(row.updated_at),
        )

    async def save_plan(
        self,
        plan: ExecutionPlan,
        *,
        revision_reason: str,
    ) -> ExecutionPlan:
        now = datetime.now(UTC)
        stored = plan.model_copy(update={"revision_reason": revision_reason, "updated_at": now})
        findings_payload = [f.model_dump(mode="json") for f in stored.validation_findings]

        async with self._session_factory() as session:
            existing_stmt = select(AgentPlan).where(
                and_(
                    AgentPlan.plan_id == stored.plan_id,
                    AgentPlan.tenant_id == stored.tenant_id,
                )
            )
            existing = (await session.execute(existing_stmt)).scalar_one_or_none()

            if existing is None:
                row = AgentPlan(
                    plan_id=stored.plan_id,
                    current_version=stored.version,
                    tenant_id=stored.tenant_id,
                    requested_by=stored.requested_by,
                    status=stored.status.value,
                    goal_text=stored.goal.goal,
                    goal_json=stored.goal.model_dump(mode="json"),
                    input_json=dict(stored.input),
                    execution_layers_json=list(stored.execution_layers),
                    validation_findings_json=findings_payload,
                    approval_required=stored.approval_required,
                    approval_reasons_json=list(stored.approval_reasons),
                    clarification_questions_json=list(stored.clarification_questions),
                    policy_version=stored.policy_version,
                    max_steps=stored.max_steps,
                    max_replans=stored.max_replans,
                    replan_count=stored.replan_count,
                    revision_reason=revision_reason,
                    correlation_id=stored.correlation_id,
                    source_request_id=stored.source_request_id,
                    workflow_execution_id=stored.workflow_execution_id,
                )
                session.add(row)
            else:
                existing.current_version = stored.version
                existing.status = stored.status.value
                existing.goal_text = stored.goal.goal
                existing.goal_json = stored.goal.model_dump(mode="json")
                existing.input_json = dict(stored.input)
                existing.execution_layers_json = list(stored.execution_layers)
                existing.validation_findings_json = findings_payload
                existing.approval_required = stored.approval_required
                existing.approval_reasons_json = list(stored.approval_reasons)
                existing.clarification_questions_json = list(stored.clarification_questions)
                existing.policy_version = stored.policy_version
                existing.replan_count = stored.replan_count
                existing.revision_reason = revision_reason
                existing.workflow_execution_id = stored.workflow_execution_id

            # Persist immutable revision snapshot
            rev_row = AgentPlanRevision(
                revision_id=f"planrev_{uuid4().hex[:16]}",
                plan_id=stored.plan_id,
                version=stored.version,
                tenant_id=stored.tenant_id,
                status=stored.status.value,
                revision_reason=revision_reason,
                policy_version=stored.policy_version,
                snapshot_json=stored.model_dump(mode="json"),
                validation_findings_json=findings_payload,
            )
            session.add(rev_row)

            # Persist task rows for this plan version
            for task in stored.tasks:
                session.add(
                    AgentPlanTask(
                        plan_task_pk=f"plantask_{uuid4().hex[:16]}",
                        plan_id=stored.plan_id,
                        plan_version=stored.version,
                        tenant_id=stored.tenant_id,
                        task_id=task.task_id,
                        description=task.description,
                        required_capabilities_json=list(task.required_capabilities),
                        depends_on_json=list(task.depends_on),
                        input_refs_json=list(task.input_refs),
                        output_key=task.output_key,
                        required=task.required,
                        requires_evidence=task.requires_evidence,
                        is_side_effecting=task.is_side_effecting,
                        estimated_tokens=task.estimated_tokens,
                        parallel_group=task.parallel_group,
                        resolved_agent_id=task.resolved_agent_id,
                        resolved_agent_version=task.resolved_agent_version,
                    )
                )

            await session.commit()

        loaded = await self.get_plan(stored.plan_id, stored.tenant_id)
        assert loaded is not None
        return loaded

    async def get_plan(self, plan_id: str, tenant_id: str) -> ExecutionPlan | None:
        async with self._session_factory() as session:
            stmt = select(AgentPlan).where(
                and_(AgentPlan.plan_id == plan_id, AgentPlan.tenant_id == tenant_id)
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                return None

            tasks_stmt = (
                select(AgentPlanTask)
                .where(
                    and_(
                        AgentPlanTask.plan_id == plan_id,
                        AgentPlanTask.plan_version == row.current_version,
                        AgentPlanTask.tenant_id == tenant_id,
                    )
                )
                .order_by(AgentPlanTask.parallel_group.asc(), AgentPlanTask.task_id.asc())
            )
            task_rows = list((await session.execute(tasks_stmt)).scalars().all())
            return self._rows_to_plan(row, task_rows)

    async def list_plans(
        self,
        tenant_id: str,
        *,
        status: PlanStatus | None = None,
        limit: int = 50,
    ) -> list[ExecutionPlan]:
        async with self._session_factory() as session:
            conds = [AgentPlan.tenant_id == tenant_id]
            if status is not None:
                conds.append(AgentPlan.status == status.value)
            stmt = (
                select(AgentPlan)
                .where(and_(*conds))
                .order_by(AgentPlan.created_at.desc())
                .limit(max(1, min(limit, 200)))
            )
            rows = list((await session.execute(stmt)).scalars().all())
            results: list[ExecutionPlan] = []
            for row in rows:
                t_stmt = (
                    select(AgentPlanTask)
                    .where(
                        and_(
                            AgentPlanTask.plan_id == row.plan_id,
                            AgentPlanTask.plan_version == row.current_version,
                            AgentPlanTask.tenant_id == tenant_id,
                        )
                    )
                    .order_by(AgentPlanTask.parallel_group.asc(), AgentPlanTask.task_id.asc())
                )
                t_rows = list((await session.execute(t_stmt)).scalars().all())
                results.append(self._rows_to_plan(row, t_rows))
            return results

    async def list_revisions(
        self, plan_id: str, tenant_id: str
    ) -> list[PlanRevisionSnapshot]:
        async with self._session_factory() as session:
            stmt = (
                select(AgentPlanRevision)
                .where(
                    and_(
                        AgentPlanRevision.plan_id == plan_id,
                        AgentPlanRevision.tenant_id == tenant_id,
                    )
                )
                .order_by(AgentPlanRevision.version.asc())
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [
                PlanRevisionSnapshot(
                    revision_id=r.revision_id,
                    plan_id=r.plan_id,
                    version=r.version,
                    tenant_id=r.tenant_id,
                    status=PlanStatus(r.status),
                    revision_reason=r.revision_reason,
                    policy_version=r.policy_version,
                    snapshot=dict(r.snapshot_json or {}),
                    validation_findings=[
                        ValidationFinding.model_validate(f)
                        for f in (r.validation_findings_json or [])
                    ],
                    created_at=self._ensure_utc(r.created_at),
                )
                for r in rows
            ]

    async def append_event(self, event: PlanEventRecord) -> None:
        async with self._session_factory() as session:
            session.add(
                AgentPlanEvent(
                    event_id=event.event_id,
                    plan_id=event.plan_id,
                    tenant_id=event.tenant_id,
                    event_type=event.event_type,
                    actor_id=event.actor_id,
                    correlation_id=event.correlation_id,
                    details_json=dict(event.details),
                )
            )
            await session.commit()

    async def list_events(self, plan_id: str, tenant_id: str) -> list[PlanEventRecord]:
        async with self._session_factory() as session:
            stmt = (
                select(AgentPlanEvent)
                .where(
                    and_(
                        AgentPlanEvent.plan_id == plan_id,
                        AgentPlanEvent.tenant_id == tenant_id,
                    )
                )
                .order_by(AgentPlanEvent.created_at.asc())
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [
                PlanEventRecord(
                    event_id=r.event_id,
                    plan_id=r.plan_id,
                    tenant_id=r.tenant_id,
                    event_type=r.event_type,
                    actor_id=r.actor_id,
                    correlation_id=r.correlation_id,
                    details=dict(r.details_json or {}),
                    created_at=self._ensure_utc(r.created_at),
                )
                for r in rows
            ]

    async def mark_submitted(
        self,
        plan_id: str,
        tenant_id: str,
        *,
        workflow_execution_id: str,
    ) -> ExecutionPlan:
        async with self._session_factory() as session:
            stmt = (
                update(AgentPlan)
                .where(and_(AgentPlan.plan_id == plan_id, AgentPlan.tenant_id == tenant_id))
                .values(
                    status=PlanStatus.SUBMITTED.value,
                    workflow_execution_id=workflow_execution_id,
                )
            )
            res = await session.execute(stmt)
            await session.commit()
            if res.rowcount == 0:
                raise PlanNotFoundError(plan_id)

        loaded = await self.get_plan(plan_id, tenant_id)
        assert loaded is not None
        return loaded
