"""KEEP Enterprise Platform — Organization Endpoints (`/api/v1/organizations`)."""

from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
    require_roles,
)
from backend.app.api.dependencies.database import get_db
from backend.app.core.constants import UserRole
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from backend.app.services.org_service import OrganizationService
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/organizations", tags=["Organizations"])
org_service = OrganizationService()


@router.post(
    "",
    response_model=ApiResponse[OrganizationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create enterprise organization",
    description="Provisions a new enterprise tenant container.",
)
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)
    ),
) -> ApiResponse[OrganizationResponse]:
    """Creates a new organization."""
    org = await org_service.create_organization(
        db=db,
        payload=payload,
        creator_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Organization created successfully.",
        data=org,
    )


@router.get(
    "/current",
    response_model=ApiResponse[OrganizationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current organization details",
    description="Returns organization details for the active tenant boundary.",
)
async def get_current_organization(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[OrganizationResponse]:
    """Retrieves the organization matching the caller's JWT tenant."""
    org = await org_service.get_current_organization(
        db=db,
        org_id=current_user.organization_id,
    )
    return ApiResponse(
        success=True,
        message="Organization details retrieved.",
        data=org,
    )


@router.get(
    "/{id}",
    response_model=ApiResponse[OrganizationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get organization by ID",
    description="Retrieves organization details enforcing tenant isolation.",
)
async def get_organization_by_id(
    id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[OrganizationResponse]:
    """Retrieves an organization with multi-tenant boundary check."""
    is_super = current_user.role == UserRole.SUPER_ADMIN
    org = await org_service.get_organization_by_id(
        db=db,
        org_id=id,
        caller_org_id=current_user.organization_id,
        is_super_admin=is_super,
    )
    return ApiResponse(
        success=True,
        message="Organization retrieved.",
        data=org,
    )


@router.patch(
    "/{id}",
    response_model=ApiResponse[OrganizationResponse],
    status_code=status.HTTP_200_OK,
    summary="Update organization settings",
    description="Updates organization workspace settings and configurations.",
)
async def update_organization(
    id: UUID,
    payload: OrganizationUpdate,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[OrganizationResponse]:
    """Updates organization settings."""
    is_super = current_user.role == UserRole.SUPER_ADMIN
    if not is_super and id != current_user.organization_id:
        from backend.app.core.constants import ErrorCode
        from backend.app.core.exceptions import ForbiddenException

        raise ForbiddenException(
            message="Cross-tenant access forbidden.",
            code=ErrorCode.TENANT_ACCESS_DENIED,
        )

    org = await org_service.update_organization(
        db=db,
        org_id=id,
        payload=payload,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Organization updated successfully.",
        data=org,
    )


@router.delete(
    "/{id}",
    response_model=ApiResponse[dict[str, bool]],
    status_code=status.HTTP_200_OK,
    summary="Archive / delete organization",
    description="Soft-deletes and archives an enterprise tenant.",
)
async def delete_organization(
    id: UUID,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict[str, bool]]:
    """Archives an organization."""
    is_super = current_user.role == UserRole.SUPER_ADMIN
    if not is_super and id != current_user.organization_id:
        from backend.app.core.constants import ErrorCode
        from backend.app.core.exceptions import ForbiddenException

        raise ForbiddenException(
            message="Cross-tenant access forbidden.",
            code=ErrorCode.TENANT_ACCESS_DENIED,
        )

    await org_service.delete_organization(
        db=db,
        org_id=id,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Organization archived successfully.",
        data={"is_deleted": True},
    )
