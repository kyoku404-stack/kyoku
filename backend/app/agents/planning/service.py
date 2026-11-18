"""KEEP Phase 4.4 — Planning & Reasoning Engine Service Facade.

Coordinates the end-to-end planning pipeline:
  1. Caller zero-trust authorization & prompt-injection screening
  2. Goal parsing (`GoalParser`) with ambiguity clarification support
  3. Structured plan generation (`PlanGenerator`) with bounded regeneration
  4. DAG decomposition & 9-point validation (`PlanValidator`)
  5. Durable persistence of plans, immutable revisions, tasks & audit events
  6. Bounded revision (`revise_plan`) with fresh re-authorization
  7. Fail-closed submission of validated plans to Phase 4.3 (`execute_plan`)

Owner: Member 4 (FastAPI, Persistence & Integration Testing)
Specification: devdocs/p4/p4.4.txt (Sections 5, 8, 9, 10)
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import (
    PlanApprovalRequiredError,
    PlanNotExecutableError,
    PlanNotFoundError,
    PlanReplanLimitExceededError,
)
from backend.app.agents.planning.agent_selector import CapabilityAgentSelector
from backend.app.agents.planning.contracts import (
    ExecutionPlan,
    PlanCreateRequest,
    PlanEventRecord,
    PlanExecuteRequest,
    PlanRepositoryInterface,
    PlanReviseRequest,
    PlanRevisionSnapshot,
    PlanStatus,
    PlanToWorkflowExecutorInterface,
)
from backend.app.agents.planning.decomposer import TaskDecomposer
from backend.app.agents.planning.goal_parser import GoalParser
from backend.app.agents.planning.plan_generator import PlanGenerator
from backend.app.agents.planning.policies import KeepPlanningPolicyEngine
from backend.app.agents.planning.validator import PlanValidator
from backend.app.agents.registry import AgentRegistry
from backend.app.core.logging import get_logger

logger = get_logger("agents.planning")


class KeepPlanningService:
    """High-level KEEP planning service coordinating Members 1–4 and Phase 4.3 handoff."""

    def __init__(
        self,
        *,
        agent_registry: AgentRegistry,
        plan_repository: PlanRepositoryInterface,
        orchestrator_bridge: PlanToWorkflowExecutorInterface | None = None,
        goal_parser: GoalParser | None = None,
        plan_generator: PlanGenerator | None = None,
        decomposer: TaskDecomposer | None = None,
        agent_selector: CapabilityAgentSelector | None = None,
        policy_engine: KeepPlanningPolicyEngine | None = None,
        plan_validator: PlanValidator | None = None,
    ) -> None:
        self.agent_registry = agent_registry
        self.plan_repository = plan_repository
        self.orchestrator_bridge = orchestrator_bridge
        self.goal_parser = goal_parser or GoalParser()
        self.plan_generator = plan_generator or PlanGenerator()
        self.decomposer = decomposer or TaskDecomposer()
        self.agent_selector = agent_selector or CapabilityAgentSelector(agent_registry)
        self.policy_engine = policy_engine or KeepPlanningPolicyEngine()
        self.plan_validator = plan_validator or PlanValidator(
            agent_registry=agent_registry,
            decomposer=self.decomposer,
            agent_selector=self.agent_selector,
            policy_engine=self.policy_engine,
        )

    async def create_plan(
        self,
        request: PlanCreateRequest,
        context: AgentContext,
        *,
        source_request_id: str | None = None,
    ) -> ExecutionPlan:
        """Parses goal, generates a bounded plan, validates all 9 checks, and persists revision 1."""
        self.policy_engine.authorize_planning_caller(
            goal_text=request.goal,
            input_data=request.input,
            context=context,
        )

        correlation_id = request.correlation_id or context.correlation_id
        goal_spec = await self.goal_parser.parse(request)
        available_caps = self.agent_selector.list_available_capabilities()

        # Bounded auto-regeneration loop if candidate fails structural graph check
        attempt = 0
        feedback: str | None = None
        final_plan: ExecutionPlan | None = None

        while True:
            candidate = await self.plan_generator.generate(
                goal_spec,
                available_capabilities=available_caps,
                input_data=request.input,
                max_steps=request.max_steps,
                max_replans=request.max_replans,
                version=1,
                replan_count=attempt,
                feedback=feedback,
                revision_reason="Initial plan generation",
            )
            candidate = candidate.model_copy(
                update={
                    "tenant_id": context.tenant_id,
                    "requested_by": context.user_id,
                    "correlation_id": correlation_id,
                    "source_request_id": source_request_id,
                }
            )

            report = await self.plan_validator.validate_plan(candidate, context=context)
            final_plan = report.plan

            # Only auto-regenerate on structural graph errors within max_replans
            graph_errors = [f for f in report.findings if f.check == "graph_integrity"]
            if graph_errors and attempt < request.max_replans:
                attempt += 1
                feedback = "; ".join(f.message for f in graph_errors)
                continue
            break

        assert final_plan is not None
        persisted = await self.plan_repository.save_plan(
            final_plan,
            revision_reason=final_plan.revision_reason,
        )
        await self.plan_repository.append_event(
            PlanEventRecord(
                plan_id=persisted.plan_id,
                tenant_id=context.tenant_id,
                event_type=f"plan.{persisted.status.value}",
                actor_id=context.user_id,
                correlation_id=correlation_id,
                details={
                    "version": persisted.version,
                    "task_count": len(persisted.tasks),
                    "approval_required": persisted.approval_required,
                    "findings_count": len(persisted.validation_findings),
                },
            )
        )
        logger.info(
            "event=plan.created plan_id=%s version=%s status=%s tasks=%d approval_required=%s correlation_id=%s",
            persisted.plan_id,
            persisted.version,
            persisted.status.value,
            len(persisted.tasks),
            persisted.approval_required,
            correlation_id,
        )
        return persisted

    async def get_plan(self, plan_id: str, context: AgentContext) -> ExecutionPlan:
        self.policy_engine.security_policy.verify_trusted_context(context)
        plan = await self.plan_repository.get_plan(plan_id, context.tenant_id)
        if plan is None:
            raise PlanNotFoundError(plan_id)
        return plan

    async def list_plans(
        self,
        context: AgentContext,
        *,
        status: PlanStatus | None = None,
        limit: int = 50,
    ) -> list[ExecutionPlan]:
        self.policy_engine.security_policy.verify_trusted_context(context)
        return await self.plan_repository.list_plans(
            context.tenant_id, status=status, limit=limit
        )

    async def get_validation_details(
        self, plan_id: str, context: AgentContext
    ) -> tuple[ExecutionPlan, list[PlanRevisionSnapshot], list[PlanEventRecord]]:
        plan = await self.get_plan(plan_id, context)
        revisions = await self.plan_repository.list_revisions(plan_id, context.tenant_id)
        events = await self.plan_repository.list_events(plan_id, context.tenant_id)
        return plan, revisions, events

    async def revise_plan(
        self,
        plan_id: str,
        request: PlanReviseRequest,
        context: AgentContext,
    ) -> ExecutionPlan:
        """Creates an immutable new plan revision within `max_replans` and re-verifies authorization."""
        current = await self.get_plan(plan_id, context)
        if current.replan_count >= current.max_replans:
            raise PlanReplanLimitExceededError(plan_id, current.max_replans)

        merged_input = {**current.input, **request.input_updates}
        next_goal_text = request.updated_goal or current.goal.goal

        # Fresh authorization check — never inherit prior revision authorization (Section 10)
        self.policy_engine.authorize_planning_caller(
            goal_text=next_goal_text,
            input_data=merged_input,
            context=context,
        )

        parse_req = PlanCreateRequest(
            goal=next_goal_text,
            expected_output=request.expected_output or current.goal.expected_output,
            constraints=(
                request.constraints if request.constraints is not None else current.goal.constraints
            ),
            success_criteria=current.goal.success_criteria,
            input=merged_input,
            max_steps=current.max_steps,
            max_replans=current.max_replans,
            correlation_id=current.correlation_id,
        )
        goal_spec = await self.goal_parser.parse(parse_req)
        available_caps = self.agent_selector.list_available_capabilities()

        candidate = await self.plan_generator.generate(
            goal_spec,
            available_capabilities=available_caps,
            input_data=merged_input,
            max_steps=current.max_steps,
            max_replans=current.max_replans,
            plan_id=current.plan_id,
            version=current.version + 1,
            replan_count=current.replan_count + 1,
            feedback=request.reason,
            revision_reason=request.reason,
        )
        candidate = candidate.model_copy(
            update={
                "tenant_id": context.tenant_id,
                "requested_by": context.user_id,
                "correlation_id": current.correlation_id,
                "source_request_id": current.source_request_id,
                "created_at": current.created_at,
            }
        )

        report = await self.plan_validator.validate_plan(candidate, context=context)
        persisted = await self.plan_repository.save_plan(
            report.plan,
            revision_reason=request.reason,
        )
        await self.plan_repository.append_event(
            PlanEventRecord(
                plan_id=persisted.plan_id,
                tenant_id=context.tenant_id,
                event_type="plan.revised",
                actor_id=context.user_id,
                correlation_id=persisted.correlation_id,
                details={
                    "previous_version": current.version,
                    "new_version": persisted.version,
                    "replan_count": persisted.replan_count,
                    "reason": request.reason,
                    "status": persisted.status.value,
                },
            )
        )
        logger.info(
            "event=plan.revised plan_id=%s version=%s replan_count=%d status=%s correlation_id=%s",
            persisted.plan_id,
            persisted.version,
            persisted.replan_count,
            persisted.status.value,
            persisted.correlation_id,
        )
        return persisted

    async def execute_plan(
        self,
        plan_id: str,
        request: PlanExecuteRequest,
        context: AgentContext,
    ) -> tuple[ExecutionPlan, Any]:
        """Re-authorizes and submits a validated plan to Phase 4.3 Orchestration Engine."""
        plan = await self.get_plan(plan_id, context)

        # Fail-closed status gating (ADR-079)
        if plan.status == PlanStatus.APPROVAL_REQUIRED or plan.approval_required:
            raise PlanApprovalRequiredError(
                plan.plan_id,
                plan.approval_reasons or ["Human approval is required before executing this plan."],
            )
        if plan.status != PlanStatus.VALIDATED:
            raise PlanNotExecutableError(plan.plan_id, plan.status.value)

        # Re-verify current caller authorization before handing off to Phase 4.3
        self.policy_engine.authorize_planning_caller(
            goal_text=plan.goal.goal,
            input_data=plan.input,
            context=context,
        )
        revalidation = await self.plan_validator.validate_plan(plan, context=context)
        if revalidation.approval_required:
            raise PlanApprovalRequiredError(plan.plan_id, revalidation.approval_reasons)
        if not revalidation.is_executable:
            raise PlanNotExecutableError(plan.plan_id, revalidation.plan.status.value)

        if self.orchestrator_bridge is None:
            raise RuntimeError("KeepPlanningService is not bound to a Phase 4.3 orchestrator bridge.")

        workflow_record = await self.orchestrator_bridge.execute_plan(
            revalidation.plan,
            context,
            mode=request.mode,
            timeout_seconds=request.timeout_seconds,
        )
        submitted_plan = await self.plan_repository.mark_submitted(
            plan.plan_id,
            context.tenant_id,
            workflow_execution_id=workflow_record.workflow_execution_id,
        )
        await self.plan_repository.append_event(
            PlanEventRecord(
                plan_id=plan.plan_id,
                tenant_id=context.tenant_id,
                event_type="plan.submitted",
                actor_id=context.user_id,
                correlation_id=plan.correlation_id,
                details={
                    "workflow_execution_id": workflow_record.workflow_execution_id,
                    "workflow_status": workflow_record.status.value,
                    "mode": request.mode,
                },
            )
        )
        logger.info(
            "event=plan.submitted plan_id=%s workflow_execution_id=%s status=%s correlation_id=%s",
            plan.plan_id,
            workflow_record.workflow_execution_id,
            workflow_record.status.value,
            plan.correlation_id,
        )
        return submitted_plan, workflow_record
