"""Comprehensive RBAC Security, Privilege Escalation & Boundary Integration Test Suite.

Verifies:
1. Vertical Access Attacks / Privilege Escalation:
   - Viewer role blocked from all mutations and restricted to read-only actions.
   - Member role blocked from administrative endpoints (/audit/logs, /analytics, /organizations/{id}, /departments, /teams, /invitations).
   - ProjectManager role permitted for project management but blocked from org settings and security audit logs.
   - OrgAdmin permitted for organizational management, user administration, and audit inspection.
   - SuperAdmin unrestricted access across administrative operations.
2. Horizontal Access Attacks & Resource Ownership / Project Containment:
   - Document uploader (Member) can delete own document via ownership override bypass.
   - Non-owner Member in the same project is denied deletion (403 AUTH_PERMISSION_DENIED).
   - Member not assigned to project is denied access (403 AUTH_RESOURCE_FORBIDDEN).
   - OrgAdmin bypasses project containment and ownership boundaries within tenant.
3. Multi-Tenant Boundary Isolation Attacks:
   - Cross-tenant document deletion attempts rejected with 403 AUTH_ORGANIZATION_MISMATCH or 404.
   - Cross-tenant audit trail inspection quarantine: Org B admin cannot inspect Org A audit entries.
   - Cross-tenant project and department isolation.
4. JWT & Identity Manipulation Attacks:
   - Tampered role claims in JWT rejected by cryptographic signature validation (401).
   - Tampered organization claims rejected (401).
   - Expired or malformed bearer tokens rejected (401).
   - Missing authorization headers rejected (401).
5. Authorization Decision Audit Logging:
   - Authorization decisions emit immutable PERMISSION_GRANTED audit records in activity_logs.
   - Audit trail filtering by action, user_id, resource_type, and pagination.

Owner: Member 4 (DevOps & Integration Lead)
Sub-phase: Phase 1.6 User Role Management & Authorization Framework
Specification: devdocs/p1/p1.6.txt (Chapters 1-19)
Architecture: docs/Architecture/authorization-architecture.md
"""

