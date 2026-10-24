"""Database Connection & Session Factory.

Manages SQLAlchemy 2.0 asynchronous engine and session creation.
"""

from collections.abc import AsyncGenerator

from backend.app.core.config import settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

db_url = settings.DATABASE_URL or "postgresql+asyncpg://keep_user:keep_password@localhost:5432/keep_db"
is_sqlite = db_url.startswith("sqlite")

engine_kwargs: dict[str, object] = {
    "echo": (settings.LOG_LEVEL.upper() == "DEBUG"),
    "future": True,
}

if not is_sqlite:
    engine_kwargs.update({
        "pool_pre_ping": settings.DB_POOL_PRE_PING,
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
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


async def close_async_engine() -> None:
    """Gracefully disposes connection pools on server shutdown."""
    await async_engine.dispose()


async def check_database_readiness() -> bool:
    """Quick database connectivity check for container lifecycle validation."""
    try:
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:  # noqa: BLE001
        return False

