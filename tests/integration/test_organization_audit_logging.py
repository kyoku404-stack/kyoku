"""Integration Test Suite: Phase 1.5 Organization & Workspace Audit Logging.

Verifies that administrative organizational lifecycle actions emit immutable
records into activity_logs adhering to Chapter 17 of devdocs/p1/p1.5.txt:
- Organization create, update, delete
- Department create, update, delete
- Team create, update, delete
- Project create, update, archive
- Invitation send, revoke, accept
- Member role update and removal
"""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.constants import UserRole
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.activity import ActivityLog
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestOrganizationAuditLogging(unittest.TestCase):
    """Integration test suite verifying activity audit logs for Phase 1.5 mutations."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine) as session:
            cls.org = Organization(
                name=f"Audit Org {uuid4().hex[:6]}",
                domain=f"audit_{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.flush()

            cls.admin = User(
                email=f"admin_{uuid4().hex[:6]}@audit.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Audit Admin",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org.id,
                is_active=True,
            )
            cls.member = User(
                email=f"member_{uuid4().hex[:6]}@audit.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Audit Member",
                role=UserRole.MEMBER,
                organization_id=cls.org.id,
                is_active=True,
            )
            session.add_all([cls.admin, cls.member])
            session.flush()

            cls.org_uuid = cls.org.id
            cls.org_id = str(cls.org.id)
            cls.admin_id = str(cls.admin.id)
            cls.admin_email = str(cls.admin.email)
            cls.member_id = str(cls.member.id)
            cls.member_email = str(cls.member.email)

            session.commit()

        cls.admin_token = create_access_token(
            data={
                "sub": cls.admin_id,
                "email": cls.admin_email,
                "role": UserRole.ORG_ADMIN,
                "org_id": cls.org_id,
            }
        )
        cls.auth_headers = {"Authorization": f"Bearer {cls.admin_token}"}

    def _query_latest_activity(self, action: str) -> ActivityLog | None:
        """Helper to fetch the latest activity log for a specific action in this organization."""
        with Session(sync_test_engine) as session:
            stmt = (
                select(ActivityLog)
                .where(
                    ActivityLog.action == action,
                    ActivityLog.organization_id == self.org_uuid,
                )
                .order_by(ActivityLog.created_at.desc())
            )
            return session.execute(stmt).scalars().first()

    def test_department_lifecycle_audit_logging(self) -> None:
        """Verify department creation, update, and deletion emit activity logs."""
        # 1. Create Department
        dept_name = f"Dept Audit {uuid4().hex[:4]}"
        res = self.client.post(
            "/api/v1/departments",
            json={"name": dept_name, "description": "Audit logging test"},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 201)
        dept_id = res.json()["data"]["id"]

        log = self._query_latest_activity("DEPARTMENT_CREATED")
        self.assertIsNotNone(log)
        self.assertEqual(str(log.resource_id), dept_id)
        self.assertEqual(log.resource_type, "department")
        self.assertIn(dept_name, log.details)

        # 2. Update Department
        updated_desc = "Updated description for audit"
        up_res = self.client.patch(
            f"/api/v1/departments/{dept_id}",
            json={"description": updated_desc},
            headers=self.auth_headers,
        )
        self.assertEqual(up_res.status_code, 200)

        up_log = self._query_latest_activity("DEPARTMENT_UPDATED")
        self.assertIsNotNone(up_log)
        self.assertEqual(str(up_log.resource_id), dept_id)
        self.assertEqual(up_log.resource_type, "department")

        # 3. Delete Department
        del_res = self.client.delete(
            f"/api/v1/departments/{dept_id}",
            headers=self.auth_headers,
        )
        self.assertEqual(del_res.status_code, 200)

        del_log = self._query_latest_activity("DEPARTMENT_DELETED")
        self.assertIsNotNone(del_log)
        self.assertEqual(str(del_log.resource_id), dept_id)
        self.assertEqual(del_log.resource_type, "department")

    def test_team_lifecycle_audit_logging(self) -> None:
        """Verify team creation, update, and deletion emit activity logs."""
        # 1. Create Team
        team_name = f"Team Audit {uuid4().hex[:4]}"
        res = self.client.post(
            "/api/v1/teams",
            json={"name": team_name, "description": "Team audit test"},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 201)
        team_id = res.json()["data"]["id"]

        log = self._query_latest_activity("TEAM_CREATED")
        self.assertIsNotNone(log)
        self.assertEqual(str(log.resource_id), team_id)
        self.assertEqual(log.resource_type, "team")
        self.assertIn(team_name, log.details)

        # 2. Update Team
        up_res = self.client.patch(
            f"/api/v1/teams/{team_id}",
            json={"description": "Updated team description"},
            headers=self.auth_headers,
        )
        self.assertEqual(up_res.status_code, 200)

        up_log = self._query_latest_activity("TEAM_UPDATED")
        self.assertIsNotNone(up_log)
        self.assertEqual(str(up_log.resource_id), team_id)
        self.assertEqual(up_log.resource_type, "team")

        # 3. Delete Team
        del_res = self.client.delete(
            f"/api/v1/teams/{team_id}",
            headers=self.auth_headers,
        )
        self.assertEqual(del_res.status_code, 200)

        del_log = self._query_latest_activity("TEAM_DELETED")
        self.assertIsNotNone(del_log)
        self.assertEqual(str(del_log.resource_id), team_id)
        self.assertEqual(del_log.resource_type, "team")

    def test_project_lifecycle_audit_logging(self) -> None:
        """Verify project workspace creation, update, and archiving emit activity logs."""
        # 1. Create Project
        proj_name = f"Project Audit {uuid4().hex[:4]}"
        res = self.client.post(
            "/api/v1/projects",
            json={"name": proj_name, "description": "Project workspace audit test", "status": "ACTIVE"},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 201)
        proj_id = res.json()["data"]["id"]

        log = self._query_latest_activity("PROJECT_CREATED")
        self.assertIsNotNone(log)
        self.assertEqual(str(log.resource_id), proj_id)
        self.assertEqual(log.resource_type, "project")

        # 2. Update Project
        up_res = self.client.patch(
            f"/api/v1/projects/{proj_id}",
            json={"priority": "HIGH"},
            headers=self.auth_headers,
        )
        self.assertEqual(up_res.status_code, 200)

        up_log = self._query_latest_activity("PROJECT_UPDATED")
        self.assertIsNotNone(up_log)
        self.assertEqual(str(up_log.resource_id), proj_id)
        self.assertEqual(up_log.resource_type, "project")

        # 3. Archive Project
        del_res = self.client.delete(
            f"/api/v1/projects/{proj_id}",
            headers=self.auth_headers,
        )
        self.assertEqual(del_res.status_code, 200)

        del_log = self._query_latest_activity("PROJECT_ARCHIVED")
        self.assertIsNotNone(del_log)
        self.assertEqual(str(del_log.resource_id), proj_id)
        self.assertEqual(del_log.resource_type, "project")

    def test_invitation_lifecycle_audit_logging(self) -> None:
        """Verify member invitation dispatch and revocation emit activity logs."""
        # 1. Dispatch Invitation
        invitee_email = f"invited_{uuid4().hex[:6]}@audit.com"
        res = self.client.post(
            "/api/v1/invitations",
            json={"email": invitee_email, "role": UserRole.MEMBER},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 201)
        invitation_id = res.json()["data"]["id"]

        log = self._query_latest_activity("INVITATION_SENT")
        self.assertIsNotNone(log)
        self.assertEqual(str(log.resource_id), invitation_id)
        self.assertEqual(log.resource_type, "invitation")
        self.assertIn(invitee_email, log.details)

        # 2. Revoke Invitation
        del_res = self.client.delete(
            f"/api/v1/invitations/{invitation_id}",
            headers=self.auth_headers,
        )
        self.assertEqual(del_res.status_code, 200)

        del_log = self._query_latest_activity("INVITATION_REVOKED")
        self.assertIsNotNone(del_log)
        self.assertEqual(str(del_log.resource_id), invitation_id)
        self.assertEqual(del_log.resource_type, "invitation")

    def test_member_management_audit_logging(self) -> None:
        """Verify updating member role and removing member emit activity logs."""
        # Create a disposable member for role update and removal
        with Session(sync_test_engine) as session:
            disp_user = User(
                email=f"disp_{uuid4().hex[:6]}@audit.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Disposable Member",
                role=UserRole.MEMBER,
                organization_id=self.org_uuid,
                is_active=True,
            )
            session.add(disp_user)
            session.commit()
            disp_user_id = str(disp_user.id)
            disp_email = str(disp_user.email)

        # 1. Update Member Role
        up_res = self.client.patch(
            f"/api/v1/members/{disp_user_id}",
            json={"role": UserRole.MANAGER},
            headers=self.auth_headers,
        )
        self.assertEqual(up_res.status_code, 200)

        role_log = self._query_latest_activity("MEMBER_UPDATED")
        self.assertIsNotNone(role_log)
        self.assertEqual(str(role_log.resource_id), disp_user_id)
        self.assertEqual(role_log.resource_type, "user")
        self.assertIn(disp_email, role_log.details)

        # 2. Remove Member
        del_res = self.client.delete(
            f"/api/v1/members/{disp_user_id}",
            headers=self.auth_headers,
        )
        self.assertEqual(del_res.status_code, 200)

        rem_log = self._query_latest_activity("MEMBER_REMOVED")
        self.assertIsNotNone(rem_log)
        self.assertEqual(str(rem_log.resource_id), disp_user_id)
        self.assertEqual(rem_log.resource_type, "user")
