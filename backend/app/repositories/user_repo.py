"""KEEP Enterprise Platform — User Repository."""

from typing import Any

from backend.app.repositories.base import BaseRepository
from backend.app.schemas.user import UserCreate, UserUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository(BaseRepository[Any, UserCreate, UserUpdate]):
    """Repository handling User entity persistence operations."""

    def __init__(self, model: Any = None) -> None:
        super().__init__(model)

    async def get_by_email(self, db: AsyncSession, email: str) -> Any | None:
        """Retrieves a user record by unique email."""
        if not self.model:
            return None
        result = await db.execute(select(self.model).where(self.model.email == email))
        return result.scalars().first()
