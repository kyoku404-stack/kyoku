"""KEEP Enterprise Platform — Organization Management Service."""

from datetime import UTC, datetime
from uuid import UUID

from backend.app.repositories.org_repo import OrganizationRepository
from backend.app.schemas.organization import OrganizationResponse
from backend.app.services.base import BaseService
from sqlalchemy.ext.asyncio import AsyncSession


class OrganizationService(BaseService[OrganizationRepository]):
    """Service handling tenant organizations."""

    def __init__(self, repository: OrganizationRepository | None = None) -> None:
        super().__init__(repository or OrganizationRepository())

    async def get_current_organization(
        self,
        db: AsyncSession | None,
        org_id: UUID,
    ) -> OrganizationResponse:
        """Returns details for the active tenant organization."""
        return OrganizationResponse(
            id=org_id,
            name="Acme Global Enterprise",
            domain="acme.com",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=None,
        )
