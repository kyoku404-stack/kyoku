"""KEEP Enterprise Platform — Department Endpoints (`/api/v1/departments`)."""

from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
    require_roles,
)
from backend.app.api.dependencies.database import get_db
from backend.app.core.constants import UserRole
from backend.app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)
from backend.app.schemas.envelope import ApiResponse
from backend.app.services.department_service import DepartmentService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/departments", tags=["Departments"])
dept_service = DepartmentService()


@router.post(
    "",
    response_model=ApiResponse[DepartmentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create department",
    description="Creates a new department within the caller's organization.",
)
async def create_department(
    payload: DepartmentCreate,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DepartmentResponse]:
    """Creates a new department."""
    dept = await dept_service.create_department(
        db=db,
        org_id=current_user.organization_id,
        payload=payload,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Department created successfully.",
        data=dept,
    )


@router.get(
    "",
    response_model=ApiResponse[list[DepartmentResponse]],
    status_code=status.HTTP_200_OK,
    summary="List departments",
    description="Returns all active departments for the caller's organization.",
)
async def list_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[DepartmentResponse]]:
    """Lists departments in tenant."""
    departments = await dept_service.list_departments(
        db=db,
        org_id=current_user.organization_id,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        success=True,
        message="Departments retrieved successfully.",
        data=departments,
    )


@router.get(
    "/{id}",
    response_model=ApiResponse[DepartmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get department by ID",
    description="Returns department details strictly scoped to caller's organization.",
)
async def get_department(
    id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DepartmentResponse]:
    """Retrieves department details."""
    dept = await dept_service.get_department(
        db=db,
        org_id=current_user.organization_id,
        dept_id=id,
    )
    return ApiResponse(
        success=True,
        message="Department retrieved successfully.",
        data=dept,
    )


@router.patch(
    "/{id}",
    response_model=ApiResponse[DepartmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Update department",
    description="Updates department attributes.",
)
async def update_department(
    id: UUID,
    payload: DepartmentUpdate,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DepartmentResponse]:
    """Updates a department."""
    dept = await dept_service.update_department(
        db=db,
        org_id=current_user.organization_id,
        dept_id=id,
        payload=payload,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Department updated successfully.",
        data=dept,
    )


@router.delete(
    "/{id}",
    response_model=ApiResponse[dict[str, bool]],
    status_code=status.HTTP_200_OK,
    summary="Delete department",
    description="Soft-deletes a department.",
)
async def delete_department(
    id: UUID,
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict[str, bool]]:
    """Deletes a department."""
    await dept_service.delete_department(
        db=db,
        org_id=current_user.organization_id,
        dept_id=id,
        caller_user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Department deleted successfully.",
        data={"deleted": True},
    )
