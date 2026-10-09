"""Database Connection & Session Factory.

Manages SQLAlchemy 2.0 asynchronous engine and session creation.
"""

from collections.abc import AsyncGenerator

from backend.app.core.config import settings
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

db_url = settings.DATABASE_URL or "postgresql+asyncpg://keep_user:keep_password@localhost:5432/keep_db"
is_sqlite = db_url.startswith("sqlite")

engine_kwargs = {
    "echo": (settings.LOG_LEVEL.upper() == "DEBUG"),
    "future": True,
}

if not is_sqlite:
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    })

# Create async engine with connection pooling
async_engine = create_async_engine(db_url, **engine_kwargs)

# Async session factory
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection generator for FastAPI endpoints."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
