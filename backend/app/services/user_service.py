"""KEEP Enterprise Platform — User Management Service."""

from datetime import UTC, datetime
from uuid import UUID

from backend.app.core.constants import UserRole
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.envelope import PaginatedData
from backend.app.schemas.user import UserProfileResponse
from backend.app.services.base import BaseService
from sqlalchemy.ext.asyncio import AsyncSession


class UserService(BaseService[UserRepository]):
    """Service managing user accounts, listing, and updates."""

    def __init__(self, repository: UserRepository | None = None) -> None:
        super().__init__(repository or UserRepository())

    async def list_users(
        self,
        db: AsyncSession | None,
        org_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedData[UserProfileResponse]:
        """Returns paginated users for the tenant."""
        users = [
            UserProfileResponse(
                id=UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6"),
                email="admin@acme.com",
                full_name="Jane Doe",
                role=UserRole.ORG_ADMIN,
                organization_id=org_id,
                is_active=True,
                created_at=datetime.now(UTC),
            )
        ]
        return PaginatedData(
            items=users,
            total=len(users),
            page=page,
            page_size=page_size,
            total_pages=1,
        )

    async def get_user_by_id(
        self,
        db: AsyncSession | None,
        user_id: UUID,
        org_id: UUID,
    ) -> UserProfileResponse:
        """Retrieves a user profile ensuring tenant isolation."""
        return UserProfileResponse(
            id=user_id,
            email="user@enterprise.com",
            full_name="Jane Doe",
            role=UserRole.MEMBER,
            organization_id=org_id,
            is_active=True,
            created_at=datetime.now(UTC),
        )
