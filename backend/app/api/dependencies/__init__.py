"""API Dependencies package initialization."""

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
    get_current_user,
    oauth2_scheme,
    require_roles,
)
from backend.app.api.dependencies.authorization import (
    audit_authorization,
    authorize,
    check_resource_access,
    get_user_project_ids,
    require_permission,
    require_role,
)
from backend.app.api.dependencies.database import get_db
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context

__all__ = [
    "AuthenticatedUser",
    "TenantContext",
    "audit_authorization",
    "authorize",
    "check_resource_access",
    "get_current_active_user",
    "get_current_user",
    "get_db",
    "get_tenant_context",
    "get_user_project_ids",
    "oauth2_scheme",
    "require_permission",
    "require_role",
    "require_roles",
]
