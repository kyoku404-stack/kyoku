"""API Dependencies package initialization."""

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
    get_current_user,
    oauth2_scheme,
    require_roles,
)
from backend.app.api.dependencies.database import get_db
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context

__all__ = [
    "AuthenticatedUser",
    "TenantContext",
    "get_current_active_user",
    "get_current_user",
    "get_db",
    "get_tenant_context",
    "oauth2_scheme",
    "require_roles",
]
