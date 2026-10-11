"""KEEP Enterprise Platform — Member Management Endpoints (`/api/v1/members`)."""

from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
    require_roles,
)
from backend.app.api.dependencies.database import get_db
from backend.app.core.constants import UserRole
from backend.app.schemas.envelope import ApiResponse, PaginatedData
from backend.app.schemas.member import MemberResponse, MemberUpdate
from backend.app.services.member_service import MemberService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/members", tags=["Members"])
member_service = MemberService()


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[MemberResponse]],
    status_code=status.HTTP_200_OK,
    summary="List enterprise members",
    description="Returns a paginated directory of organization members with filtering.",
)
async def list_members(
    department_id: UUID | None = Query(None, description="Filter by department ID"),
    team_id: UUID | None = Query(None, description="Filter by team ID"),
    role: str | None = Query(None, description="Filter by RBAC role"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedData[MemberResponse]]:
    """Lists members for the caller's organization."""
    result = await member_service.list_members(
        db=db,
        org_id=current_user.organization_id,
        department_id=department_id,
        team_id=team_id,
        role=role,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(
        success=True,
        message="Members retrieved successfully.",
        data=result,
    )


@router.patch(
    "/{user_id}",
    response_model=ApiResponse[MemberResponse],
    status_code=status.HTTP_200_OK,
    summary="Update member assignment or role",
    description="Modifies a member's department, team, role, or active status.",
)
async def update_member(
    user_id: UUID,
    payload: MemberUpdate,
    current_user: AuthenticatedUser = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[MemberResponse]:
    """Updates member privileges and assignments."""
    member = await member_service.update_member(
        db=db,
        org_id=current_user.organization_id,
        user_id=user_id,
        payload=payload,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Member updated successfully.",
        data=member,
    )


@router.delete(
    "/{user_id}",
    response_model=ApiResponse[dict[str, bool]],
    status_code=status.HTTP_200_OK,
    summary="Remove member from organization",
    description="Soft-deletes and deactivates a member within the organization.",
)
async def remove_member(
    user_id: UUID,
    current_user: AuthenticatedUser = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict[str, bool]]:
    """Removes a member."""
    await member_service.remove_member(
        db=db,
        org_id=current_user.organization_id,
        user_id=user_id,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Member removed successfully.",
        data={"removed": True},
    )
