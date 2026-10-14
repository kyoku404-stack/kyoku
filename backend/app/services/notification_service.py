"""KEEP Enterprise Platform — Notification Service.

Coordinates user notification retrieval, read state changes, and event dispatch.
"""

from uuid import UUID

from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import NotFoundException
from backend.app.repositories.notification_repo import NotificationRepository
from backend.app.schemas.dashboard import (
    NotificationCreate,
    NotificationReadAllResponse,
    NotificationResponse,
)
from backend.app.schemas.envelope import PaginatedData
from sqlalchemy.ext.asyncio import AsyncSession


class NotificationService:
    """Service managing user-targeted notifications."""

    def __init__(self, repo: NotificationRepository | None = None) -> None:
        self.repo = repo or NotificationRepository()

    async def list_notifications(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> PaginatedData[NotificationResponse]:
        """Returns paginated notifications scoped to authenticated user."""
        items, total = await self.repo.list_for_user(
            db=db,
            org_id=org_id,
            user_id=user_id,
            page=page,
            page_size=page_size,
            unread_only=unread_only,
        )
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1
        serialized_items = [NotificationResponse.model_validate(n) for n in items]

        return PaginatedData(
            items=serialized_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def mark_as_read(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        notification_id: UUID,
    ) -> NotificationResponse:
        """Marks a single notification as read."""
        notification = await self.repo.mark_as_read(
            db=db,
            org_id=org_id,
            user_id=user_id,
            notification_id=notification_id,
        )
        if not notification:
            raise NotFoundException(
                message=f"Notification {notification_id} not found.",
                code=ErrorCode.NOT_FOUND,
                details={"notification_id": str(notification_id)},
            )
        return NotificationResponse.model_validate(notification)

    async def mark_all_as_read(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
    ) -> NotificationReadAllResponse:
        """Marks all unread notifications for user as read."""
        updated_count = await self.repo.mark_all_read(
            db=db,
            org_id=org_id,
            user_id=user_id,
        )
        return NotificationReadAllResponse(updated_count=updated_count)

    async def send_notification(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        payload: NotificationCreate,
    ) -> NotificationResponse:
        """Creates and stores a notification for a user."""
        notification = await self.repo.create_user_notification(
            db=db,
            org_id=org_id,
            user_id=user_id,
            notification_type=payload.type,
            title=payload.title,
            body=payload.body,
            action_url=payload.action_url,
        )
        return NotificationResponse.model_validate(notification)

    async def get_unread_count(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
    ) -> int:
        """Returns the total number of unread notifications for a user."""
        return await self.repo.count_unread(db=db, org_id=org_id, user_id=user_id)
