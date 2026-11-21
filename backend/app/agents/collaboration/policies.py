"""KEEP Phase 4.8 — Collaboration Policy Engine.

Enforces zero-trust multi-tenancy, RBAC roles, permission boundaries,
and supervisory conflict escalation rules.

Specification: devdocs/p4/p4.8.txt
Owner: Member 3 (Peer Review, Policies & Conflict Resolution)
"""

from __future__ import annotations

import logging

from backend.app.agents.collaboration.contracts import (
    CollaborationSecurityContext,
    CollaborationSession,
)
from backend.app.agents.errors import (
    CollaborationAccessDeniedError,
    CollaborationTenantIsolationViolationError,
)

logger = logging.getLogger(__name__)

# Roles authorized to submit manual or supervisory conflict resolutions
_SUPERVISORY_ROLES = {"admin", "lead", "architect", "supervisor", "agent.admin"}


class CollaborationPolicyEngine:
    """Evaluates security context and authorization rules for collaboration actions."""

    def authorize_session_access(
        self,
        session: CollaborationSession,
        security_context: CollaborationSecurityContext,
    ) -> None:
        """Enforces tenant boundary isolation between session and requesting context."""
        if not security_context.tenant_id:
            raise CollaborationAccessDeniedError("Missing tenant context.")

        if session.tenant_id != security_context.tenant_id:
            logger.warning(
                "Tenant isolation breach attempted: caller tenant '%s' tried to access session '%s' belonging to tenant '%s'.",
                security_context.tenant_id,
                session.session_id,
                session.tenant_id,
            )
            raise CollaborationTenantIsolationViolationError(
                security_context.tenant_id, session.tenant_id
            )

    def authorize_action(
        self,
        action: str,
        security_context: CollaborationSecurityContext,
    ) -> None:
        """Verifies that the principal has permissions for the requested action."""
        if not security_context.user_id:
            raise CollaborationAccessDeniedError("Missing authenticated user context.")

        # If user has explicit permissions or roles
        if "admin" in security_context.roles:
            return

        if action in ("start_session", "cancel_session", "dispatch_task"):
            required_perms = {"agent.invoke", "collaboration.write", "collaboration.invoke"}
            if not any(p in required_perms for p in security_context.permissions) and not any(
                r in ("lead", "architect", "engineer", "agent") for r in security_context.roles
            ):
                raise CollaborationAccessDeniedError(f"Principal lacks permissions to execute '{action}'.")

        elif action in ("read_session", "list_messages", "list_findings", "list_reviews"):
            required_perms = {"agent.read", "collaboration.read", "agent.invoke"}
            if not any(p in required_perms for p in security_context.permissions) and not security_context.roles:
                raise CollaborationAccessDeniedError(f"Principal lacks permissions to execute '{action}'.")

    def authorize_conflict_resolution(
        self,
        security_context: CollaborationSecurityContext,
    ) -> None:
        """Validates that only supervisory roles or administrators can resolve escalated conflicts."""
        has_supervisory_role = any(r in _SUPERVISORY_ROLES for r in security_context.roles)
        has_admin_perm = any(p in ("agent.admin", "collaboration.admin") for p in security_context.permissions)

        if not has_supervisory_role and not has_admin_perm:
            raise CollaborationAccessDeniedError(
                "Conflict resolution requires supervisory role ('admin', 'lead', 'architect') or 'agent.admin' permission."
            )
