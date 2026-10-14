"""KEEP Enterprise Platform — Dashboard Domain Service.

Coordinates dashboard data aggregation, Redis caching, KPI counters,
role-aware filtering, time-series analytics, and global search.
Derived from devdocs/p1/p1.7.txt and docs/Architecture/dashboard-architecture.md.
"""

import json
from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.core.cache import cache
from backend.app.core.constants import ErrorCode, UserRole
from backend.app.core.exceptions import RoleRequiredException
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.repositories.dashboard_repo import DashboardRepository
from backend.app.repositories.org_repo import OrganizationRepository
from backend.app.schemas.dashboard import (
    ActivityEventResponse,
    DashboardAnalyticsSummaryResponse,
    DashboardKPI,
    DashboardOrg,
    DashboardSummaryResponse,
    DashboardUser,
    DocumentSummaryResponse,
    GlobalSearchResponse,
    ProjectSummaryResponse,
)
from backend.app.schemas.envelope import PaginatedData
from sqlalchemy.ext.asyncio import AsyncSession


class DashboardService:
    """Service providing aggregated dashboard data, caching, and analytics."""

    def __init__(
        self,
        dashboard_repo: DashboardRepository | None = None,
        org_repo: OrganizationRepository | None = None,
    ) -> None:
        self.dashboard_repo = dashboard_repo or DashboardRepository()
        self.org_repo = org_repo or OrganizationRepository()

    def _determine_greeting(self, time_zone_str: str | None = None) -> str:
        """Determines time of day greeting based on organization/user timezone."""
        try:
            tz = ZoneInfo(time_zone_str) if time_zone_str else timezone.utc
            now = datetime.now(tz)
        except Exception:
            now = datetime.now(timezone.utc)

        hour = now.hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        else:
            return "evening"

    def _is_admin(self, user: AuthenticatedUser) -> bool:
        """Helper to determine if caller has administrative organization privileges."""
        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        return role_str in {
            UserRole.SUPER_ADMIN.value,
            UserRole.ORG_ADMIN.value,
            "SuperAdmin",
            "OrgAdmin",
            "ADMIN",
            "admin",
        }

    async def get_dashboard_summary(
        self,
        db: AsyncSession,
        current_user: AuthenticatedUser,
    ) -> DashboardSummaryResponse:
        """Retrieves or builds the personalized dashboard summary with 60s Redis caching."""
        cache_key = f"dashboard:{current_user.id}:{current_user.organization_id}"
        cached_data = await cache.get(cache_key)
        if cached_data:
            try:
                parsed = json.loads(cached_data)
                return DashboardSummaryResponse.model_validate(parsed)
            except Exception:
                pass

        # 1. Fetch organization details
        org = await self.org_repo.get_active_by_id(db, current_user.organization_id)
        org_name = org.name if org else "Default Organization"
        org_logo = org.logo_url if org else None
        org_tz = org.time_zone if org else "UTC"

        # 2. Compute KPI counters
        kpis = await self.dashboard_repo.get_kpi_counters(db, current_user.organization_id)

        # 3. AI Queries Today counter (admin only)
        ai_queries_today = 0
        if self._is_admin(current_user):
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            counter_key = f"ai_queries_today:{current_user.organization_id}:{today_str}"
            ai_queries_today = await cache.get_counter(counter_key)

        role_str = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )
        greeting = self._determine_greeting(org_tz)

        # Fetch user details for accurate profile info
        db_user = await db.get(User, current_user.id)
        user_full_name = db_user.full_name if db_user else (getattr(current_user, "full_name", None) or "User")

        summary = DashboardSummaryResponse(
            user=DashboardUser(
                id=current_user.id,
                full_name=user_full_name,
                email=current_user.email,
                role=role_str,
                avatar_url=None,
            ),
            organization=DashboardOrg(
                id=current_user.organization_id,
                name=org_name,
                logo_url=org_logo,
                plan="enterprise",
            ),
            kpi=DashboardKPI(
                total_projects=kpis["total_projects"],
                total_documents=kpis["total_documents"],
                total_members=kpis["total_members"],
                upcoming_meetings=kpis["upcoming_meetings"],
                storage_used_bytes=kpis["storage_used_bytes"],
                storage_quota_bytes=107374182400,
                ai_queries_today=ai_queries_today,
            ),
            greeting_time_of_day=greeting,
        )

        # Cache for 60 seconds
        await cache.set(cache_key, summary.model_dump_json(), ttl=60)
        return summary

    async def get_activity_feed(
        self,
        db: AsyncSession,
        current_user: AuthenticatedUser,
        filter_type: str = "all",
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedData[ActivityEventResponse]:
        """Returns paginated activity events for tenant."""
        items, total = await self.dashboard_repo.get_activity_feed(
            db=db,
            org_id=current_user.organization_id,
            filter_type=filter_type,
            page=page,
            page_size=page_size,
        )
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1
        return PaginatedData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_recent_projects(
        self,
        db: AsyncSession,
        current_user: AuthenticatedUser,
        limit: int = 6,
    ) -> list[ProjectSummaryResponse]:
        """Returns projects recently updated, role-scoped."""
        is_admin = self._is_admin(current_user)
        return await self.dashboard_repo.get_recent_projects(
            db=db,
            org_id=current_user.organization_id,
            user_id=current_user.id,
            is_admin=is_admin,
            limit=limit,
        )

    async def get_recent_documents(
        self,
        db: AsyncSession,
        current_user: AuthenticatedUser,
        limit: int = 8,
    ) -> list[DocumentSummaryResponse]:
        """Returns documents recently accessed or updated, role-scoped."""
        is_admin = self._is_admin(current_user)
        return await self.dashboard_repo.get_recent_documents(
            db=db,
            org_id=current_user.organization_id,
            user_id=current_user.id,
            is_admin=is_admin,
            limit=limit,
        )

    async def get_analytics_summary(
        self,
        db: AsyncSession,
        current_user: AuthenticatedUser,
        period: str = "week",
    ) -> DashboardAnalyticsSummaryResponse:
        """Returns aggregated organization time-series analytics with 300s Redis caching.

        Strictly enforces ADMIN / ORG_ADMIN authorization per Section 5.6.
        """
        if not self._is_admin(current_user):
            role_val = (
                current_user.role.value
                if hasattr(current_user.role, "value")
                else str(current_user.role)
            )
            raise RoleRequiredException(
                message="Analytics summary requires ADMIN or ORG_ADMIN privileges.",
                code=ErrorCode.AUTH_ROLE_REQUIRED,
                details={
                    "required_roles": ["OrgAdmin", "SuperAdmin", "ADMIN"],
                    "user_role": role_val,
                },
            )

        cache_key = f"analytics:{current_user.organization_id}:{period}"
        cached_data = await cache.get(cache_key)
        if cached_data:
            try:
                parsed = json.loads(cached_data)
                return DashboardAnalyticsSummaryResponse.model_validate(parsed)
            except Exception:
                pass

        analytics = await self.dashboard_repo.get_analytics_summary(
            db=db,
            org_id=current_user.organization_id,
            period=period,
        )

        await cache.set(cache_key, analytics.model_dump_json(), ttl=300)
        return analytics

    async def global_search(
        self,
        db: AsyncSession,
        current_user: AuthenticatedUser,
        query: str,
        search_type: str = "all",
        page: int = 1,
        page_size: int = 10,
    ) -> GlobalSearchResponse:
        """Executes multi-entity full-text search scoped to caller organization."""
        items, total = await self.dashboard_repo.global_search(
            db=db,
            org_id=current_user.organization_id,
            query=query,
            search_type=search_type,
            page=page,
            page_size=page_size,
        )
        return GlobalSearchResponse(
            query=query,
            total=total,
            items=items,
        )
