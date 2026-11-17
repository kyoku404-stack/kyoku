"""KEEP Phase 4.3 — Workflow-Level Security, Budgets, Timeouts & Concurrency Policies.

Enforces zero-trust context validation, spoofed-identity rejection, prompt-injection
screening, per-step and resume re-authorization, input size caps, timeout bounds,
and per-tenant/global workflow concurrency limits.

Owner: Member 3 (Workflow Reliability, Security & Recovery)
Specification: devdocs/p4/p4.3.txt (Sections 3, 8, 9, 15)
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import (
    AgentAuthorizationError,
    AgentContractValidationError,
    AgentErrorCode,
    AgentPromptInjectionError,
    AgentTenantIsolationError,
    WorkflowBudgetExceededError,
)
from backend.app.agents.orchestration.workflow_contracts import (
    WorkflowDefinition,
    WorkflowExecutionRecord,
    WorkflowRequest,
)
from backend.app.services.security.agent_permissions import AgentPermissionEvaluator
from backend.app.services.security.agent_policy import (
    AgentPolicyInterface,
    KeepAgentPolicyEngine,
)
from backend.app.services.security.contracts import (
    DefaultAIGuardrailEngine,
    GuardrailStatus,
)

_SPOOFED_IDENTITY_KEYS = ("tenant_id", "organization_id", "user_id", "requested_by", "roles", "permissions")


@dataclass(frozen=True)
class WorkflowBudgetConfig:
    """Configurable safety bounds for multi-agent workflow orchestration."""

    default_timeout_seconds: float = 120.0
    max_timeout_seconds: float = 600.0
    max_agent_invocations: int = 12
    max_concurrent_workflows_global: int = 50
    max_concurrent_workflows_per_tenant: int = 10
    max_input_bytes: int = 131_072  # 128 KiB


class KeepWorkflowPolicyEngine:
    """Centralized workflow-level authorization, safety, timeout, and concurrency policy engine."""

    def __init__(
        self,
        *,
        config: WorkflowBudgetConfig | None = None,
        security_policy: AgentPolicyInterface | None = None,
        permission_evaluator: AgentPermissionEvaluator | None = None,
        guardrails: DefaultAIGuardrailEngine | None = None,
    ) -> None:
        self.config = config or WorkflowBudgetConfig()
        self.permission_evaluator = permission_evaluator or AgentPermissionEvaluator()
        self.security_policy: AgentPolicyInterface = security_policy or KeepAgentPolicyEngine(
            permission_evaluator=self.permission_evaluator
        )
        self.guardrails = guardrails or DefaultAIGuardrailEngine()
        self._active_global: set[str] = set()
        self._active_by_tenant: dict[str, set[str]] = {}

    def _reject_spoofed_identity_fields(self, input_data: dict, context: AgentContext) -> None:
        for key in _SPOOFED_IDENTITY_KEYS:
            if key in input_data:
                val = input_data[key]
                if key in ("tenant_id", "organization_id") and str(val) != context.tenant_id:
                    raise AgentTenantIsolationError(
                        f"Workflow input attempted to spoof '{key}' across tenant boundaries."
                    )
                if key in ("user_id", "requested_by") and str(val) != context.user_id:
                    raise AgentAuthorizationError(
                        f"Workflow input attempted to spoof caller identity via '{key}'.",
                        code=AgentErrorCode.AGENT_UNAUTHORIZED,
                    )
                if key in ("roles", "permissions"):
                    raise AgentAuthorizationError(
                        f"Workflow input must not supply privilege override field '{key}'.",
                        code=AgentErrorCode.AGENT_UNAUTHORIZED,
                    )

    def _validate_input_budget(self, goal: str, input_data: dict) -> None:
        encoded = json.dumps({"goal": goal, "input": input_data}, default=str).encode("utf-8")
        if len(encoded) > self.config.max_input_bytes:
            raise AgentContractValidationError(
                f"Workflow payload size ({len(encoded)} bytes) exceeds limit "
                f"({self.config.max_input_bytes} bytes).",
                code=AgentErrorCode.EXECUTION_INPUT_TOO_LARGE,
            )

    def _screen_prompt_injection(self, goal: str) -> None:
        status, flags = self.guardrails.evaluate_prompt(goal)
        if status == GuardrailStatus.BLOCKED:
            raise AgentPromptInjectionError(
                f"Workflow goal blocked by KEEP prompt-injection guardrail ({', '.join(flags)})."
            )

    def authorize_submission(
        self,
        definition: WorkflowDefinition,
        request: WorkflowRequest,
        context: AgentContext,
    ) -> float:
        """Authorizes workflow submission and returns effective clamped timeout in seconds."""
        self.security_policy.verify_trusted_context(context)

        if not self.permission_evaluator.can_invoke_agent(context):
            raise AgentAuthorizationError(
                f"Caller lacks 'agent.invoke' permission required to run workflow '{definition.workflow_id}'.",
                code=AgentErrorCode.AGENT_UNAUTHORIZED,
            )

        self._reject_spoofed_identity_fields(request.input, context)
        self._validate_input_budget(request.goal, request.input)
        self._screen_prompt_injection(request.goal)

        upper_bound = min(definition.max_timeout_seconds, self.config.max_timeout_seconds)
        requested = request.timeout_seconds or min(
            definition.default_timeout_seconds, self.config.default_timeout_seconds
        )
        return max(0.05, min(float(requested), upper_bound))

    def authorize_step(
        self,
        *,
        definition: WorkflowDefinition,
        node_name: str,
        agent_id: str,
        context: AgentContext,
    ) -> None:
        """Verifies caller context and invocation permissions before each graph node runs."""
        self.security_policy.verify_trusted_context(context)
        if not self.permission_evaluator.can_invoke_agent(context):
            raise AgentAuthorizationError(
                f"Caller is not authorized to invoke agent '{agent_id}' at step '{node_name}' "
                f"of workflow '{definition.workflow_id}'.",
                code=AgentErrorCode.AGENT_UNAUTHORIZED,
            )

    def authorize_resume(
        self,
        definition: WorkflowDefinition,
        record: WorkflowExecutionRecord,
        context: AgentContext,
    ) -> None:
        """Re-verifies tenant isolation and CURRENT caller permissions before checkpoint resume."""
        self.security_policy.verify_trusted_context(context)
        if record.tenant_id != context.tenant_id:
            raise AgentTenantIsolationError(
                "Cross-tenant workflow checkpoint resume is strictly forbidden."
            )
        if not self.permission_evaluator.can_invoke_agent(context):
            raise AgentAuthorizationError(
                f"Permission revoked: caller lacks 'agent.invoke' to resume workflow "
                f"'{definition.workflow_id}' ({record.workflow_execution_id}).",
                code=AgentErrorCode.AGENT_UNAUTHORIZED,
            )

    def acquire_slot(self, tenant_id: str, workflow_execution_id: str) -> None:
        """Reserves global and per-tenant active workflow concurrency slots."""
        if (
            workflow_execution_id not in self._active_global
            and len(self._active_global) >= self.config.max_concurrent_workflows_global
        ):
            raise WorkflowBudgetExceededError(
                f"Global active workflow concurrency cap reached ({self.config.max_concurrent_workflows_global}).",
                limit=self.config.max_concurrent_workflows_global,
            )

        tenant_set = self._active_by_tenant.setdefault(tenant_id, set())
        if (
            workflow_execution_id not in tenant_set
            and len(tenant_set) >= self.config.max_concurrent_workflows_per_tenant
        ):
            raise WorkflowBudgetExceededError(
                f"Tenant active workflow concurrency cap reached ({self.config.max_concurrent_workflows_per_tenant}).",
                limit=self.config.max_concurrent_workflows_per_tenant,
            )

        self._active_global.add(workflow_execution_id)
        tenant_set.add(workflow_execution_id)

    def release_slot(self, tenant_id: str, workflow_execution_id: str) -> None:
        """Releases concurrency slots unconditionally in a `finally` block."""
        self._active_global.discard(workflow_execution_id)
        tenant_set = self._active_by_tenant.get(tenant_id)
        if tenant_set is not None:
            tenant_set.discard(workflow_execution_id)
            if not tenant_set:
                self._active_by_tenant.pop(tenant_id, None)

    @property
    def active_count(self) -> int:
        return len(self._active_global)
