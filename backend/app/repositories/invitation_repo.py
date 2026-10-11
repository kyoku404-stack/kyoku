"""KEEP Enterprise Platform — User Invitation Repository."""

from uuid import UUID

from backend.app.models.invitation import Invitation
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.invitation import InvitationCreate
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class InvitationRepository(BaseRepository[Invitation, InvitationCreate, BaseModel]):
    """Repository handling user invitations persistence."""

    def __init__(self, model: type[Invitation] = Invitation) -> None:
        super().__init__(model)

    async def get_by_token(self, db: AsyncSession, token: str) -> Invitation | None:
        """Retrieves an invitation by unique secure token."""
        stmt = select(self.model).where(self.model.token == token)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_pending_by_email(
        self, db: AsyncSession, org_id: UUID, email: str
    ) -> Invitation | None:
        """Checks for existing pending invitation for email in this organization."""
        stmt = (
            select(self.model)
            .where(
                self.model.organization_id == org_id,
                self.model.email == email,
                self.model.status == "PENDING",
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_id_scoped(
        self, db: AsyncSession, org_id: UUID, invitation_id: UUID
    ) -> Invitation | None:
        """Retrieves an invitation strictly scoped to organization."""
        stmt = (
            select(self.model)
            .where(
                self.model.id == invitation_id,
                self.model.organization_id == org_id,
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def list_for_organization(
        self,
        db: AsyncSession,
        org_id: UUID,
        status: str | None = "PENDING",
        skip: int = 0,
        limit: int = 100,
    ) -> list[Invitation]:
        """Lists invitations for an organization."""
        stmt = select(self.model).where(self.model.organization_id == org_id)
        if status:
            stmt = stmt.where(self.model.status == status)

        stmt = stmt.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
