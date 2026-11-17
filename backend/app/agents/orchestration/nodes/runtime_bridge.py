"""KEEP Phase 4.3 — Phase 4.2 AgentRuntime Bridge for Orchestration Graph Nodes.

Enforces ADR-074: every graph node MUST invoke registered agents through KEEP's
Phase 4.2 `AgentRuntime.submit(..., mode="sync")` so individual execution records,
RBAC policies, timeouts, retries, and correlation IDs remain unified and auditable.

Owner: Member 2 (Graph State, Routing & Workflow Execution)
Specification: devdocs/p4/p4.3.txt (Sections 2, 6, 8)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from backend.app.agents.contracts import AgentContext, AgentRequest, AgentResult
from backend.app.agents.errors import (
    AgentErrorCode,
    AgentLayerError,
    WorkflowBudgetExceededError,
)
from backend.app.agents.orchestration.workflow_contracts import (
    WorkflowDefinition,
    WorkflowStepLink,
    WorkflowStepRole,
)
from backend.app.agents.runtime.lifecycle import ExecutionRecord, ExecutionStatus

OnStepCallback = Callable[[WorkflowStepLink], Awaitable[None]]


class RuntimeNodeInvoker:
    """Invokes registered KEEP agents via Phase 4.2 AgentRuntime with step linkage & budget enforcement."""

    def __init__(
        self,
        *,
        runtime: Any,
        definition: WorkflowDefinition,
        on_step: OnStepCallback | None = None,
        workflow_policy: Any | None = None,
    ) -> None:
        self._runtime = runtime
        self._definition = definition
        self._on_step = on_step
        self._workflow_policy = workflow_policy
        self._invocations_used = 0

    @property
    def invocations_used(self) -> int:
        return self._invocations_used

    async def invoke_node_agent(
        self,
        *,
        workflow_execution_id: str,
        node_name: str,
        agent_id: str,
        goal: str,
        input_data: dict[str, Any],
        context: AgentContext,
        correlation_id: str,
        role: WorkflowStepRole = "required",
        is_side_effecting: bool = False,
        timeout_seconds: float | None = None,
    ) -> tuple[ExecutionRecord, AgentResult]:
        """Executes an agent via Phase 4.2 AgentRuntime and emits a linked WorkflowStepLink."""
        if self._invocations_used >= self._definition.max_agent_invocations:
            raise WorkflowBudgetExceededError(
                f"Workflow '{self._definition.workflow_id}' exceeded max agent invocation budget "
                f"({self._definition.max_agent_invocations}).",
                limit=self._definition.max_agent_invocations,
            )

        if self._workflow_policy is not None and hasattr(self._workflow_policy, "authorize_step"):
            self._workflow_policy.authorize_step(
                definition=self._definition,
                node_name=node_name,
                agent_id=agent_id,
                context=context,
            )

        self._invocations_used += 1
        started_at = datetime.now(UTC)

        agent_req = AgentRequest(
            goal=goal,
            input=dict(input_data),
            correlation_id=correlation_id,
        )

        record: ExecutionRecord = await self._runtime.submit(
            agent_id,
            agent_req,
            context,
            mode="sync",
            timeout_seconds=timeout_seconds,
        )

        completed_at = datetime.now(UTC)
        duration_ms = (
            record.duration_ms
            if record.duration_ms is not None
            else max(0, int((completed_at - started_at).total_seconds() * 1000))
        )

        # Fetch validated result if execution reached terminal state
        if record.status == ExecutionStatus.SUCCEEDED:
            try:
                result = await self._runtime.get_result(record.execution_id, context)
            except AgentLayerError:
                if record.result_payload:
                    result = AgentResult.model_validate(record.result_payload)
                else:
                    result = AgentResult.failure(
                        code=AgentErrorCode.AGENT_EXECUTION_FAILED,
                        message=f"Unable to load result for execution '{record.execution_id}'.",
                    )
        else:
            if record.result_payload:
                result = AgentResult.model_validate(record.result_payload)
            else:
                result = AgentResult.failure(
                    code=(
                        AgentErrorCode(record.error_code)
                        if record.error_code
                        and record.error_code in {c.value for c in AgentErrorCode}
                        else AgentErrorCode.AGENT_EXECUTION_FAILED
                    ),
                    message=record.error_message
                    or f"Agent '{agent_id}' finished with status {record.status.value}.",
                    retryable=record.status == ExecutionStatus.TIMED_OUT,
                )

        step_link = WorkflowStepLink(
            workflow_execution_id=workflow_execution_id,
            tenant_id=context.tenant_id,
            node_name=node_name,
            agent_id=agent_id,
            agent_execution_id=record.execution_id,
            role=role,
            status=record.status.value,
            attempt_number=record.attempt_number,
            duration_ms=duration_ms,
            error_code=record.error_code,
            is_side_effecting=is_side_effecting,
            started_at=record.started_at or started_at,
            completed_at=record.completed_at or completed_at,
        )

        if self._on_step is not None:
            await self._on_step(step_link)

        return record, result
