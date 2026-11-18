"""KEEP Phase 4.4 — Phase 4.3 Orchestration Bridge for Validated ExecutionPlans.

Compiles a KEEP-validated `ExecutionPlan` (its topological parallel layers and
resolved Phase 4.1 agent bindings) into a Phase 4.3 `CompiledKeepWorkflowGraph`
executed through `KeepOrchestrationService` -> `RuntimeNodeInvoker` -> Phase 4.2
`AgentRuntime`, preserving zero-trust policies, shared `correlation_id`, parallel
branch fan-out/fan-in, and linked workflow + agent execution persistence.

Owner: Member 4 (FastAPI, Persistence & Integration Testing)
Specification: devdocs/p4/p4.4.txt (Sections 2, 5, 9, 12)
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.adapters.langgraph_orchestrator import (
    END,
    START,
    CompiledKeepWorkflowGraph,
    KeepStateGraph,
)
from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import AgentErrorCode, AgentLayerError
from backend.app.agents.orchestration.nodes.runtime_bridge import RuntimeNodeInvoker
from backend.app.agents.orchestration.service import KeepOrchestrationService
from backend.app.agents.orchestration.workflow_contracts import (
    WorkflowDefinition,
    WorkflowExecutionRecord,
    WorkflowMode,
    WorkflowRequest,
    WorkflowStatus,
)
from backend.app.agents.planning.contracts import ExecutionPlan, PlannedTask
from backend.app.agents.runtime.lifecycle import ExecutionStatus

DYNAMIC_PLAN_WORKFLOW_ID = "dynamic_planned_workflow"
DYNAMIC_PLAN_WORKFLOW_DEFINITION = WorkflowDefinition(
    workflow_id=DYNAMIC_PLAN_WORKFLOW_ID,
    name="Phase 4.4 Dynamically Planned Multi-Agent Workflow",
    version="1.0.0",
    description=(
        "Compiles and executes a KEEP-validated Phase 4.4 ExecutionPlan through Phase 4.3 "
        "orchestration and Phase 4.2 AgentRuntime without bypassing any security or budget policy."
    ),
    task_type="planned_execution",
    required_capabilities=[],
    required_agents=[],
    optional_agents=[],
    allow_partial_success=True,
    default_timeout_seconds=120.0,
    max_timeout_seconds=600.0,
    max_agent_invocations=20,
    tags=["phase-4.4", "dynamic-plan", "orchestrated"],
)


def _make_planned_task_node(invoker: RuntimeNodeInvoker, task: PlannedTask):
    """Wraps a single validated PlannedTask as a Phase 4.3 graph node invoking Phase 4.2 runtime."""

    async def planned_task_node(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        if not task.resolved_agent_id:
            if not task.required:
                return {
                    "failed_optional_steps": [task.task_id],
                    "warnings": [
                        f"Optional planned task '{task.task_id}' skipped: no resolved agent."
                    ],
                }
            raise AgentLayerError(
                f"Required planned task '{task.task_id}' has no resolved agent.",
                code=AgentErrorCode.PLAN_CAPABILITY_UNAVAILABLE,
                http_status=422,
            )

        base_input = dict(state.get("input") or {})
        prior_branches = dict(state.get("branch_results") or {})
        referenced_outputs = {
            ref: prior_branches[ref] for ref in task.input_refs if ref in prior_branches
        }
        node_input = {
            **base_input,
            "task_id": task.task_id,
            "plan_id": state.get("plan_id"),
            "upstream_outputs": referenced_outputs,
            "evidence": list(state.get("evidence") or []),
        }

        record, result = await invoker.invoke_node_agent(
            workflow_execution_id=str(state["workflow_execution_id"]),
            node_name=task.task_id,
            agent_id=task.resolved_agent_id,
            goal=task.description,
            input_data=node_input,
            context=context,
            correlation_id=str(state["correlation_id"]),
            role="required" if task.required else "optional",
            is_side_effecting=task.is_side_effecting,
        )

        if record.status != ExecutionStatus.SUCCEEDED or result.status != "succeeded":
            if not task.required:
                return {
                    "execution_ids": [record.execution_id],
                    "failed_optional_steps": [task.task_id],
                    "warnings": [
                        (
                            f"Optional planned task '{task.task_id}' ({task.resolved_agent_id}) "
                            f"failed: {result.error_message or record.status.value}"
                        )
                    ],
                }
            raise AgentLayerError(
                result.error_message or f"Required planned task '{task.task_id}' failed.",
                code=AgentErrorCode.WORKFLOW_STEP_FAILED,
                http_status=500,
                details={"task_id": task.task_id, "execution_id": record.execution_id},
            )

        return {
            "branch_results": {
                task.output_key: {
                    "task_id": task.task_id,
                    "agent_id": task.resolved_agent_id,
                    "agent_version": task.resolved_agent_version,
                    "output": result.output,
                }
            },
            "evidence": [ev.model_dump(mode="json") for ev in result.evidence],
            "execution_ids": [record.execution_id],
            "warnings": list(result.warnings),
        }

    return planned_task_node


def _make_plan_aggregator_node(plan: ExecutionPlan):
    """Aggregates all planned task outputs and evidence into a unified WorkflowResult payload."""

    async def aggregate_plan(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        branch_outputs = dict(state.get("branch_results") or {})
        failed_optional = list(state.get("failed_optional_steps") or [])
        evidence = list(state.get("evidence") or [])

        final_status = (
            WorkflowStatus.PARTIALLY_SUCCEEDED if failed_optional else WorkflowStatus.SUCCEEDED
        )
        return {
            "workflow_status": final_status.value,
            "final_result": {
                "answer_type": "planned_execution",
                "plan_id": plan.plan_id,
                "plan_version": plan.version,
                "goal": plan.goal.goal,
                "expected_output": plan.goal.expected_output,
                "execution_layers": plan.execution_layers,
                "task_outputs": branch_outputs,
                "completed_outputs": sorted(branch_outputs.keys()),
                "failed_optional_steps": failed_optional,
                "evidence_count": len(evidence),
                "tenant_id": context.tenant_id,
            },
        }

    return aggregate_plan


def compile_execution_plan_graph(
    plan: ExecutionPlan,
    *,
    runtime: Any,
    definition: WorkflowDefinition = DYNAMIC_PLAN_WORKFLOW_DEFINITION,
    on_step: Any | None = None,
    workflow_policy: Any | None = None,
) -> CompiledKeepWorkflowGraph:
    """Compiles a validated ExecutionPlan's parallel layers into a Phase 4.3 KeepStateGraph."""
    invoker = RuntimeNodeInvoker(
        runtime=runtime,
        definition=definition,
        on_step=on_step,
        workflow_policy=workflow_policy,
    )
    task_map = {t.task_id: t for t in plan.tasks}
    layers = plan.execution_layers or [[t.task_id] for t in plan.tasks]

    graph = KeepStateGraph()
    for task in plan.tasks:
        graph.add_node(task.task_id, _make_planned_task_node(invoker, task))
    graph.add_node("aggregate_plan", _make_plan_aggregator_node(plan))

    # Connect START -> layer[0], layer[i] -> layer[i+1], layer[-1] -> aggregate_plan -> END
    for first_tid in layers[0]:
        graph.add_edge(START, first_tid)

    for idx in range(len(layers) - 1):
        curr_layer = layers[idx]
        next_layer = layers[idx + 1]
        for src_tid in curr_layer:
            for dst_tid in next_layer:
                # Wire layer progression cleanly so parallel nodes converge before next layer starts
                if src_tid in task_map and dst_tid in task_map:
                    graph.add_edge(src_tid, dst_tid)

    for last_tid in layers[-1]:
        graph.add_edge(last_tid, "aggregate_plan")
    graph.add_edge("aggregate_plan", END)
    return graph.compile()


