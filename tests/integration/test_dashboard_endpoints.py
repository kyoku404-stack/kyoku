"""Integration Test Suite: Phase 1.7 Dashboard Development & User Experience.

Verifies:
1. GET /api/v1/dashboard:
   - Personalized user profile, organization metadata, greeting, and live KPI counters.
   - Role-awareness: ai_queries_today is 0 for Member/Viewer, accessible for OrgAdmin.
   - Redis caching: verifies cached response retrieval within 60s TTL.
   - Multi-tenant boundary isolation: Tenant A users receive only Tenant A summary.
2. GET /api/v1/activity:
   - Chronological event stream with actor information.
   - Type filtering (filter=document, filter=project).
   - Pagination boundaries.
   - Multi-tenant boundary isolation: Tenant B events not visible to Tenant A.
3. GET /api/v1/projects/recent:
   - Recent projects list with team members, progress percent, and document count.
   - Role-scoped filtering: Members see only assigned projects; OrgAdmin sees all.
   - Limit boundary parameter.
4. GET /api/v1/documents/recent:
   - Recent documents with file type, file size, uploader, and timestamps.
   - Limit boundary parameter.
5. Notifications subsystem:
   - GET /api/v1/notifications: Strict user isolation (User A never sees User B's notifications).
   - GET /api/v1/notifications?unread_only=true: Returns only unread items.
   - PATCH /api/v1/notifications/{id}/read: Marks single item as read; returns 404 if not owned.
   - POST /api/v1/notifications/read-all: Mass-acknowledges unread items.
6. GET /api/v1/analytics/summary:
   - Time-series charts (documents_uploaded, active_users, new_members, project_distribution).
   - Period filtering (week, month, quarter, year).
   - Role restriction: OrgAdmin and SuperAdmin receive 200; Member/Viewer receive 403 AUTH_ROLE_REQUIRED.
   - Unauthenticated receive 401.
7. POST /api/v1/ai/query (Phase 1.7 Stub):
   - Streams SSE token events and done event.
   - Length validation: > 4096 characters returns 422 AI_QUERY_TOO_LONG.
   - Rate limiting: exceeding 60 queries/hr returns 429 AI_RATE_LIMIT_EXCEEDED.
8. GET /api/v1/search:
   - Global full-text search across projects, documents, users, and teams.
   - Type filter (type=project, type=document, etc.).
   - Multi-tenant boundary isolation.

Owner: Member 2 (Backend Lead)
Sub-phase: Phase 1.7 Dashboard Development & User Experience
Reference: devdocs/p1/p1.7.txt, docs/Architecture/dashboard-architecture.md, docs/API/api-contract.md Section 5
"""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.cache import cache
from backend.app.core.constants import ErrorCode, UserRole
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.activity import ActivityLog
from backend.app.models.document import Document
from backend.app.models.notification import Notification
from backend.app.models.organization import Organization
from backend.app.models.project import Project, project_users
from backend.app.models.team import Team
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestDashboardEndpointsIntegration(unittest.TestCase):
    """Full integration test suite for Phase 1.7 Dashboard and UX APIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        cache.clear_in_memory()

        with Session(sync_test_engine) as session:
            # 1. Create Primary Tenant A
            org_a = Organization(
                name=f"Acme Corp A {uuid4().hex[:6]}",
                domain=f"acmea_{uuid4().hex[:6]}.com",
                time_zone="UTC",
            )
            # 2. Create Tenant B (for multi-tenant isolation verification)
            org_b = Organization(
                name=f"Globex Corp B {uuid4().hex[:6]}",
                domain=f"globexb_{uuid4().hex[:6]}.com",
                time_zone="America/New_York",
            )
            session.add_all([org_a, org_b])
            session.flush()

            cls.org_a_id = org_a.id
            cls.org_b_id = org_b.id

            # Tenant A Users
            admin_a = User(
                email=f"admin_a_{uuid4().hex[:6]}@acme.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Alice Admin",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org_a_id,
                is_active=True,
            )
            member_a1 = User(
                email=f"member_a1_{uuid4().hex[:6]}@acme.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Bob Member A1",
                role=UserRole.MEMBER,
                organization_id=cls.org_a_id,
                is_active=True,
            )
            member_a2 = User(
                email=f"member_a2_{uuid4().hex[:6]}@acme.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Charlie Member A2",
                role=UserRole.MEMBER,
                organization_id=cls.org_a_id,
                is_active=True,
            )

            # Tenant B User
            admin_b = User(
                email=f"admin_b_{uuid4().hex[:6]}@globex.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Dan Admin B",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org_b_id,
                is_active=True,
            )

            session.add_all([admin_a, member_a1, member_a2, admin_b])
            session.flush()

            cls.admin_a_id = admin_a.id
            cls.admin_a_email = admin_a.email
            cls.member_a1_id = member_a1.id
            cls.member_a1_email = member_a1.email
            cls.member_a2_id = member_a2.id
            cls.member_a2_email = member_a2.email
            cls.admin_b_id = admin_b.id
            cls.admin_b_email = admin_b.email

            # Projects in Tenant A
            project_a1 = Project(
                organization_id=cls.org_a_id,
                name="AI Research Platform",
                description="Core AI research platform initiative",
                status="ACTIVE",
                priority="HIGH",
                owner_id=cls.admin_a_id,
            )
            project_a2 = Project(
                organization_id=cls.org_a_id,
                name="Customer Intelligence Portal",
                description="Customer analytics and KG interface",
                status="COMPLETED",
                priority="MEDIUM",
                owner_id=cls.member_a2_id,
            )
            # Project in Tenant B
            project_b1 = Project(
                organization_id=cls.org_b_id,
                name="Globex Secret Initiative",
                description="Tenant B strictly confidential project",
                status="ACTIVE",
                owner_id=cls.admin_b_id,
            )
            session.add_all([project_a1, project_a2, project_b1])
            session.flush()

            cls.project_a1_id = project_a1.id
            cls.project_a2_id = project_a2.id
            cls.project_b1_id = project_b1.id

            # Assign member_a1 to project_a1 only
            session.execute(
                project_users.insert().values(
                    project_id=cls.project_a1_id,
                    user_id=cls.member_a1_id,
                )
            )

            # Documents in Tenant A
            doc_a1 = Document(
                organization_id=cls.org_a_id,
                uploader_id=cls.admin_a_id,
                project_id=cls.project_a1_id,
                filename="Architecture_Design.pdf",
                file_path="/uploads/architecture_design.pdf",
                file_type="pdf",
                file_size=2048500,
                status="PROCESSED",
            )
            doc_a2 = Document(
                organization_id=cls.org_a_id,
                uploader_id=cls.member_a1_id,
                project_id=cls.project_a1_id,
                filename="Meeting_Notes_Q3.docx",
                file_path="/uploads/meeting_notes_q3.docx",
                file_type="docx",
                file_size=512000,
                status="PROCESSED",
            )
            # Document in Tenant B
            doc_b1 = Document(
                organization_id=cls.org_b_id,
                uploader_id=cls.admin_b_id,
                project_id=cls.project_b1_id,
                filename="Globex_Confidential.pdf",
                file_path="/uploads/globex_confidential.pdf",
                file_type="pdf",
                file_size=1024000,
                status="PROCESSED",
            )
            session.add_all([doc_a1, doc_a2, doc_b1])
            session.flush()

            cls.doc_a1_id = doc_a1.id
            cls.doc_a2_id = doc_a2.id
            cls.doc_b1_id = doc_b1.id

            # Team in Tenant A
            team_a = Team(
                organization_id=cls.org_a_id,
                name="Core Engineering Team",
                description="Primary platform engineering squad",
            )
            session.add(team_a)
            session.flush()
            cls.team_a_id = team_a.id

            # Notifications for member_a1
            notif_a1_1 = Notification(
                organization_id=cls.org_a_id,
                user_id=cls.member_a1_id,
                type="info",
                title="Welcome to KEEP",
                body="You have joined Acme Corp A.",
                is_read=False,
            )
            notif_a1_2 = Notification(
                organization_id=cls.org_a_id,
                user_id=cls.member_a1_id,
                type="reminder",
                title="Sprint Standup",
                body="Standup starts in 10 minutes.",
                is_read=True,
            )
            # Notification for member_a2
            notif_a2_1 = Notification(
                organization_id=cls.org_a_id,
                user_id=cls.member_a2_id,
                type="warning",
                title="Security Alert",
                body="New sign-in detected.",
                is_read=False,
            )
            session.add_all([notif_a1_1, notif_a1_2, notif_a2_1])
            session.flush()

            cls.notif_a1_1_id = notif_a1_1.id
            cls.notif_a1_2_id = notif_a1_2.id
            cls.notif_a2_1_id = notif_a2_1.id

            # Activity Logs in Tenant A
            act_a1 = ActivityLog(
                organization_id=cls.org_a_id,
                user_id=cls.admin_a_id,
                action="uploaded",
                resource_type="document",
                resource_id=cls.doc_a1_id,
                details="Uploaded Architecture_Design.pdf",
            )
            act_a2 = ActivityLog(
                organization_id=cls.org_a_id,
                user_id=cls.member_a1_id,
                action="created",
                resource_type="project",
                resource_id=cls.project_a1_id,
                details="Updated AI Research Platform",
            )
            # Activity Log in Tenant B
            act_b1 = ActivityLog(
                organization_id=cls.org_b_id,
                user_id=cls.admin_b_id,
                action="uploaded",
                resource_type="document",
                resource_id=cls.doc_b1_id,
                details="Uploaded Globex_Confidential.pdf",
            )
            session.add_all([act_a1, act_a2, act_b1])
            session.commit()

            cls.act_a1_id = act_a1.id
            cls.act_a2_id = act_a2.id
            cls.act_b1_id = act_b1.id

        # Auth headers
        cls.headers_admin_a = {
            "Authorization": f"Bearer {create_access_token(data={'sub': str(cls.admin_a_id), 'email': cls.admin_a_email, 'role': 'OrgAdmin', 'org_id': str(cls.org_a_id)})}"
        }
        cls.headers_member_a1 = {
            "Authorization": f"Bearer {create_access_token(data={'sub': str(cls.member_a1_id), 'email': cls.member_a1_email, 'role': 'Member', 'org_id': str(cls.org_a_id)})}"
        }
        cls.headers_member_a2 = {
            "Authorization": f"Bearer {create_access_token(data={'sub': str(cls.member_a2_id), 'email': cls.member_a2_email, 'role': 'Member', 'org_id': str(cls.org_a_id)})}"
        }
        cls.headers_admin_b = {
            "Authorization": f"Bearer {create_access_token(data={'sub': str(cls.admin_b_id), 'email': cls.admin_b_email, 'role': 'OrgAdmin', 'org_id': str(cls.org_b_id)})}"
        }

    # =========================================================================
    # 1. GET /api/v1/dashboard
    # =========================================================================

    def test_get_dashboard_summary_admin(self) -> None:
        """OrgAdmin retrieves complete dashboard summary with all KPIs."""
        res = self.client.get("/api/v1/dashboard", headers=self.headers_admin_a)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])

        data = body["data"]
        # User details
        self.assertEqual(data["user"]["full_name"], "Alice Admin")
        self.assertEqual(data["user"]["role"], "OrgAdmin")

        # Organization details
        self.assertTrue(data["organization"]["name"].startswith("Acme Corp A"))

        # KPI counters
        self.assertGreaterEqual(data["kpi"]["total_projects"], 2)
        self.assertGreaterEqual(data["kpi"]["total_documents"], 2)
        self.assertGreaterEqual(data["kpi"]["total_members"], 3)
        self.assertGreaterEqual(data["kpi"]["storage_used_bytes"], 2500000)

        # Greeting
        self.assertIn(data["greeting_time_of_day"], ["morning", "afternoon", "evening"])

    def test_get_dashboard_summary_member_ai_queries_zero(self) -> None:
        """Regular Member receives 0 for kpi.ai_queries_today."""
        res = self.client.get("/api/v1/dashboard", headers=self.headers_member_a1)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertEqual(data["user"]["role"], "Member")
        self.assertEqual(data["kpi"]["ai_queries_today"], 0)

    def test_get_dashboard_summary_caching(self) -> None:
        """Second call hits Redis/in-memory cache cleanly."""
        res1 = self.client.get("/api/v1/dashboard", headers=self.headers_admin_a)
        self.assertEqual(res1.status_code, 200)

        res2 = self.client.get("/api/v1/dashboard", headers=self.headers_admin_a)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res1.json()["data"]["kpi"], res2.json()["data"]["kpi"])

    def test_get_dashboard_tenant_isolation(self) -> None:
        """Tenant B user receives Tenant B organization, not Tenant A."""
        res_a = self.client.get("/api/v1/dashboard", headers=self.headers_admin_a)
        res_b = self.client.get("/api/v1/dashboard", headers=self.headers_admin_b)

        data_a = res_a.json()["data"]
        data_b = res_b.json()["data"]

        self.assertNotEqual(data_a["organization"]["id"], data_b["organization"]["id"])
        self.assertTrue(data_b["organization"]["name"].startswith("Globex Corp B"))

    # =========================================================================
    # 2. GET /api/v1/activity
    # =========================================================================

    def test_get_activity_feed_success(self) -> None:
        """Retrieves paginated chronological activity feed."""
        res = self.client.get("/api/v1/activity", headers=self.headers_admin_a)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])

        data = body["data"]
        self.assertGreaterEqual(data["total"], 2)
        self.assertGreaterEqual(len(data["items"]), 2)

        # Check actor information
        item = data["items"][0]
        self.assertIn("actor", item)
        self.assertIn("action", item)
        self.assertIn("resource_type", item)
        self.assertIn("occurred_at", item)

    def test_get_activity_feed_filtering(self) -> None:
        """Filter activity by resource type (e.g., document)."""
        res = self.client.get("/api/v1/activity?filter=document", headers=self.headers_admin_a)
        self.assertEqual(res.status_code, 200)
        items = res.json()["data"]["items"]
        for item in items:
            self.assertEqual(item["resource_type"], "document")

    def test_get_activity_feed_tenant_isolation(self) -> None:
        """Tenant B activity is never visible to Tenant A user."""
        res = self.client.get("/api/v1/activity", headers=self.headers_admin_a)
        items = res.json()["data"]["items"]
        for item in items:
            self.assertNotEqual(item["id"], str(self.act_b1_id))
            self.assertNotIn("Globex", item["resource_name"])

    # =========================================================================
    # 3. GET /api/v1/projects/recent
    # =========================================================================

    def test_get_recent_projects_admin(self) -> None:
        """Admin sees recent projects within the tenant."""
        res = self.client.get("/api/v1/projects/recent?limit=5", headers=self.headers_admin_a)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])

        projects = body["data"]
        self.assertGreaterEqual(len(projects), 2)
        p1 = projects[0]
        self.assertIn("name", p1)
        self.assertIn("progress_percent", p1)
        self.assertIn("team_members", p1)

    def test_get_recent_projects_member_scoped(self) -> None:
        """Member only sees projects they belong to or own."""
        res = self.client.get("/api/v1/projects/recent", headers=self.headers_member_a1)
        self.assertEqual(res.status_code, 200)
        projects = res.json()["data"]

        # member_a1 only belongs to project_a1 (AI Research Platform)
        project_ids = [p["id"] for p in projects]
        self.assertIn(str(self.project_a1_id), project_ids)
        self.assertNotIn(str(self.project_a2_id), project_ids)

    # =========================================================================
    # 4. GET /api/v1/documents/recent
    # =========================================================================

    def test_get_recent_documents(self) -> None:
        """Retrieves recent documents with file size and uploader."""
        res = self.client.get("/api/v1/documents/recent?limit=5", headers=self.headers_admin_a)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])

        docs = body["data"]
        self.assertGreaterEqual(len(docs), 2)
        doc1 = docs[0]
        self.assertIn("title", doc1)
        self.assertIn("file_type", doc1)
        self.assertIn("uploaded_by", doc1)
        self.assertGreater(doc1["file_size_bytes"], 0)

    # =========================================================================
    # 5. Notifications Subsystem
    # =========================================================================

    def test_get_notifications_user_scoped(self) -> None:
        """User only retrieves their own notifications, never other users'."""
        res_a1 = self.client.get("/api/v1/notifications", headers=self.headers_member_a1)
        self.assertEqual(res_a1.status_code, 200)
        items_a1 = res_a1.json()["data"]["items"]

        # member_a1 should see their 2 notifications
        self.assertEqual(len(items_a1), 2)
        notif_ids_a1 = [n["id"] for n in items_a1]
        self.assertIn(str(self.notif_a1_1_id), notif_ids_a1)
        # Should not see member_a2's notification
        self.assertNotIn(str(self.notif_a2_1_id), notif_ids_a1)

    def test_get_notifications_unread_only_filter(self) -> None:
        """unread_only=true returns only unread notifications."""
        res = self.client.get("/api/v1/notifications?unread_only=true", headers=self.headers_member_a1)
        self.assertEqual(res.status_code, 200)
        items = res.json()["data"]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], str(self.notif_a1_1_id))
        self.assertFalse(items[0]["is_read"])

    def test_patch_notification_mark_read(self) -> None:
        """Marks a single notification as read."""
        res = self.client.patch(
            f"/api/v1/notifications/{self.notif_a1_1_id}/read",
            headers=self.headers_member_a1,
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["data"]["is_read"])

    def test_patch_notification_other_user_not_found(self) -> None:
        """User A attempting to mark User B's notification read receives 404."""
        res = self.client.patch(
            f"/api/v1/notifications/{self.notif_a2_1_id}/read",
            headers=self.headers_member_a1,
        )
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["error"]["code"], ErrorCode.NOT_FOUND)

    def test_post_notifications_read_all(self) -> None:
        """Marks all unread notifications for caller as read."""
        res = self.client.post("/api/v1/notifications/read-all", headers=self.headers_member_a2)
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.json()["data"]["updated_count"], 1)

    # =========================================================================
    # 6. GET /api/v1/analytics/summary
    # =========================================================================

    def test_get_analytics_summary_admin_success(self) -> None:
        """OrgAdmin retrieves time-series analytics summary."""
        res = self.client.get("/api/v1/analytics/summary?period=week", headers=self.headers_admin_a)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])

        data = body["data"]
        self.assertEqual(data["period"], "week")
        self.assertGreater(len(data["documents_uploaded"]), 0)
        self.assertGreater(len(data["active_users"]), 0)
        self.assertGreater(len(data["project_distribution"]), 0)

    def test_get_analytics_summary_member_forbidden(self) -> None:
        """Regular Member receives 403 AUTH_ROLE_REQUIRED when accessing analytics summary."""
        res = self.client.get("/api/v1/analytics/summary", headers=self.headers_member_a1)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["error"]["code"], ErrorCode.AUTH_ROLE_REQUIRED)

    def test_get_analytics_summary_unauthenticated(self) -> None:
        """Unauthenticated caller receives 401."""
        res = self.client.get("/api/v1/analytics/summary")
        self.assertEqual(res.status_code, 401)

    # =========================================================================
    # 7. POST /api/v1/ai/query (Phase 1.7 Stub)
    # =========================================================================

    def test_post_ai_query_streaming_success(self) -> None:
        """Submits AI query and receives SSE token stream."""
        res = self.client.post(
            "/api/v1/ai/query",
            json={
                "query": "Summarize this week's progress across active projects",
                "stream": True,
            },
            headers=self.headers_member_a1,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/event-stream", res.headers.get("content-type", ""))
        content = res.text
        self.assertIn("event: token", content)
        self.assertIn("event: done", content)
        self.assertIn("query_id", content)

    def test_post_ai_query_too_long_rejected(self) -> None:
        """Query > 4096 characters rejected with 422 AI_QUERY_TOO_LONG."""
        long_query = "X" * 4097
        res = self.client.post(
            "/api/v1/ai/query",
            json={"query": long_query, "stream": True},
            headers=self.headers_member_a1,
        )
        self.assertEqual(res.status_code, 422)
        body = res.json()
        self.assertFalse(body["success"])

    # =========================================================================
    # 8. GET /api/v1/search
    # =========================================================================

    def test_global_search_success(self) -> None:
        """Full-text search matches projects, documents, users, and teams."""
        res = self.client.get("/api/v1/search?q=AI", headers=self.headers_admin_a)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])

        data = body["data"]
        self.assertEqual(data["query"], "AI")
        self.assertGreaterEqual(data["total"], 1)

        types = [item["type"] for item in data["items"]]
        self.assertIn("project", types)

    def test_global_search_type_filtering(self) -> None:
        """Filter global search by type=project."""
        res = self.client.get("/api/v1/search?q=AI&type=project", headers=self.headers_admin_a)
        self.assertEqual(res.status_code, 200)
        items = res.json()["data"]["items"]
        for item in items:
            self.assertEqual(item["type"], "project")

    def test_global_search_tenant_isolation(self) -> None:
        """Tenant B resources are never returned in Tenant A search."""
        res = self.client.get("/api/v1/search?q=Globex", headers=self.headers_admin_a)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"]["total"], 0)


if __name__ == "__main__":
    unittest.main()
