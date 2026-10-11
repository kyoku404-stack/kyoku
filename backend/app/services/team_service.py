"""KEEP Enterprise Platform — Team Management Service."""

from datetime import UTC, datetime
from uuid import UUID

from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import ConflictException, NotFoundException
from backend.app.models.team import Team
from backend.app.repositories.department_repo import DepartmentRepository
from backend.app.repositories.team_repo import TeamRepository
from backend.app.schemas.team import TeamCreate, TeamResponse, TeamUpdate
from backend.app.services.activity_service import ActivityService
from backend.app.services.base import BaseService
from sqlalchemy.ext.asyncio import AsyncSession


class TeamService(BaseService[TeamRepository]):
    """Service handling collaborative team units."""

    def __init__(
        self,
        repository: TeamRepository | None = None,
        department_repo: DepartmentRepository | None = None,
    ) -> None:
        super().__init__(repository or TeamRepository())
        self.department_repo = department_repo or DepartmentRepository()

    async def create_team(
        self,
        db: AsyncSession,
        org_id: UUID,
        payload: TeamCreate,
        caller_user_id: UUID,
    ) -> TeamResponse:
        """Creates a new team within the organization."""
        existing = await self.repository.get_by_name(db, org_id, payload.name)
        if existing:
            raise ConflictException(
                message=f"Team '{payload.name}' already exists in this organization.",
                code=ErrorCode.TEAM_NAME_EXISTS,
            )

        if payload.department_id:
            dept = await self.department_repo.get_by_id_scoped(db, org_id, payload.department_id)
            if not dept:
                raise NotFoundException(
                    message=f"Department with ID '{payload.department_id}' not found in this organization.",
                    code=ErrorCode.DEPT_NOT_FOUND,
                )

        team = Team(
            organization_id=org_id,
            department_id=payload.department_id,
            lead_user_id=payload.lead_user_id,
            name=payload.name,
            description=payload.description,
            is_deleted=False,
        )
        db.add(team)
        await db.flush()
        await db.refresh(team)

        await ActivityService.record_activity(
            db,
            organization_id=org_id,
            user_id=caller_user_id,
            action="TEAM_CREATED",
            resource_type="team",
            resource_id=team.id,
            details=f"Created team '{team.name}'",
        )
        await db.commit()
        await db.refresh(team)

        return TeamResponse(
            id=team.id,
            organization_id=team.organization_id,
            department_id=team.department_id,
            lead_user_id=team.lead_user_id,
            name=team.name,
            description=team.description,
            member_count=0,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    async def list_teams(
        self,
        db: AsyncSession,
        org_id: UUID,
        department_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TeamResponse]:
        """Lists teams for the tenant with optional department filtering."""
        teams = await self.repository.list_for_organization(
            db, org_id, department_id=department_id, skip=skip, limit=limit
        )
        responses: list[TeamResponse] = []
        for t in teams:
            member_count = await self.repository.get_member_count(db, t.id)
            responses.append(
                TeamResponse(
                    id=t.id,
                    organization_id=t.organization_id,
                    department_id=t.department_id,
                    lead_user_id=t.lead_user_id,
                    name=t.name,
                    description=t.description,
                    member_count=member_count,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                )
            )
        return responses

    async def get_team(
        self,
        db: AsyncSession,
        org_id: UUID,
        team_id: UUID,
    ) -> TeamResponse:
        """Retrieves team details strictly scoped to tenant."""
        team = await self.repository.get_by_id_scoped(db, org_id, team_id)
        if not team:
            raise NotFoundException(
                message=f"Team with ID '{team_id}' not found.",
                code=ErrorCode.TEAM_NOT_FOUND,
            )

        member_count = await self.repository.get_member_count(db, team.id)
        return TeamResponse(
            id=team.id,
            organization_id=team.organization_id,
            department_id=team.department_id,
            lead_user_id=team.lead_user_id,
            name=team.name,
            description=team.description,
            member_count=member_count,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    async def update_team(
        self,
        db: AsyncSession,
        org_id: UUID,
        team_id: UUID,
        payload: TeamUpdate,
        caller_user_id: UUID,
    ) -> TeamResponse:
        """Updates team attributes."""
        team = await self.repository.get_by_id_scoped(db, org_id, team_id)
        if not team:
            raise NotFoundException(
                message=f"Team with ID '{team_id}' not found.",
                code=ErrorCode.TEAM_NOT_FOUND,
            )

        if payload.name and payload.name != team.name:
            existing = await self.repository.get_by_name(db, org_id, payload.name)
            if existing and existing.id != team.id:
                raise ConflictException(
                    message=f"Team name '{payload.name}' is already in use.",
                    code=ErrorCode.TEAM_NAME_EXISTS,
                )
            team.name = payload.name

        if payload.department_id is not None:
            dept = await self.department_repo.get_by_id_scoped(db, org_id, payload.department_id)
            if not dept:
                raise NotFoundException(
                    message=f"Department with ID '{payload.department_id}' not found.",
                    code=ErrorCode.DEPT_NOT_FOUND,
                )
            team.department_id = payload.department_id

        if payload.lead_user_id is not None:
            team.lead_user_id = payload.lead_user_id
        if payload.description is not None:
            team.description = payload.description

        db.add(team)
        await db.flush()

        await ActivityService.record_activity(
            db,
            organization_id=org_id,
            user_id=caller_user_id,
            action="TEAM_UPDATED",
            resource_type="team",
            resource_id=team.id,
            details=f"Updated team '{team.name}'",
        )
        await db.commit()
        await db.refresh(team)

        member_count = await self.repository.get_member_count(db, team.id)
        return TeamResponse(
            id=team.id,
            organization_id=team.organization_id,
            department_id=team.department_id,
            lead_user_id=team.lead_user_id,
            name=team.name,
            description=team.description,
            member_count=member_count,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    async def delete_team(
        self,
        db: AsyncSession,
        org_id: UUID,
        team_id: UUID,
        caller_user_id: UUID,
    ) -> bool:
        """Soft-deletes a team."""
        team = await self.repository.get_by_id_scoped(db, org_id, team_id)
        if not team:
            raise NotFoundException(
                message=f"Team with ID '{team_id}' not found.",
                code=ErrorCode.TEAM_NOT_FOUND,
            )

        team.is_deleted = True
        team.deleted_at = datetime.now(UTC)
        db.add(team)
        await db.flush()

        await ActivityService.record_activity(
            db,
            organization_id=org_id,
            user_id=caller_user_id,
            action="TEAM_DELETED",
            resource_type="team",
            resource_id=team.id,
            details=f"Deleted team '{team.name}'",
        )
        await db.commit()
        return True
