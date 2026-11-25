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
