"""KEEP Phase 4.1 — Agent Permissions & Trusted Identity Context Mapping.

Maps KEEP's existing JWT authentication (`AuthenticatedUser`) and canonical
RBAC permission matrix (`AIPermission`, `ROLE_PERMISSIONS`) to the Phase 4
multi-agent layer without duplicating KEEP's authorization rules.

Owner: Member 3 (Security, Permissions & Governance)
Specification: devdocs/p4/p4.1.txt (Sections 3, 4.2, 4.3, 9)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from backend.app.agents.contracts import AgentContext, generate_correlation_id
from backend.app.agents.errors import AgentErrorCode
from backend.app.agents.metadata import AgentCapability, AgentMetadata, CapabilityAccess
from backend.app.services.ai.interfaces import AIPermission
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from backend.app.api.dependencies.auth import AuthenticatedUser


# Minimum KEEP permissions required for each capability access tier.
ACCESS_TIER_REQUIRED_PERMISSIONS: dict[CapabilityAccess, set[str]] = {
    "read": {AIPermission.AGENT_INVOKE.value},
    "write": {AIPermission.AGENT_INVOKE.value, AIPermission.TOOL_EXECUTE.value},
    "sensitive": {AIPermission.AGENT_MANAGE.value},
}

# Roles permitted to execute write-tier capabilities without explicit override.
WRITE_CAPABLE_ROLES: frozenset[str] = frozenset(
    {"Member", "Manager", "ProjectManager", "OrgAdmin", "SuperAdmin"}
)

# Roles permitted to inspect disabled agents or invoke sensitive-tier capabilities.
ADMIN_AGENT_ROLES: frozenset[str] = frozenset({"OrgAdmin", "SuperAdmin"})


class AgentPermissionDecision(BaseModel):
    """Structured authorization decision emitted by AgentPermissionEvaluator."""

    allowed: bool
    reason: str
    denied_capabilities: list[str] = Field(default_factory=list)
    error_code: AgentErrorCode | None = None


def build_trusted_agent_context(
    user: AuthenticatedUser,
    *,
    correlation_id: str | None = None,
    deadline_seconds: int = 60,
) -> AgentContext:
    """Constructs a trusted AgentContext strictly from KEEP's verified JWT principal.

    Never accepts user_id, tenant_id, roles, or permissions from client request bodies.
    """
    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    return AgentContext(
        user_id=str(user.id),
        tenant_id=str(user.organization_id),
        correlation_id=(correlation_id or "").strip() or generate_correlation_id(),
        roles=[role_value],
        permissions=set(user.permissions),
        deadline_seconds=deadline_seconds,
        trusted_source="keep_jwt_auth",
    )


class AgentPermissionEvaluator:
    """Evaluates whether a trusted AgentContext may discover or invoke agent capabilities."""

    def can_view_disabled_agents(self, context: AgentContext) -> bool:
        """Only OrgAdmin/SuperAdmin or holders of AGENT_MANAGE may view disabled agents."""
        return (
            AIPermission.AGENT_MANAGE.value in context.permissions
            or any(role in ADMIN_AGENT_ROLES for role in context.roles)
        )

    def can_manage_agents(self, context: AgentContext) -> bool:
        """Checks administrative agent management privilege."""
        return (
            AIPermission.AGENT_MANAGE.value in context.permissions
            or any(role in ADMIN_AGENT_ROLES for role in context.roles)
        )

    def evaluate_capability(
        self,
        capability: AgentCapability,
        context: AgentContext,
    ) -> AgentPermissionDecision:
        """Evaluates whether `context` is authorized for a single AgentCapability."""
        required_perms = ACCESS_TIER_REQUIRED_PERMISSIONS[capability.access]
        missing = sorted(p for p in required_perms if p not in context.permissions)
        if missing:
            return AgentPermissionDecision(
                allowed=False,
                reason=(
                    f"Capability '{capability.name}' (access='{capability.access}') requires "
                    f"permissions: {', '.join(missing)}."
                ),
                denied_capabilities=[capability.name],
                error_code=AgentErrorCode.AGENT_CAPABILITY_DENIED,
            )

        if capability.access == "sensitive" and not self.can_manage_agents(context):
            return AgentPermissionDecision(
                allowed=False,
                reason=(
                    f"Sensitive capability '{capability.name}' requires administrative role "
                    "(OrgAdmin or SuperAdmin)."
                ),
                denied_capabilities=[capability.name],
                error_code=AgentErrorCode.AGENT_CAPABILITY_DENIED,
            )

        return AgentPermissionDecision(
            allowed=True,
            reason=f"Authorized capability '{capability.name}' ({capability.access}).",
        )

    def evaluate_agent_invocation(
        self,
        metadata: AgentMetadata,
        context: AgentContext,
        *,
        requested_capabilities: list[str] | None = None,
    ) -> AgentPermissionDecision:
        """Evaluates whether `context` may invoke `metadata` with the requested or declared capabilities."""
        if AIPermission.AGENT_INVOKE.value not in context.permissions:
            return AgentPermissionDecision(
                allowed=False,
                reason="Caller lacks required permission 'agent.invoke'.",
                error_code=AgentErrorCode.AGENT_UNAUTHORIZED,
            )

        # Determine which declared capabilities apply to this invocation.
        if requested_capabilities:
            target_caps: list[AgentCapability] = []
            undeclared: list[str] = []
            for cap_name in requested_capabilities:
                cap = metadata.get_capability(cap_name)
                if cap is None:
                    undeclared.append(cap_name)
                else:
                    target_caps.append(cap)
            if undeclared:
                return AgentPermissionDecision(
                    allowed=False,
                    reason=(
                        f"Requested capabilities not declared by agent '{metadata.agent_id}': "
                        f"{', '.join(undeclared)}."
                    ),
                    denied_capabilities=undeclared,
                    error_code=AgentErrorCode.AGENT_CAPABILITY_DENIED,
                )
        else:
            target_caps = list(metadata.capabilities)

        denied: list[str] = []
        reasons: list[str] = []
        for cap in target_caps:
            decision = self.evaluate_capability(cap, context)
            if not decision.allowed:
                denied.append(cap.name)
                reasons.append(decision.reason)

        if denied:
            return AgentPermissionDecision(
                allowed=False,
                reason=" ".join(reasons),
                denied_capabilities=denied,
                error_code=AgentErrorCode.AGENT_CAPABILITY_DENIED,
            )

        return AgentPermissionDecision(
            allowed=True,
            reason=f"Caller authorized to invoke agent '{metadata.agent_id}'.",
        )
