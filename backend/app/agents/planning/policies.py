"""KEEP Phase 4.4 — Planning Security, Authorization, Budget & Approval Policies.

Enforces zero-trust context validation, spoofed identity rejection, prompt-injection
screening on goals and LLM-generated task descriptions, RBAC capability-tier checks
against resolved Phase 4.1 agents, resource budget bounds, and fail-closed approval
gating for write/sensitive/side-effecting actions (ADR-077, ADR-079).

Owner: Member 3 (Agent Selection, Policies & Plan Validation)
Specification: devdocs/p4/p4.4.txt (Sections 3, 8, 9)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import (
    AgentAuthorizationError,
    AgentErrorCode,
    AgentPromptInjectionError,
    AgentTenantIsolationError,
)
from backend.app.agents.planning.contracts import (
    ExecutionPlan,
    ValidationFinding,
    ValidationSeverity,
)
from backend.app.agents.registry import AgentRegistry
from backend.app.services.security.agent_permissions import AgentPermissionEvaluator
from backend.app.services.security.agent_policy import (
    AgentPolicyInterface,
    KeepAgentPolicyEngine,
)
from backend.app.services.security.contracts import (
    DefaultAIGuardrailEngine,
    GuardrailStatus,
)

PLANNING_POLICY_VERSION = "1.0.0"

_SPOOFED_IDENTITY_KEYS = (
    "tenant_id",
    "organization_id",
    "user_id",
    "requested_by",
    "roles",
    "permissions",
)


@dataclass(frozen=True)
class PlanningBudgetConfig:
    """Resource and safety limits enforced on every ExecutionPlan."""

    max_tasks: int = 20
    max_replans: int = 3
    max_total_tokens: int = 100_000
    max_estimated_duration_seconds: float = 300.0
    max_parallel_width: int = 6


class KeepPlanningPolicyEngine:
    """Enforces KEEP's planning security, RBAC, resource budget, and approval rules."""

    def __init__(
        self,
        *,
        config: PlanningBudgetConfig | None = None,
        security_policy: AgentPolicyInterface | None = None,
        permission_evaluator: AgentPermissionEvaluator | None = None,
        guardrails: DefaultAIGuardrailEngine | None = None,
    ) -> None:
        self.config = config or PlanningBudgetConfig()
        self.permission_evaluator = permission_evaluator or AgentPermissionEvaluator()
        self.security_policy: AgentPolicyInterface = security_policy or KeepAgentPolicyEngine(
            permission_evaluator=self.permission_evaluator
        )
        self.guardrails = guardrails or DefaultAIGuardrailEngine()

    def authorize_planning_caller(
        self,
        *,
        goal_text: str,
        input_data: dict[str, Any],
        context: AgentContext,
    ) -> None:
        """Verifies trusted context, RBAC permission, no spoofed identity, and prompt safety."""
        self.security_policy.verify_trusted_context(context)

        if not self.permission_evaluator.can_invoke_agent(context):
            raise AgentAuthorizationError(
                "Caller lacks 'agent.invoke' permission required to create or execute plans.",
                code=AgentErrorCode.AGENT_UNAUTHORIZED,
            )

        for key in _SPOOFED_IDENTITY_KEYS:
            if key in input_data:
                val = input_data[key]
                if key in ("tenant_id", "organization_id") and str(val) != context.tenant_id:
                    raise AgentTenantIsolationError(
                        f"Planning input attempted to spoof '{key}' across tenant boundaries."
                    )
                if key in ("user_id", "requested_by") and str(val) != context.user_id:
                    raise AgentAuthorizationError(
                        f"Planning input attempted to spoof caller identity via '{key}'.",
                        code=AgentErrorCode.AGENT_UNAUTHORIZED,
                    )
                if key in ("roles", "permissions"):
                    raise AgentAuthorizationError(
                        f"Planning input must not supply privilege override field '{key}'.",
                        code=AgentErrorCode.AGENT_UNAUTHORIZED,
                    )

        status, flags = self.guardrails.evaluate_prompt(goal_text)
        if status == GuardrailStatus.BLOCKED:
            raise AgentPromptInjectionError(
                f"Planning goal blocked by KEEP prompt-injection guardrail ({', '.join(flags)})."
            )

    def evaluate_plan_policies(
        self,
        plan: ExecutionPlan,
        *,
        agent_registry: AgentRegistry,
        context: AgentContext,
    ) -> tuple[list[ValidationFinding], bool, list[str]]:
        """Runs authorization, guardrail, budget, and approval checks over a resolved ExecutionPlan."""
        self.security_policy.verify_trusted_context(context)

        findings: list[ValidationFinding] = []
        approval_reasons: list[str] = []

        if not self.permission_evaluator.can_invoke_agent(context):
            findings.append(
                ValidationFinding(
                    code="PLAN_POLICY_REJECTED",
                    check="authorization",
                    severity=ValidationSeverity.ERROR,
                    message="Caller lacks 'agent.invoke' permission to authorize this plan.",
                )
            )

        if plan.tenant_id and plan.tenant_id != context.tenant_id:
            findings.append(
                ValidationFinding(
                    code="AGENT_TENANT_ISOLATION_VIOLATION",
                    check="authorization",
                    severity=ValidationSeverity.ERROR,
                    message="Plan tenant_id does not match authenticated caller tenant boundary.",
                )
            )

        # Screen goal and every LLM-proposed task description for prompt injection
        goal_status, goal_flags = self.guardrails.evaluate_prompt(plan.goal.goal)
        if goal_status == GuardrailStatus.BLOCKED:
            findings.append(
                ValidationFinding(
                    code="AGENT_PROMPT_INJECTION_BLOCKED",
                    check="authorization",
                    severity=ValidationSeverity.ERROR,
                    message=f"Goal failed prompt-injection guardrail ({', '.join(goal_flags)}).",
                )
            )

        total_tokens = 0
        total_duration = 0.0

        for task in plan.tasks:
            total_tokens += task.estimated_tokens
            total_duration += task.estimated_duration_seconds

            t_status, t_flags = self.guardrails.evaluate_prompt(task.description)
            if t_status == GuardrailStatus.BLOCKED:
                findings.append(
                    ValidationFinding(
                        code="AGENT_PROMPT_INJECTION_BLOCKED",
                        check="authorization",
                        severity=ValidationSeverity.ERROR,
                        message=(
                            f"LLM-proposed task '{task.task_id}' failed prompt-injection guardrail "
                            f"({', '.join(t_flags)})."
                        ),
                        task_id=task.task_id,
                    )
                )

            if task.is_side_effecting:
                reason = (
                    f"Task '{task.task_id}' performs a side-effecting action requiring human approval."
                )
                approval_reasons.append(reason)
                findings.append(
                    ValidationFinding(
                        code="PLAN_APPROVAL_REQUIRED",
                        check="approval_requirements",
                        severity=ValidationSeverity.WARNING,
                        message=reason,
                        task_id=task.task_id,
                    )
                )

            if task.resolved_agent_id:
                meta = agent_registry.get_metadata(task.resolved_agent_id)
                decision = self.permission_evaluator.evaluate_agent_invocation(
                    meta,
                    context,
                    requested_capabilities=task.required_capabilities,
                )
                if not decision.allowed:
                    findings.append(
                        ValidationFinding(
                            code="PLAN_POLICY_REJECTED",
                            check="authorization",
                            severity=ValidationSeverity.ERROR,
                            message=(
                                f"Caller is not authorized for agent '{meta.agent_id}' "
                                f"on task '{task.task_id}': {decision.reason}"
                            ),
                            task_id=task.task_id,
                            details={"agent_id": meta.agent_id},
                        )
                    )

                # Flag approval requirement for write or sensitive capability tiers
                needed_caps = {c.lower() for c in task.required_capabilities}
                for cap in meta.capabilities:
                    if cap.name.lower() in needed_caps and cap.access in ("write", "sensitive"):
                        reason = (
                            f"Task '{task.task_id}' uses {cap.access}-tier capability "
                            f"'{cap.name}' on agent '{meta.agent_id}'."
                        )
                        if reason not in approval_reasons:
                            approval_reasons.append(reason)
                            findings.append(
                                ValidationFinding(
                                    code="PLAN_APPROVAL_REQUIRED",
                                    check="approval_requirements",
                                    severity=ValidationSeverity.WARNING,
                                    message=reason,
                                    task_id=task.task_id,
                                )
                            )

        # Resource budget checks
        if len(plan.tasks) > min(plan.max_steps, self.config.max_tasks):
            findings.append(
                ValidationFinding(
                    code="PLAN_BUDGET_EXCEEDED",
                    check="resource_budgets",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        f"Plan task count ({len(plan.tasks)}) exceeds configured budget "
                        f"({min(plan.max_steps, self.config.max_tasks)})."
                    ),
                )
            )

        if total_tokens > self.config.max_total_tokens:
            findings.append(
                ValidationFinding(
                    code="PLAN_BUDGET_EXCEEDED",
                    check="resource_budgets",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        f"Estimated token budget ({total_tokens}) exceeds limit "
                        f"({self.config.max_total_tokens})."
                    ),
                )
            )

        if total_duration > self.config.max_estimated_duration_seconds:
            findings.append(
                ValidationFinding(
                    code="PLAN_BUDGET_EXCEEDED",
                    check="resource_budgets",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        f"Estimated duration ({total_duration:.1f}s) exceeds budget "
                        f"({self.config.max_estimated_duration_seconds:.1f}s)."
                    ),
                )
            )

        for layer_idx, layer in enumerate(plan.execution_layers):
            if len(layer) > self.config.max_parallel_width:
                findings.append(
                    ValidationFinding(
                        code="PLAN_BUDGET_EXCEEDED",
                        check="resource_budgets",
                        severity=ValidationSeverity.ERROR,
                        message=(
                            f"Parallel layer {layer_idx} width ({len(layer)}) exceeds max "
                            f"parallel width ({self.config.max_parallel_width})."
                        ),
                    )
                )

        if plan.replan_count > min(plan.max_replans, self.config.max_replans):
            findings.append(
                ValidationFinding(
                    code="PLAN_REPLAN_LIMIT_EXCEEDED",
                    check="safe_regeneration",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        f"Plan replan_count ({plan.replan_count}) exceeds budget "
                        f"({min(plan.max_replans, self.config.max_replans)})."
                    ),
                )
            )

        return findings, len(approval_reasons) > 0, approval_reasons
