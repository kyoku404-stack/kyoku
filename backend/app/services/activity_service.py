"""KEEP Enterprise Platform — Audit & Activity Logging Service."""

from uuid import UUID

from backend.app.models.activity import ActivityLog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class ActivityService:
    """Service to record and retrieve immutable structured audit and activity events."""

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

    @staticmethod
    async def get_audit_logs(
        db: AsyncSession,
        *,
        organization_id: UUID,
        user_id: UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[ActivityLog], int]:
        """Retrieves paginated audit logs scoped to the tenant organization."""
        query = select(ActivityLog).where(ActivityLog.organization_id == organization_id)
        count_query = select(func.count(ActivityLog.id)).where(ActivityLog.organization_id == organization_id)

        if user_id is not None:
            query = query.where(ActivityLog.user_id == user_id)
            count_query = count_query.where(ActivityLog.user_id == user_id)

        if action is not None:
            query = query.where(ActivityLog.action == action)
            count_query = count_query.where(ActivityLog.action == action)

        if resource_type is not None:
            query = query.where(ActivityLog.resource_type == resource_type)
            count_query = count_query.where(ActivityLog.resource_type == resource_type)

        # Count total
        total_res = await db.execute(count_query)
        total = total_res.scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        query = query.order_by(ActivityLog.created_at.desc()).offset(offset).limit(page_size)

        result = await db.execute(query)
        logs = list(result.scalars().all())

        return logs, total
