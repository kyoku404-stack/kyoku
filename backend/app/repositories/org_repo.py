"""KEEP Enterprise Platform — Organization Repository."""

from uuid import UUID

from backend.app.models.organization import Organization
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.organization import OrganizationCreate, OrganizationUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class OrganizationRepository(
    BaseRepository[Organization, OrganizationCreate, OrganizationUpdate]
):
    """Repository handling Organization/Tenant entity operations."""

    def __init__(self, model: type[Organization] = Organization) -> None:
        super().__init__(model)

    async def get_by_domain(self, db: AsyncSession, domain: str) -> Organization | None:
        """Retrieves an active organization record by corporate domain."""
        stmt = (
            select(self.model)
            .where(
                self.model.domain == domain,
                self.model.is_deleted.is_(False),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, name: str) -> Organization | None:
        """Retrieves an active organization record by name."""
        stmt = (
            select(self.model)
            .where(
                self.model.name == name,
                self.model.is_deleted.is_(False),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_active_by_id(self, db: AsyncSession, org_id: UUID) -> Organization | None:
        """Retrieves an active organization by ID."""
        stmt = (
            select(self.model)
            .where(
                self.model.id == org_id,
                self.model.is_deleted.is_(False),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()