class PlanOrchestrationBridge:
    """Submits KEEP-validated ExecutionPlans into Phase 4.3 KeepOrchestrationService."""

    def __init__(self, orchestration_service: KeepOrchestrationService) -> None:
        self.orchestration_service = orchestration_service
        self._pending_plans: dict[str, ExecutionPlan] = {}
        self._ensure_dynamic_workflow_registered()

    def _ensure_dynamic_workflow_registered(self) -> None:
        wf_registry = self.orchestration_service.workflow_registry
        try:
            wf_registry.get_definition(DYNAMIC_PLAN_WORKFLOW_ID, allow_disabled=True)
        except AgentLayerError:
            wf_registry.register(
                DYNAMIC_PLAN_WORKFLOW_DEFINITION,
                self._graph_factory,
                validate_deps=False,
            )

    def _graph_factory(
        self,
        *,
        runtime: Any,
        definition: WorkflowDefinition,
        on_step: Any | None = None,
        workflow_policy: Any | None = None,
    ) -> CompiledKeepWorkflowGraph:
        # Resolve the ExecutionPlan carried inside WorkflowState["input"]["__plan_snapshot__"]
        bridge = self

        class _DeferredPlanGraph:
            async def arun(
                self,
                initial_state: dict[str, Any],
                *,
                context: AgentContext,
                resume_from_node: str | None = None,
                completed_nodes: set[str] | None = None,
                checkpoint_callback: Any | None = None,
                cancel_checker: Any | None = None,
            ) -> dict[str, Any]:
                wf_input = dict(initial_state.get("input") or {})
                plan_id = str(wf_input.get("plan_id") or "")
                plan = bridge._pending_plans.get(plan_id)
                if plan is None and "__plan_snapshot__" in wf_input:
                    plan = ExecutionPlan.model_validate(wf_input["__plan_snapshot__"])
                if plan is None:
                    raise AgentLayerError(
                        f"Missing ExecutionPlan snapshot for dynamic workflow (plan_id='{plan_id}').",
                        code=AgentErrorCode.PLAN_NOT_FOUND,
                        http_status=404,
                    )

                compiled = compile_execution_plan_graph(
                    plan,
                    runtime=runtime,
                    definition=definition,
                    on_step=on_step,
                    workflow_policy=workflow_policy,
                )
                enriched_state = {
                    **initial_state,
                    "plan_id": plan.plan_id,
                    "input": {
                        k: v
                        for k, v in wf_input.items()
                        if k != "__plan_snapshot__"
                    },
                }
                return await compiled.arun(
                    enriched_state,
                    context=context,
                    resume_from_node=resume_from_node,
                    completed_nodes=completed_nodes,
                    checkpoint_callback=checkpoint_callback,
                    cancel_checker=cancel_checker,
                )

        return _DeferredPlanGraph()  # type: ignore[return-value]

    async def execute_plan(
        self,
        plan: ExecutionPlan,
        context: AgentContext,
        *,
        mode: WorkflowMode = "sync",
        timeout_seconds: float | None = None,
    ) -> WorkflowExecutionRecord:
        """Hands off a validated ExecutionPlan to Phase 4.3 KeepOrchestrationService."""
        self._ensure_dynamic_workflow_registered()
        self._pending_plans[plan.plan_id] = plan

        wf_input = {
            **dict(plan.input),
            "plan_id": plan.plan_id,
            "project_id": plan.input.get("project_id") or plan.goal.scope,
            "__plan_snapshot__": plan.model_dump(mode="json"),
        }
        wf_req = WorkflowRequest(
            goal=plan.goal.goal,
            input=wf_input,
            version=DYNAMIC_PLAN_WORKFLOW_DEFINITION.version,
            mode=mode,
            timeout_seconds=timeout_seconds,
            correlation_id=plan.correlation_id or context.correlation_id,
        )
        return await self.orchestration_service.submit_workflow(
            DYNAMIC_PLAN_WORKFLOW_ID,
            wf_req,
            context,
        )
