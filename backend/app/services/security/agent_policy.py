"""KEEP Phase 4.1 — Agent Security Policy Engine, Guardrails & Audit Events.

Enforces zero-trust boundaries for KEEP's multi-agent layer:
1. Trusted execution context verification (rejects spoofed identity/tenant overrides).
2. Strict multi-tenant isolation across all agent and adapter calls.
3. Capability & access-tier RBAC enforcement (read, write, sensitive).
4. Prompt-injection screening via KEEP's Phase 3.3 `DefaultAIGuardrailEngine`.
5. Untrusted retrieved-content sanitization and unauthorized tool-call prevention.
6. Structured, secret-safe audit event recording.

Owner: Member 3 (Security, Permissions & Governance)
Specification: devdocs/p4/p4.1.txt (Sections 3, 4.3, 9)
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any, Literal, Protocol, runtime_checkable

from backend.app.agents.contracts import AgentContext, AgentRequest
from backend.app.agents.errors import (
    AgentAuthorizationError,
    AgentErrorCode,
    AgentPromptInjectionError,
    AgentTenantIsolationError,
    sanitize_error_message,
)
from backend.app.agents.metadata import AgentCapability, AgentMetadata, CapabilityAccess
from backend.app.services.security.agent_permissions import (
    AgentPermissionDecision,
    AgentPermissionEvaluator,
)
from backend.app.services.security.contracts import (
    BaseAIGuardrailEngine,
    DefaultAIGuardrailEngine,
    GuardrailStatus,
)
from pydantic import BaseModel, Field

_UNTRUSTED_CONTROL_PATTERN = re.compile(
    r"(?i)(?:ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions|"
    r"system\s+prompt|###\s*system|```\s*system|bypass\s+(?:rbac|security|tenant))"
)

_SENSITIVE_IDENTITY_KEYS: frozenset[str] = frozenset(
    {"tenant_id", "organization_id", "org_id", "user_id"}
)


class AgentAuditEvent(BaseModel):
    """Structured security audit record emitted on every agent policy evaluation."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: Literal[
        "agent.invoke.allowed",
        "agent.invoke.denied",
        "agent.tenant.violation",
        "agent.prompt_injection.blocked",
        "agent.tool.allowed",
        "agent.tool.denied",
    ]
    agent_id: str
    user_id: str
    tenant_id: str
    correlation_id: str
    outcome: Literal["ALLOWED", "DENIED", "BLOCKED"]
    reason: str
    details: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class AgentPolicyInterface(Protocol):
    """Protocol implemented by KEEP agent security policy engines."""

    def verify_trusted_context(self, context: AgentContext) -> None:
        ...

    def enforce_tenant_boundary(self, context: AgentContext, target_tenant_id: str) -> None:
        ...

    def authorize_invocation(
        self,
        metadata: AgentMetadata,
        request: AgentRequest,
        context: AgentContext,
    ) -> AgentPermissionDecision:
        ...

    def authorize_tool_call(
        self,
        metadata: AgentMetadata,
        tool_name: str,
        required_access: CapabilityAccess,
        context: AgentContext,
    ) -> AgentPermissionDecision:
        ...

    def sanitize_untrusted_content(self, content: str) -> str:
        ...


