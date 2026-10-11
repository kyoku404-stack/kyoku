"""KEEP Enterprise Platform — Member Management Service."""

import math
from datetime import UTC, datetime
from uuid import UUID

from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import NotFoundException
from backend.app.models.user import User
from backend.app.repositories.department_repo import DepartmentRepository
from backend.app.repositories.team_repo import TeamRepository
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.envelope import PaginatedData
from backend.app.schemas.member import MemberResponse, MemberUpdate
from backend.app.services.activity_service import ActivityService
from backend.app.services.base import BaseService
from sqlalchemy.ext.asyncio import AsyncSession


class MemberService(BaseService[UserRepository]):
    """Service handling organization member directory and privilege management."""

    def __init__(
        self,
        repository: UserRepository | None = None,
        department_repo: DepartmentRepository | None = None,
        team_repo: TeamRepository | None = None,
    ) -> None:
        super().__init__(repository or UserRepository())
        self.department_repo = department_repo or DepartmentRepository()
        self.team_repo = team_repo or TeamRepository()

    def _to_response(self, u: User) -> MemberResponse:
        return MemberResponse(
            id=u.id,
            organization_id=u.organization_id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            department_id=u.department_id,
            team_id=u.team_id,
            is_active=u.is_active,
            created_at=u.created_at,
        )

    async def list_members(
        self,
        db: AsyncSession,
        org_id: UUID,
        department_id: UUID | None = None,
        team_id: UUID | None = None,
        role: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedData[MemberResponse]:
        """Returns paginated member directory for the tenant."""
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        skip = (page - 1) * page_size

        users = await self.repository.list_members(
            db,
            org_id=org_id,
            department_id=department_id,
            team_id=team_id,
            role=role,
            skip=skip,
            limit=page_size,
        )
        total = await self.repository.count_members(
            db,
            org_id=org_id,
            department_id=department_id,
            team_id=team_id,
            role=role,
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return PaginatedData[MemberResponse](
            items=[self._to_response(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_member(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        payload: MemberUpdate,
        caller_user_id: UUID,
    ) -> MemberResponse:
        """Updates member role, department, team, or active status."""
        user = await self.repository.get_by_id_scoped(db, org_id, user_id)
        if not user:
            raise NotFoundException(
                message=f"Member with ID '{user_id}' not found in this organization.",
                code=ErrorCode.USER_NOT_FOUND,
            )

        if payload.department_id is not None:
            dept = await self.department_repo.get_by_id_scoped(db, org_id, payload.department_id)
            if not dept:
                raise NotFoundException(
                    message=f"Department with ID '{payload.department_id}' not found.",
                    code=ErrorCode.DEPT_NOT_FOUND,
                )
            user.department_id = payload.department_id

        if payload.team_id is not None:
            team = await self.team_repo.get_by_id_scoped(db, org_id, payload.team_id)
            if not team:
                raise NotFoundException(
                    message=f"Team with ID '{payload.team_id}' not found.",
                    code=ErrorCode.TEAM_NOT_FOUND,
                )
            user.team_id = payload.team_id

        if payload.role is not None:
            user.role = payload.role
        if payload.is_active is not None:
            user.is_active = payload.is_active

        db.add(user)
        await db.flush()

        await ActivityService.record_activity(
            db,
            organization_id=org_id,
            user_id=caller_user_id,
            action="MEMBER_UPDATED",
            resource_type="user",
            resource_id=user.id,
            details=f"Updated member '{user.email}' (role: {user.role}, active: {user.is_active})",
        )
        await db.commit()
        await db.refresh(user)
        return self._to_response(user)

    async def remove_member(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        caller_user_id: UUID,
    ) -> bool:
        """Removes / soft-deletes a member from the tenant."""
        user = await self.repository.get_by_id_scoped(db, org_id, user_id)
        if not user:
            raise NotFoundException(
                message=f"Member with ID '{user_id}' not found in this organization.",
                code=ErrorCode.USER_NOT_FOUND,
            )

        user.is_deleted = True
        user.is_active = False
        user.deleted_at = datetime.now(UTC)
        db.add(user)
        await db.flush()

        await ActivityService.record_activity(
            db,
            organization_id=org_id,
            user_id=caller_user_id,
            action="MEMBER_REMOVED",
            resource_type="user",
            resource_id=user.id,
            details=f"Removed member '{user.email}'",
        )
        await db.commit()
        return True
