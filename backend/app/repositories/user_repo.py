"""KEEP Enterprise Platform — User Repository."""

from uuid import UUID

from backend.app.models.user import User
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.user import UserCreate, UserUpdate
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Repository handling User entity persistence operations."""

    def __init__(self, model: type[User] = User) -> None:
        super().__init__(model)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Retrieves a user record by unique email."""
        if not self.model:
            return None
        result = await db.execute(select(self.model).where(self.model.email == email))
        return result.scalars().first()

    async def get_by_id_scoped(
        self, db: AsyncSession, org_id: UUID, user_id: UUID
    ) -> User | None:
        """Retrieves a user record scoped to the organization."""
        stmt = (
            select(self.model)
            .where(
                self.model.id == user_id,
                self.model.organization_id == org_id,
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def list_members(
        self,
        db: AsyncSession,
        org_id: UUID,
        department_id: UUID | None = None,
        team_id: UUID | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[User]:
        """Lists users belonging to an organization with optional filters."""
        stmt = (
            select(self.model)
            .where(
                self.model.organization_id == org_id,
                self.model.is_deleted.is_(False),
            )
        )
        if department_id:
            stmt = stmt.where(self.model.department_id == department_id)
        if team_id:
            stmt = stmt.where(self.model.team_id == team_id)
        if role:
            stmt = stmt.where(self.model.role == role)
        if is_active is not None:
            stmt = stmt.where(self.model.is_active.is_(is_active))

        stmt = stmt.order_by(self.model.full_name).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_members(
        self,
        db: AsyncSession,
        org_id: UUID,
        department_id: UUID | None = None,
        team_id: UUID | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        """Counts users belonging to an organization with optional filters."""
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.organization_id == org_id,
                self.model.is_deleted.is_(False),
            )
        )
        if department_id:
            stmt = stmt.where(self.model.department_id == department_id)
        if team_id:
            stmt = stmt.where(self.model.team_id == team_id)
        if role:
            stmt = stmt.where(self.model.role == role)
        if is_active is not None:
            stmt = stmt.where(self.model.is_active.is_(is_active))

        result = await db.execute(stmt)
        return int(result.scalar_one_or_none() or 0)
