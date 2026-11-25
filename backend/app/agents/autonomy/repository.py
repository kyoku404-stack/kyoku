"""KEEP Phase 4.9 — Autonomous Workflow Repository Protocol & In-Memory Store.

Provides BaseAutonomyRepository and InMemoryAutonomyRepository for deterministic
unit tests and fallback operation. Member 2 adds SqlAlchemyAutonomyRepository.

Owner: Member 1 (Core Interface) / Member 2 (SQLAlchemy Persistence)
Specification: devdocs/p4/p4.9.txt (Section 7)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from backend.app.agents.autonomy.contracts import (
    AutonomousStepRecord,
    AutonomousWorkflowRecord,
    AutonomyBudgetSnapshot,
    AutonomyDecisionRecord,
    AutonomyEventRecord,
    AutonomyStatus,
)


class BaseAutonomyRepository(ABC):
    """Abstract tenant-isolated repository for autonomous workflow persistence."""

    @abstractmethod
    async def create_workflow(
        self,
        workflow: AutonomousWorkflowRecord,
        budget: AutonomyBudgetSnapshot,
    ) -> AutonomousWorkflowRecord: ...

    @abstractmethod
    async def get_workflow(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> AutonomousWorkflowRecord | None: ...

    @abstractmethod
    async def find_by_idempotency_key(
        self,
        tenant_id: str,
        requested_by: str,
        idempotency_key: str,
    ) -> AutonomousWorkflowRecord | None: ...

    @abstractmethod
    async def update_workflow(
        self,
        workflow: AutonomousWorkflowRecord,
    ) -> AutonomousWorkflowRecord: ...

    @abstractmethod
    async def list_workflows(
        self,
        tenant_id: str,
        status: AutonomyStatus | None = None,
        limit: int = 50,
    ) -> list[AutonomousWorkflowRecord]: ...

    @abstractmethod
    async def save_steps(
        self,
        execution_id: str,
        tenant_id: str,
        steps: list[AutonomousStepRecord],
    ) -> list[AutonomousStepRecord]: ...

    @abstractmethod
    async def upsert_step(self, step: AutonomousStepRecord) -> AutonomousStepRecord: ...

    @abstractmethod
    async def list_steps(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> list[AutonomousStepRecord]: ...

    @abstractmethod
    async def append_decision(
        self,
        decision: AutonomyDecisionRecord,
    ) -> AutonomyDecisionRecord: ...

    @abstractmethod
    async def list_decisions(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> list[AutonomyDecisionRecord]: ...

    @abstractmethod
    async def append_event(self, event: AutonomyEventRecord) -> AutonomyEventRecord: ...

    @abstractmethod
    async def list_events(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> list[AutonomyEventRecord]: ...

    @abstractmethod
    async def get_budget(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> AutonomyBudgetSnapshot | None: ...

    @abstractmethod
    async def update_budget(
        self,
        budget: AutonomyBudgetSnapshot,
    ) -> AutonomyBudgetSnapshot: ...


class InMemoryAutonomyRepository(BaseAutonomyRepository):
    """Thread/async-safe tenant-isolated in-memory store for Phase 4.9 workflows."""

    def __init__(self) -> None:
        self._workflows: dict[str, AutonomousWorkflowRecord] = {}
        self._budgets: dict[str, AutonomyBudgetSnapshot] = {}
        self._steps: dict[str, list[AutonomousStepRecord]] = {}
        self._decisions: dict[str, list[AutonomyDecisionRecord]] = {}
        self._events: dict[str, list[AutonomyEventRecord]] = {}

    async def create_workflow(
        self,
        workflow: AutonomousWorkflowRecord,
        budget: AutonomyBudgetSnapshot,
    ) -> AutonomousWorkflowRecord:
        workflow_copy = workflow.model_copy(deep=True)
        budget_copy = budget.model_copy(deep=True)
        workflow_copy.budget = budget_copy
        self._workflows[workflow.execution_id] = workflow_copy
        self._budgets[workflow.execution_id] = budget_copy
        self._steps.setdefault(workflow.execution_id, [])
        self._decisions.setdefault(workflow.execution_id, [])
        self._events.setdefault(workflow.execution_id, [])
        return workflow_copy.model_copy(deep=True)

    async def get_workflow(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> AutonomousWorkflowRecord | None:
        wf = self._workflows.get(execution_id)
        if wf is None or wf.tenant_id != tenant_id:
            return None
        copy = wf.model_copy(deep=True)
        budget = self._budgets.get(execution_id)
        if budget is not None:
            copy.budget = budget.model_copy(deep=True)
        return copy

    async def find_by_idempotency_key(
        self,
        tenant_id: str,
        requested_by: str,
        idempotency_key: str,
    ) -> AutonomousWorkflowRecord | None:
        for wf in self._workflows.values():
            if (
                wf.tenant_id == tenant_id
                and wf.requested_by == requested_by
                and wf.idempotency_key == idempotency_key
            ):
                return await self.get_workflow(wf.execution_id, tenant_id)
        return None

    async def update_workflow(
        self,
        workflow: AutonomousWorkflowRecord,
    ) -> AutonomousWorkflowRecord:
        existing = self._workflows.get(workflow.execution_id)
        if existing is None or existing.tenant_id != workflow.tenant_id:
            return workflow.model_copy(deep=True)
        updated = workflow.model_copy(deep=True)
        updated.updated_at = datetime.now(UTC)
        self._workflows[workflow.execution_id] = updated
        if updated.budget is not None:
            self._budgets[workflow.execution_id] = updated.budget.model_copy(deep=True)
        return updated.model_copy(deep=True)

    async def list_workflows(
        self,
        tenant_id: str,
        status: AutonomyStatus | None = None,
        limit: int = 50,
    ) -> list[AutonomousWorkflowRecord]:
        results = [
            wf.model_copy(deep=True)
            for wf in self._workflows.values()
            if wf.tenant_id == tenant_id and (status is None or wf.status == status)
        ]
        results.sort(key=lambda item: item.created_at, reverse=True)
        for item in results:
            budget = self._budgets.get(item.execution_id)
            if budget is not None:
                item.budget = budget.model_copy(deep=True)
        return results[:limit]

    async def save_steps(
        self,
        execution_id: str,
        tenant_id: str,
        steps: list[AutonomousStepRecord],
    ) -> list[AutonomousStepRecord]:
        wf = self._workflows.get(execution_id)
        if wf is None or wf.tenant_id != tenant_id:
            return []
        existing = list(self._steps.get(execution_id, []))
        existing_ids = {s.step_id for s in existing}
        for step in steps:
            if step.tenant_id != tenant_id:
                continue
            if step.step_id in existing_ids:
                existing = [
                    step.model_copy(deep=True) if s.step_id == step.step_id else s
                    for s in existing
                ]
            else:
                existing.append(step.model_copy(deep=True))
                existing_ids.add(step.step_id)
        self._steps[execution_id] = existing
        return [s.model_copy(deep=True) for s in existing]

    async def upsert_step(self, step: AutonomousStepRecord) -> AutonomousStepRecord:
        await self.save_steps(step.execution_id, step.tenant_id, [step])
        return step.model_copy(deep=True)

    async def list_steps(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> list[AutonomousStepRecord]:
        wf = self._workflows.get(execution_id)
        if wf is None or wf.tenant_id != tenant_id:
            return []
        steps = [s.model_copy(deep=True) for s in self._steps.get(execution_id, [])]
        steps.sort(key=lambda s: (s.plan_version, s.step_order))
        return steps

    async def append_decision(
        self,
        decision: AutonomyDecisionRecord,
    ) -> AutonomyDecisionRecord:
        wf = self._workflows.get(decision.execution_id)
        if wf is not None and wf.tenant_id == decision.tenant_id:
            self._decisions.setdefault(decision.execution_id, []).append(
                decision.model_copy(deep=True)
            )
        return decision.model_copy(deep=True)

    async def list_decisions(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> list[AutonomyDecisionRecord]:
        wf = self._workflows.get(execution_id)
        if wf is None or wf.tenant_id != tenant_id:
            return []
        return [d.model_copy(deep=True) for d in self._decisions.get(execution_id, [])]

    async def append_event(self, event: AutonomyEventRecord) -> AutonomyEventRecord:
        wf = self._workflows.get(event.execution_id)
        if wf is not None and wf.tenant_id == event.tenant_id:
            self._events.setdefault(event.execution_id, []).append(event.model_copy(deep=True))
        return event.model_copy(deep=True)

    async def list_events(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> list[AutonomyEventRecord]:
        wf = self._workflows.get(execution_id)
        if wf is None or wf.tenant_id != tenant_id:
            return []
        return [e.model_copy(deep=True) for e in self._events.get(execution_id, [])]

    async def get_budget(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> AutonomyBudgetSnapshot | None:
        wf = self._workflows.get(execution_id)
        if wf is None or wf.tenant_id != tenant_id:
            return None
        b = self._budgets.get(execution_id)
        return b.model_copy(deep=True) if b is not None else None

    async def update_budget(
        self,
        budget: AutonomyBudgetSnapshot,
    ) -> AutonomyBudgetSnapshot:
        wf = self._workflows.get(budget.execution_id)
        if wf is not None and wf.tenant_id == budget.tenant_id:
            copy = budget.model_copy(deep=True)
            copy.updated_at = datetime.now(UTC)
            self._budgets[budget.execution_id] = copy
            return copy.model_copy(deep=True)
        return budget.model_copy(deep=True)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


class SqlAlchemyAutonomyRepository(BaseAutonomyRepository):
    """Durable SQLAlchemy repository persisting Phase 4.9 workflows, steps, decisions, events, and budgets."""

    def __init__(
        self,
        session_factory: object | None = None,
        *,
        session: object | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._session = session
        self._fallback = InMemoryAutonomyRepository()

    @property
    def is_persistent(self) -> bool:
        return self._session_factory is not None or self._session is not None

    @staticmethod
    def _to_budget(row: object) -> AutonomyBudgetSnapshot:
        return AutonomyBudgetSnapshot(
            execution_id=row.execution_id,  # type: ignore[attr-defined]
            tenant_id=row.tenant_id,  # type: ignore[attr-defined]
            max_steps=row.max_steps,  # type: ignore[attr-defined]
            steps_consumed=row.steps_consumed,  # type: ignore[attr-defined]
            max_replans=row.max_replans,  # type: ignore[attr-defined]
            replans_consumed=row.replans_consumed,  # type: ignore[attr-defined]
            max_agent_attempts=row.max_agent_attempts,  # type: ignore[attr-defined]
            total_agent_attempts=row.total_agent_attempts,  # type: ignore[attr-defined]
            deadline_seconds=row.deadline_seconds,  # type: ignore[attr-defined]
            updated_at=_ensure_utc(row.updated_at) or datetime.now(UTC),  # type: ignore[attr-defined]
        )

    @staticmethod
    def _to_workflow(row: object, budget: AutonomyBudgetSnapshot | None = None) -> AutonomousWorkflowRecord:
        from backend.app.agents.autonomy.contracts import AutonomyPolicy

        return AutonomousWorkflowRecord(
            execution_id=row.execution_id,  # type: ignore[attr-defined]
            tenant_id=row.tenant_id,  # type: ignore[attr-defined]
            requested_by=row.requested_by,  # type: ignore[attr-defined]
            workflow_id=row.workflow_id,  # type: ignore[attr-defined]
            objective=row.objective,  # type: ignore[attr-defined]
            status=row.status,  # type: ignore[attr-defined]
            policy=AutonomyPolicy.model_validate(row.policy_snapshot or {}),  # type: ignore[attr-defined]
            budget=budget,
            current_plan=dict(row.current_plan or {}),  # type: ignore[attr-defined]
            current_step_index=row.current_step_index,  # type: ignore[attr-defined]
            replan_count=row.replan_count,  # type: ignore[attr-defined]
            termination_reason=row.termination_reason,  # type: ignore[attr-defined]
            limitations=list(row.limitations or []),  # type: ignore[attr-defined]
            final_result=dict(row.final_result or {}),  # type: ignore[attr-defined]
            checkpoint_ref=row.checkpoint_ref,  # type: ignore[attr-defined]
            idempotency_key=row.idempotency_key,  # type: ignore[attr-defined]
            idempotency_fingerprint=row.idempotency_fingerprint,  # type: ignore[attr-defined]
            deadline_at=_ensure_utc(row.deadline_at) or datetime.now(UTC),  # type: ignore[attr-defined]
            created_at=_ensure_utc(row.created_at) or datetime.now(UTC),  # type: ignore[attr-defined]
            updated_at=_ensure_utc(row.updated_at) or datetime.now(UTC),  # type: ignore[attr-defined]
            completed_at=_ensure_utc(row.completed_at),  # type: ignore[attr-defined]
        )

    @staticmethod
    def _to_step(row: object) -> AutonomousStepRecord:
        return AutonomousStepRecord(
            step_id=row.step_id,  # type: ignore[attr-defined]
            execution_id=row.execution_id,  # type: ignore[attr-defined]
            tenant_id=row.tenant_id,  # type: ignore[attr-defined]
            plan_version=row.plan_version,  # type: ignore[attr-defined]
            step_order=row.step_order,  # type: ignore[attr-defined]
            title=row.title,  # type: ignore[attr-defined]
            agent_id=row.agent_id,  # type: ignore[attr-defined]
            tool_id=row.tool_id,  # type: ignore[attr-defined]
            required_capability=row.required_capability,  # type: ignore[attr-defined]
            is_side_effecting=row.is_side_effecting,  # type: ignore[attr-defined]
            status=row.status,  # type: ignore[attr-defined]
            attempt=row.attempt,  # type: ignore[attr-defined]
            max_attempts=row.max_attempts,  # type: ignore[attr-defined]
            inputs=dict(row.inputs or {}),  # type: ignore[attr-defined]
            outputs=dict(row.outputs or {}),  # type: ignore[attr-defined]
            error_code=row.error_code,  # type: ignore[attr-defined]
            created_at=_ensure_utc(row.created_at) or datetime.now(UTC),  # type: ignore[attr-defined]
            completed_at=_ensure_utc(row.completed_at),  # type: ignore[attr-defined]
        )

    async def create_workflow(
        self,
        workflow: AutonomousWorkflowRecord,
        budget: AutonomyBudgetSnapshot,
    ) -> AutonomousWorkflowRecord:
        if not self.is_persistent:
            return await self._fallback.create_workflow(workflow, budget)

        from backend.app.models.agent_autonomy import (
            AutonomousWorkflowModel,
            AutonomyBudgetModel,
        )

        wf_row = AutonomousWorkflowModel(
            execution_id=workflow.execution_id,
            tenant_id=workflow.tenant_id,
            requested_by=workflow.requested_by,
            workflow_id=workflow.workflow_id,
            objective=workflow.objective,
            status=workflow.status,
            policy_snapshot=workflow.policy.model_dump(mode="json"),
            current_plan=dict(workflow.current_plan),
            current_step_index=workflow.current_step_index,
            replan_count=workflow.replan_count,
            termination_reason=workflow.termination_reason,
            limitations=list(workflow.limitations),
            final_result=dict(workflow.final_result),
            checkpoint_ref=workflow.checkpoint_ref,
            idempotency_key=workflow.idempotency_key,
            idempotency_fingerprint=workflow.idempotency_fingerprint,
            deadline_at=workflow.deadline_at,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            completed_at=workflow.completed_at,
        )
        budget_row = AutonomyBudgetModel(
            execution_id=budget.execution_id,
            tenant_id=budget.tenant_id,
            max_steps=budget.max_steps,
            steps_consumed=budget.steps_consumed,
            max_replans=budget.max_replans,
            replans_consumed=budget.replans_consumed,
            max_agent_attempts=budget.max_agent_attempts,
            total_agent_attempts=budget.total_agent_attempts,
            deadline_seconds=budget.deadline_seconds,
            updated_at=budget.updated_at,
        )
        if self._session_factory is not None:
            async with self._session_factory() as db:  # type: ignore[operator]
                db.add(wf_row)
                db.add(budget_row)
                await db.commit()
        elif self._session is not None:
            self._session.add(wf_row)  # type: ignore[attr-defined]
            self._session.add(budget_row)  # type: ignore[attr-defined]
            await self._session.flush()  # type: ignore[attr-defined]
        res = workflow.model_copy(deep=True)
        res.budget = budget.model_copy(deep=True)
        return res

    async def get_workflow(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> AutonomousWorkflowRecord | None:
        if not self.is_persistent:
            return await self._fallback.get_workflow(execution_id, tenant_id)

        from backend.app.models.agent_autonomy import (
            AutonomousWorkflowModel,
            AutonomyBudgetModel,
        )
        from sqlalchemy import select

        async def _query(db: object) -> AutonomousWorkflowRecord | None:
            wf_stmt = select(AutonomousWorkflowModel).where(
                AutonomousWorkflowModel.execution_id == execution_id,
                AutonomousWorkflowModel.tenant_id == tenant_id,
            )
            wf_row = (await db.execute(wf_stmt)).scalar_one_or_none()  # type: ignore[attr-defined]
            if wf_row is None:
                return None
            b_stmt = select(AutonomyBudgetModel).where(
                AutonomyBudgetModel.execution_id == execution_id,
                AutonomyBudgetModel.tenant_id == tenant_id,
            )
            b_row = (await db.execute(b_stmt)).scalar_one_or_none()  # type: ignore[attr-defined]
            budget = self._to_budget(b_row) if b_row is not None else None
            return self._to_workflow(wf_row, budget)

        if self._session_factory is not None:
            async with self._session_factory() as db:  # type: ignore[operator]
                return await _query(db)
        return await _query(self._session)

    async def find_by_idempotency_key(
        self,
        tenant_id: str,
        requested_by: str,
        idempotency_key: str,
    ) -> AutonomousWorkflowRecord | None:
        if not self.is_persistent:
            return await self._fallback.find_by_idempotency_key(
                tenant_id, requested_by, idempotency_key
            )

        from backend.app.models.agent_autonomy import AutonomousWorkflowModel
        from sqlalchemy import select

        async def _query(db: object) -> str | None:
            stmt = select(AutonomousWorkflowModel.execution_id).where(
                AutonomousWorkflowModel.tenant_id == tenant_id,
                AutonomousWorkflowModel.requested_by == requested_by,
                AutonomousWorkflowModel.idempotency_key == idempotency_key,
            )
            return (await db.execute(stmt)).scalar_one_or_none()  # type: ignore[attr-defined]

        if self._session_factory is not None:
            async with self._session_factory() as db:  # type: ignore[operator]
                exec_id = await _query(db)
        else:
            exec_id = await _query(self._session)
        if exec_id is None:
            return None
        return await self.get_workflow(exec_id, tenant_id)

    async def update_workflow(
        self,
        workflow: AutonomousWorkflowRecord,
    ) -> AutonomousWorkflowRecord:
        if not self.is_persistent:
            return await self._fallback.update_workflow(workflow)

        from backend.app.models.agent_autonomy import AutonomousWorkflowModel
        from sqlalchemy import select

        now = datetime.now(UTC)

        async def _mutate(db: object, *, commit: bool) -> None:
            stmt = select(AutonomousWorkflowModel).where(
                AutonomousWorkflowModel.execution_id == workflow.execution_id,
                AutonomousWorkflowModel.tenant_id == workflow.tenant_id,
            )
            row = (await db.execute(stmt)).scalar_one_or_none()  # type: ignore[attr-defined]
            if row is not None:
                row.status = workflow.status
                row.policy_snapshot = workflow.policy.model_dump(mode="json")
                row.current_plan = dict(workflow.current_plan)
                row.current_step_index = workflow.current_step_index
                row.replan_count = workflow.replan_count
                row.termination_reason = workflow.termination_reason
                row.limitations = list(workflow.limitations)
                row.final_result = dict(workflow.final_result)
                row.checkpoint_ref = workflow.checkpoint_ref
                row.updated_at = now
                row.completed_at = workflow.completed_at
                if commit:
                    await db.commit()  # type: ignore[attr-defined]
                else:
                    await db.flush()  # type: ignore[attr-defined]

        if self._session_factory is not None:
            async with self._session_factory() as db:  # type: ignore[operator]
                await _mutate(db, commit=True)
        else:
            await _mutate(self._session, commit=False)
        res = workflow.model_copy(deep=True)
        res.updated_at = now
        return res

    async def list_workflows(
        self,
        tenant_id: str,
        status: AutonomyStatus | None = None,
        limit: int = 50,
    ) -> list[AutonomousWorkflowRecord]:
        if not self.is_persistent:
            return await self._fallback.list_workflows(tenant_id, status=status, limit=limit)

        from backend.app.models.agent_autonomy import (
            AutonomousWorkflowModel,
            AutonomyBudgetModel,
        )
        from sqlalchemy import select

        async def _query(db: object) -> list[AutonomousWorkflowRecord]:
            stmt = (
                select(AutonomousWorkflowModel)
                .where(AutonomousWorkflowModel.tenant_id == tenant_id)
                .order_by(AutonomousWorkflowModel.created_at.desc())
                .limit(limit)
            )
            if status is not None:
                stmt = stmt.where(AutonomousWorkflowModel.status == status)
            rows = (await db.execute(stmt)).scalars().all()  # type: ignore[attr-defined]
            if not rows:
                return []
            exec_ids = [r.execution_id for r in rows]
            b_stmt = select(AutonomyBudgetModel).where(
                AutonomyBudgetModel.tenant_id == tenant_id,
                AutonomyBudgetModel.execution_id.in_(exec_ids),
            )
            b_rows = (await db.execute(b_stmt)).scalars().all()  # type: ignore[attr-defined]
            budget_map = {b.execution_id: self._to_budget(b) for b in b_rows}
            return [self._to_workflow(r, budget_map.get(r.execution_id)) for r in rows]

        if self._session_factory is not None:
            async with self._session_factory() as db:  # type: ignore[operator]
                return await _query(db)
        return await _query(self._session)

    async def save_steps(
        self,
        execution_id: str,
        tenant_id: str,
        steps: list[AutonomousStepRecord],
    ) -> list[AutonomousStepRecord]:
        if not self.is_persistent:
            return await self._fallback.save_steps(execution_id, tenant_id, steps)

        from backend.app.models.agent_autonomy import AutonomousWorkflowStepModel
        from sqlalchemy import select

        async def _mutate(db: object, *, commit: bool) -> None:
            for step in steps:
                if step.tenant_id != tenant_id:
                    continue
                stmt = select(AutonomousWorkflowStepModel).where(
                    AutonomousWorkflowStepModel.step_id == step.step_id,
                    AutonomousWorkflowStepModel.tenant_id == tenant_id,
                )
                row = (await db.execute(stmt)).scalar_one_or_none()  # type: ignore[attr-defined]
                if row is None:
                    db.add(  # type: ignore[attr-defined]
                        AutonomousWorkflowStepModel(
                            step_id=step.step_id,
                            execution_id=execution_id,
                            tenant_id=tenant_id,
                            plan_version=step.plan_version,
                            step_order=step.step_order,
                            title=step.title,
                            agent_id=step.agent_id,
                            tool_id=step.tool_id,
                            required_capability=step.required_capability,
                            is_side_effecting=step.is_side_effecting,
                            status=step.status,
                            attempt=step.attempt,
                            max_attempts=step.max_attempts,
                            inputs=dict(step.inputs),
                            outputs=dict(step.outputs),
                            error_code=step.error_code,
                            created_at=step.created_at,
                            completed_at=step.completed_at,
                        )
                    )
                else:
                    row.status = step.status
                    row.attempt = step.attempt
                    row.outputs = dict(step.outputs)
                    row.error_code = step.error_code
                    row.completed_at = step.completed_at
            if commit:
                await db.commit()  # type: ignore[attr-defined]
            else:
                await db.flush()  # type: ignore[attr-defined]

        if self._session_factory is not None:
            async with self._session_factory() as db:  # type: ignore[operator]
                await _mutate(db, commit=True)
        else:
            await _mutate(self._session, commit=False)
        return await self.list_steps(execution_id, tenant_id)

    async def upsert_step(self, step: AutonomousStepRecord) -> AutonomousStepRecord:
        await self.save_steps(step.execution_id, step.tenant_id, [step])
        return step.model_copy(deep=True)

    async def list_steps(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> list[AutonomousStepRecord]:
        if not self.is_persistent:
            return await self._fallback.list_steps(execution_id, tenant_id)

        from backend.app.models.agent_autonomy import AutonomousWorkflowStepModel
        from sqlalchemy import select

        async def _query(db: object) -> list[AutonomousStepRecord]:
            stmt = (
                select(AutonomousWorkflowStepModel)
                .where(
                    AutonomousWorkflowStepModel.execution_id == execution_id,
                    AutonomousWorkflowStepModel.tenant_id == tenant_id,
                )
                .order_by(
                    AutonomousWorkflowStepModel.plan_version.asc(),
                    AutonomousWorkflowStepModel.step_order.asc(),
                )
            )
            rows = (await db.execute(stmt)).scalars().all()  # type: ignore[attr-defined]
            return [self._to_step(r) for r in rows]

        if self._session_factory is not None:
            async with self._session_factory() as db:  # type: ignore[operator]
                return await _query(db)
        return await _query(self._session)

    async def append_decision(
        self,
        decision: AutonomyDecisionRecord,
    ) -> AutonomyDecisionRecord:
        if not self.is_persistent:
            return await self._fallback.append_decision(decision)

        from backend.app.models.agent_autonomy import AutonomyDecisionModel

        row = AutonomyDecisionModel(
            decision_id=decision.decision_id,
            execution_id=decision.execution_id,
            tenant_id=decision.tenant_id,
            action=decision.action,
            reason=decision.reason,
            evaluation_snapshot=dict(decision.evaluation_snapshot),
            remaining_steps=decision.remaining_steps,
            created_at=decision.created_at,
        )
        if self._session_factory is not None:
            async with self._session_factory() as db:  # type: ignore[operator]
                db.add(row)
                await db.commit()
        elif self._session is not None:
            self._session.add(row)  # type: ignore[attr-defined]
            await self._session.flush()  # type: ignore[attr-defined]
        return decision.model_copy(deep=True)

    async def list_decisions(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> list[AutonomyDecisionRecord]:
        if not self.is_persistent:
            return await self._fallback.list_decisions(execution_id, tenant_id)

        from backend.app.models.agent_autonomy import AutonomyDecisionModel
        from sqlalchemy import select

        async def _query(db: object) -> list[AutonomyDecisionRecord]:
            stmt = (
                select(AutonomyDecisionModel)
                .where(
                    AutonomyDecisionModel.execution_id == execution_id,
                    AutonomyDecisionModel.tenant_id == tenant_id,
                )
                .order_by(AutonomyDecisionModel.created_at.asc())
            )
            rows = (await db.execute(stmt)).scalars().all()  # type: ignore[attr-defined]
            return [
                AutonomyDecisionRecord(
                    decision_id=r.decision_id,
                    execution_id=r.execution_id,
                    tenant_id=r.tenant_id,
                    action=r.action,  # type: ignore[arg-type]
                    reason=r.reason,
                    evaluation_snapshot=dict(r.evaluation_snapshot or {}),
                    remaining_steps=r.remaining_steps,
                    created_at=_ensure_utc(r.created_at) or datetime.now(UTC),
                )
                for r in rows
            ]

        if self._session_factory is not None:
            async with self._session_factory() as db:  # type: ignore[operator]
                return await _query(db)
        return await _query(self._session)

    async def append_event(self, event: AutonomyEventRecord) -> AutonomyEventRecord:
        if not self.is_persistent:
            return await self._fallback.append_event(event)

        from backend.app.models.agent_autonomy import AutonomyEventModel

        row = AutonomyEventModel(
            event_id=event.event_id,
            execution_id=event.execution_id,
            tenant_id=event.tenant_id,
            event_type=event.event_type,
            actor_id=event.actor_id,
            details=dict(event.details),
            created_at=event.created_at,
        )
        if self._session_factory is not None:
            async with self._session_factory() as db:  # type: ignore[operator]
                db.add(row)
                await db.commit()
        elif self._session is not None:
            self._session.add(row)  # type: ignore[attr-defined]
            await self._session.flush()  # type: ignore[attr-defined]
        return event.model_copy(deep=True)

    async def list_events(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> list[AutonomyEventRecord]:
        if not self.is_persistent:
            return await self._fallback.list_events(execution_id, tenant_id)

        from backend.app.models.agent_autonomy import AutonomyEventModel
        from sqlalchemy import select

        async def _query(db: object) -> list[AutonomyEventRecord]:
            stmt = (
                select(AutonomyEventModel)
                .where(
                    AutonomyEventModel.execution_id == execution_id,
                    AutonomyEventModel.tenant_id == tenant_id,
                )
                .order_by(AutonomyEventModel.created_at.asc())
            )
            rows = (await db.execute(stmt)).scalars().all()  # type: ignore[attr-defined]
            return [
                AutonomyEventRecord(
                    event_id=r.event_id,
                    execution_id=r.execution_id,
                    tenant_id=r.tenant_id,
                    event_type=r.event_type,
                    actor_id=r.actor_id,
                    details=dict(r.details or {}),
                    created_at=_ensure_utc(r.created_at) or datetime.now(UTC),
                )
                for r in rows
            ]

        if self._session_factory is not None:
            async with self._session_factory() as db:  # type: ignore[operator]
                return await _query(db)
        return await _query(self._session)

    async def get_budget(
        self,
        execution_id: str,
        tenant_id: str,
    ) -> AutonomyBudgetSnapshot | None:
        if not self.is_persistent:
            return await self._fallback.get_budget(execution_id, tenant_id)

        from backend.app.models.agent_autonomy import AutonomyBudgetModel
        from sqlalchemy import select

        async def _query(db: object) -> AutonomyBudgetSnapshot | None:
            stmt = select(AutonomyBudgetModel).where(
                AutonomyBudgetModel.execution_id == execution_id,
                AutonomyBudgetModel.tenant_id == tenant_id,
            )
            row = (await db.execute(stmt)).scalar_one_or_none()  # type: ignore[attr-defined]
            return self._to_budget(row) if row is not None else None

        if self._session_factory is not None:
            async with self._session_factory() as db:  # type: ignore[operator]
                return await _query(db)
        return await _query(self._session)

    async def update_budget(
        self,
        budget: AutonomyBudgetSnapshot,
    ) -> AutonomyBudgetSnapshot:
        if not self.is_persistent:
            return await self._fallback.update_budget(budget)

        from backend.app.models.agent_autonomy import AutonomyBudgetModel
        from sqlalchemy import select

        now = datetime.now(UTC)

        async def _mutate(db: object, *, commit: bool) -> None:
            stmt = select(AutonomyBudgetModel).where(
                AutonomyBudgetModel.execution_id == budget.execution_id,
                AutonomyBudgetModel.tenant_id == budget.tenant_id,
            )
            row = (await db.execute(stmt)).scalar_one_or_none()  # type: ignore[attr-defined]
            if row is not None:
                row.steps_consumed = budget.steps_consumed
                row.replans_consumed = budget.replans_consumed
                row.total_agent_attempts = budget.total_agent_attempts
                row.updated_at = now
                if commit:
                    await db.commit()  # type: ignore[attr-defined]
                else:
                    await db.flush()  # type: ignore[attr-defined]

        if self._session_factory is not None:
            async with self._session_factory() as db:  # type: ignore[operator]
                await _mutate(db, commit=True)
        else:
            await _mutate(self._session, commit=False)
        res = budget.model_copy(deep=True)
        res.updated_at = now
        return res
