"""KEEP Phase 4.9 — Autonomous Workflow Engine Service Facade.

Coordinates autonomous workflow submission, bounded LangGraph execution,
step & event inspection, cancellation, and permission-revalidated resume.

Owner: Member 3 / Member 4 Integration Facade
Specification: devdocs/p4/p4.9.txt (Sections 6, 7)
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from backend.app.agents.autonomy.contracts import (
    TERMINAL_AUTONOMY_STATUSES,
    AutonomousStepRecord,
    AutonomousWorkflowRecord,
    AutonomousWorkflowRequest,
    AutonomySecurityContext,
    AutonomyStatus,
    AutonomyTimelineResponse,
    CancelWorkflowRequest,
    ResumeWorkflowRequest,
)
from backend.app.agents.autonomy.controller import AutonomousWorkflowController
from backend.app.agents.autonomy.evaluator import ProgressEvaluator
from backend.app.agents.autonomy.graph import build_autonomous_workflow_graph
from backend.app.agents.autonomy.planner_adapter import AutonomyPlannerAdapter
from backend.app.agents.autonomy.policy import AutonomyPolicyEngine
from backend.app.agents.autonomy.repository import (
    BaseAutonomyRepository,
    InMemoryAutonomyRepository,
)
from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import (
    AgentLayerError,
    AutonomousWorkflowInvalidStateError,
)


class AutonomousWorkflowService:
    """High-level KEEP Autonomous Workflow Engine service."""

    def __init__(
        self,
        repository: BaseAutonomyRepository | None = None,
        *,
        workflow_registry: Any | None = None,
        agent_registry: Any | None = None,
        planning_service: Any | None = None,
        runtime_service: Any | None = None,
        orchestration_service: Any | None = None,
        tool_executor: Any | None = None,
        memory_service: Any | None = None,
        collaboration_service: Any | None = None,
        step_executor_fn: Any | None = None,
    ) -> None:
        self.repository = repository or InMemoryAutonomyRepository()
        self.controller = AutonomousWorkflowController(
            self.repository,
            workflow_registry=workflow_registry,
        )
        self.policy_engine = AutonomyPolicyEngine(agent_registry=agent_registry)
        self.planner_adapter = AutonomyPlannerAdapter(
            planning_service=planning_service,
            agent_registry=agent_registry,
        )
        self.evaluator = ProgressEvaluator()
        self.runtime_service = runtime_service
        self.orchestration_service = orchestration_service
        self.tool_executor = tool_executor
        self.memory_service = memory_service
        self.collaboration_service = collaboration_service
        self.step_executor_fn = step_executor_fn
        self._background_tasks: dict[str, asyncio.Task[Any]] = {}

    def _to_agent_context(self, sec: AutonomySecurityContext) -> AgentContext:
        return AgentContext(
            user_id=sec.user_id,
            tenant_id=sec.tenant_id,
            roles=list(sec.roles),
            permissions=list(sec.permissions),
            correlation_id=sec.correlation_id or f"corr_{uuid4().hex[:12]}",
            trusted=True,
        )

    def _compile_graph(self) -> Any:
        return build_autonomous_workflow_graph(
            self.repository,
            controller=self.controller,
            planner_adapter=self.planner_adapter,
            evaluator=self.evaluator,
            policy_engine=self.policy_engine,
            runtime_service=self.runtime_service,
            orchestration_service=self.orchestration_service,
            tool_executor=self.tool_executor,
            memory_service=self.memory_service,
            collaboration_service=self.collaboration_service,
            step_executor_fn=self.step_executor_fn,
        )

    async def start_workflow(
        self,
        request: AutonomousWorkflowRequest,
        security_context: AutonomySecurityContext,
    ) -> AutonomousWorkflowRecord:
        """Validates policy, creates workflow record, and runs bounded autonomous loop."""
        self.policy_engine.authorize_objective(request.objective, security_context)
        clamped_policy = self.policy_engine.enforce_server_limits(request.policy, security_context)
        bounded_request = request.model_copy(update={"policy": clamped_policy})

        record = await self.controller.initialize_workflow(bounded_request, security_context)
        # Idempotent replay returns existing non-pending or already-tracked workflow without duplicate run
        if record.status != "pending":
            return record

        initial_state: dict[str, Any] = {
            "execution_id": record.execution_id,
            "tenant_id": security_context.tenant_id,
            "user_id": security_context.user_id,
            "workflow_id": record.workflow_id,
            "objective": record.objective,
            "context_metadata": dict(request.context_metadata),
            "completed_steps": [],
            "approval_granted": False,
        }

        if request.mode == "async":
            task = asyncio.create_task(
                self._run_graph(record.execution_id, initial_state, security_context)
            )
            self._background_tasks[record.execution_id] = task
            return await self.controller.get_workflow_or_raise(
                record.execution_id, security_context
            )

        await self._run_graph(record.execution_id, initial_state, security_context)
        return await self.controller.get_workflow_or_raise(record.execution_id, security_context)

    async def _run_graph(
        self,
        execution_id: str,
        initial_state: dict[str, Any],
        security_context: AutonomySecurityContext,
    ) -> None:
        graph = self._compile_graph()
        ctx = self._to_agent_context(security_context)
        try:
            await graph.arun(initial_state, context=ctx, max_supersteps=128)
        except (AgentLayerError, ValueError, RuntimeError, TimeoutError) as exc:
            wf = await self.repository.get_workflow(execution_id, security_context.tenant_id)
            if wf is not None and wf.status not in TERMINAL_AUTONOMY_STATUSES:
                await self.controller.terminate(
                    execution_id,
                    security_context,
                    target_status="failed",
                    reason=f"Execution failed: {exc}",
                    actor_id="system:controller",
                )

    async def get_workflow(
        self,
        execution_id: str,
        security_context: AutonomySecurityContext,
    ) -> AutonomousWorkflowRecord:
        wf = await self.controller.get_workflow_or_raise(execution_id, security_context)
        self.policy_engine.authorize_read(wf.tenant_id, security_context)
        return wf

    async def list_workflows(
        self,
        security_context: AutonomySecurityContext,
        *,
        status: AutonomyStatus | None = None,
        limit: int = 50,
    ) -> list[AutonomousWorkflowRecord]:
        self.policy_engine.authorize_read(security_context.tenant_id, security_context)
        return await self.repository.list_workflows(
            security_context.tenant_id,
            status=status,
            limit=limit,
        )

    async def list_steps(
        self,
        execution_id: str,
        security_context: AutonomySecurityContext,
    ) -> list[AutonomousStepRecord]:
        wf = await self.get_workflow(execution_id, security_context)
        return await self.repository.list_steps(wf.execution_id, security_context.tenant_id)

    async def get_timeline(
        self,
        execution_id: str,
        security_context: AutonomySecurityContext,
    ) -> AutonomyTimelineResponse:
        wf = await self.get_workflow(execution_id, security_context)
        decisions = await self.repository.list_decisions(
            wf.execution_id, security_context.tenant_id
        )
        events = await self.repository.list_events(wf.execution_id, security_context.tenant_id)
        return AutonomyTimelineResponse(
            execution_id=wf.execution_id,
            decisions=decisions,
            events=events,
        )

    async def cancel_workflow(
        self,
        execution_id: str,
        request: CancelWorkflowRequest,
        security_context: AutonomySecurityContext,
    ) -> AutonomousWorkflowRecord:
        wf = await self.get_workflow(execution_id, security_context)
        self.policy_engine.authorize_resume(wf.tenant_id, security_context)
        task = self._background_tasks.pop(execution_id, None)
        if task is not None and not task.done():
            task.cancel()
        return await self.controller.cancel(execution_id, request.reason, security_context)

    async def resume_workflow(
        self,
        execution_id: str,
        request: ResumeWorkflowRequest,
        security_context: AutonomySecurityContext,
    ) -> AutonomousWorkflowRecord:
        """Revalidates caller permissions and safely resumes a paused workflow without repeating completed steps."""
        wf = await self.get_workflow(execution_id, security_context)
        if wf.status not in ("awaiting_approval", "pending"):
            raise AutonomousWorkflowInvalidStateError(execution_id, wf.status, "resume")

        is_write_approval = wf.status == "awaiting_approval"
        self.policy_engine.authorize_resume(
            wf.tenant_id,
            security_context,
            is_write_approval=is_write_approval,
        )

        if not request.approve:
            return await self.controller.cancel(
                execution_id,
                f"Write approval denied: {request.reason}",
                security_context,
            )

        # Ensure deadline has not expired while waiting for approval
        await self.controller.check_budget_and_deadline(
            execution_id,
            security_context,
            now=datetime.now(UTC),
            require_step_capacity=True,
        )

        await self.controller.record_event(
            execution_id=execution_id,
            tenant_id=security_context.tenant_id,
            event_type="approval.resumed",
            actor_id=security_context.user_id,
            details={"reason": request.reason, "approved": True},
        )

        steps = await self.repository.list_steps(execution_id, security_context.tenant_id)
        completed = [
            {
                "step_id": s.step_id,
                "title": s.title,
                "agent_id": s.agent_id,
                "outputs": s.outputs,
            }
            for s in steps
            if s.status == "succeeded"
        ]

        resume_state: dict[str, Any] = {
            "execution_id": execution_id,
            "tenant_id": security_context.tenant_id,
            "user_id": security_context.user_id,
            "workflow_id": wf.workflow_id,
            "objective": wf.objective,
            "completed_steps": completed,
            "approval_granted": True,
        }
        await self._run_graph(execution_id, resume_state, security_context)
        return await self.controller.get_workflow_or_raise(execution_id, security_context)
