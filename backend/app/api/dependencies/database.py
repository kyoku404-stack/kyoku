"""KEEP Enterprise Platform — Database Session Dependency."""

from collections.abc import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an asynchronous SQLAlchemy session."""
    async for session in get_async_session():
        yield session
