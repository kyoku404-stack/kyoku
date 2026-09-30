"""KEEP Enterprise Platform — Document Repository."""

from typing import Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.repositories.base import BaseRepository
from backend.app.schemas.document import DocumentResponse


class DocumentRepository(BaseRepository[Any, Any, Any]):
    """Repository handling Document metadata entity operations."""

    def __init__(self, model: Any = None) -> None:
        super().__init__(model)

    async def get_by_tenant(
        self,
        db: AsyncSession,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Any]:
        """Retrieves documents isolated to a specific organization tenant."""
        if not self.model:
            return []
        stmt = (
            select(self.model)
            .where(self.model.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
