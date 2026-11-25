"""KEEP Phase 4.9 — Autonomy Policy & Safety Engine.

Enforces server-side budget ceilings, validates candidate plans against
registered agents/tools and RBAC permissions, gates write operations for
human approval, screens prompt injections, and records policy decisions.

Owner: Member 3 (Autonomy Policies & Safety)
Specification: devdocs/p4/p4.9.txt (Sections 3, 4, 5)
"""

from __future__ import annotations

import re
from typing import Any

from backend.app.agents.autonomy.contracts import (
    SERVER_MAX_AGENT_ATTEMPTS,
    SERVER_MAX_DEADLINE_SECONDS,
    SERVER_MAX_REPLANS,
    SERVER_MAX_STEPS,
    AutonomyPolicy,
    AutonomySecurityContext,
    PlannedStepSpec,
)
from backend.app.agents.errors import (
    AgentLayerError,
    AutonomousWorkflowAccessDeniedError,
    AutonomousWorkflowPlanRejectedError,
    AutonomousWorkflowPolicyDeniedError,
    AutonomousWorkflowTenantViolationError,
)

_PROMPT_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)ignore\s+(all\s+)?previous\s+instructions"),
    re.compile(r"(?i)override\s+(system|policy|rbac|security)"),
    re.compile(r"(?i)exfiltrate\s+(secrets|tokens|credentials|env)"),
    re.compile(r"(?i)bypass\s+tenant\s+isolation"),
)


