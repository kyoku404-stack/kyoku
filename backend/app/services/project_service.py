"""KEEP Enterprise Platform — Project Workspace Management Service."""

from datetime import UTC, datetime
from uuid import UUID

from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import ConflictException, NotFoundException
from backend.app.models.project import Project
from backend.app.repositories.project_repo import ProjectRepository
from backend.app.repositories.team_repo import TeamRepository
from backend.app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from backend.app.services.activity_service import ActivityService
from backend.app.services.base import BaseService
from sqlalchemy.ext.asyncio import AsyncSession


class ProjectService(BaseService[ProjectRepository]):
    """Service handling collaborative project workspaces."""

    def __init__(
        self,
        repository: ProjectRepository | None = None,
        team_repo: TeamRepository | None = None,
    ) -> None:
        super().__init__(repository or ProjectRepository())
        self.team_repo = team_repo or TeamRepository()

    def _to_response(self, p: Project) -> ProjectResponse:
        return ProjectResponse(
            id=p.id,
            organization_id=p.organization_id,
            team_id=p.team_id,
            owner_id=p.owner_id,
            name=p.name,
            description=p.description,
            department=p.department,
            status=p.status,
            priority=p.priority,
            timeline=p.timeline,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )

    async def create_project(
        self,
        db: AsyncSession,
        org_id: UUID,
        payload: ProjectCreate,
        caller_user_id: UUID,
    ) -> ProjectResponse:
        """Creates a new project workspace."""
        existing = await self.repository.get_by_name(db, org_id, payload.name)
        if existing:
            raise ConflictException(
                message=f"Project '{payload.name}' already exists in this organization.",
                code=ErrorCode.PROJECT_NAME_EXISTS,
            )

        if payload.team_id:
            team = await self.team_repo.get_by_id_scoped(db, org_id, payload.team_id)
            if not team:
                raise NotFoundException(
                    message=f"Team with ID '{payload.team_id}' not found.",
                    code=ErrorCode.TEAM_NOT_FOUND,
                )

        project = Project(
            organization_id=org_id,
            team_id=payload.team_id,
            owner_id=caller_user_id,
            name=payload.name,
            description=payload.description,
            priority=payload.priority,
            timeline=payload.timeline,
            status="ACTIVE",
            is_deleted=False,
        )
        db.add(project)
        await db.flush()
        await db.refresh(project)

        await ActivityService.record_activity(
            db,
            organization_id=org_id,
            user_id=caller_user_id,
            action="PROJECT_CREATED",
            resource_type="project",
            resource_id=project.id,
            details=f"Created project '{project.name}'",
        )
        await db.commit()
        await db.refresh(project)
        return self._to_response(project)

    async def list_projects(
        self,
        db: AsyncSession,
        org_id: UUID,
        team_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProjectResponse]:
        """Lists projects for the tenant."""
        projects = await self.repository.list_for_organization(
            db, org_id, team_id=team_id, status=status, skip=skip, limit=limit
        )
        return [self._to_response(p) for p in projects]

    async def get_project(
        self,
        db: AsyncSession,
        org_id: UUID,
        project_id: UUID,
    ) -> ProjectResponse:
        """Retrieves project workspace details."""
        project = await self.repository.get_by_id_scoped(db, org_id, project_id)
        if not project:
            raise NotFoundException(
                message=f"Project with ID '{project_id}' not found.",
                code=ErrorCode.PROJECT_NOT_FOUND,
            )
        return self._to_response(project)

    async def update_project(
        self,
        db: AsyncSession,
        org_id: UUID,
        project_id: UUID,
        payload: ProjectUpdate,
        caller_user_id: UUID,
    ) -> ProjectResponse:
        """Updates project workspace metadata."""
        project = await self.repository.get_by_id_scoped(db, org_id, project_id)
        if not project:
            raise NotFoundException(
                message=f"Project with ID '{project_id}' not found.",
                code=ErrorCode.PROJECT_NOT_FOUND,
            )

        if payload.name and payload.name != project.name:
            existing = await self.repository.get_by_name(db, org_id, payload.name)
            if existing and existing.id != project.id:
                raise ConflictException(
                    message=f"Project name '{payload.name}' is already in use.",
                    code=ErrorCode.PROJECT_NAME_EXISTS,
                )
            project.name = payload.name

        if payload.team_id is not None:
            team = await self.team_repo.get_by_id_scoped(db, org_id, payload.team_id)
            if not team:
                raise NotFoundException(
                    message=f"Team with ID '{payload.team_id}' not found.",
                    code=ErrorCode.TEAM_NOT_FOUND,
                )
            project.team_id = payload.team_id

        if payload.description is not None:
            project.description = payload.description
        if payload.status is not None:
            project.status = payload.status
        if payload.priority is not None:
            project.priority = payload.priority
        if payload.timeline is not None:
            project.timeline = payload.timeline

        db.add(project)
        await db.flush()

        await ActivityService.record_activity(
            db,
            organization_id=org_id,
            user_id=caller_user_id,
            action="PROJECT_UPDATED",
            resource_type="project",
            resource_id=project.id,
            details=f"Updated project '{project.name}'",
        )
        await db.commit()
        await db.refresh(project)
        return self._to_response(project)

    async def delete_project(
        self,
        db: AsyncSession,
        org_id: UUID,
        project_id: UUID,
        caller_user_id: UUID,
    ) -> bool:
        """Archives and soft-deletes a project workspace."""
        project = await self.repository.get_by_id_scoped(db, org_id, project_id)
        if not project:
            raise NotFoundException(
                message=f"Project with ID '{project_id}' not found.",
                code=ErrorCode.PROJECT_NOT_FOUND,
            )

        project.is_deleted = True
        project.status = "ARCHIVED"
        project.deleted_at = datetime.now(UTC)
        db.add(project)
        await db.flush()

        await ActivityService.record_activity(
            db,
            organization_id=org_id,
            user_id=caller_user_id,
            action="PROJECT_ARCHIVED",
            resource_type="project",
            resource_id=project.id,
            details=f"Archived project '{project.name}'",
        )
        await db.commit()
        return True
