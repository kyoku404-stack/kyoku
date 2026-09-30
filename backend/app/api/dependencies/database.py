"""KEEP Enterprise Platform — Database Session Dependency."""

from collections.abc import AsyncGenerator

from backend.app.db.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an asynchronous SQLAlchemy session."""
    async for session in get_async_session():
        yield session
