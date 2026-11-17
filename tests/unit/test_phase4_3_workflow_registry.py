"""Phase 4.3 Member 1 Unit Tests — Workflow Contracts, Registry & Orchestration Service."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from backend.app.agents.contracts import AgentContext, EvidenceReference
from backend.app.agents.errors import (
    AgentAuthorizationError,
    InvalidWorkflowTransitionError,
    WorkflowAlreadyRegisteredError,
    WorkflowDependencyMissingError,
    WorkflowDisabledError,
    WorkflowIdempotencyConflictError,
    WorkflowNotFoundError,
)
from backend.app.agents.orchestration.service import KeepOrchestrationService
from backend.app.agents.orchestration.workflow_contracts import (
    WorkflowDefinition,
    WorkflowExecutionRecord,
    WorkflowRequest,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStepLink,
    is_valid_workflow_transition,
)
from backend.app.agents.orchestration.workflow_registry import WorkflowRegistry
from backend.app.agents.service import build_default_agent_registry


def _make_context(
    *,
    tenant_id: str = "org-alpha",
    user_id: str = "user-1",
    role: str = "Member",
    permissions: list[str] | None = None,
) -> AgentContext:
    perms = (
        permissions
        if permissions is not None
        else ["agent.view", "agent.invoke", "document.read", "ai.search"]
    )
    return AgentContext(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=[role],
        permissions=perms,
        correlation_id="corr-phase43-m1",
        trusted=True,
    )


class _InMemWorkflowRepo:
    """Minimal in-memory repository stub for Member 1 unit isolation."""

    def __init__(self) -> None:
        self.records: dict[str, WorkflowExecutionRecord] = {}
        self.steps: dict[str, list[WorkflowStepLink]] = {}

    async def create(self, record: WorkflowExecutionRecord) -> WorkflowExecutionRecord:
        self.records[record.workflow_execution_id] = record.model_copy(deep=True)
        self.steps[record.workflow_execution_id] = []
        return self.records[record.workflow_execution_id]

    async def get(
        self, workflow_execution_id: str, tenant_id: str
    ) -> WorkflowExecutionRecord | None:
        rec = self.records.get(workflow_execution_id)
        if rec is None or rec.tenant_id != tenant_id:
            return None
        return rec.model_copy(deep=True)

    async def get_by_idempotency_key(
        self, tenant_id: str, requested_by: str, idempotency_key: str
    ) -> WorkflowExecutionRecord | None:
        for rec in self.records.values():
            if (
                rec.tenant_id == tenant_id
                and rec.requested_by == requested_by
                and rec.idempotency_key == idempotency_key
            ):
                return rec.model_copy(deep=True)
        return None

    async def list_executions(
        self,
        tenant_id: str,
        *,
        workflow_id: str | None = None,
        status: WorkflowStatus | None = None,
        limit: int = 50,
    ) -> list[WorkflowExecutionRecord]:
        items = [r for r in self.records.values() if r.tenant_id == tenant_id]
        if workflow_id:
            items = [r for r in items if r.workflow_id == workflow_id]
        if status:
            items = [r for r in items if r.status == status]
        return items[:limit]

    async def mark_running(
        self,
        workflow_execution_id: str,
        tenant_id: str,
        *,
        started_at: datetime,
        deadline_at: datetime | None = None,
        allow_from_recoverable: bool = False,
    ) -> WorkflowExecutionRecord:
        rec = self.records[workflow_execution_id]
        if not is_valid_workflow_transition(rec.status, WorkflowStatus.RUNNING):
            raise InvalidWorkflowTransitionError(
                workflow_execution_id, rec.status.value, WorkflowStatus.RUNNING.value
            )
        rec = rec.model_copy(
            update={"status": WorkflowStatus.RUNNING, "started_at": started_at, "deadline_at": deadline_at}
        )
        self.records[workflow_execution_id] = rec
        return rec

    async def append_step(
        self, workflow_execution_id: str, tenant_id: str, step: WorkflowStepLink
    ) -> None:
        self.steps.setdefault(workflow_execution_id, []).append(step)
        rec = self.records[workflow_execution_id]
        if step.agent_execution_id not in rec.execution_ids:
            rec.execution_ids.append(step.agent_execution_id)

    async def update_checkpoint_ref(
        self, workflow_execution_id: str, tenant_id: str, checkpoint_ref: str
    ) -> None:
        self.records[workflow_execution_id].checkpoint_ref = checkpoint_ref

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
        rec = self.records[workflow_execution_id]
        rec = rec.model_copy(
            update={
                "status": status,
                "result": result,
                "completed_at": completed_at,
                "duration_ms": duration_ms,
                "error_code": error_code,
                "error_message": error_message,
                "warnings": warnings or rec.warnings,
            }
        )
        self.records[workflow_execution_id] = rec
        return rec

    async def request_cancel(
        self, workflow_execution_id: str, tenant_id: str, *, cancelled_at: datetime
    ) -> WorkflowExecutionRecord:
        rec = self.records[workflow_execution_id]
        rec = rec.model_copy(
            update={"status": WorkflowStatus.CANCELLED, "cancel_requested": True, "completed_at": cancelled_at}
        )
        self.records[workflow_execution_id] = rec
        return rec

    async def list_steps(
        self, workflow_execution_id: str, tenant_id: str
    ) -> list[WorkflowStepLink]:
        return list(self.steps.get(workflow_execution_id, []))

    async def list_stale_running(self, now: datetime) -> list[WorkflowExecutionRecord]:
        return []


class _MockGraphRunner:
    def __init__(self, *, version: str, on_step=None) -> None:
        self._version = version
        self._on_step = on_step

    async def arun(
        self,
        initial_state: dict[str, Any],
        *,
        context: AgentContext,
        resume_from_node: str | None = None,
        completed_nodes: set[str] | None = None,
        checkpoint_callback=None,
        cancel_checker=None,
    ) -> dict[str, Any]:
        if self._on_step is not None:
            await self._on_step(
                WorkflowStepLink(
                    workflow_execution_id=initial_state["workflow_execution_id"],
                    tenant_id=context.tenant_id,
                    node_name="mock_step",
                    agent_id="reference",
                    agent_execution_id=f"exec_mock_{self._version}",
                    status="SUCCEEDED",
                )
            )
        return {
            "workflow_status": WorkflowStatus.SUCCEEDED.value,
            "final_result": {
                "summary": f"Completed via v{self._version} for goal: {initial_state['goal']}",
                "version_executed": self._version,
            },
            "evidence": [
                EvidenceReference(
                    source_id="doc-1",
                    source_type="document",
                    title="Architecture Spec",
                )
            ],
            "execution_ids": [f"exec_mock_{self._version}"],
            "warnings": [],
        }


class TestPhase43WorkflowRegistryAndService:
    def test_workflow_lifecycle_transition_matrix(self) -> None:
        assert is_valid_workflow_transition(WorkflowStatus.PENDING, WorkflowStatus.RUNNING)
        assert is_valid_workflow_transition(WorkflowStatus.RUNNING, WorkflowStatus.SUCCEEDED)
        assert is_valid_workflow_transition(
            WorkflowStatus.RUNNING, WorkflowStatus.PARTIALLY_SUCCEEDED
        )
        assert is_valid_workflow_transition(WorkflowStatus.FAILED, WorkflowStatus.RUNNING)
        assert not is_valid_workflow_transition(WorkflowStatus.SUCCEEDED, WorkflowStatus.RUNNING)
        assert not is_valid_workflow_transition(WorkflowStatus.CANCELLED, WorkflowStatus.SUCCEEDED)

    def test_registry_register_version_resolve_and_duplicate_guard(self) -> None:
        registry = WorkflowRegistry()
        v1 = WorkflowDefinition(
            workflow_id="knowledge_analysis",
            name="Knowledge Analysis",
            version="1.0.0",
            task_type="analysis",
        )
        v2 = WorkflowDefinition(
            workflow_id="knowledge_analysis",
            name="Knowledge Analysis v2",
            version="2.0.0",
            task_type="analysis",
        )
        registry.register(v1, lambda **kw: _MockGraphRunner(version="1.0.0", on_step=kw.get("on_step")))
        registry.register(v2, lambda **kw: _MockGraphRunner(version="2.0.0", on_step=kw.get("on_step")))

        with pytest.raises(WorkflowAlreadyRegisteredError):
            registry.register(v1, lambda **kw: _MockGraphRunner(version="1.0.0"))

        latest_def, _ = registry.get("knowledge_analysis")
        assert latest_def.version == "2.0.0"

        pinned_def, _ = registry.get("knowledge_analysis", version="1.0.0")
        assert pinned_def.version == "1.0.0"

    def test_registry_validates_agent_dependencies_against_agent_registry(self) -> None:
        agent_registry = build_default_agent_registry()
        wf_registry = WorkflowRegistry(agent_registry=agent_registry)

        missing_dep_def = WorkflowDefinition(
            workflow_id="missing_agents_wf",
            name="Missing Agents",
            version="1.0.0",
            required_agents=["nonexistent_agent"],
            required_capabilities=["nonexistent.cap"],
        )
        with pytest.raises(WorkflowDependencyMissingError) as exc_info:
            wf_registry.register(missing_dep_def, lambda **kw: _MockGraphRunner(version="1.0.0"))
        assert "agent:nonexistent_agent" in exc_info.value.details["missing"]
        assert "capability:nonexistent.cap" in exc_info.value.details["missing"]

        valid_def = WorkflowDefinition(
            workflow_id="reference_wf",
            name="Reference Workflow",
            version="1.0.0",
            required_agents=["reference"],
        )
        wf_registry.register(valid_def, lambda **kw: _MockGraphRunner(version="1.0.0"))
        assert wf_registry.count() == 1

    def test_registry_disable_blocks_new_submissions_without_losing_pinned_version(self) -> None:
        registry = WorkflowRegistry()
        defn = WorkflowDefinition(
            workflow_id="guarded_wf",
            name="Guarded Workflow",
            version="1.0.0",
        )
        registry.register(defn, lambda **kw: _MockGraphRunner(version="1.0.0"))
        registry.set_enabled("guarded_wf", False, version="1.0.0")

        with pytest.raises(WorkflowDisabledError):
            registry.get("guarded_wf")

        # Pinned execution lookup with allow_disabled=True still succeeds
        pinned, _ = registry.get("guarded_wf", version="1.0.0", allow_disabled=True)
        assert pinned.enabled is False

        with pytest.raises(WorkflowNotFoundError):
            registry.get("unknown_wf")

    @pytest.mark.asyncio
    async def test_orchestration_service_sync_execution_idempotency_and_version_pinning(
        self,
    ) -> None:
        registry = WorkflowRegistry()
        registry.register(
            WorkflowDefinition(workflow_id="demo_wf", name="Demo v1", version="1.0.0"),
            lambda **kw: _MockGraphRunner(version="1.0.0", on_step=kw.get("on_step")),
        )
        registry.register(
            WorkflowDefinition(workflow_id="demo_wf", name="Demo v2", version="2.0.0"),
            lambda **kw: _MockGraphRunner(version="2.0.0", on_step=kw.get("on_step")),
        )

        repo = _InMemWorkflowRepo()
        service = KeepOrchestrationService(
            workflow_registry=registry,
            repository=repo,
            runtime=object(),
        )
        ctx = _make_context()

        rec = await service.submit_workflow(
            "demo_wf",
            WorkflowRequest(goal="Summarize decisions", version="1.0.0", mode="sync"),
            ctx,
            idempotency_key="wf-idem-1",
        )
        assert rec.status == WorkflowStatus.SUCCEEDED
        assert rec.workflow_version == "1.0.0"
        assert rec.result is not None
        assert rec.result.output["version_executed"] == "1.0.0"
        assert len(rec.result.evidence) == 1

        # Same idempotency key + same payload replays existing record
        replayed = await service.submit_workflow(
            "demo_wf",
            WorkflowRequest(goal="Summarize decisions", version="1.0.0", mode="sync"),
            ctx,
            idempotency_key="wf-idem-1",
        )
        assert replayed.workflow_execution_id == rec.workflow_execution_id

        # Same idempotency key + different goal raises 409 conflict
        with pytest.raises(WorkflowIdempotencyConflictError):
            await service.submit_workflow(
                "demo_wf",
                WorkflowRequest(goal="Different goal", version="1.0.0", mode="sync"),
                ctx,
                idempotency_key="wf-idem-1",
            )

        # Non-admin cannot disable workflow
        with pytest.raises(AgentAuthorizationError):
            service.set_workflow_enabled("demo_wf", False, ctx, version="1.0.0")