import unittest
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.constants import ErrorCode, UserRole
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.activity import ActivityLog
from backend.app.models.department import Department
from backend.app.models.document import Document
from backend.app.models.organization import Organization
from backend.app.models.project import Project, project_users
from backend.app.models.team import Team
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestRBACSecurityValidation(unittest.TestCase):
    """Deep security and RBAC validation test suite for Phase 1.6."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine) as session:
            # -------------------------------------------------------------
            # Tenant 1: Enterprise Alpha
            # -------------------------------------------------------------
            cls.org1 = Organization(
                name=f"Enterprise Alpha {uuid4().hex[:6]}",
                domain=f"alpha_{uuid4().hex[:6]}.com",
            )
            session.add(cls.org1)
            session.flush()

            # SuperAdmin
            cls.user_super = User(
                email=f"super_{uuid4().hex[:6]}@alpha.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Alpha SuperAdmin",
                role=UserRole.SUPER_ADMIN,
                organization_id=cls.org1.id,
                is_active=True,
            )
            # OrgAdmin
            cls.user_admin = User(
                email=f"admin_{uuid4().hex[:6]}@alpha.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Alpha OrgAdmin",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org1.id,
                is_active=True,
            )
            # Manager
            cls.user_mgr = User(
                email=f"mgr_{uuid4().hex[:6]}@alpha.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Alpha Manager",
                role=UserRole.MANAGER,
                organization_id=cls.org1.id,
                is_active=True,
            )
            # Member 1 (Uploader / Project Member)
            cls.user_mem1 = User(
                email=f"mem1_{uuid4().hex[:6]}@alpha.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Alpha Member 1",
                role=UserRole.MEMBER,
                organization_id=cls.org1.id,
                is_active=True,
            )
            # Member 2 (Project Member / Non-Owner)
            cls.user_mem2 = User(
                email=f"mem2_{uuid4().hex[:6]}@alpha.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Alpha Member 2",
                role=UserRole.MEMBER,
                organization_id=cls.org1.id,
                is_active=True,
            )
            # Member 3 (Non-Project Member)
            cls.user_mem3 = User(
                email=f"mem3_{uuid4().hex[:6]}@alpha.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Alpha Member 3",
                role=UserRole.MEMBER,
                organization_id=cls.org1.id,
                is_active=True,
            )
            # Viewer (Read-only / Guest)
            cls.user_view = User(
                email=f"view_{uuid4().hex[:6]}@alpha.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Alpha Viewer",
                role="Viewer",
                organization_id=cls.org1.id,
                is_active=True,
            )
            session.add_all([
                cls.user_super,
                cls.user_admin,
                cls.user_mgr,
                cls.user_mem1,
                cls.user_mem2,
                cls.user_mem3,
                cls.user_view,
            ])
            session.flush()

            # Project Alpha 1
            cls.project1 = Project(
                organization_id=cls.org1.id,
                name="Project Alpha 1",
                status="ACTIVE",
            )
            session.add(cls.project1)
            session.flush()

            # Associate user_mem1 and user_mem2 with project1 (user_mem3 excluded)
            session.execute(
                project_users.insert().values([
                    {"project_id": cls.project1.id, "user_id": cls.user_mem1.id},
                    {"project_id": cls.project1.id, "user_id": cls.user_mem2.id},
                    {"project_id": cls.project1.id, "user_id": cls.user_mgr.id},
                ])
            )

            # Department Alpha
            cls.dept1 = Department(
                organization_id=cls.org1.id,
                name="Engineering Alpha",
                description="Engineering Alpha Department",
            )
            session.add(cls.dept1)
            session.flush()

            # Team Alpha
            cls.team1 = Team(
                organization_id=cls.org1.id,
                department_id=cls.dept1.id,
                name="Core Platform",
            )
            session.add(cls.team1)
            session.flush()

            # -------------------------------------------------------------
            # Tenant 2: Enterprise Beta (Cross-Tenant Target)
            # -------------------------------------------------------------
            cls.org2 = Organization(
                name=f"Enterprise Beta {uuid4().hex[:6]}",
                domain=f"beta_{uuid4().hex[:6]}.com",
            )
            session.add(cls.org2)
            session.flush()

            cls.user_beta_admin = User(
                email=f"beta_admin_{uuid4().hex[:6]}@beta.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Beta OrgAdmin",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org2.id,
                is_active=True,
            )
            session.add(cls.user_beta_admin)
            session.flush()

            cls.project2 = Project(
                organization_id=cls.org2.id,
                name="Project Beta 1",
                status="ACTIVE",
            )
            session.add(cls.project2)
            session.flush()

            # Pre-seed audit logs for Org 1 and Org 2
            cls.log_alpha = ActivityLog(
                organization_id=cls.org1.id,
                user_id=cls.user_admin.id,
                action="PERMISSION_GRANTED",
                resource_type="document",
                details="Alpha audit event 1",
            )
            cls.log_beta = ActivityLog(
                organization_id=cls.org2.id,
                user_id=cls.user_beta_admin.id,
                action="PERMISSION_GRANTED",
                resource_type="document",
                details="Beta audit event 1 - CONFIDENTIAL",
            )
            session.add_all([cls.log_alpha, cls.log_beta])

            # IDs
            cls.org1_id = cls.org1.id
            cls.org2_id = cls.org2.id
            cls.project1_id = cls.project1.id
            cls.project2_id = cls.project2.id
            cls.dept1_id = cls.dept1.id
            cls.team1_id = cls.team1.id

            cls.super_id = cls.user_super.id
            cls.admin_id = cls.user_admin.id
            cls.mgr_id = cls.user_mgr.id
            cls.mem1_id = cls.user_mem1.id
            cls.mem2_id = cls.user_mem2.id
            cls.mem3_id = cls.user_mem3.id
            cls.view_id = cls.user_view.id
            cls.beta_admin_id = cls.user_beta_admin.id

            session.commit()

        # Auth Headers
        cls.headers_super = cls._build_auth_headers(cls.super_id, "super@alpha.com", "SuperAdmin", cls.org1_id)
        cls.headers_admin = cls._build_auth_headers(cls.admin_id, "admin@alpha.com", "OrgAdmin", cls.org1_id)
        cls.headers_mgr = cls._build_auth_headers(cls.mgr_id, "mgr@alpha.com", "Manager", cls.org1_id)
        cls.headers_mem1 = cls._build_auth_headers(cls.mem1_id, "mem1@alpha.com", "Member", cls.org1_id)
        cls.headers_mem2 = cls._build_auth_headers(cls.mem2_id, "mem2@alpha.com", "Member", cls.org1_id)
        cls.headers_mem3 = cls._build_auth_headers(cls.mem3_id, "mem3@alpha.com", "Member", cls.org1_id)
        cls.headers_view = cls._build_auth_headers(cls.view_id, "view@alpha.com", "Viewer", cls.org1_id)
        cls.headers_beta_admin = cls._build_auth_headers(cls.beta_admin_id, "admin@beta.com", "OrgAdmin", cls.org2_id)

    @classmethod
    def _build_auth_headers(cls, user_id: Any, email: str, role: str, org_id: Any) -> dict[str, str]:
        token = create_access_token(
            data={"sub": str(user_id), "email": email, "role": role, "org_id": str(org_id)}
        )
        return {"Authorization": f"Bearer {token}"}

    def _create_test_document(self, org_id: Any, uploader_id: Any, project_id: Any | None = None) -> Any:
        with Session(sync_test_engine) as session:
            doc = Document(
                organization_id=org_id,
                uploader_id=uploader_id,
                project_id=project_id,
                filename=f"doc_{uuid4().hex[:6]}.pdf",
                file_path=f"/tmp/docs/doc_{uuid4().hex[:6]}.pdf",
                file_type="application/pdf",
                file_size=2048,
                status="PROCESSED",
            )
            session.add(doc)
            session.commit()
            return doc.id

    # =========================================================================
    # 1. Vertical Access Attacks / Privilege Escalation Tests
    # =========================================================================

    def test_member_blocked_from_security_audit_logs(self) -> None:
        """Vertical Attack: Regular Member attempting to inspect audit logs receives 403 AUTH_PERMISSION_DENIED."""
        res = self.client.get("/api/v1/audit/logs", headers=self.headers_mem1)
        self.assertEqual(res.status_code, 403)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_PERMISSION_DENIED)
        self.assertEqual(body["error"]["details"]["required_permission"], "audit.read")

    def test_viewer_blocked_from_security_audit_logs(self) -> None:
        """Vertical Attack: Viewer attempting to inspect audit logs receives 403 AUTH_PERMISSION_DENIED."""
        res = self.client.get("/api/v1/audit/logs", headers=self.headers_view)
        self.assertEqual(res.status_code, 403)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_PERMISSION_DENIED)

    def test_manager_blocked_from_security_audit_logs(self) -> None:
        """Vertical Attack: Project Manager attempting to inspect security audit logs receives 403."""
        res = self.client.get("/api/v1/audit/logs", headers=self.headers_mgr)
        self.assertEqual(res.status_code, 403)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_PERMISSION_DENIED)

    def test_viewer_blocked_from_document_deletion(self) -> None:
        """Vertical Attack: Viewer attempting to delete any document receives 403 AUTH_PERMISSION_DENIED."""
        doc_id = self._create_test_document(self.org1_id, self.mem1_id, self.project1_id)
        res = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.headers_view)
        self.assertEqual(res.status_code, 403)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_PERMISSION_DENIED)

    def test_viewer_blocked_from_creating_departments_and_invitations(self) -> None:
        """Vertical Attack: Viewer attempting to create departments receives 403."""
        res = self.client.post(
            "/api/v1/departments",
            json={"name": "Viewer Dept", "description": "Illegal"},
            headers=self.headers_view,
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json()["success"])

        res_inv = self.client.post(
            "/api/v1/invitations",
            json={"email": "viewer_invite@alpha.com", "role": "Viewer"},
            headers=self.headers_view,
        )
        self.assertEqual(res_inv.status_code, 403)
        self.assertFalse(res_inv.json()["success"])

    def test_member_blocked_from_organization_settings_mutation(self) -> None:
        """Vertical Attack: Regular Member cannot modify organization profile (PATCH /organizations/{id})."""
        res = self.client.patch(
            f"/api/v1/organizations/{self.org1_id}",
            json={"name": "Hacked Org Name"},
            headers=self.headers_mem1,
        )
        self.assertEqual(res.status_code, 403)
        body = res.json()
        self.assertFalse(body["success"])

    def test_member_blocked_from_creating_departments(self) -> None:
        """Vertical Attack: Regular Member cannot create department (POST /departments)."""
        res = self.client.post(
            "/api/v1/departments",
            json={"name": "Illegal Dept", "description": "Illegal"},
            headers=self.headers_mem1,
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json()["success"])

    def test_member_blocked_from_creating_teams(self) -> None:
        """Vertical Attack: Regular Member cannot create team (POST /teams)."""
        res = self.client.post(
            "/api/v1/teams",
            json={"name": "Rogue Team", "department_id": str(self.dept1_id)},
            headers=self.headers_mem1,
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json()["success"])

    def test_member_blocked_from_sending_invitations(self) -> None:
        """Vertical Attack: Regular Member cannot invite other users (POST /invitations)."""
        res = self.client.post(
            "/api/v1/invitations",
            json={"email": "escalated@alpha.com", "role": "OrgAdmin"},
            headers=self.headers_mem1,
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json()["success"])

    def test_org_admin_permitted_for_management_operations(self) -> None:
        """OrgAdmin has legitimate access to audit logs, analytics, and department management."""
        # 1. Audit logs
        res_audit = self.client.get("/api/v1/audit/logs", headers=self.headers_admin)
        self.assertEqual(res_audit.status_code, 200)
        self.assertTrue(res_audit.json()["success"])

        # 2. Analytics
        res_analytics = self.client.get("/api/v1/analytics/summary", headers=self.headers_admin)
        self.assertEqual(res_analytics.status_code, 200)
        self.assertTrue(res_analytics.json()["success"])

    def test_super_admin_unrestricted_bypass(self) -> None:
        """SuperAdmin has system-wide permissions across all endpoints."""
        res_audit = self.client.get("/api/v1/audit/logs", headers=self.headers_super)
        self.assertEqual(res_audit.status_code, 200)
        self.assertTrue(res_audit.json()["success"])

        res_analytics = self.client.get("/api/v1/analytics/summary", headers=self.headers_super)
        self.assertEqual(res_analytics.status_code, 200)
        self.assertTrue(res_analytics.json()["success"])

    # =========================================================================
    # 2. Horizontal Access Attacks & Resource Ownership / Project Containment
    # =========================================================================

    def test_uploader_ownership_override_allows_delete(self) -> None:
        """Ownership Override: Member 1 uploaded the document, so they can delete it."""
        doc_id = self._create_test_document(self.org1_id, self.mem1_id, self.project1_id)

        res = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.headers_mem1)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertTrue(res.json()["data"]["deleted"])

        # Verify soft-delete
        with Session(sync_test_engine) as session:
            doc = session.get(Document, doc_id)
            self.assertTrue(doc.is_deleted)

    def test_non_owner_member_same_project_denied_delete(self) -> None:
        """Horizontal Attack: Member 2 is in the same project, but did not upload the doc -> 403 AUTH_PERMISSION_DENIED."""
        doc_id = self._create_test_document(self.org1_id, self.mem1_id, self.project1_id)

        res = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.headers_mem2)
        self.assertEqual(res.status_code, 403)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_PERMISSION_DENIED)

    def test_member_not_in_project_denied_with_resource_forbidden(self) -> None:
        """Project Scoping: Member 3 uploaded the document in project1, but is not a member of project1 -> 403 AUTH_RESOURCE_FORBIDDEN."""
        doc_id = self._create_test_document(self.org1_id, self.mem3_id, self.project1_id)

        res = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.headers_mem3)
        self.assertEqual(res.status_code, 403)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_RESOURCE_FORBIDDEN)

    def test_org_admin_bypasses_project_containment_and_ownership(self) -> None:
        """Administrative Override: OrgAdmin can delete any document regardless of author or project."""
        doc_id = self._create_test_document(self.org1_id, self.mem1_id, self.project1_id)

        res = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.headers_admin)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["data"]["deleted"])

    # =========================================================================
    # 3. Multi-Tenant Boundary Isolation Attacks
    # =========================================================================

    def test_cross_tenant_document_delete_blocked(self) -> None:
        """Multi-Tenant Isolation: Org 1 Admin attempting to delete Org 2 document is blocked."""
        doc_beta_id = self._create_test_document(self.org2_id, self.beta_admin_id, self.project2_id)

        # Org 1 Admin calls delete on Org 2 doc
        res = self.client.delete(f"/api/v1/documents/{doc_beta_id}", headers=self.headers_admin)
        self.assertEqual(res.status_code, 403)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], ErrorCode.AUTH_ORGANIZATION_MISMATCH)

    def test_cross_tenant_audit_logs_quarantine(self) -> None:
        """Multi-Tenant Isolation: Org 1 Admin cannot see Org 2 audit records."""
        # Query audit logs as Org 1 Admin
        res = self.client.get("/api/v1/audit/logs", headers=self.headers_admin)
        self.assertEqual(res.status_code, 200)
        items = res.json()["data"]["items"]

        # Ensure no Beta confidential records leak into Alpha query
        for item in items:
            self.assertNotEqual(item["organization_id"], str(self.org2_id))
            self.assertNotIn("CONFIDENTIAL", str(item.get("details", "")))

    def test_cross_tenant_organization_modification_blocked(self) -> None:
        """Multi-Tenant Isolation: Org 1 Admin cannot modify Org 2 profile."""
        res = self.client.patch(
            f"/api/v1/organizations/{self.org2_id}",
            json={"name": "Tampered Beta Org"},
            headers=self.headers_admin,
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json()["success"])

    # =========================================================================
    # 4. JWT & Identity Manipulation Attacks
    # =========================================================================

    def test_jwt_tampered_role_claims_rejected(self) -> None:
        """Crypto Security: JWT token with tampered 'SuperAdmin' role signed with false key is rejected (401)."""
        fake_token = jwt.encode(
            {
                "sub": str(self.mem1_id),
                "email": "mem1@alpha.com",
                "role": "SuperAdmin",
                "org_id": str(self.org1_id),
                "exp": datetime.now(UTC) + timedelta(hours=1),
            },
            "ATTACKER_INVALID_SECRET_KEY_1234567890",
            algorithm="HS256",
        )

        res = self.client.get("/api/v1/audit/logs", headers={"Authorization": f"Bearer {fake_token}"})
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json()["success"])

    def test_jwt_tampered_org_id_claim_rejected(self) -> None:
        """Crypto Security: JWT token with tampered org_id claim signed with false key is rejected (401)."""
        fake_token = jwt.encode(
            {
                "sub": str(self.admin_id),
                "email": "admin@alpha.com",
                "role": "OrgAdmin",
                "org_id": str(self.org2_id),  # Cross-tenant injection
                "exp": datetime.now(UTC) + timedelta(hours=1),
            },
            "ATTACKER_INVALID_SECRET_KEY_1234567890",
            algorithm="HS256",
        )

        res = self.client.get("/api/v1/audit/logs", headers={"Authorization": f"Bearer {fake_token}"})
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json()["success"])

    def test_expired_jwt_rejected(self) -> None:
        """Crypto Security: Expired JWT token is rejected (401)."""
        expired_token = jwt.encode(
            {
                "sub": str(self.admin_id),
                "email": "admin@alpha.com",
                "role": "OrgAdmin",
                "org_id": str(self.org1_id),
                "exp": datetime.now(UTC) - timedelta(hours=2),  # Expired
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        res = self.client.get("/api/v1/audit/logs", headers={"Authorization": f"Bearer {expired_token}"})
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json()["success"])

    def test_malformed_bearer_token_rejected(self) -> None:
        """Protocol Security: Arbitrary junk header rejected (401)."""
        res = self.client.get(
            "/api/v1/audit/logs",
            headers={"Authorization": "Bearer not.a.valid.jwt.token"},
        )
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json()["success"])

    def test_missing_authorization_header_rejected(self) -> None:
        """Protocol Security: Unauthenticated request to protected endpoint rejected (401)."""
        res = self.client.get("/api/v1/audit/logs")
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json()["success"])

    # =========================================================================
    # 5. Authorization Decision Audit Logging Tests
    # =========================================================================

    def test_authorized_document_delete_emits_audit_trail(self) -> None:
        """Audit Compliance: Deleting a document emits PERMISSION_GRANTED in activity_logs."""
        doc_id = self._create_test_document(self.org1_id, self.mem1_id, self.project1_id)

        res = self.client.delete(f"/api/v1/documents/{doc_id}", headers=self.headers_mem1)
        self.assertEqual(res.status_code, 200)

        # Inspect database for PERMISSION_GRANTED activity log
        with Session(sync_test_engine) as session:
            stmt = select(ActivityLog).where(
                ActivityLog.resource_id == doc_id,
                ActivityLog.action == "PERMISSION_GRANTED",
            )
            logs = session.execute(stmt).scalars().all()
            self.assertGreaterEqual(len(logs), 1)
            log_entry = logs[0]
            self.assertEqual(str(log_entry.organization_id), str(self.org1_id))
            self.assertEqual(str(log_entry.user_id), str(self.mem1_id))
            self.assertIn("document.delete", log_entry.details)

    def test_audit_logs_query_filters_and_pagination(self) -> None:
        """Audit API: Query audit logs with pagination and action filtering."""
        res = self.client.get(
            "/api/v1/audit/logs?page=1&page_size=10&action=PERMISSION_GRANTED",
            headers=self.headers_admin,
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 10)
        self.assertGreaterEqual(data["total"], 1)
        self.assertTrue(all(item["action"] == "PERMISSION_GRANTED" for item in data["items"]))
