"""KEEP Enterprise Platform — Department Repository."""

from uuid import UUID

from backend.app.models.department import Department
from backend.app.models.team import Team
from backend.app.models.user import User
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.department import DepartmentCreate, DepartmentUpdate
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class DepartmentRepository(
    BaseRepository[Department, DepartmentCreate, DepartmentUpdate]
):
    """Repository handling Department entity persistence."""

    def __init__(self, model: type[Department] = Department) -> None:
        super().__init__(model)

    async def get_by_name(
        self, db: AsyncSession, org_id: UUID, name: str
    ) -> Department | None:
        """Retrieves a department by name within an organization."""
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
        self, db: AsyncSession, org_id: UUID, department_id: UUID
    ) -> Department | None:
        """Retrieves an active department strictly scoped to the tenant."""
        stmt = (
            select(self.model)
            .where(
                self.model.id == department_id,
                self.model.organization_id == org_id,
                self.model.is_deleted.is_(False),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def list_for_organization(
        self, db: AsyncSession, org_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Department]:
        """Lists active departments for a given organization."""
        stmt = (
            select(self.model)
            .where(
                self.model.organization_id == org_id,
                self.model.is_deleted.is_(False),
            )
            .order_by(self.model.name)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_team_count(self, db: AsyncSession, department_id: UUID) -> int:
        """Counts active teams in a department."""
        stmt = (
            select(func.count(Team.id))
            .where(Team.department_id == department_id, Team.is_deleted.is_(False))
        )
        result = await db.execute(stmt)
        return int(result.scalar_one_or_none() or 0)

    async def get_member_count(self, db: AsyncSession, department_id: UUID) -> int:
        """Counts active users assigned to a department."""
        stmt = (
            select(func.count(User.id))
            .where(User.department_id == department_id, User.is_deleted.is_(False))
        )
        result = await db.execute(stmt)
        return int(result.scalar_one_or_none() or 0)
