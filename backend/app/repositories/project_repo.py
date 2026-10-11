"""KEEP Enterprise Platform — Project Repository."""

from uuid import UUID

from backend.app.models.project import Project
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.project import ProjectCreate, ProjectUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ProjectRepository(BaseRepository[Project, ProjectCreate, ProjectUpdate]):
    """Repository handling Project workspace persistence."""

    def __init__(self, model: type[Project] = Project) -> None:
        super().__init__(model)

    async def get_by_name(
        self, db: AsyncSession, org_id: UUID, name: str
    ) -> Project | None:
        """Retrieves a project by name within an organization."""
        stmt = (
            select(self.model)
            .where(
                self.model.organization_id == org_id,
                self.model.name == name,
                self.model.is_deleted.is_(False),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_id_scoped(
        self, db: AsyncSession, org_id: UUID, project_id: UUID
    ) -> Project | None:
        """Retrieves an active project strictly scoped to the tenant."""
        stmt = (
            select(self.model)
            .where(
                self.model.id == project_id,
                self.model.organization_id == org_id,
                self.model.is_deleted.is_(False),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def list_for_organization(
        self,
        db: AsyncSession,
        org_id: UUID,
        team_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Project]:
        """Lists active projects for a given organization with optional filters."""
        stmt = (
            select(self.model)
            .where(
                self.model.organization_id == org_id,
                self.model.is_deleted.is_(False),
            )
        )
        if team_id:
            stmt = stmt.where(self.model.team_id == team_id)
        if status:
            stmt = stmt.where(self.model.status == status)

        stmt = stmt.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
