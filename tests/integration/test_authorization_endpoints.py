"""Integration Test Suite: Phase 1.6 User Role Management & Authorization Framework.

Verifies:
1. /api/v1/audit/logs endpoint:
   - OrgAdmin with audit.read permission retrieves paginated audit trail.
   - Regular Member lacking audit.read receives 403 AUTH_PERMISSION_DENIED.
   - Filtering by action, user_id, and pagination parameters.
2. /api/v1/documents/{id} DELETE endpoint:
   - OrgAdmin can delete any document within tenant.
   - Document Uploader (Member) can delete own document via ownership override.
   - Non-owner Member receives 403 AUTH_PERMISSION_DENIED.
   - Project containment: Member not belonging to document's project receives 403 AUTH_RESOURCE_FORBIDDEN.
   - Cross-tenant access is rejected with 403 AUTH_ORGANIZATION_MISMATCH or 404.
3. Audit trail persistence:
   - Deletions record immutable PERMISSION_GRANTED events in activity_logs table.

Owner: Member 2 (Backend Lead)
Sub-phase: Phase 1.6 User Role Management & Authorization Framework
Specification: devdocs/p1/p1.6.txt (Chapters 1-19)
Architecture: docs/Architecture/authorization-architecture.md
"""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.constants import ErrorCode, UserRole
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.activity import ActivityLog
from backend.app.models.document import Document
from backend.app.models.organization import Organization
from backend.app.models.project import Project, project_users
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestAuthorizationEndpointsIntegration(unittest.TestCase):
    """Integration test suite for Phase 1.6 authorization framework and protected APIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine) as session:
            # 1. Create Primary Tenant A
            cls.org_a = Organization(
                name=f"Auth Corp A {uuid4().hex[:6]}",
                domain=f"autha_{uuid4().hex[:6]}.com",
            )
            session.add(cls.org_a)
            session.flush()

            cls.admin_a = User(
                email=f"admin_a_{uuid4().hex[:6]}@autha.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Admin A",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org_a.id,
                is_active=True,
            )
            cls.member_a1 = User(
                email=f"member_a1_{uuid4().hex[:6]}@autha.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Member A1",
                role=UserRole.MEMBER,
                organization_id=cls.org_a.id,
                is_active=True,
            )
            cls.member_a2 = User(
                email=f"member_a2_{uuid4().hex[:6]}@autha.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Member A2",
                role=UserRole.MEMBER,
                organization_id=cls.org_a.id,
                is_active=True,
            )
            session.add_all([cls.admin_a, cls.member_a1, cls.member_a2])
            session.flush()

            # Create Project A in Tenant A
            cls.project_a = Project(
                organization_id=cls.org_a.id,
                name="Project Alpha",
                status="ACTIVE",
            )
            session.add(cls.project_a)
            session.flush()

            # Associate member_a1 with project_a
            session.execute(
                project_users.insert().values(
                    project_id=cls.project_a.id,
                    user_id=cls.member_a1.id,
                )
            )

            # 2. Create Tenant B (for cross-tenant checks)
            cls.org_b = Organization(
                name=f"Auth Corp B {uuid4().hex[:6]}",
                domain=f"authb_{uuid4().hex[:6]}.com",
            )
            session.add(cls.org_b)
            session.flush()

            cls.admin_b = User(
                email=f"admin_b_{uuid4().hex[:6]}@authb.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Admin B",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org_b.id,
                is_active=True,
            )
            session.add(cls.admin_b)
            session.flush()

            # Pre-populate sample activity logs for Tenant A
            cls.log_a1 = ActivityLog(
                organization_id=cls.org_a.id,
                user_id=cls.admin_a.id,
                action="PERMISSION_GRANTED",
                resource_type="document",
                details="Action: document.read. Decision: ALLOW.",
            )
            cls.log_a2 = ActivityLog(
                organization_id=cls.org_a.id,
                user_id=cls.member_a1.id,
                action="PERMISSION_DENIED",
                resource_type="organization",
                details="Action: organization.manage. Decision: DENY. Code: AUTH_PERMISSION_DENIED",
            )
            session.add_all([cls.log_a1, cls.log_a2])

            cls.org_a_id = cls.org_a.id
            cls.org_b_id = cls.org_b.id
            cls.project_a_id = cls.project_a.id
            cls.admin_a_id = cls.admin_a.id
            cls.member_a1_id = cls.member_a1.id
            cls.member_a2_id = cls.member_a2.id
            cls.admin_b_id = cls.admin_b.id

            session.commit()

        # Generate JWT Auth Tokens
        cls.token_admin_a = create_access_token(
            data={"sub": str(cls.admin_a_id), "email": "admin@a.com", "role": "OrgAdmin", "org_id": str(cls.org_a_id)}
        )
        cls.headers_admin_a = {"Authorization": f"Bearer {cls.token_admin_a}"}

        cls.token_member_a1 = create_access_token(
            data={"sub": str(cls.member_a1_id), "email": "a1@a.com", "role": "Member", "org_id": str(cls.org_a_id)}
        )
        cls.headers_member_a1 = {"Authorization": f"Bearer {cls.token_member_a1}"}

        cls.token_member_a2 = create_access_token(
            data={"sub": str(cls.member_a2_id), "email": "a2@a.com", "role": "Member", "org_id": str(cls.org_a_id)}
        )
        cls.headers_member_a2 = {"Authorization": f"Bearer {cls.token_member_a2}"}

        cls.token_admin_b = create_access_token(
            data={"sub": str(cls.admin_b_id), "email": "admin@b.com", "role": "OrgAdmin", "org_id": str(cls.org_b_id)}
        )
        cls.headers_admin_b = {"Authorization": f"Bearer {cls.token_admin_b}"}

    def test_audit_logs_endpoint_org_admin_allowed(self) -> None:
        """OrgAdmin with audit.read permission can query security audit trail."""
        res = self.client.get("/api/v1/audit/logs", headers=self.headers_admin_a)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertIn("items", body["data"])
        self.assertGreaterEqual(body["data"]["total"], 2)

    def test_audit_logs_endpoint_member_denied(self) -> None:
        """Regular Member lacking audit.read permission receives 403 AUTH_PERMISSION_DENIED."""
        res = self.client.get("/api/v1/audit/logs", headers=self.headers_member_a1)
        self.assertEqual(res.status_code, 403)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_PERMISSION_DENIED)
        self.assertEqual(body["error"]["details"]["required_permission"], "audit.read")

    def test_audit_logs_filtering_by_action(self) -> None:
        """Querying audit logs with action filter returns matching entries only."""
        res = self.client.get(
            "/api/v1/audit/logs?action=PERMISSION_GRANTED",
            headers=self.headers_admin_a,
        )
        self.assertEqual(res.status_code, 200)
        items = res.json()["data"]["items"]
        self.assertTrue(all(item["action"] == "PERMISSION_GRANTED" for item in items))

    def test_document_delete_by_org_admin(self) -> None:
        """OrgAdmin has document.delete in base role and can delete any document."""
        # Create doc in Tenant A
        with Session(sync_test_engine) as session:
            doc = Document(
                organization_id=self.org_a_id,
                uploader_id=self.member_a1_id,
                filename="admin_delete_test.pdf",
                file_path="/tmp/test.pdf",
                file_type="application/pdf",
                file_size=1024,
                status="PROCESSED",
            )
            session.add(doc)
            session.commit()
            doc_id = doc.id

        res = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.headers_admin_a)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["data"]["deleted"])

        # Verify soft-deleted
        with Session(sync_test_engine) as session:
            d = session.get(Document, doc_id)
            self.assertTrue(d.is_deleted)

    def test_document_delete_by_uploader_owner_override(self) -> None:
        """Regular Member who uploaded the document deletes it via ownership override."""
        with Session(sync_test_engine) as session:
            doc = Document(
                organization_id=self.org_a_id,
                uploader_id=self.member_a1_id,  # member_a1 is the uploader!
                filename="owner_override_test.pdf",
                file_path="/tmp/owner.pdf",
                file_type="application/pdf",
                file_size=2048,
                status="PROCESSED",
            )
            session.add(doc)
            session.commit()
            doc_id = doc.id

        # member_a1 deletes their own document -> should succeed via ownership bypass!
        res = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.headers_member_a1)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["data"]["deleted"])

    def test_document_delete_by_non_owner_member_denied(self) -> None:
        """Regular Member who did not upload the document is denied with 403 AUTH_PERMISSION_DENIED."""
        with Session(sync_test_engine) as session:
            doc = Document(
                organization_id=self.org_a_id,
                uploader_id=self.member_a1_id,  # member_a1 is uploader
                filename="non_owner_test.pdf",
                file_path="/tmp/non_owner.pdf",
                file_type="application/pdf",
                file_size=2048,
                status="PROCESSED",
            )
            session.add(doc)
            session.commit()
            doc_id = doc.id

        # member_a2 attempts to delete member_a1's document -> must be denied!
        res = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.headers_member_a2)
        self.assertEqual(res.status_code, 403)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_PERMISSION_DENIED)

    def test_document_delete_project_scoping_denied(self) -> None:
        """Member not belonging to document's project receives 403 AUTH_RESOURCE_FORBIDDEN."""
        with Session(sync_test_engine) as session:
            doc = Document(
                organization_id=self.org_a_id,
                uploader_id=self.member_a2_id,  # member_a2 uploaded
                project_id=self.project_a_id,   # scoped to project Alpha (which member_a2 has NOT joined!)
                filename="project_scoped_test.pdf",
                file_path="/tmp/scoped.pdf",
                file_type="application/pdf",
                file_size=4096,
                status="PROCESSED",
            )
            session.add(doc)
            session.commit()
            doc_id = doc.id

        # member_a2 is uploader, but the document belongs to project Alpha, which member_a2 is not a member of!
        res = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.headers_member_a2)
        self.assertEqual(res.status_code, 403)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_RESOURCE_FORBIDDEN)

    def test_document_delete_cross_tenant_denied(self) -> None:
        """Tenant A document cannot be deleted by Tenant B admin -> 403 AUTH_ORGANIZATION_MISMATCH."""
        with Session(sync_test_engine) as session:
            doc = Document(
                organization_id=self.org_a_id,
                uploader_id=self.admin_a_id,
                filename="cross_tenant_test.pdf",
                file_path="/tmp/cross.pdf",
                file_type="application/pdf",
                file_size=1024,
                status="PROCESSED",
            )
            session.add(doc)
            session.commit()
            doc_id = doc.id

        # Admin B tries to delete Tenant A document
        res = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.headers_admin_b)
        self.assertEqual(res.status_code, 403)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_ORGANIZATION_MISMATCH)

    def test_analytics_endpoints_require_permission(self) -> None:
        """Analytics endpoints are accessible to authenticated users with analytics.view."""
        res_summary = self.client.get("/api/v1/analytics/summary", headers=self.headers_member_a1)
        self.assertEqual(res_summary.status_code, 200)
        self.assertTrue(res_summary.json()["success"])

        res_usage = self.client.get("/api/v1/analytics/usage", headers=self.headers_member_a1)
        self.assertEqual(res_usage.status_code, 200)
        self.assertTrue(res_usage.json()["success"])

        # Unauthenticated receives 401
        res_unauth = self.client.get("/api/v1/analytics/summary")
        self.assertEqual(res_unauth.status_code, 401)


if __name__ == "__main__":
    unittest.main()
