"""KEEP Enterprise Platform — Project Workspace Endpoints (`/api/v1/projects`)."""

from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
    require_roles,
)
from backend.app.api.dependencies.database import get_db
from backend.app.core.constants import UserRole
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from backend.app.services.project_service import ProjectService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/projects", tags=["Projects"])
project_service = ProjectService()


@router.post(
    "",
    response_model=ApiResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
    description="Creates a collaborative project workspace.",
)
async def create_project(
    payload: ProjectCreate,
    current_user: AuthenticatedUser = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
            UserRole.MANAGER,
            UserRole.PROJECT_MANAGER,
            UserRole.MEMBER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ProjectResponse]:
    """Creates a new project workspace."""
    project = await project_service.create_project(
        db=db,
        org_id=current_user.organization_id,
        payload=payload,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Project created successfully.",
        data=project,
    )


@router.get(
    "",
    response_model=ApiResponse[list[ProjectResponse]],
    status_code=status.HTTP_200_OK,
    summary="List projects",
    description="Lists active projects for the organization with optional team and status filters.",
)
async def list_projects(
    team_id: UUID | None = Query(None, description="Filter by team ID"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status (ACTIVE, ARCHIVED, COMPLETED)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[ProjectResponse]]:
    """Lists projects in tenant."""
    projects = await project_service.list_projects(
        db=db,
        org_id=current_user.organization_id,
        team_id=team_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        success=True,
        message="Projects retrieved successfully.",
        data=projects,
    )


@router.get(
    "/{id}",
    response_model=ApiResponse[ProjectResponse],
    status_code=status.HTTP_200_OK,
    summary="Get project by ID",
    description="Returns project details strictly scoped to caller's organization.",
)
async def get_project(
    id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ProjectResponse]:
    """Retrieves project details."""
    project = await project_service.get_project(
        db=db,
        org_id=current_user.organization_id,
        project_id=id,
    )
    return ApiResponse(
        success=True,
        message="Project retrieved successfully.",
        data=project,
    )


@router.patch(
    "/{id}",
    response_model=ApiResponse[ProjectResponse],
    status_code=status.HTTP_200_OK,
    summary="Update project",
    description="Updates project metadata and status.",
)
async def update_project(
    id: UUID,
    payload: ProjectUpdate,
    current_user: AuthenticatedUser = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.ORG_ADMIN,
            UserRole.MANAGER,
            UserRole.PROJECT_MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ProjectResponse]:
    """Updates a project workspace."""
    project = await project_service.update_project(
        db=db,
        org_id=current_user.organization_id,
        project_id=id,
        payload=payload,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Project updated successfully.",
        data=project,
    )


@router.delete(
    "/{id}",
    response_model=ApiResponse[dict[str, bool]],
    status_code=status.HTTP_200_OK,
    summary="Archive / delete project",
    description="Archives and soft-deletes a project workspace.",
)
async def delete_project(
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
    """Archives a project."""
    await project_service.delete_project(
        db=db,
        org_id=current_user.organization_id,
        project_id=id,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Project archived successfully.",
        data={"archived": True},
    )
