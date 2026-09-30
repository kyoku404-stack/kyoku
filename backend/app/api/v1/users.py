"""KEEP Enterprise Platform — User Endpoints (`/api/v1/users`)."""

from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_user,
    require_roles,
)
from backend.app.api.dependencies.database import get_db
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context
from backend.app.core.constants import UserRole
from backend.app.schemas.envelope import ApiResponse, PaginatedData
from backend.app.schemas.user import UserProfileResponse
from backend.app.services.user_service import UserService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["Users"])
user_service = UserService()


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[UserProfileResponse]],
    status_code=status.HTTP_200_OK,
    summary="List tenant users",
    description="Lists all users belonging to the current tenant organization (Admin/Manager only).",
)
async def list_users(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedData[UserProfileResponse]]:
    """Returns paginated users for tenant."""
    users = await user_service.list_users(
        db=db,
        org_id=tenant.organization_id,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(
        success=True,
        message="Users retrieved successfully.",
        data=users,
    )


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user details by ID",
    description="Retrieves a specific user's details within the tenant boundary.",
)
async def get_user(
    user_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserProfileResponse]:
    """Returns specific user details."""
    user = await user_service.get_user_by_id(
        db=db,
        user_id=user_id,
        org_id=tenant.organization_id,
    )
    return ApiResponse(
        success=True,
        message="User details retrieved.",
        data=user,
    )
