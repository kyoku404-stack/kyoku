"""KEEP Enterprise Platform — Authorization & Permission Dependencies.

Provides FastAPI dependency factories and validation utilities for Role-Based
Access Control (RBAC), resource-level authorization policies, and audit logging.
Derived from devdocs/p1/p1.6.txt and docs/Architecture/authorization-architecture.md.
"""

from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any
from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
)
from backend.app.core.authorization import default_policy_engine
from backend.app.core.constants import ErrorCode, UserRole
from backend.app.core.exceptions import (
    OrganizationMismatchException,
    PermissionDeniedException,
    PolicyFailedException,
    ResourceForbiddenException,
    RoleRequiredException,
)
from backend.app.models.project import project_users
from backend.app.services.activity_service import ActivityService
from backend.app.services.ai.interfaces import (
    AIPermission,
    AuthorizationDecision,
    BaseAuthorizationPolicyEngine,
    ResourceAuthorizationContext,
    ResourceType,
)
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def require_permission(
    permission: str | AIPermission,
    resource_type: ResourceType | None = None,
) -> Callable[[AuthenticatedUser], Coroutine[Any, Any, AuthenticatedUser]]:
    """FastAPI dependency factory enforcing action-based permission checks.

    Validates that the authenticated user holds the required action permission
    derived from their role in the canonical permission matrix.

    Args:
        permission: The permission key to enforce (e.g., 'document.read', 'user.invite').
        resource_type: Optional target resource category for error context.

    Returns:
        Dependency callable resolving to the AuthenticatedUser.
    """
    perm_key = permission.value if hasattr(permission, "value") else str(permission)

    async def permission_checker(
        current_user: AuthenticatedUser = Depends(get_current_active_user),
    ) -> AuthenticatedUser:
        if not current_user.has_permission(perm_key):
            res_val = resource_type.value if hasattr(resource_type, "value") else str(resource_type) if resource_type else None
            role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
            raise PermissionDeniedException(
                message="You do not have permission to perform this action.",
                code=ErrorCode.AUTH_PERMISSION_DENIED,
                details={
                    "required_permission": perm_key,
                    "user_role": role_val,
                    "resource_type": res_val,
                },
            )
        return current_user

    return permission_checker


def require_role(
    *allowed_roles: UserRole | str,
) -> Callable[[AuthenticatedUser], Coroutine[Any, Any, AuthenticatedUser]]:
    """FastAPI dependency factory enforcing strict role-tier restrictions.

    Raises RoleRequiredException (HTTP 403, AUTH_ROLE_REQUIRED) if caller does
    not match the allowed role tier.

    Args:
        allowed_roles: Variadic collection of acceptable UserRole values.

    Returns:
        Dependency callable resolving to the AuthenticatedUser.
    """
    normalized_allowed: set[str] = {
        r.value if hasattr(r, "value") else str(r) for r in allowed_roles
    }

    async def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_active_user),
    ) -> AuthenticatedUser:
        user_role_str = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )
        if user_role_str not in normalized_allowed:
            raise RoleRequiredException(
                message=f"Operation requires one of the following roles: {sorted(normalized_allowed)}.",
                code=ErrorCode.AUTH_ROLE_REQUIRED,
                details={
                    "required_roles": sorted(normalized_allowed),
                    "user_role": user_role_str,
                },
            )
        return current_user

    return role_checker


