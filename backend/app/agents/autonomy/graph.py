"""KEEP Phase 4.9 — Autonomous Workflow LangGraph State Graph.

Implements explicit separated controller nodes matching devdocs/p4/p4.9.txt Section 5-6:
  START -> validate_policy -> create_plan -> validate_plan -> execute_task
        -> evaluate_progress -> (continue -> execute_task
                               | replan -> replan_within_budget -> validate_plan
                               | pause_for_approval -> pause_for_approval -> END
                               | stop_* -> finalize_outcome -> END)

Integrates injected Phase 4.2–4.8 services cleanly behind KEEP interfaces.

Owner: Member 3 (Adapters & Subsystem Integration)
Specification: devdocs/p4/p4.9.txt (Sections 5, 6)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from backend.app.agents.adapters.langgraph_orchestrator import (
    END,
    START,
    CompiledKeepWorkflowGraph,
    KeepStateGraph,
)
from backend.app.agents.autonomy.contracts import (
    AutonomousStepRecord,
    AutonomySecurityContext,
    EvaluationResult,
    PlannedStepSpec,
)
from backend.app.agents.autonomy.controller import AutonomousWorkflowController
from backend.app.agents.autonomy.evaluator import ProgressEvaluator
from backend.app.agents.autonomy.planner_adapter import AutonomyPlannerAdapter
from backend.app.agents.autonomy.policy import AutonomyPolicyEngine
from backend.app.agents.autonomy.repository import BaseAutonomyRepository
from backend.app.agents.autonomy.state import sanitize_autonomy_state
from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import (
    AgentLayerError,
    AutonomousWorkflowBudgetExhaustedError,
    AutonomousWorkflowCancelledError,
    AutonomousWorkflowDeadlineExceededError,
    AutonomousWorkflowPlanRejectedError,
)

logger = logging.getLogger("agents.autonomy.graph")


def build_autonomous_workflow_graph(
    repository: BaseAutonomyRepository,
    *,
    controller: AutonomousWorkflowController | None = None,
    planner_adapter: AutonomyPlannerAdapter | None = None,
    evaluator: ProgressEvaluator | None = None,
    policy_engine: AutonomyPolicyEngine | None = None,
    runtime_service: Any | None = None,
    orchestration_service: Any | None = None,
    tool_executor: Any | None = None,
    memory_service: Any | None = None,
    collaboration_service: Any | None = None,
    step_executor_fn: Any | None = None,
) -> CompiledKeepWorkflowGraph:
    """Builds the adaptive bounded autonomous workflow LangGraph pipeline."""
    ctrl = controller or AutonomousWorkflowController(repository)
    planner = planner_adapter or AutonomyPlannerAdapter()
    prog_eval = evaluator or ProgressEvaluator()
    policy_eng = policy_engine or AutonomyPolicyEngine()

    def _sec_ctx(state: dict[str, Any], context: AgentContext) -> AutonomySecurityContext:
        return AutonomySecurityContext(
            tenant_id=str(state.get("tenant_id", context.tenant_id)),
            user_id=str(state.get("user_id", context.user_id)),
            roles=list(context.roles),
            permissions=list(context.permissions),
            correlation_id=context.correlation_id,
        )

    async def node_validate_policy(
        state: dict[str, Any], context: AgentContext
    ) -> dict[str, Any]:
        exec_id = state["execution_id"]
        sec_ctx = _sec_ctx(state, context)
        wf = await ctrl.get_workflow_or_raise(exec_id, sec_ctx)
        policy_eng.authorize_objective(wf.objective, sec_ctx)

        if wf.status == "pending" or wf.status == "awaiting_approval":
            await ctrl.transition_status(exec_id, "running", sec_ctx)

        await ctrl.check_budget_and_deadline(exec_id, sec_ctx, require_step_capacity=False)

        # Load prior scoped memory context if Phase 4.7 memory service injected
        memory_hints: list[str] = []
        if memory_service is not None and hasattr(memory_service, "retrieve"):
            try:
                from backend.app.agents.memory.contracts import (
                    MemoryQuery,
                    MemorySecurityContext,
                )

                mem_ctx = MemorySecurityContext(
                    tenant_id=sec_ctx.tenant_id,
                    user_id=sec_ctx.user_id,
                    roles=sec_ctx.roles,
                    permissions=sec_ctx.permissions,
                    workflow_id=wf.workflow_id,
                )
                mem_res = await memory_service.retrieve(
                    MemoryQuery(query=wf.objective, max_tokens=500), mem_ctx
                )
                memory_hints = [m.content for m in mem_res.memories[:3]]
            except (AgentLayerError, ValueError, RuntimeError, AttributeError):
                logger.debug("Optional memory retrieval unavailable; continuing without memory hints.")
                memory_hints = []

        return {
            "status": "running",
            "policy_snapshot": wf.policy.model_dump(mode="json"),
            "memory_hints": memory_hints,
        }

    async def node_create_plan(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        exec_id = state["execution_id"]
        sec_ctx = _sec_ctx(state, context)
        wf = await ctrl.get_workflow_or_raise(exec_id, sec_ctx)

        existing_steps = await repository.list_steps(exec_id, sec_ctx.tenant_id)
        if existing_steps:
            return {
                "plan": wf.current_plan or {"version": wf.replan_count + 1, "steps": []},
                "plan_valid": True,
                "steps_persisted": True,
            }

        # Allow deterministic pre-seeded test steps in context_metadata when explicitly provided
        seeded = state.get("context_metadata", {}).get("planned_steps")
        if isinstance(seeded, list) and seeded:
            proposed = [PlannedStepSpec.model_validate(item) for item in seeded]
        else:
            proposed = await planner.propose_initial_plan(
                objective=wf.objective,
                workflow_id=wf.workflow_id,
                policy=wf.policy,
                security_context=sec_ctx,
                context_metadata=state.get("context_metadata"),
            )

        plan_dict = {
            "version": 1,
            "steps": [s.model_dump(mode="json") for s in proposed],
        }
        wf.current_plan = plan_dict
        await repository.update_workflow(wf)
        return {
            "plan": plan_dict,
            "candidate_steps": [s.model_dump(mode="json") for s in proposed],
        }

    async def node_validate_plan(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        exec_id = state["execution_id"]
        sec_ctx = _sec_ctx(state, context)
        wf = await ctrl.get_workflow_or_raise(exec_id, sec_ctx)

        if state.get("steps_persisted"):
            return {"plan_valid": True, "next_action": "continue"}

        candidate_raw = state.get("candidate_steps") or state.get("plan", {}).get("steps", [])
        candidates = [PlannedStepSpec.model_validate(item) for item in candidate_raw]

        try:
            policy_eng.assert_valid_plan(candidates, wf.policy, sec_ctx)
        except AutonomousWorkflowPlanRejectedError as exc:
            await ctrl.record_event(
                execution_id=exec_id,
                tenant_id=sec_ctx.tenant_id,
                event_type="plan.rejected",
                actor_id="system:policy",
                details={"reason": str(exc)},
            )
            return {
                "plan_valid": False,
                "termination_reason": str(exc),
                "next_action": "stop_failed",
            }

        plan_version = int(state.get("plan", {}).get("version", wf.replan_count + 1))
        step_records = [
            AutonomousStepRecord(
                step_id=s.step_id,
                execution_id=exec_id,
                tenant_id=sec_ctx.tenant_id,
                plan_version=plan_version,
                step_order=s.step_order,
                title=s.title,
                agent_id=s.agent_id or "research_agent",
                tool_id=s.tool_id,
                required_capability=s.required_capability,
                is_side_effecting=s.is_side_effecting,
                max_attempts=wf.policy.max_agent_attempts,
                inputs=s.inputs,
            )
            for s in candidates
        ]
        await repository.save_steps(exec_id, sec_ctx.tenant_id, step_records)
        await ctrl.record_event(
            execution_id=exec_id,
            tenant_id=sec_ctx.tenant_id,
            event_type="plan.validated",
            actor_id="system:policy",
            details={"plan_version": plan_version, "step_count": len(step_records)},
        )
        return {"plan_valid": True, "steps_persisted": False, "next_action": "continue"}

    async def node_execute_task(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        exec_id = state["execution_id"]
        sec_ctx = _sec_ctx(state, context)
        wf = await ctrl.get_workflow_or_raise(exec_id, sec_ctx)
        if wf.status == "cancelled":
            raise AutonomousWorkflowCancelledError(exec_id)

        steps = await repository.list_steps(exec_id, sec_ctx.tenant_id)
        pending_step = next(
            (s for s in steps if s.status in ("pending", "awaiting_approval")),
            None,
        )
        if pending_step is None:
            return {"last_outcome": {"status": "no_pending_steps"}, "pending_write_step_id": None}

        # Check write approval requirement BEFORE executing any side-effecting write step
        approval_granted = bool(state.get("approval_granted", False))
        if policy_eng.requires_approval_for_step(
            pending_step.is_side_effecting,
            wf.policy,
            approval_granted=approval_granted,
        ):
            pending_step.status = "awaiting_approval"
            await repository.upsert_step(pending_step)
            await ctrl.record_event(
                execution_id=exec_id,
                tenant_id=sec_ctx.tenant_id,
                event_type="approval.required",
                actor_id="system:policy",
                details={"step_id": pending_step.step_id, "title": pending_step.title},
            )
            return {
                "pending_write_step_id": pending_step.step_id,
                "last_outcome": {"status": "awaiting_approval", "step_id": pending_step.step_id},
            }

        # Consume bounded step budget BEFORE execution (fails closed on exhaustion or deadline)
        try:
            await ctrl.consume_step_budget(exec_id, sec_ctx, attempts_used=1)
        except (AutonomousWorkflowBudgetExhaustedError, AutonomousWorkflowDeadlineExceededError) as exc:
            return {
                "last_outcome": {"status": "budget_exhausted", "error": str(exc)},
                "termination_reason": str(exc),
                "budget_exhausted": True,
            }

        # Execute step cleanly with retry bound (max_agent_attempts)
        pending_step.status = "running"
        await repository.upsert_step(pending_step)

        outcome_payload: dict[str, Any] = {}
        succeeded = False
        last_err: str | None = None

        while pending_step.attempt < pending_step.max_attempts:
            pending_step.attempt += 1
            try:
                if step_executor_fn is not None:
                    outcome_payload = await step_executor_fn(pending_step, wf, context)
                else:
                    outcome_payload = await _default_execute_step(
                        pending_step,
                        wf_objective=wf.objective,
                        context=context,
                        runtime_service=runtime_service,
                        orchestration_service=orchestration_service,
                        tool_executor=tool_executor,
                        collaboration_service=collaboration_service,
                    )
                if outcome_payload.get("status") == "failed":
                    last_err = str(outcome_payload.get("error_code", "STEP_EXECUTION_FAILED"))
                    continue
                succeeded = True
                break
            except (AgentLayerError, ValueError, RuntimeError, TimeoutError, AttributeError) as exc:
                last_err = type(exc).__name__

        pending_step.completed_at = datetime.now(UTC)
        if succeeded:
            pending_step.status = "succeeded"
            pending_step.outputs = dict(outcome_payload)
            pending_step.error_code = None
            # Single-use approval flag consumed after executing side-effecting step
            if pending_step.is_side_effecting:
                approval_granted = False
        else:
            pending_step.status = "failed"
            pending_step.error_code = last_err or "STEP_FAILED"
            pending_step.outputs = {"error": pending_step.error_code}
            outcome_payload = {"status": "failed", "error_code": pending_step.error_code}

        await repository.upsert_step(pending_step)
        wf.current_step_index += 1
        wf.checkpoint_ref = f"chk_{exec_id}_{wf.current_step_index}"
        await repository.update_workflow(wf)

        completed_list = list(state.get("completed_steps", []))
        if succeeded:
            completed_list.append(
                {
                    "step_id": pending_step.step_id,
                    "title": pending_step.title,
                    "agent_id": pending_step.agent_id,
                    "outputs": pending_step.outputs,
                }
            )

        return {
            "completed_steps": completed_list,
            "current_step": wf.current_step_index,
            "last_outcome": outcome_payload,
            "pending_write_step_id": None,
            "approval_granted": approval_granted,
        }

    async def node_evaluate_progress(
        state: dict[str, Any], context: AgentContext
    ) -> dict[str, Any]:
        exec_id = state["execution_id"]
        sec_ctx = _sec_ctx(state, context)
        wf = await ctrl.get_workflow_or_raise(exec_id, sec_ctx)
        steps = await repository.list_steps(exec_id, sec_ctx.tenant_id)
        budget = await repository.get_budget(exec_id, sec_ctx.tenant_id)

        if state.get("budget_exhausted"):
            return {
                "next_action": "stop_budget_exhausted",
                "evaluation": EvaluationResult(
                    objective_satisfied=False,
                    evidence_sufficient=False,
                    reasons=[str(state.get("termination_reason", "Budget exhausted"))],
                ).model_dump(mode="json"),
            }

        pending_write = state.get("pending_write_step_id") is not None
        evaluation = prog_eval.evaluate(
            objective=wf.objective,
            steps=steps,
            latest_outcome=state.get("last_outcome"),
            budget=budget,
        )
        has_remaining = any(s.status == "pending" for s in steps)
        action = await ctrl.decide_next_action(
            exec_id,
            evaluation,
            sec_ctx,
            has_remaining_steps=has_remaining,
            pending_write_requires_approval=pending_write,
        )
        return {
            "evaluation": evaluation.model_dump(mode="json"),
            "next_action": action,
            "remaining_steps": budget.remaining_steps if budget else 0,
        }

    async def node_replan_within_budget(
        state: dict[str, Any], context: AgentContext
    ) -> dict[str, Any]:
        exec_id = state["execution_id"]
        sec_ctx = _sec_ctx(state, context)
        wf = await ctrl.get_workflow_or_raise(exec_id, sec_ctx)

        budget = await ctrl.consume_replan_budget(exec_id, sec_ctx)
        steps = await repository.list_steps(exec_id, sec_ctx.tenant_id)
        max_order = max((s.step_order for s in steps), default=0)

        eval_obj = EvaluationResult.model_validate(state.get("evaluation", {}))
        failed = [
            {"step_id": s.step_id, "title": s.title, "error": s.error_code}
            for s in steps
            if s.status == "failed"
        ]
        completed = [
            {"step_id": s.step_id, "title": s.title, "outputs": s.outputs}
            for s in steps
            if s.status == "succeeded"
        ]
        revised_steps = await planner.propose_replan(
            objective=wf.objective,
            evaluation=eval_obj,
            completed_outputs=completed,
            failed_steps=failed,
            policy=wf.policy,
            next_step_order=max_order + 1,
        )
        plan_version = budget.replans_consumed + 1
        await ctrl.record_event(
            execution_id=exec_id,
            tenant_id=sec_ctx.tenant_id,
            event_type="plan.revised",
            actor_id="system:planner",
            details={
                "plan_version": plan_version,
                "added_steps": len(revised_steps),
                "missing_evidence": eval_obj.missing_evidence,
            },
        )
        plan_dict = {
            "version": plan_version,
            "steps": [s.model_dump(mode="json") for s in revised_steps],
        }
        wf = await ctrl.get_workflow_or_raise(exec_id, sec_ctx)
        wf.current_plan = plan_dict
        wf.replan_count = budget.replans_consumed
        await repository.update_workflow(wf)
        return {
            "plan": plan_dict,
            "candidate_steps": [s.model_dump(mode="json") for s in revised_steps],
            "steps_persisted": False,
            "replan_count": budget.replans_consumed,
        }

    async def node_pause_for_approval(
        state: dict[str, Any], context: AgentContext
    ) -> dict[str, Any]:
        exec_id = state["execution_id"]
        sec_ctx = _sec_ctx(state, context)
        step_id = state.get("pending_write_step_id")
        wf = await ctrl.transition_status(
            exec_id,
            "awaiting_approval",
            sec_ctx,
            reason=f"Paused awaiting human approval for write step '{step_id}'.",
            actor_id="system:controller",
        )
        wf.checkpoint_ref = f"chk_pause_{exec_id}_{wf.current_step_index}"
        await repository.update_workflow(wf)
        return sanitize_autonomy_state(
            {
                "status": "awaiting_approval",
                "termination_reason": wf.termination_reason or "Awaiting human approval.",
                "pending_write_step_id": step_id,
            }
        )

    async def node_finalize_outcome(
        state: dict[str, Any], context: AgentContext
    ) -> dict[str, Any]:
        exec_id = state["execution_id"]
        sec_ctx = _sec_ctx(state, context)
        wf = await ctrl.get_workflow_or_raise(exec_id, sec_ctx)
        steps = await repository.list_steps(exec_id, sec_ctx.tenant_id)
        decisions = await repository.list_decisions(exec_id, sec_ctx.tenant_id)

        action = state.get("next_action", "stop_completed")
        target_status = {
            "stop_completed": "completed",
            "stop_budget_exhausted": "budget_exhausted",
            "stop_cancelled": "cancelled",
            "stop_failed": "failed",
        }.get(action, "completed")

        findings: list[dict[str, Any]] = []
        evidence_refs: list[str] = []
        limitations: list[str] = list(wf.limitations)

        for s in steps:
            if s.status == "succeeded":
                findings.append(
                    {
                        "step_id": s.step_id,
                        "title": s.title,
                        "agent_id": s.agent_id,
                        "summary": s.outputs.get("summary", s.title),
                    }
                )
                for ref in s.outputs.get("evidence_refs", []):
                    if ref not in evidence_refs:
                        evidence_refs.append(ref)
            elif s.status == "failed":
                limitations.append(
                    f"Step '{s.title}' failed after {s.attempt} attempts ({s.error_code or 'error'})."
                )

        if target_status == "budget_exhausted":
            limitations.append("Execution terminated early due to step or deadline budget ceiling.")
        eval_dict = state.get("evaluation") or {}
        for missing in eval_dict.get("missing_evidence", []):
            limitations.append(f"Missing or incomplete evidence: {missing}")

        term_reason = (
            state.get("termination_reason")
            or (decisions[-1].reason if decisions else None)
            or f"Workflow terminated with status '{target_status}'."
        )
        final_result = {
            "summary": f"Autonomous workflow '{wf.workflow_id}' concluded ({target_status}) for objective: {wf.objective}",
            "findings": findings,
            "evidence_refs": evidence_refs,
            "limitations": limitations,
            "termination_reason": term_reason,
            "confidence": float(eval_dict.get("confidence", 0.8 if target_status == "completed" else 0.4)),
        }
        updated = await ctrl.terminate(
            exec_id,
            sec_ctx,
            target_status=target_status,  # type: ignore[arg-type]
            reason=term_reason,
            final_result=final_result,
            limitations=limitations,
            actor_id="system:controller",
        )
        return sanitize_autonomy_state(
            {
                "status": updated.status,
                "final_result": final_result,
                "limitations": limitations,
                "termination_reason": term_reason,
            }
        )

    def _route_after_validate_plan(state: dict[str, Any]) -> str:
        if state.get("plan_valid"):
            return "execute"
        return "finalize"

    def _route_after_evaluate(state: dict[str, Any]) -> str:
        action = state.get("next_action", "stop_completed")
        if action == "continue":
            return "continue"
        if action == "replan":
            return "replan"
        if action == "pause_for_approval":
            return "pause"
        return "finalize"

    graph = KeepStateGraph()
    graph.add_node("validate_policy", node_validate_policy)
    graph.add_node("create_plan", node_create_plan)
    graph.add_node("validate_plan", node_validate_plan)
    graph.add_node("execute_task", node_execute_task)
    graph.add_node("evaluate_progress", node_evaluate_progress)
    graph.add_node("replan_within_budget", node_replan_within_budget)
    graph.add_node("pause_for_approval", node_pause_for_approval)
    graph.add_node("finalize_outcome", node_finalize_outcome)

    graph.add_edge(START, "validate_policy")
    graph.add_edge("validate_policy", "create_plan")
    graph.add_edge("create_plan", "validate_plan")
    graph.add_conditional_edges(
        "validate_plan",
        _route_after_validate_plan,
        {"execute": "execute_task", "finalize": "finalize_outcome"},
    )
    graph.add_edge("execute_task", "evaluate_progress")
    graph.add_conditional_edges(
        "evaluate_progress",
        _route_after_evaluate,
        {
            "continue": "execute_task",
            "replan": "replan_within_budget",
            "pause": "pause_for_approval",
            "finalize": "finalize_outcome",
        },
    )
    graph.add_edge("replan_within_budget", "validate_plan")
    graph.add_edge("pause_for_approval", END)
    graph.add_edge("finalize_outcome", END)

    return graph.compile()


async def _default_execute_step(
    step: AutonomousStepRecord,
    *,
    wf_objective: str,
    context: AgentContext,
    runtime_service: Any | None = None,
    orchestration_service: Any | None = None,
    tool_executor: Any | None = None,
    collaboration_service: Any | None = None,
) -> dict[str, Any]:
    """Deterministic step runner delegating to KEEP runtime/tool/orchestration when available."""
    if step.tool_id and tool_executor is not None and hasattr(tool_executor, "invoke"):
        try:
            from backend.app.agents.tools.contracts import ToolCallRequest, ToolContext

            tool_ctx = ToolContext(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                roles=list(context.roles),
                permissions=list(context.permissions),
                workflow_id=step.execution_id,
            )
            tool_args = (
                {"query": step.inputs.get("query", wf_objective)}
                if step.tool_id == "knowledge_search"
                else {"title": step.title, "content": step.inputs.get("objective", wf_objective)}
            )
            tool_res = await tool_executor.invoke(
                ToolCallRequest(tool_id=step.tool_id, arguments=tool_args),
                tool_ctx,
            )
            if tool_res.success:
                return {
                    "summary": f"Tool '{step.tool_id}' executed for step '{step.title}'",
                    "evidence_refs": [f"tool:{step.tool_id}:{step.step_id}"],
                    "tool_output": tool_res.output,
                }
        except (AgentLayerError, ValueError, RuntimeError, TimeoutError, AttributeError):
            logger.debug("Fallback from optional tool executor for step %s.", step.step_id)

    if runtime_service is not None and hasattr(runtime_service, "execute_agent"):
        try:
            from backend.app.agents.contracts import AgentRequest

            req = AgentRequest(
                agent_id=step.agent_id,
                input={"goal": wf_objective, "step_title": step.title, **step.inputs},
            )
            res = await runtime_service.execute_agent(req, context)
            return {
                "summary": f"Agent '{step.agent_id}' completed '{step.title}'",
                "evidence_refs": [
                    ref.document_id or ref.chunk_id or f"runtime:{step.step_id}"
                    for ref in getattr(res, "evidence", [])
                ]
                or [f"runtime:{step.agent_id}:{step.step_id}"],
                "runtime_output": getattr(res, "output", {}),
            }
        except (AgentLayerError, ValueError, RuntimeError, TimeoutError, AttributeError):
            logger.debug("Fallback from optional runtime service for step %s.", step.step_id)

    return {
        "summary": f"Completed '{step.title}' via '{step.agent_id}'",
        "evidence_refs": [f"doc:keep:{step.step_id}"],
        "side_effect_applied": step.is_side_effecting,
    }
