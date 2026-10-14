"""KEEP Enterprise Platform — Notification Repository.

Provides database access operations for user notifications.
"""

from uuid import UUID

from backend.app.models.notification import Notification
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.dashboard import NotificationCreate
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class NotificationRepository(BaseRepository[Notification, NotificationCreate, NotificationCreate]):
    """Repository handling notification persistence and status updates."""

    def __init__(self, model: type[Notification] = Notification) -> None:
        super().__init__(model)

    async def list_for_user(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> tuple[list[Notification], int]:
        """Retrieves paginated notifications scoped to user and tenant."""
        base_filters = [
            self.model.organization_id == org_id,
            self.model.user_id == user_id,
            self.model.is_deleted.is_(False),
        ]
        if unread_only:
            base_filters.append(self.model.is_read.is_(False))

        # Count total
        count_stmt = select(func.count(self.model.id)).where(*base_filters)
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        # Retrieve items
        offset = (page - 1) * page_size
        stmt = (
            select(self.model)
            .where(*base_filters)
            .order_by(self.model.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_by_id_scoped(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        notification_id: UUID,
    ) -> Notification | None:
        """Retrieves a single notification scoped to tenant and user."""
        stmt = (
            select(self.model)
            .where(
                self.model.id == notification_id,
                self.model.organization_id == org_id,
                self.model.user_id == user_id,
                self.model.is_deleted.is_(False),
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def mark_as_read(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        notification_id: UUID,
    ) -> Notification | None:
        """Marks a single notification as read."""
        item = await self.get_by_id_scoped(db, org_id, user_id, notification_id)
        if not item:
            return None

        item.is_read = True
        await db.flush()
        await db.refresh(item)
        return item

    async def mark_all_read(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
    ) -> int:
        """Marks all unread notifications for a user as read."""
        stmt = (
            update(self.model)
            .where(
                self.model.organization_id == org_id,
                self.model.user_id == user_id,
                self.model.is_read.is_(False),
                self.model.is_deleted.is_(False),
            )
            .values(is_read=True)
        )
        res = await db.execute(stmt)
        await db.flush()
        return res.rowcount or 0

    async def count_unread(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
    ) -> int:
        """Counts unread notifications for user."""
        stmt = select(func.count(self.model.id)).where(
            self.model.organization_id == org_id,
            self.model.user_id == user_id,
            self.model.is_read.is_(False),
            self.model.is_deleted.is_(False),
        )
        res = await db.execute(stmt)
        return res.scalar() or 0

    async def create_user_notification(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        notification_type: str,
        title: str,
        body: str,
        action_url: str | None = None,
    ) -> Notification:
        """Creates and persists a new user notification."""
        notification = Notification(
            organization_id=org_id,
            user_id=user_id,
            type=notification_type,
            title=title,
            body=body,
            action_url=action_url,
            is_read=False,
        )
        db.add(notification)
        await db.flush()
        await db.refresh(notification)
        return notification
