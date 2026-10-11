"""KEEP Enterprise Platform — Audit & Activity Logging Service."""

from uuid import UUID

from backend.app.models.activity import ActivityLog
from sqlalchemy.ext.asyncio import AsyncSession


class ActivityService:
    """Service to record immutable structured audit and activity events."""

    @staticmethod
    async def record_activity(
        db: AsyncSession,
        *,
        organization_id: UUID,
        user_id: UUID | None,
        action: str,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        details: str | None = None,
        ip_address: str | None = None,
    ) -> ActivityLog:
        """Appends an immutable audit event to activity_logs table."""
        log = ActivityLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
        db.add(log)
        await db.flush()
        return log
