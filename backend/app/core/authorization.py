"""KEEP Enterprise Platform — Centralized Authorization Policy Engine & Ownership Checker.

Implements the 7-step authorization evaluation pipeline defined in
docs/Architecture/authorization-architecture.md:
1. Tenant Boundary check (cross-tenant isolation barrier).
2. Role Permission lookup & hierarchical inheritance evaluation.
3. Resource-level ownership override verification.
4. Project containment and workspace membership verification.
5. Standardized AuthorizationDecision generation with structured error codes.
"""

from typing import Any, ClassVar
from uuid import UUID

from backend.app.core.constants import UserRole
from backend.app.services.ai.interfaces import (
    ROLE_PERMISSIONS,
    AuthorizationDecision,
    BaseAuthorizationPolicyEngine,
    BaseResourceOwnershipChecker,
    ResourceAuthorizationContext,
    ResourceType,
)


class ResourceOwnershipChecker(BaseResourceOwnershipChecker):
    """Concrete resource ownership evaluator.

    Validates whether an authenticated caller is the author, creator, or uploader
    of a target resource, allowing ownership-based privilege overrides.
    """

    def __init__(self) -> None:
        # In-memory ownership registry for test scenarios and cached lookup
        # Maps (resource_type, resource_id) -> owner_user_id
        self._registry: dict[tuple[ResourceType | str, UUID], UUID] = {}

    def register_owner(
        self,
        resource_type: ResourceType | str,
        resource_id: UUID,
        owner_id: UUID,
    ) -> None:
        """Explicitly registers an owner for a resource in the local registry."""
        key_type = resource_type if isinstance(resource_type, ResourceType) else ResourceType(str(resource_type))
        self._registry[(key_type, resource_id)] = owner_id

    def clear_registry(self) -> None:
        """Clears registered ownership mappings."""
        self._registry.clear()

    def is_owner(
        self,
        caller_id: UUID,
        resource_type: ResourceType,
        resource_id: UUID,
        organization_id: UUID,
    ) -> bool:
        """Evaluates whether the caller is the owner of the designated resource."""
        # 1. Check explicit registry mapping
        reg_owner = self._registry.get((resource_type, resource_id))
        if reg_owner is not None:
            return reg_owner == caller_id

        # 2. String representation fallback for registry
        str_owner = self._registry.get((resource_type.value, resource_id))
        if str_owner is not None:
            return str_owner == caller_id

        return False


class AuthorizationPolicyEngine(BaseAuthorizationPolicyEngine):
    """Centralized authorization policy engine implementing the 7-step pipeline.

    Evaluates access requests based on:
    - Multi-tenant boundary quarantine
    - Granular action-based role permissions
    - Ownership-based permission overrides
    - Project containment & workspace membership
    """

    # Operations where resource ownership bypasses base role permission deficits
    OWNERSHIP_OVERRIDE_PERMISSIONS: ClassVar[set[str]] = {
        "document.update",
        "document.delete",
        "document.read",
        "meeting.manage",
        "meeting.read",
        "chat_session.delete",
        "chat_session.read",
    }

    # Administrative roles that bypass project workspace membership requirements
    PROJECT_BYPASS_ROLES: ClassVar[set[str]] = {
        UserRole.ORG_ADMIN.value,
        UserRole.SUPER_ADMIN.value,
        "OrgAdmin",
        "SuperAdmin",
        "OrganizationAdmin",
    }

    def __init__(
        self,
        ownership_checker: BaseResourceOwnershipChecker | None = None,
    ) -> None:
        self.ownership_checker: BaseResourceOwnershipChecker = (
            ownership_checker or ResourceOwnershipChecker()
        )

    def evaluate_access(
        self,
        context: ResourceAuthorizationContext,
    ) -> AuthorizationDecision:
        """Evaluates all authorization rules for a single resource access request.

        7-Step Execution Pipeline:
        1. Tenant Isolation: caller_org_id == resource_org_id.
        2. Role Permissions lookup via canonical matrix.
        3. Ownership Override Check (if base role lacks permission).
        4. Project Containment Check (if resource is project-scoped).
        5. Return ALLOW or DENY decision with structured error code.
        """
        # Step 1: Tenant Boundary (Hard isolation short-circuit)
        if context.caller_org_id != context.resource_org_id:
            return AuthorizationDecision.deny(
                error_code="AUTH_ORGANIZATION_MISMATCH",
                reason="Cross-tenant access is strictly prohibited",
                required_permission=context.required_permission,
                resource_type=context.resource_type.value if hasattr(context.resource_type, "value") else str(context.resource_type),
            )

        # Step 2: Role Permission Lookup
        caller_permissions = self._resolve_caller_permissions(context.caller_role)
        has_role_permission = context.required_permission in caller_permissions

        # Step 3: Ownership Override Check
        is_owner = False
        if context.resource_owner_id and context.caller_id == context.resource_owner_id or self.ownership_checker.is_owner(
            caller_id=context.caller_id,
            resource_type=context.resource_type,
            resource_id=context.resource_id,
            organization_id=context.caller_org_id,
        ):
            is_owner = True

        if not has_role_permission:
            if is_owner and context.required_permission in self.OWNERSHIP_OVERRIDE_PERMISSIONS:
                has_role_permission = True
            else:
                return AuthorizationDecision.deny(
                    error_code="AUTH_PERMISSION_DENIED",
                    reason=f"Caller lacks required permission '{context.required_permission}'",
                    required_permission=context.required_permission,
                    resource_type=context.resource_type.value if hasattr(context.resource_type, "value") else str(context.resource_type),
                )

        # Step 4: Project Membership Containment Check (for project-scoped resources)
        if (
            context.caller_role not in self.PROJECT_BYPASS_ROLES
            and context.resource_project_id is not None
            and context.resource_project_id not in context.caller_project_ids
        ):
            return AuthorizationDecision.deny(
                error_code="AUTH_RESOURCE_FORBIDDEN",
                reason="Caller is not a member of the required project workspace",
                required_permission=context.required_permission,
                resource_type=context.resource_type.value if hasattr(context.resource_type, "value") else str(context.resource_type),
            )

        # Step 5: Authorization Allowed
        return AuthorizationDecision.allow(
            reason=f"Access granted for action '{context.required_permission}'"
        )

    def evaluate_bulk_access(
        self,
        contexts: list[ResourceAuthorizationContext],
    ) -> list[AuthorizationDecision]:
        """Bulk evaluation for filtering lists of resources (e.g., search results)."""
        return [self.evaluate_access(ctx) for ctx in contexts]

    def evaluate_policy_rules(
        self,
        context: ResourceAuthorizationContext,
        custom_rules: list[Any] | None = None,
    ) -> AuthorizationDecision:
        """Phase 3+ ABAC extension hook for custom organization policy evaluation."""
        base_decision = self.evaluate_access(context)
        if not base_decision.allowed:
            return base_decision

        if not custom_rules:
            return base_decision

        # Future rule processing engine
        return base_decision

    def _resolve_caller_permissions(self, role: str) -> set[str]:
        """Resolves the canonical action-based permissions for a given role name."""
        if role in ROLE_PERMISSIONS:
            return ROLE_PERMISSIONS[role]

        # Case normalization
        for canonical_role, perms in ROLE_PERMISSIONS.items():
            if canonical_role.lower() == role.lower():
                return perms

        return set()


# Global Singleton Instances
default_ownership_checker = ResourceOwnershipChecker()
default_policy_engine = AuthorizationPolicyEngine(ownership_checker=default_ownership_checker)