def check_resource_access(
    context: ResourceAuthorizationContext,
    engine: BaseAuthorizationPolicyEngine | None = None,
) -> AuthorizationDecision:
    """Evaluates a resource-level authorization context and raises structured exceptions on denial.

    Args:
        context: Full caller and target resource authorization context.
        engine: Custom policy engine instance or default singleton.

    Returns:
        AuthorizationDecision if granted.

    Raises:
        OrganizationMismatchException: When cross-tenant access is attempted.
        ResourceForbiddenException: When caller lacks project membership.
        PermissionDeniedException: When caller lacks required action permission.
        RoleRequiredException: When minimum role requirement is unfulfilled.
        PolicyFailedException: For other policy engine rejections.
    """
    policy_engine = engine or default_policy_engine
    decision = policy_engine.evaluate_access(context)

    if decision.allowed:
        return decision

    details = {
        "required_permission": decision.required_permission,
        "resource_type": decision.resource_type,
        "reason": decision.reason,
    }

    if decision.error_code == "AUTH_ORGANIZATION_MISMATCH":
        raise OrganizationMismatchException(
            message=decision.reason or "Cross-tenant access attempted.",
            code=ErrorCode.AUTH_ORGANIZATION_MISMATCH,
            details=details,
        )
    elif decision.error_code == "AUTH_RESOURCE_FORBIDDEN":
        raise ResourceForbiddenException(
            message=decision.reason or "Resource is inaccessible.",
            code=ErrorCode.AUTH_RESOURCE_FORBIDDEN,
            details=details,
        )
    elif decision.error_code == "AUTH_ROLE_REQUIRED":
        raise RoleRequiredException(
            message=decision.reason or "Required role not assigned.",
            code=ErrorCode.AUTH_ROLE_REQUIRED,
            details=details,
        )
    elif decision.error_code == "AUTH_PERMISSION_DENIED":
        raise PermissionDeniedException(
            message=decision.reason or "You do not have permission to perform this action.",
            code=ErrorCode.AUTH_PERMISSION_DENIED,
            details=details,
        )
    else:
        raise PolicyFailedException(
            message=decision.reason or "Policy evaluation failed.",
            code=ErrorCode.AUTH_POLICY_FAILED,
            details=details,
        )


async def get_user_project_ids(
    user_id: UUID,
    db: AsyncSession,
) -> set[UUID]:
    """Queries project memberships for a given user from project_users table."""
    stmt = select(project_users.c.project_id).where(project_users.c.user_id == user_id)
    result = await db.execute(stmt)
    return {row[0] for row in result.fetchall()}


async def audit_authorization(
    db: AsyncSession,
    *,
    caller: AuthenticatedUser,
    action: str,
    decision: AuthorizationDecision,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
    ip_address: str | None = None,
) -> None:
    """Emits an immutable structured audit log entry for an authorization decision."""
    event_action = "PERMISSION_GRANTED" if decision.allowed else "PERMISSION_DENIED"
    details = f"Action: {action}. Decision: {'ALLOW' if decision.allowed else 'DENY'}. Reason: {decision.reason}"
    if decision.error_code:
        details += f" Code: {decision.error_code}"

    await ActivityService.record_activity(
        db=db,
        organization_id=caller.organization_id,
        user_id=caller.id,
        action=event_action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )


def authorize(
    permission: str | AIPermission,
    resource_type: ResourceType | None = None,
) -> Callable[..., Any]:
    """Decorator for route handlers or service methods enforcing authorization.

    Inspects kwargs for 'current_user' (AuthenticatedUser) and validates permission.
    """
    perm_key = permission.value if hasattr(permission, "value") else str(permission)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            current_user: AuthenticatedUser | None = kwargs.get("current_user")
            if current_user and not current_user.has_permission(perm_key):
                role_val = (
                    current_user.role.value
                    if hasattr(current_user.role, "value")
                    else str(current_user.role)
                )
                res_val = (
                    resource_type.value
                    if hasattr(resource_type, "value")
                    else str(resource_type)
                    if resource_type
                    else None
                )
                raise PermissionDeniedException(
                    message="You do not have permission to perform this action.",
                    code=ErrorCode.AUTH_PERMISSION_DENIED,
                    details={
                        "required_permission": perm_key,
                        "user_role": role_val,
                        "resource_type": res_val,
                    },
                )
            return await func(*args, **kwargs)

        return async_wrapper

    return decorator
