"""KEEP Enterprise Platform — Organization Repository."""

from typing import Any

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
        """Retrieves an organization record by corporate domain."""
        if not self.model:
            return None
        result = await db.execute(select(self.model).where(self.model.domain == domain))
        return result.scalars().first()
