"""KEEP Enterprise Platform — Multi-Tenant Isolation Dependency."""

from uuid import UUID

from backend.app.api.dependencies.auth import AuthenticatedUser, get_current_active_user
from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import ForbiddenException
from fastapi import Depends


class TenantContext:
    """Encapsulates tenant-specific execution context."""

    def __init__(self, organization_id: UUID, user_id: UUID) -> None:
        self.organization_id = organization_id
        self.user_id = user_id


async def get_tenant_context(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> TenantContext:
    """Extracts tenant boundary context from the active authenticated principal."""
    if not current_user.organization_id:
        raise ForbiddenException(
            message="User is not associated with an active enterprise tenant.",
            code=ErrorCode.TENANT_MISMATCH,
        )
    return TenantContext(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )
