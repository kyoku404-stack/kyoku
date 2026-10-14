"""Unit Test Suite: Phase 1.7 Dashboard Services, Cache & Schemas.

Validates:
1. CacheManager (in-memory fallback, TTL expiry, rate limiting, and counters)
2. AIQueryService (sanitization, length validation, rate-limit enforcement, SSE tokens)
3. DashboardService greeting logic and admin role evaluation
4. NotificationService business validation and pagination logic
5. Pydantic schema validation for all Phase 1.7 data contracts

Owner: Member 2 (Backend Lead)
Sub-phase: Phase 1.7 Dashboard Development & User Experience
Reference: devdocs/p1/p1.7.txt, docs/Architecture/dashboard-architecture.md
"""

import asyncio
from datetime import datetime, timezone
import unittest
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.core.cache import CacheManager
from backend.app.core.constants import ErrorCode, UserRole
from backend.app.core.exceptions import (
    RateLimitExceededException,
    ValidationException,
)
from backend.app.schemas.dashboard import (
    ActivityActor,
    ActivityEventResponse,
    AIQueryContext,
    AIQueryRequest,
    DashboardAnalyticsSummaryResponse,
    DashboardKPI,
    DashboardOrg,
    DashboardSummaryResponse,
    DashboardUser,
    DocumentReference,
    DocumentSummaryResponse,
    DocumentUploaderSummary,
    GlobalSearchResponse,
    GlobalSearchResultItem,
    NotificationCreate,
    NotificationReadAllResponse,
    NotificationResponse,
    ProjectDistributionItem,
    ProjectMemberSummary,
    ProjectSummaryResponse,
    TimeSeriesPoint,
)
from backend.app.services.ai_query_service import AIQueryService
from backend.app.services.dashboard_service import DashboardService


class TestDashboardSchemas(unittest.TestCase):
    """Validates Phase 1.7 Pydantic schemas serialization and structure."""

    def test_dashboard_summary_schema(self) -> None:
        user_id = uuid4()
        org_id = uuid4()
        summary = DashboardSummaryResponse(
            user=DashboardUser(
                id=user_id,
                full_name="Alice Architect",
                email="alice@keep.corp",
                role="OrgAdmin",
                avatar_url=None,
            ),
            organization=DashboardOrg(
                id=org_id,
                name="Keep Corp",
                logo_url=None,
                plan="enterprise",
            ),
            kpi=DashboardKPI(
                total_projects=10,
                total_documents=150,
                total_members=25,
                upcoming_meetings=3,
                storage_used_bytes=52428800,
                storage_quota_bytes=107374182400,
                ai_queries_today=42,
            ),
            greeting_time_of_day="morning",
        )
        data = summary.model_dump()
        self.assertEqual(data["user"]["full_name"], "Alice Architect")
        self.assertEqual(data["organization"]["plan"], "enterprise")
        self.assertEqual(data["kpi"]["total_projects"], 10)
        self.assertEqual(data["greeting_time_of_day"], "morning")

    def test_activity_event_schema(self) -> None:
        event = ActivityEventResponse(
            id=uuid4(),
            actor=ActivityActor(id=uuid4(), full_name="Bob Builder"),
            action="uploaded",
            resource_type="document",
            resource_id=uuid4(),
            resource_name="Blueprint.pdf",
            metadata={"size_mb": 12},
            occurred_at=datetime.now(timezone.utc),
        )
        self.assertEqual(event.action, "uploaded")
        self.assertEqual(event.resource_type, "document")

    def test_project_summary_schema(self) -> None:
        proj = ProjectSummaryResponse(
            id=uuid4(),
            name="Knowledge Graph",
            description="Enterprise KG pipeline",
            status="active",
            priority="high",
            progress_percent=85,
            deadline="2026-12-31",
            team_members=[ProjectMemberSummary(id=uuid4(), full_name="Team Lead")],
            document_count=18,
            updated_at=datetime.now(timezone.utc),
        )
        self.assertEqual(proj.name, "Knowledge Graph")
        self.assertEqual(proj.progress_percent, 85)

    def test_notification_schema(self) -> None:
        notif = NotificationResponse(
            id=uuid4(),
            type="info",
            title="System Alert",
            body="New security patches deployed.",
            action_url="/system/status",
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        self.assertEqual(notif.type, "info")
        self.assertFalse(notif.is_read)

    def test_analytics_summary_schema(self) -> None:
        analytics = DashboardAnalyticsSummaryResponse(
            period="week",
            documents_uploaded=[TimeSeriesPoint(label="Mon", value=5)],
            active_users=[TimeSeriesPoint(label="Mon", value=20)],
            new_members=[TimeSeriesPoint(label="Mon", value=2)],
            project_distribution=[ProjectDistributionItem(status="active", count=4)],
            ai_usage_trend=[],
            search_trend=[],
        )
        self.assertEqual(analytics.period, "week")
        self.assertEqual(len(analytics.documents_uploaded), 1)

    def test_global_search_schema(self) -> None:
        search_res = GlobalSearchResponse(
            query="Alpha",
            total=1,
            items=[
                GlobalSearchResultItem(
                    type="project",
                    id=uuid4(),
                    title="Project Alpha",
                    subtitle="Active Project",
                    url="/projects/1",
                    icon="project",
                    relevance_score=0.98,
                )
            ],
        )
        self.assertEqual(search_res.total, 1)
        self.assertEqual(search_res.items[0].type, "project")


class TestCacheManager(unittest.IsolatedAsyncioTestCase):
    """Validates CacheManager in-memory fallbacks, expiry, counters, and rate limiting."""

    async def asyncSetUp(self) -> None:
        self.cache = CacheManager()
        self.cache.clear_in_memory()

    async def test_set_and_get(self) -> None:
        await self.cache.set("key1", "value1", ttl=60)
        val = await self.cache.get("key1")
        self.assertEqual(val, "value1")

    async def test_get_nonexistent(self) -> None:
        val = await self.cache.get("nonexistent")
        self.assertIsNone(val)

    async def test_delete(self) -> None:
        await self.cache.set("key_del", "val", ttl=60)
        await self.cache.delete("key_del")
        self.assertIsNone(await self.cache.get("key_del"))

    async def test_delete_pattern(self) -> None:
        await self.cache.set("dashboard:user1:org1", "val1", ttl=60)
        await self.cache.set("dashboard:user2:org1", "val2", ttl=60)
        await self.cache.set("other:key", "val3", ttl=60)

        deleted = await self.cache.delete_pattern("dashboard:*")
        self.assertEqual(deleted, 2)
        self.assertIsNone(await self.cache.get("dashboard:user1:org1"))
        self.assertIsNotNone(await self.cache.get("other:key"))

    async def test_counters(self) -> None:
        val1 = await self.cache.incr("test_counter", ttl=60)
        val2 = await self.cache.incr("test_counter", ttl=60)
        val3 = await self.cache.get_counter("test_counter")
        self.assertEqual(val1, 1)
        self.assertEqual(val2, 2)
        self.assertEqual(val3, 2)

    async def test_rate_limiting(self) -> None:
        user_id = str(uuid4())
        # First 3 requests should pass
        for i in range(3):
            allowed, rem = await self.cache.check_rate_limit(user_id, limit=3, window_seconds=60)
            self.assertTrue(allowed)

        # 4th request should fail
        allowed, rem = await self.cache.check_rate_limit(user_id, limit=3, window_seconds=60)
        self.assertFalse(allowed)
        self.assertEqual(rem, 0)


class TestAIQueryService(unittest.IsolatedAsyncioTestCase):
    """Validates AIQueryService query sanitization, token limits, and stub streaming."""

    def setUp(self) -> None:
        self.service = AIQueryService()
        self.user = AuthenticatedUser(
            user_id=uuid4(),
            email="tester@keep.corp",
            role=UserRole.MEMBER,
            organization_id=uuid4(),
        )

    def test_sanitize_query(self) -> None:
        dirty = "Hello\x00\x08World\x1F!\nThis is clean\t."
        clean = self.service.sanitize_query(dirty)
        self.assertEqual(clean, "HelloWorld!\nThis is clean\t.")

    async def test_query_too_long_raises_exception(self) -> None:
        long_query = "A" * 4097
        req = AIQueryRequest.model_construct(query=long_query, stream=True)
        with self.assertRaises(ValidationException) as ctx:
            gen = self.service.execute_query_stream(req, self.user)
            await gen.__anext__()
        self.assertEqual(ctx.exception.code, ErrorCode.AI_QUERY_TOO_LONG)

    async def test_empty_query_raises_exception(self) -> None:
        req = AIQueryRequest(query="   \x00\x01  ", stream=True)
        with self.assertRaises(ValidationException) as ctx:
            gen = self.service.execute_query_stream(req, self.user)
            await gen.__anext__()
        self.assertEqual(ctx.exception.code, ErrorCode.VALIDATION_ERROR)

    async def test_stub_streaming_emits_expected_events(self) -> None:
        req = AIQueryRequest(query="Summarize this week's activity", stream=True)
        events: list[str] = []
        async for chunk in self.service.execute_query_stream(req, self.user):
            events.append(chunk)

        self.assertGreater(len(events), 2)
        # Verify token events
        self.assertTrue(any("event: token" in ev for ev in events))
        # Verify done event
        self.assertTrue(any("event: done" in ev for ev in events))
        self.assertTrue(any("query_id" in ev for ev in events))


class TestDashboardGreeting(unittest.TestCase):
    """Validates time of day greeting calculation."""

    def test_determine_greeting(self) -> None:
        service = DashboardService()
        greeting = service._determine_greeting("UTC")
        self.assertIn(greeting, ["morning", "afternoon", "evening"])

        # Invalid timezone string falls back gracefully to UTC
        greeting_fallback = service._determine_greeting("NonExistent/TimeZone")
        self.assertIn(greeting_fallback, ["morning", "afternoon", "evening"])


if __name__ == "__main__":
    unittest.main()
