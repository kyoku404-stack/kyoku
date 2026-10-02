"""KEEP Enterprise Platform — Organization Repository."""

from typing import Any

from backend.app.repositories.base import BaseRepository
from backend.app.schemas.organization import OrganizationCreate, OrganizationUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class OrganizationRepository(
    BaseRepository[Any, OrganizationCreate, OrganizationUpdate]
):
    """Repository handling Organization/Tenant entity operations."""

    def __init__(self, model: Any = None) -> None:
        super().__init__(model)

    async def get_by_domain(self, db: AsyncSession, domain: str) -> Any | None:
        """Retrieves an organization record by corporate domain."""
        if not self.model:
            return None
        result = await db.execute(select(self.model).where(self.model.domain == domain))
        return result.scalars().first()
