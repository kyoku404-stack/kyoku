"""KEEP Enterprise Platform — Team Endpoints (`/api/v1/teams`)."""

from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
    require_roles,
)
from backend.app.api.dependencies.database import get_db
from backend.app.core.constants import UserRole
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.team import TeamCreate, TeamResponse, TeamUpdate
from backend.app.services.team_service import TeamService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/teams", tags=["Teams"])
team_service = TeamService()


@router.post(
    "",
    response_model=ApiResponse[TeamResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create team",
    description="Creates a new collaborative team unit.",
)
async def create_team(
    payload: TeamCreate,
    current_user: AuthenticatedUser = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
            UserRole.MANAGER,
            UserRole.PROJECT_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TeamResponse]:
    """Creates a new team."""
    team = await team_service.create_team(
        db=db,
        org_id=current_user.organization_id,
        payload=payload,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Team created successfully.",
        data=team,
    )


@router.get(
    "",
    response_model=ApiResponse[list[TeamResponse]],
    status_code=status.HTTP_200_OK,
    summary="List teams",
    description="Returns all active teams for the caller's organization, with optional department filtering.",
)
async def list_teams(
    department_id: UUID | None = Query(None, description="Filter by parent department ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[TeamResponse]]:
    """Lists teams in tenant."""
    teams = await team_service.list_teams(
        db=db,
        org_id=current_user.organization_id,
        department_id=department_id,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        success=True,
        message="Teams retrieved successfully.",
        data=teams,
    )


@router.get(
    "/{id}",
    response_model=ApiResponse[TeamResponse],
    status_code=status.HTTP_200_OK,
    summary="Get team by ID",
    description="Returns team details strictly scoped to caller's organization.",
)
async def get_team(
    id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TeamResponse]:
    """Retrieves team details."""
    team = await team_service.get_team(
        db=db,
        org_id=current_user.organization_id,
        team_id=id,
    )
    return ApiResponse(
        success=True,
        message="Team retrieved successfully.",
        data=team,
    )


@router.patch(
    "/{id}",
    response_model=ApiResponse[TeamResponse],
    status_code=status.HTTP_200_OK,
    summary="Update team",
    description="Updates team attributes.",
)
async def update_team(
    id: UUID,
    payload: TeamUpdate,
    current_user: AuthenticatedUser = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
            UserRole.MANAGER,
            UserRole.PROJECT_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TeamResponse]:
    """Updates a team."""
    team = await team_service.update_team(
        db=db,
        org_id=current_user.organization_id,
        team_id=id,
        payload=payload,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Team updated successfully.",
        data=team,
    )


@router.delete(
    "/{id}",
    response_model=ApiResponse[dict[str, bool]],
    status_code=status.HTTP_200_OK,
    summary="Delete team",
    description="Soft-deletes a team.",
)
async def delete_team(
    id: UUID,
    current_user: AuthenticatedUser = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
            UserRole.MANAGER,
            UserRole.PROJECT_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict[str, bool]]:
    """Deletes a team."""
    await team_service.delete_team(
        db=db,
        org_id=current_user.organization_id,
        team_id=id,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Team deleted successfully.",
        data={"deleted": True},
    )