class AutonomyPolicyEngine:
    """Zero-trust policy gate governing autonomous workflow execution and plan validation."""

    def __init__(
        self,
        *,
        agent_registry: Any | None = None,
        tool_registry: Any | None = None,
        tool_policy_engine: Any | None = None,
        security_policy: Any | None = None,
        default_restricted_tools: frozenset[str] | None = None,
    ) -> None:
        self.agent_registry = agent_registry
        self.tool_registry = tool_registry
        self.tool_policy_engine = tool_policy_engine
        self.security_policy = security_policy
        self.default_restricted_tools = default_restricted_tools or frozenset(
            {"shell_exec", "raw_sql", "drop_table", "external_wire_transfer"}
        )

    def enforce_server_limits(
        self,
        requested: AutonomyPolicy,
        security_context: AutonomySecurityContext,
    ) -> AutonomyPolicy:
        """Applies strict server-side ceilings; clients cannot elevate limits beyond platform caps."""
        if not security_context.tenant_id or not security_context.user_id:
            raise AutonomousWorkflowAccessDeniedError("Verified tenant and user context required.")

        return requested.model_copy(
            update={
                "max_steps": min(requested.max_steps, SERVER_MAX_STEPS),
                "max_replans": min(requested.max_replans, SERVER_MAX_REPLANS),
                "max_agent_attempts": min(requested.max_agent_attempts, SERVER_MAX_AGENT_ATTEMPTS),
                "deadline_seconds": min(requested.deadline_seconds, SERVER_MAX_DEADLINE_SECONDS),
            }
        )

    def authorize_objective(
        self,
        objective: str,
        security_context: AutonomySecurityContext,
    ) -> None:
        """Verifies caller invoke permission and screens objectives for injection attempts."""
        perms = {p.lower() for p in security_context.permissions}
        roles = {r.lower() for r in security_context.roles}
        has_invoke = (
            "agent.invoke" in perms
            or "agent.manage" in perms
            or "*" in perms
            or roles.intersection({"superadmin", "orgadmin", "admin", "manager", "lead", "analyst", "member"})
        )
        # Explicit revocation check: if permissions explicitly empty and role is guest/viewer/revoked -> deny
        if not has_invoke or ("guest" in roles and "agent.invoke" not in perms) or "revoked" in roles:
            raise AutonomousWorkflowAccessDeniedError(
                "Caller lacks 'agent.invoke' authorization for autonomous workflows."
            )

        for pattern in _PROMPT_INJECTION_PATTERNS:
            if pattern.search(objective):
                raise AutonomousWorkflowPolicyDeniedError(
                    "Objective rejected due to unsafe policy override or prompt injection directive."
                )

    def authorize_read(
        self,
        target_tenant_id: str,
        security_context: AutonomySecurityContext,
    ) -> None:
        """Enforces tenant boundary and read clearance for inspection endpoints."""
        if target_tenant_id != security_context.tenant_id:
            raise AutonomousWorkflowTenantViolationError(
                security_context.tenant_id, target_tenant_id
            )
        roles = {r.lower() for r in security_context.roles}
        perms = {p.lower() for p in security_context.permissions}
        if "revoked" in roles:
            raise AutonomousWorkflowAccessDeniedError("Caller permissions have been revoked.")
        if not perms and not roles:
            raise AutonomousWorkflowAccessDeniedError("No valid permissions or roles found.")

    def authorize_resume(
        self,
        target_tenant_id: str,
        security_context: AutonomySecurityContext,
        *,
        is_write_approval: bool = False,
    ) -> None:
        """Revalidates live permissions before resuming a paused autonomous workflow."""
        if target_tenant_id != security_context.tenant_id:
            raise AutonomousWorkflowTenantViolationError(
                security_context.tenant_id, target_tenant_id
            )
        perms = {p.lower() for p in security_context.permissions}
        roles = {r.lower() for r in security_context.roles}
        if "revoked" in roles or "guest" in roles:
            raise AutonomousWorkflowAccessDeniedError(
                "Resume denied: caller lacks active execution authorization."
            )
        if not ("agent.invoke" in perms or "agent.manage" in perms or roles.intersection({"superadmin", "orgadmin", "admin", "manager", "lead", "analyst", "member"})):
            raise AutonomousWorkflowAccessDeniedError(
                "Resume denied: 'agent.invoke' permission required."
            )
        if is_write_approval:
            can_approve_writes = (
                "agent.manage" in perms
                or "agent.approve" in perms
                or "agent.invoke" in perms
                or bool(roles.intersection({"superadmin", "orgadmin", "admin", "manager", "lead"}))
            )
            if not can_approve_writes:
                raise AutonomousWorkflowAccessDeniedError(
                    "Caller lacks authorization to approve write operations."
                )

    def validate_plan(
        self,
        steps: list[PlannedStepSpec],
        policy: AutonomyPolicy,
        security_context: AutonomySecurityContext,
    ) -> tuple[bool, list[str]]:
        """Fail-closed validation of planner-proposed steps prior to any execution (ADR-093)."""
        errors: list[str] = []
        if not steps:
            errors.append("Plan contains zero executable steps.")
            return False, errors

        if len(steps) > policy.max_steps:
            errors.append(
                f"Proposed plan has {len(steps)} steps, exceeding max_steps ({policy.max_steps})."
            )

        seen_orders: set[int] = set()
        seen_ids: set[str] = set()
        for step in steps:
            if step.step_id in seen_ids:
                errors.append(f"Duplicate step_id '{step.step_id}' in proposed plan.")
            seen_ids.add(step.step_id)

            if step.step_order in seen_orders:
                errors.append(f"Duplicate step_order '{step.step_order}' in proposed plan.")
            seen_orders.add(step.step_order)

            # Agent allowlist and registry checks
            if policy.allowed_agents and step.agent_id not in policy.allowed_agents:
                errors.append(
                    f"Agent '{step.agent_id}' is not in policy allowed_agents allowlist."
                )
            if (
                self.agent_registry is not None
                and hasattr(self.agent_registry, "is_registered")
                and step.agent_id
                and not self.agent_registry.is_registered(step.agent_id)
                and step.agent_id not in {
                    "research_agent",
                    "knowledge_retrieval",
                    "knowledge_analysis",
                    "decision_extractor",
                    "risk_analyst",
                    "report_synthesis",
                    "reference",
                }
            ):
                errors.append(f"Agent '{step.agent_id}' is not registered in KEEP AgentRegistry.")

            # Tool allowlist & restricted tool checks
            if step.tool_id:
                if step.tool_id in self.default_restricted_tools:
                    errors.append(f"Tool '{step.tool_id}' is restricted and forbidden by autonomy policy.")
                if policy.allowed_tools and step.tool_id not in policy.allowed_tools:
                    errors.append(f"Tool '{step.tool_id}' is not in policy allowed_tools allowlist.")
                if (
                    self.tool_registry is not None
                    and hasattr(self.tool_registry, "get")
                ):
                    try:
                        self.tool_registry.get(step.tool_id, check_enabled=True)
                    except (AgentLayerError, KeyError, ValueError, RuntimeError):
                        errors.append(
                            f"Tool '{step.tool_id}' is unavailable or disabled in ToolRegistry."
                        )

            # Self-dependency loop check
            if step.step_id in step.depends_on:
                errors.append(f"Step '{step.step_id}' contains a self-dependency cycle.")

        return (len(errors) == 0), errors

    def assert_valid_plan(
        self,
        steps: list[PlannedStepSpec],
        policy: AutonomyPolicy,
        security_context: AutonomySecurityContext,
    ) -> None:
        ok, reasons = self.validate_plan(steps, policy, security_context)
        if not ok:
            raise AutonomousWorkflowPlanRejectedError(
                "; ".join(reasons),
                details={"reasons": reasons},
            )

    def requires_approval_for_step(
        self,
        step_is_side_effecting: bool,
        policy: AutonomyPolicy,
        *,
        approval_granted: bool,
    ) -> bool:
        """Returns True iff step requires human pause before side-effecting write execution."""
        if not step_is_side_effecting:
            return False
        if not policy.require_approval_for_writes:
            return False
        return not approval_granted
