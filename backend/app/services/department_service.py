"""KEEP Enterprise Platform — Department Management Service."""

from datetime import UTC, datetime
from uuid import UUID

from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import ConflictException, NotFoundException
from backend.app.models.department import Department
from backend.app.repositories.department_repo import DepartmentRepository
from backend.app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)
from backend.app.services.activity_service import ActivityService
from backend.app.services.base import BaseService
from sqlalchemy.ext.asyncio import AsyncSession


class DepartmentService(BaseService[DepartmentRepository]):
    """Service handling department lifecycle and tenant-scoped governance."""

    def __init__(self, repository: DepartmentRepository | None = None) -> None:
        super().__init__(repository or DepartmentRepository())

    async def create_department(
        self,
        db: AsyncSession,
        org_id: UUID,
        payload: DepartmentCreate,
        caller_user_id: UUID,
    ) -> DepartmentResponse:
        """Creates a new department within the tenant."""
        existing = await self.repository.get_by_name(db, org_id, payload.name)
        if existing:
            raise ConflictException(
                message=f"Department '{payload.name}' already exists in this organization.",
                code=ErrorCode.DEPT_NAME_EXISTS,
            )

        dept = Department(
            organization_id=org_id,
            name=payload.name,
            description=payload.description,
            manager_id=payload.manager_id,
            is_deleted=False,
        )
        db.add(dept)
        await db.flush()
        await db.refresh(dept)

        await ActivityService.record_activity(
            db,
            organization_id=org_id,
            user_id=caller_user_id,
            action="DEPARTMENT_CREATED",
            resource_type="department",
            resource_id=dept.id,
            details=f"Created department '{dept.name}'",
        )
        await db.commit()
        await db.refresh(dept)

        return DepartmentResponse(
            id=dept.id,
            organization_id=dept.organization_id,
            name=dept.name,
            description=dept.description,
            manager_id=dept.manager_id,
            team_count=0,
            member_count=0,
            created_at=dept.created_at,
            updated_at=dept.updated_at,
        )

    async def list_departments(
        self,
        db: AsyncSession,
        org_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DepartmentResponse]:
        """Lists departments for the tenant with aggregated team and member counts."""
        depts = await self.repository.list_for_organization(db, org_id, skip=skip, limit=limit)
        responses: list[DepartmentResponse] = []
        for d in depts:
            team_count = await self.repository.get_team_count(db, d.id)
            member_count = await self.repository.get_member_count(db, d.id)
            responses.append(
                DepartmentResponse(
                    id=d.id,
                    organization_id=d.organization_id,
                    name=d.name,
                    description=d.description,
                    manager_id=d.manager_id,
                    team_count=team_count,
                    member_count=member_count,
                    created_at=d.created_at,
                    updated_at=d.updated_at,
                )
            )
        return responses

    async def get_department(
        self,
        db: AsyncSession,
        org_id: UUID,
        dept_id: UUID,
    ) -> DepartmentResponse:
        """Retrieves department details with counts strictly scoped to the tenant."""
        dept = await self.repository.get_by_id_scoped(db, org_id, dept_id)
        if not dept:
            raise NotFoundException(
                message=f"Department with ID '{dept_id}' not found.",
                code=ErrorCode.DEPT_NOT_FOUND,
            )

        team_count = await self.repository.get_team_count(db, dept.id)
        member_count = await self.repository.get_member_count(db, dept.id)
        return DepartmentResponse(
            id=dept.id,
            organization_id=dept.organization_id,
            name=dept.name,
            description=dept.description,
            manager_id=dept.manager_id,
            team_count=team_count,
            member_count=member_count,
            created_at=dept.created_at,
            updated_at=dept.updated_at,
        )

    async def update_department(
        self,
        db: AsyncSession,
        org_id: UUID,
        dept_id: UUID,
        payload: DepartmentUpdate,
        caller_user_id: UUID,
    ) -> DepartmentResponse:
        """Updates department details."""
        dept = await self.repository.get_by_id_scoped(db, org_id, dept_id)
        if not dept:
            raise NotFoundException(
                message=f"Department with ID '{dept_id}' not found.",
                code=ErrorCode.DEPT_NOT_FOUND,
            )

        if payload.name and payload.name != dept.name:
            existing = await self.repository.get_by_name(db, org_id, payload.name)
            if existing and existing.id != dept.id:
                raise ConflictException(
                    message=f"Department name '{payload.name}' is already in use.",
                    code=ErrorCode.DEPT_NAME_EXISTS,
                )
            dept.name = payload.name

        if payload.description is not None:
            dept.description = payload.description
        if payload.manager_id is not None:
            dept.manager_id = payload.manager_id

        db.add(dept)
        await db.flush()

        await ActivityService.record_activity(
            db,
            organization_id=org_id,
            user_id=caller_user_id,
            action="DEPARTMENT_UPDATED",
            resource_type="department",
            resource_id=dept.id,
            details=f"Updated department '{dept.name}'",
        )
        await db.commit()
        await db.refresh(dept)

        team_count = await self.repository.get_team_count(db, dept.id)
        member_count = await self.repository.get_member_count(db, dept.id)
        return DepartmentResponse(
            id=dept.id,
            organization_id=dept.organization_id,
            name=dept.name,
            description=dept.description,
            manager_id=dept.manager_id,
            team_count=team_count,
            member_count=member_count,
            created_at=dept.created_at,
            updated_at=dept.updated_at,
        )

    async def delete_department(
        self,
        db: AsyncSession,
        org_id: UUID,
        dept_id: UUID,
        caller_user_id: UUID,
    ) -> bool:
        """Soft-deletes a department."""
        dept = await self.repository.get_by_id_scoped(db, org_id, dept_id)
        if not dept:
            raise NotFoundException(
                message=f"Department with ID '{dept_id}' not found.",
                code=ErrorCode.DEPT_NOT_FOUND,
            )

        dept.is_deleted = True
        dept.deleted_at = datetime.now(UTC)
        db.add(dept)
        await db.flush()

        await ActivityService.record_activity(
            db,
            organization_id=org_id,
            user_id=caller_user_id,
            action="DEPARTMENT_DELETED",
            resource_type="department",
            resource_id=dept.id,
            details=f"Deleted department '{dept.name}'",
        )
        await db.commit()
        return True