class KeepAgentPolicyEngine:
    """Default zero-trust policy engine for KEEP's Phase 4 multi-agent layer."""

    def __init__(
        self,
        *,
        permission_evaluator: AgentPermissionEvaluator | None = None,
        guardrail_engine: BaseAIGuardrailEngine | None = None,
    ) -> None:
        self.permission_evaluator = permission_evaluator or AgentPermissionEvaluator()
        self.guardrail_engine: BaseAIGuardrailEngine = (
            guardrail_engine or DefaultAIGuardrailEngine()
        )
        self._audit_log: list[AgentAuditEvent] = []

    @property
    def audit_events(self) -> list[AgentAuditEvent]:
        """Returns a copy of recorded in-memory audit events."""
        return list(self._audit_log)

    def _record_audit(
        self,
        *,
        event_type: Literal[
            "agent.invoke.allowed",
            "agent.invoke.denied",
            "agent.tenant.violation",
            "agent.prompt_injection.blocked",
            "agent.tool.allowed",
            "agent.tool.denied",
        ],
        agent_id: str,
        context: AgentContext,
        outcome: Literal["ALLOWED", "DENIED", "BLOCKED"],
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self._audit_log.append(
            AgentAuditEvent(
                event_type=event_type,
                agent_id=agent_id,
                user_id=context.user_id,
                tenant_id=context.tenant_id,
                correlation_id=context.correlation_id,
                outcome=outcome,
                reason=sanitize_error_message(reason),
                details=details or {},
            )
        )

    def verify_trusted_context(self, context: AgentContext) -> None:
        """Verifies that AgentContext carries trusted provenance and non-empty tenant/user IDs."""
        if context.trusted_source not in ("keep_jwt_auth", "keep_internal_system"):
            raise AgentAuthorizationError(
                "AgentContext did not originate from trusted KEEP authentication.",
                code=AgentErrorCode.AGENT_UNTRUSTED_CONTEXT,
            )
        if not context.user_id.strip() or not context.tenant_id.strip():
            raise AgentAuthorizationError(
                "AgentContext is missing verified user_id or tenant_id.",
                code=AgentErrorCode.AGENT_UNTRUSTED_CONTEXT,
            )

    def enforce_tenant_boundary(self, context: AgentContext, target_tenant_id: str) -> None:
        """Strictly blocks any cross-tenant resource access."""
        self.verify_trusted_context(context)
        normalized_target = target_tenant_id.strip()
        if not normalized_target or normalized_target != context.tenant_id:
            self._record_audit(
                event_type="agent.tenant.violation",
                agent_id="tenant-boundary",
                context=context,
                outcome="DENIED",
                reason="Cross-tenant resource access attempt blocked.",
                details={"target_tenant_id": normalized_target},
            )
            raise AgentTenantIsolationError(
                "Cross-tenant agent access is strictly forbidden."
            )

    def _reject_spoofed_identity_in_input(
        self,
        agent_id: str,
        request: AgentRequest,
        context: AgentContext,
    ) -> None:
        """Rejects client attempts to override tenant_id or user_id inside request.input."""
        for key in _SENSITIVE_IDENTITY_KEYS:
            if key not in request.input:
                continue
            supplied = str(request.input[key]).strip()
            if not supplied:
                continue
            if key in ("tenant_id", "organization_id", "org_id") and supplied != context.tenant_id:
                self._record_audit(
                    event_type="agent.tenant.violation",
                    agent_id=agent_id,
                    context=context,
                    outcome="DENIED",
                    reason=f"Client input attempted cross-tenant override via '{key}'.",
                )
                raise AgentTenantIsolationError(
                    "Client payload cannot override authenticated tenant_id."
                )
            if key == "user_id" and supplied != context.user_id:
                self._record_audit(
                    event_type="agent.invoke.denied",
                    agent_id=agent_id,
                    context=context,
                    outcome="DENIED",
                    reason="Client input attempted user_id impersonation.",
                )
                raise AgentAuthorizationError(
                    "Client payload cannot impersonate another user_id.",
                    code=AgentErrorCode.AGENT_UNTRUSTED_CONTEXT,
                )

    def _screen_prompt_injection(
        self,
        agent_id: str,
        request: AgentRequest,
        context: AgentContext,
    ) -> None:
        """Screens request goal and serialized input against prompt injection signatures."""
        serialized_input = json.dumps(request.input, default=str) if request.input else ""
        combined_text = f"{request.goal}\n{serialized_input}"
        status, flags = self.guardrail_engine.evaluate_prompt(combined_text)
        if status == GuardrailStatus.BLOCKED:
            self._record_audit(
                event_type="agent.prompt_injection.blocked",
                agent_id=agent_id,
                context=context,
                outcome="BLOCKED",
                reason="Prompt-injection signature detected in agent request.",
                details={"flags": flags},
            )
            raise AgentPromptInjectionError(
                f"Request blocked by agent prompt-injection guardrail ({', '.join(flags)})."
            )

    def authorize_invocation(
        self,
        metadata: AgentMetadata,
        request: AgentRequest,
        context: AgentContext,
    ) -> AgentPermissionDecision:
        """Runs the complete Phase 4.1 policy gate prior to invoking any agent."""
        self.verify_trusted_context(context)
        self._reject_spoofed_identity_in_input(metadata.agent_id, request, context)

        decision = self.permission_evaluator.evaluate_agent_invocation(
            metadata=metadata,
            context=context,
            requested_capabilities=request.requested_capabilities or None,
        )
        if not decision.allowed:
            self._record_audit(
                event_type="agent.invoke.denied",
                agent_id=metadata.agent_id,
                context=context,
                outcome="DENIED",
                reason=decision.reason,
                details={"denied_capabilities": decision.denied_capabilities},
            )
            raise AgentAuthorizationError(
                decision.reason,
                code=decision.error_code or AgentErrorCode.AGENT_CAPABILITY_DENIED,
                details={"denied_capabilities": decision.denied_capabilities},
            )

        self._screen_prompt_injection(metadata.agent_id, request, context)

        self._record_audit(
            event_type="agent.invoke.allowed",
            agent_id=metadata.agent_id,
            context=context,
            outcome="ALLOWED",
            reason=decision.reason,
            details={"request_id": request.request_id, "task_id": request.task_id},
        )
        return decision

    def authorize_tool_call(
        self,
        metadata: AgentMetadata,
        tool_name: str,
        required_access: CapabilityAccess,
        context: AgentContext,
    ) -> AgentPermissionDecision:
        """Authorizes a tool/action call against declared agent capabilities and caller permissions."""
        self.verify_trusted_context(context)
        declared = metadata.get_capability(tool_name)
        if declared is None:
            reason = (
                f"Tool '{tool_name}' is not declared in capabilities for agent '{metadata.agent_id}'."
            )
            self._record_audit(
                event_type="agent.tool.denied",
                agent_id=metadata.agent_id,
                context=context,
                outcome="DENIED",
                reason=reason,
                details={"tool_name": tool_name},
            )
            raise AgentAuthorizationError(
                reason,
                code=AgentErrorCode.AGENT_TOOL_UNAUTHORIZED,
                details={"tool_name": tool_name},
            )

        effective_cap = AgentCapability(
            name=declared.name,
            description=declared.description,
            access=required_access
            if required_access == "sensitive"
            or (required_access == "write" and declared.access == "read")
            else declared.access,
        )
        decision = self.permission_evaluator.evaluate_capability(effective_cap, context)
        if not decision.allowed:
            self._record_audit(
                event_type="agent.tool.denied",
                agent_id=metadata.agent_id,
                context=context,
                outcome="DENIED",
                reason=decision.reason,
                details={"tool_name": tool_name, "required_access": effective_cap.access},
            )
            raise AgentAuthorizationError(
                decision.reason,
                code=AgentErrorCode.AGENT_TOOL_UNAUTHORIZED,
                details={"tool_name": tool_name},
            )

        self._record_audit(
            event_type="agent.tool.allowed",
            agent_id=metadata.agent_id,
            context=context,
            outcome="ALLOWED",
            reason=decision.reason,
            details={"tool_name": tool_name, "access": effective_cap.access},
        )
        return decision

    def sanitize_untrusted_content(self, content: str) -> str:
        """Neutralizes embedded instruction overrides inside untrusted retrieved content."""
        if not content:
            return ""
        return _UNTRUSTED_CONTROL_PATTERN.sub("[SANITIZED_INSTRUCTION]", content)
