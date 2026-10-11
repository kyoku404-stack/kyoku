"""Database package initialization."""

from typing import Any

from backend.app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from backend.app.db.session import async_session_factory, get_async_session


def seed_database(*args: Any, **kwargs: Any) -> Any:
    """Lazy wrapper to avoid circular import during model loading."""
    from backend.app.db.seed import seed_database as _seed
    return _seed(*args, **kwargs)


__all__ = [
    "Base",
    "SoftDeleteMixin",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "async_session_factory",
    "get_async_session",
    "seed_database",
]
