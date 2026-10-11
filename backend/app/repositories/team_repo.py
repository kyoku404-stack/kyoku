"""KEEP Enterprise Platform — Team Repository."""

from uuid import UUID

from backend.app.models.team import Team
from backend.app.models.user import User
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.team import TeamCreate, TeamUpdate
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class TeamRepository(BaseRepository[Team, TeamCreate, TeamUpdate]):
    """Repository handling Team entity persistence."""

    def __init__(self, model: type[Team] = Team) -> None:
        super().__init__(model)

    async def get_by_name(
        self, db: AsyncSession, org_id: UUID, name: str
    ) -> Team | None:
        """Retrieves a team by name within an organization."""
        stmt = (
            select(self.model)
            .where(
                self.model.organization_id == org_id,
                self.model.name == name,
                self.model.is_deleted.is_(False),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_id_scoped(
        self, db: AsyncSession, org_id: UUID, team_id: UUID
    ) -> Team | None:
        """Retrieves an active team strictly scoped to the tenant."""
        stmt = (
            select(self.model)
            .where(
                self.model.id == team_id,
                self.model.organization_id == org_id,
                self.model.is_deleted.is_(False),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def list_for_organization(
        self,
        db: AsyncSession,
        org_id: UUID,
        department_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Team]:
        """Lists active teams for a given organization, optionally filtered by department."""
        stmt = (
            select(self.model)
            .where(
                self.model.organization_id == org_id,
                self.model.is_deleted.is_(False),
            )
        )
        if department_id:
            stmt = stmt.where(self.model.department_id == department_id)

        stmt = stmt.order_by(self.model.name).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_member_count(self, db: AsyncSession, team_id: UUID) -> int:
        """Counts active members assigned to a team."""
        stmt = (
            select(func.count(User.id))
            .where(User.team_id == team_id, User.is_deleted.is_(False))
        )
        result = await db.execute(stmt)
        return int(result.scalar_one_or_none() or 0)
