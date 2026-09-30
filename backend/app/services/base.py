"""KEEP Enterprise Platform — Generic Base Service.

Encapsulates common business logic patterns and transaction boundaries.
"""

from typing import Generic, TypeVar

from backend.app.repositories.base import BaseRepository

RepoType = TypeVar("RepoType", bound=BaseRepository)


class BaseService(Generic[RepoType]):
    """Foundational service class binding business operations to a repository."""

    def __init__(self, repository: RepoType | None = None) -> None:
        self.repository = repository
