"""Integration Test Suite: Multi-Tenant Data Isolation & Security for Phase 1.5.

Validates Chapter 18 and Chapter 20 security & isolation guarantees:
1. Cross-Tenant Resource Isolation:
   - Department, Team, Project, Invitation, Member access across tenant boundaries returns 404 Not Found.
2. Tenant Boundary List Scoping:
   - Listing departments, teams, projects, members returns strictly caller tenant data.
3. RBAC Enforcement & Escalation Prevention:
   - Regular members (MEMBER role) cannot create departments, teams, projects, or invite users (403 Forbidden).
   - Privilege escalation attempts on member roles or organization settings are strictly forbidden.
4. Invitation Isolation:
   - Revoking cross-tenant invitations is blocked.
"""

import unittest
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.constants import UserRole
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.department import Department
from backend.app.models.invitation import Invitation
from backend.app.models.organization import Organization
from backend.app.models.project import Project
from backend.app.models.team import Team
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestOrganizationMultiTenantIsolation(unittest.TestCase):
    """Integration test suite enforcing strict multi-tenant isolation and security boundaries."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine) as session:
            # Create Tenant A
            cls.org_a = Organization(
                name=f"Tenant A {uuid4().hex[:6]}",
                domain=f"tenant_a_{uuid4().hex[:6]}.com",
            )
            session.add(cls.org_a)
            session.flush()

            cls.admin_a = User(
                email=f"admin_a_{uuid4().hex[:6]}@tenant-a.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Admin A",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org_a.id,
                is_active=True,
            )
            cls.member_a = User(
                email=f"member_a_{uuid4().hex[:6]}@tenant-a.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Member A",
                role=UserRole.MEMBER,
                organization_id=cls.org_a.id,
                is_active=True,
            )
            session.add_all([cls.admin_a, cls.member_a])
            session.flush()

            cls.dept_a = Department(
                organization_id=cls.org_a.id,
                name="Dept A",
                description="Tenant A Engineering",
            )
            cls.team_a = Team(
                organization_id=cls.org_a.id,
                name="Team A",
                description="Tenant A Backend",
            )
            cls.proj_a = Project(
                organization_id=cls.org_a.id,
                name="Project A",
                status="ACTIVE",
            )
            cls.invite_a = Invitation(
                organization_id=cls.org_a.id,
                email=f"invitee_a_{uuid4().hex[:6]}@tenant-a.com",
                role=UserRole.MEMBER,
                token="token_a_" + uuid4().hex,
                expires_at=datetime.now(UTC) + timedelta(days=7),
                invited_by_id=cls.admin_a.id,
                status="PENDING",
            )
            session.add_all([cls.dept_a, cls.team_a, cls.proj_a, cls.invite_a])
            session.flush()

            # Create Tenant B
            cls.org_b = Organization(
                name=f"Tenant B {uuid4().hex[:6]}",
                domain=f"tenant_b_{uuid4().hex[:6]}.com",
            )
            session.add(cls.org_b)
            session.flush()

            cls.admin_b = User(
                email=f"admin_b_{uuid4().hex[:6]}@tenant-b.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Admin B",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org_b.id,
                is_active=True,
            )
            session.add(cls.admin_b)
            session.flush()

            cls.dept_b = Department(
                organization_id=cls.org_b.id,
                name="Dept B Secret",
                description="Tenant B Secret Engineering",
            )
            cls.team_b = Team(
                organization_id=cls.org_b.id,
                name="Team B Secret",
                description="Tenant B Secret Team",
            )
            cls.proj_b = Project(
                organization_id=cls.org_b.id,
                name="Project B Secret",
                status="ACTIVE",
            )
            cls.invite_b = Invitation(
                organization_id=cls.org_b.id,
                email=f"invitee_b_{uuid4().hex[:6]}@tenant-b.com",
                role=UserRole.MEMBER,
                token="token_b_" + uuid4().hex,
                expires_at=datetime.now(UTC) + timedelta(days=7),
                invited_by_id=cls.admin_b.id,
                status="PENDING",
            )
            session.add_all([cls.dept_b, cls.team_b, cls.proj_b, cls.invite_b])
            session.flush()

            # Store IDs as strings
            cls.org_a_id = str(cls.org_a.id)
            cls.admin_a_id = str(cls.admin_a.id)
            cls.admin_a_email = str(cls.admin_a.email)
            cls.member_a_id = str(cls.member_a.id)
            cls.member_a_email = str(cls.member_a.email)
            cls.dept_a_id = str(cls.dept_a.id)
            cls.team_a_id = str(cls.team_a.id)
            cls.proj_a_id = str(cls.proj_a.id)
            cls.invite_a_id = str(cls.invite_a.id)

            cls.org_b_id = str(cls.org_b.id)
            cls.admin_b_id = str(cls.admin_b.id)
            cls.admin_b_email = str(cls.admin_b.email)
            cls.dept_b_id = str(cls.dept_b.id)
            cls.team_b_id = str(cls.team_b.id)
            cls.proj_b_id = str(cls.proj_b.id)
            cls.invite_b_id = str(cls.invite_b.id)

            session.commit()

        # Generate tokens
        token_a_admin = create_access_token(
            data={
                "sub": cls.admin_a_id,
                "email": cls.admin_a_email,
                "role": UserRole.ORG_ADMIN,
                "org_id": cls.org_a_id,
            }
        )
        token_a_member = create_access_token(
            data={
                "sub": cls.member_a_id,
                "email": cls.member_a_email,
                "role": UserRole.MEMBER,
                "org_id": cls.org_a_id,
            }
        )
        token_b_admin = create_access_token(
            data={
                "sub": cls.admin_b_id,
                "email": cls.admin_b_email,
                "role": UserRole.ORG_ADMIN,
                "org_id": cls.org_b_id,
            }
        )

        cls.headers_a_admin = {"Authorization": f"Bearer {token_a_admin}"}
        cls.headers_a_member = {"Authorization": f"Bearer {token_a_member}"}
        cls.headers_b_admin = {"Authorization": f"Bearer {token_b_admin}"}

    def test_cross_tenant_department_access_blocked(self) -> None:
        """Tenant A admin cannot view, update, or delete Tenant B's departments."""
        # GET Tenant B's department
        res = self.client.get(f"/api/v1/departments/{self.dept_b_id}", headers=self.headers_a_admin)
        self.assertEqual(res.status_code, 404)

        # PATCH Tenant B's department
        res = self.client.patch(
            f"/api/v1/departments/{self.dept_b_id}",
            json={"name": "Hacked Dept"},
            headers=self.headers_a_admin,
        )
        self.assertEqual(res.status_code, 404)

        # DELETE Tenant B's department
        res = self.client.delete(
            f"/api/v1/departments/{self.dept_b_id}", headers=self.headers_a_admin
        )
        self.assertEqual(res.status_code, 404)

    def test_cross_tenant_team_access_blocked(self) -> None:
        """Tenant A admin cannot view, update, or delete Tenant B's teams."""
        res = self.client.get(f"/api/v1/teams/{self.team_b_id}", headers=self.headers_a_admin)
        self.assertEqual(res.status_code, 404)

        res = self.client.patch(
            f"/api/v1/teams/{self.team_b_id}",
            json={"name": "Hacked Team"},
            headers=self.headers_a_admin,
        )
        self.assertEqual(res.status_code, 404)

        res = self.client.delete(f"/api/v1/teams/{self.team_b_id}", headers=self.headers_a_admin)
        self.assertEqual(res.status_code, 404)

    def test_cross_tenant_project_access_blocked(self) -> None:
        """Tenant A admin cannot view, update, or archive Tenant B's projects."""
        res = self.client.get(f"/api/v1/projects/{self.proj_b_id}", headers=self.headers_a_admin)
        self.assertEqual(res.status_code, 404)

        res = self.client.patch(
            f"/api/v1/projects/{self.proj_b_id}",
            json={"name": "Hacked Project"},
            headers=self.headers_a_admin,
        )
        self.assertEqual(res.status_code, 404)

        res = self.client.delete(f"/api/v1/projects/{self.proj_b_id}", headers=self.headers_a_admin)
        self.assertEqual(res.status_code, 404)

    def test_cross_tenant_invitation_revocation_blocked(self) -> None:
        """Tenant A admin cannot revoke Tenant B's invitations."""
        res = self.client.delete(
            f"/api/v1/invitations/{self.invite_b_id}", headers=self.headers_a_admin
        )
        self.assertEqual(res.status_code, 404)

    def test_cross_tenant_member_mutation_blocked(self) -> None:
        """Tenant A admin cannot modify or remove Tenant B's members."""
        res = self.client.patch(
            f"/api/v1/members/{self.admin_b_id}",
            json={"role": UserRole.MEMBER},
            headers=self.headers_a_admin,
        )
        self.assertEqual(res.status_code, 404)

        res = self.client.delete(f"/api/v1/members/{self.admin_b_id}", headers=self.headers_a_admin)
        self.assertEqual(res.status_code, 404)

    def test_cross_tenant_organization_details_blocked(self) -> None:
        """Tenant A admin cannot query or update Tenant B's organization metadata."""
        res = self.client.get(
            f"/api/v1/organizations/{self.org_b_id}", headers=self.headers_a_admin
        )
        self.assertEqual(res.status_code, 403)

        res = self.client.patch(
            f"/api/v1/organizations/{self.org_b_id}",
            json={"name": "Compromised Org"},
            headers=self.headers_a_admin,
        )
        self.assertEqual(res.status_code, 403)

    def test_list_scoping_strict_isolation(self) -> None:
        """Querying lists (departments, teams, projects, invitations, members) returns only Tenant A data."""
        # 1. Departments list
        res = self.client.get("/api/v1/departments", headers=self.headers_a_admin)
        self.assertEqual(res.status_code, 200)
        dept_ids = [d["id"] for d in res.json()["data"]]
        self.assertIn(self.dept_a_id, dept_ids)
        self.assertNotIn(self.dept_b_id, dept_ids)

        # 2. Teams list
        res = self.client.get("/api/v1/teams", headers=self.headers_a_admin)
        self.assertEqual(res.status_code, 200)
        team_ids = [t["id"] for t in res.json()["data"]]
        self.assertIn(self.team_a_id, team_ids)
        self.assertNotIn(self.team_b_id, team_ids)

        # 3. Projects list
        res = self.client.get("/api/v1/projects", headers=self.headers_a_admin)
        self.assertEqual(res.status_code, 200)
        proj_ids = [p["id"] for p in res.json()["data"]]
        self.assertIn(self.proj_a_id, proj_ids)
        self.assertNotIn(self.proj_b_id, proj_ids)

        # 4. Invitations list
        res = self.client.get("/api/v1/invitations", headers=self.headers_a_admin)
        self.assertEqual(res.status_code, 200)
        invite_ids = [inv["id"] for inv in res.json()["data"]]
        self.assertIn(self.invite_a_id, invite_ids)
        self.assertNotIn(self.invite_b_id, invite_ids)

        # 5. Members directory
        res = self.client.get("/api/v1/members", headers=self.headers_a_admin)
        self.assertEqual(res.status_code, 200)
        member_ids = [m["id"] for m in res.json()["data"]["items"]]
        self.assertIn(self.admin_a_id, member_ids)
        self.assertIn(self.member_a_id, member_ids)
        self.assertNotIn(self.admin_b_id, member_ids)

    def test_rbac_privilege_escalation_blocked_for_regular_member(self) -> None:
        """Regular member role is blocked with 403 Forbidden on administrative mutations."""
        # Attempt to create department
        res = self.client.post(
            "/api/v1/departments",
            json={"name": "Unauthorized Dept"},
            headers=self.headers_a_member,
        )
        self.assertEqual(res.status_code, 403)

        # Attempt to create team
        res = self.client.post(
            "/api/v1/teams",
            json={"name": "Unauthorized Team"},
            headers=self.headers_a_member,
        )
        self.assertEqual(res.status_code, 403)

        # Attempt to delete/archive project
        res = self.client.delete(
            f"/api/v1/projects/{self.proj_a_id}",
            headers=self.headers_a_member,
        )
        self.assertEqual(res.status_code, 403)

        # Attempt to dispatch invitation
        res = self.client.post(
            "/api/v1/invitations",
            json={"email": "attacker@tenant-a.com", "role": UserRole.ORG_ADMIN},
            headers=self.headers_a_member,
        )
        self.assertEqual(res.status_code, 403)

        # Attempt to elevate self role
        res = self.client.patch(
            f"/api/v1/members/{self.member_a_id}",
            json={"role": UserRole.ORG_ADMIN},
            headers=self.headers_a_member,
        )
        self.assertEqual(res.status_code, 403)

        # Attempt to update organization settings
        res = self.client.patch(
            f"/api/v1/organizations/{self.org_a_id}",
            json={"name": "Hacked Tenant"},
            headers=self.headers_a_member,
        )
        self.assertEqual(res.status_code, 403)
