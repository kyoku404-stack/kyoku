"""KEEP Phase 4.7 — Memory Access Control & Boundary Authorization.

Defines policy decisions and evaluates scope-specific access rules across
tenants, users, organizations, workflows, and agents.

Specification: devdocs/p4/p4.7.txt (Sections 4, 6, 10)
Owner: Member 3 (Privacy, Governance & Lifecycle)
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.errors import AgentErrorCode
from backend.app.agents.memory.contracts import (
    MemoryRecord,
    MemoryScope,
    MemorySecurityContext,
)
from pydantic import BaseModel, Field

ADMIN_ROLE_VARIANTS = {
    "orgadmin",
    "org_admin",
    "superadmin",
    "admin",
    "system_admin",
    "ai_admin",
}


class PolicyDecision(BaseModel):
    """Structured authorization decision returned by memory policy checks."""

    allowed: bool
    reason_code: AgentErrorCode | str = AgentErrorCode.AGENT_UNAUTHORIZED
    action: str = Field(default="read")
    details: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def allow(cls, action: str, details: dict[str, Any] | None = None) -> PolicyDecision:
        return cls(
            allowed=True,
            reason_code="ALLOWED",
            action=action,
            details=details or {},
        )

    @classmethod
    def deny(
        cls,
        reason_code: AgentErrorCode | str,
        action: str,
        details: dict[str, Any] | None = None,
    ) -> PolicyDecision:
        return cls(
            allowed=False,
            reason_code=reason_code,
            action=action,
            details=details or {},
        )


def is_tenant_admin(security_context: MemorySecurityContext) -> bool:
    """Checks whether the principal holds tenant administrative privileges."""
    if security_context.is_admin:
        return True
    return any(r.lower().replace("-", "_") in ADMIN_ROLE_VARIANTS for r in security_context.roles)


class MemoryAccessController:
    """Evaluates zero-trust multi-tenancy and scope-specific authorization."""

    def check_tenant_boundary(
        self,
        target_tenant_id: str,
        security_context: MemorySecurityContext,
    ) -> PolicyDecision:
        """Enforces physical tenant isolation."""
        if security_context.tenant_id != target_tenant_id:
            return PolicyDecision.deny(
                AgentErrorCode.MEMORY_TENANT_ISOLATION_VIOLATION,
                action="boundary_check",
                details={
                    "caller_tenant_id": security_context.tenant_id,
                    "target_tenant_id": target_tenant_id,
                },
            )
        return PolicyDecision.allow("boundary_check")

    def check_read_access(
        self,
        record: MemoryRecord,
        security_context: MemorySecurityContext,
    ) -> PolicyDecision:
        """Determines if principal is authorized to read the memory record."""
        # 1. Tenant boundary
        tenant_check = self.check_tenant_boundary(record.tenant_id, security_context)
        if not tenant_check.allowed:
            return tenant_check

        # 2. Scope-specific rules
        admin = is_tenant_admin(security_context)

        if record.scope == "user":
            if record.owner_id == security_context.user_id or admin:
                return PolicyDecision.allow("read")
            return PolicyDecision.deny(
                AgentErrorCode.MEMORY_ACCESS_DENIED,
                action="read",
                details={
                    "scope": "user",
                    "reason": "User-scoped memory is private to the owner.",
                },
            )

        if record.scope == "organization":
            # Organization memory is accessible to all members of the tenant
            return PolicyDecision.allow("read")

        if record.scope == "workflow":
            if (
                admin
                or (
                    security_context.workflow_execution_id
                    and security_context.workflow_execution_id == record.owner_id
                )
            ):
                return PolicyDecision.allow("read")
            return PolicyDecision.deny(
                AgentErrorCode.MEMORY_ACCESS_DENIED,
                action="read",
                details={
                    "scope": "workflow",
                    "reason": "Caller does not belong to active workflow execution.",
                },
            )

        if record.scope == "agent":
            if (
                admin
                or (
                    security_context.agent_execution_id
                    and security_context.agent_execution_id == record.owner_id
                )
            ):
                return PolicyDecision.allow("read")
            return PolicyDecision.deny(
                AgentErrorCode.MEMORY_ACCESS_DENIED,
                action="read",
                details={
                    "scope": "agent",
                    "reason": "Agent working memory requires matching execution ID.",
                },
            )

        return PolicyDecision.deny(
            AgentErrorCode.MEMORY_INVALID_SCOPE,
            action="read",
            details={"scope": record.scope},
        )

    def check_mutation_access(
        self,
        scope: MemoryScope,
        owner_id: str,
        target_tenant_id: str,
        action: str,
        security_context: MemorySecurityContext,
    ) -> PolicyDecision:
        """Checks rights to approve, modify, or delete a memory in given scope."""
        # 1. Tenant check
        tenant_check = self.check_tenant_boundary(target_tenant_id, security_context)
        if not tenant_check.allowed:
            return tenant_check

        admin = is_tenant_admin(security_context)

        if scope == "user":
            if owner_id == security_context.user_id or admin:
                return PolicyDecision.allow(action)
            return PolicyDecision.deny(
                AgentErrorCode.MEMORY_ACCESS_DENIED,
                action=action,
                details={
                    "scope": "user",
                    "reason": f"Cannot {action} memory owned by another user.",
                },
            )

        if scope == "organization":
            # Organization memory mutations require Org Admin privilege
            if admin:
                return PolicyDecision.allow(action)
            return PolicyDecision.deny(
                AgentErrorCode.MEMORY_ACCESS_DENIED,
                action=action,
                details={
                    "scope": "organization",
                    "reason": f"Organization memory {action} requires Org Admin privileges.",
                },
            )

        if scope in ("workflow", "agent"):
            if admin:
                return PolicyDecision.allow(action)
            if (
                scope == "workflow"
                and security_context.workflow_execution_id == owner_id
            ):
                return PolicyDecision.allow(action)
            if scope == "agent" and security_context.agent_execution_id == owner_id:
                return PolicyDecision.allow(action)
            return PolicyDecision.deny(
                AgentErrorCode.MEMORY_ACCESS_DENIED,
                action=action,
                details={
                    "scope": scope,
                    "reason": f"Execution mismatch for {scope} memory {action}.",
                },
            )

        return PolicyDecision.deny(
            AgentErrorCode.MEMORY_INVALID_SCOPE,
            action=action,
            details={"scope": scope},
        )
