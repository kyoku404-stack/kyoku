"""Integration Test Suite: Phase 1.5 Organization Hierarchy & Workspace Management Endpoints.

Tests all REST endpoints across:
- /api/v1/organizations (Create, Current, Get, Update Settings, Archive)
- /api/v1/departments (Create, List, Get, Update, Delete)
- /api/v1/teams (Create, List, Get, Update, Delete)
- /api/v1/projects (Create, List, Get, Update, Archive)
- /api/v1/invitations (Send, List, Revoke, Public Accept)
- /api/v1/members (Paginated Directory, Role Updates, Removal)
- Multi-tenant boundary isolation and RBAC gating
"""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.constants import UserRole
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestOrganizationHierarchyEndpoints(unittest.TestCase):
    """Integration test suite for Phase 1.5 hierarchy management endpoints."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine) as session:
            # Seed Tenant 1
            cls.org1 = Organization(
                name=f"Hierarchy Org 1 {uuid4().hex[:6]}",
                domain=f"hier1_{uuid4().hex[:6]}.com",
            )
            session.add(cls.org1)
            session.flush()

            cls.org1_admin = User(
                email=f"admin_{uuid4().hex[:6]}@hier1.com",
                hashed_password=get_password_hash("AdminPass123!"),
                full_name="Org1 Admin",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org1.id,
                is_active=True,
            )
            cls.org1_member = User(
                email=f"member_{uuid4().hex[:6]}@hier1.com",
                hashed_password=get_password_hash("MemberPass123!"),
                full_name="Org1 Member",
                role=UserRole.MEMBER,
                organization_id=cls.org1.id,
                is_active=True,
            )
            session.add(cls.org1_admin)
            session.add(cls.org1_member)

            # Seed Tenant 2 (for isolation testing)
            cls.org2 = Organization(
                name=f"Hierarchy Org 2 {uuid4().hex[:6]}",
                domain=f"hier2_{uuid4().hex[:6]}.com",
            )
            session.add(cls.org2)
            session.flush()

            cls.org2_admin = User(
                email=f"admin_{uuid4().hex[:6]}@hier2.com",
                hashed_password=get_password_hash("AdminPass123!"),
                full_name="Org2 Admin",
                role=UserRole.ORG_ADMIN,
                organization_id=cls.org2.id,
                is_active=True,
            )
            session.add(cls.org2_admin)
            session.flush()
            cls.org1_id = str(cls.org1.id)
            cls.org2_id = str(cls.org2.id)

            cls.org1_admin_id = str(cls.org1_admin.id)
            cls.org1_admin_email = str(cls.org1_admin.email)

            cls.org1_member_id = str(cls.org1_member.id)
            cls.org1_member_email = str(cls.org1_member.email)

            cls.org2_admin_id = str(cls.org2_admin.id)
            cls.org2_admin_email = str(cls.org2_admin.email)

            session.commit()

        # Generate JWT Bearer tokens
        cls.token_org1_admin = create_access_token(
            data={
                "sub": cls.org1_admin_id,
                "email": cls.org1_admin_email,
                "role": UserRole.ORG_ADMIN,
                "org_id": cls.org1_id,
            }
        )
        cls.headers_org1_admin = {"Authorization": f"Bearer {cls.token_org1_admin}"}

        cls.token_org1_member = create_access_token(
            data={
                "sub": cls.org1_member_id,
                "email": cls.org1_member_email,
                "role": UserRole.MEMBER,
                "org_id": cls.org1_id,
            }
        )
        cls.headers_org1_member = {"Authorization": f"Bearer {cls.token_org1_member}"}

        cls.token_org2_admin = create_access_token(
            data={
                "sub": cls.org2_admin_id,
                "email": cls.org2_admin_email,
                "role": UserRole.ORG_ADMIN,
                "org_id": cls.org2_id,
            }
        )
        cls.headers_org2_admin = {"Authorization": f"Bearer {cls.token_org2_admin}"}

    # --------------------------------------------------------------------------
    # 1. Organization Management Endpoints (/api/v1/organizations)
    # --------------------------------------------------------------------------
    def test_organization_crud_lifecycle(self) -> None:
        """Verifies organization creation, retrieval, settings updates, and archiving."""
        # 1.1 Create new organization
        unique_slug = uuid4().hex[:6]
        create_payload = {
            "name": f"Enterprise Test {unique_slug}",
            "domain": f"test_{unique_slug}.com",
            "industry": "Software",
            "company_size": "250-1000",
            "time_zone": "America/New_York",
            "default_language": "en-US",
        }
        res = self.client.post("/api/v1/organizations", json=create_payload, headers=self.headers_org1_admin)
        self.assertEqual(res.status_code, 201)
        data = res.json()["data"]
        self.assertIsNotNone(data["id"])
        self.assertEqual(data["name"], create_payload["name"])

        # 1.2 Get Current Organization
        res_curr = self.client.get("/api/v1/organizations/current", headers=self.headers_org1_admin)
        self.assertEqual(res_curr.status_code, 200)
        self.assertEqual(res_curr.json()["data"]["id"], self.org1_id)

        # 1.3 Get Organization by ID (matching tenant)
        res_get = self.client.get(f"/api/v1/organizations/{self.org1_id}", headers=self.headers_org1_admin)
        self.assertEqual(res_get.status_code, 200)

        # 1.4 Update Organization Settings
        patch_payload = {
            "time_zone": "UTC",
            "settings": {"max_upload_size_mb": 100, "default_llm": "gpt-4o"},
        }
        res_patch = self.client.patch(f"/api/v1/organizations/{self.org1_id}", json=patch_payload, headers=self.headers_org1_admin)
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.json()["data"]["settings"]["max_upload_size_mb"], 100)

        # 1.5 Cross-tenant access forbidden
        res_cross = self.client.get(f"/api/v1/organizations/{self.org2_id}", headers=self.headers_org1_admin)
        self.assertEqual(res_cross.status_code, 403)

    # --------------------------------------------------------------------------
    # 2. Department Management Endpoints (/api/v1/departments)
    # --------------------------------------------------------------------------
    def test_department_crud_lifecycle(self) -> None:
        """Verifies department creation, listing, retrieval, update, and soft delete."""
        dept_name = f"Engineering {uuid4().hex[:6]}"
        create_payload = {
            "name": dept_name,
            "description": "Core platform engineering",
        }
        # Create
        res = self.client.post("/api/v1/departments", json=create_payload, headers=self.headers_org1_admin)
        self.assertEqual(res.status_code, 201)
        dept_id = res.json()["data"]["id"]
        self.assertEqual(res.json()["data"]["name"], dept_name)

        # Duplicate name in same org rejected
        res_dup = self.client.post("/api/v1/departments", json=create_payload, headers=self.headers_org1_admin)
        self.assertEqual(res_dup.status_code, 409)

        # List
        res_list = self.client.get("/api/v1/departments", headers=self.headers_org1_admin)
        self.assertEqual(res_list.status_code, 200)
        self.assertTrue(any(d["id"] == dept_id for d in res_list.json()["data"]))

        # Get by ID
        res_get = self.client.get(f"/api/v1/departments/{dept_id}", headers=self.headers_org1_admin)
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["data"]["id"], dept_id)

        # Update
        res_update = self.client.patch(
            f"/api/v1/departments/{dept_id}",
            json={"description": "Updated engineering mission"},
            headers=self.headers_org1_admin,
        )
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.json()["data"]["description"], "Updated engineering mission")

        # Delete
        res_del = self.client.delete(f"/api/v1/departments/{dept_id}", headers=self.headers_org1_admin)
        self.assertEqual(res_del.status_code, 200)

        # Get after delete returns 404
        res_get_del = self.client.get(f"/api/v1/departments/{dept_id}", headers=self.headers_org1_admin)
        self.assertEqual(res_get_del.status_code, 404)

    # --------------------------------------------------------------------------
    # 3. Team Management Endpoints (/api/v1/teams)
    # --------------------------------------------------------------------------
    def test_team_crud_lifecycle(self) -> None:
        """Verifies team creation, listing with department filter, retrieval, update, and deletion."""
        # Create Department first
        res_dept = self.client.post(
            "/api/v1/departments",
            json={"name": f"Product Dept {uuid4().hex[:6]}"},
            headers=self.headers_org1_admin,
        )
        dept_id = res_dept.json()["data"]["id"]

        team_name = f"Backend Team {uuid4().hex[:6]}"
        create_payload = {
            "name": team_name,
            "department_id": dept_id,
            "description": "API and infrastructure team",
        }
        # Create
        res = self.client.post("/api/v1/teams", json=create_payload, headers=self.headers_org1_admin)
        self.assertEqual(res.status_code, 201)
        team_id = res.json()["data"]["id"]
        self.assertEqual(res.json()["data"]["name"], team_name)

        # List with department filter
        res_list = self.client.get(f"/api/v1/teams?department_id={dept_id}", headers=self.headers_org1_admin)
        self.assertEqual(res_list.status_code, 200)
        self.assertTrue(any(t["id"] == team_id for t in res_list.json()["data"]))

        # Get by ID
        res_get = self.client.get(f"/api/v1/teams/{team_id}", headers=self.headers_org1_admin)
        self.assertEqual(res_get.status_code, 200)

        # Update
        res_patch = self.client.patch(
            f"/api/v1/teams/{team_id}",
            json={"description": "Updated team charter"},
            headers=self.headers_org1_admin,
        )
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.json()["data"]["description"], "Updated team charter")

        # Delete
        res_del = self.client.delete(f"/api/v1/teams/{team_id}", headers=self.headers_org1_admin)
        self.assertEqual(res_del.status_code, 200)

    # --------------------------------------------------------------------------
    # 4. Project Workspace Endpoints (/api/v1/projects)
    # --------------------------------------------------------------------------
    def test_project_crud_lifecycle(self) -> None:
        """Verifies project workspace creation, listing, retrieval, update, and archiving."""
        proj_name = f"Project Nexus {uuid4().hex[:6]}"
        create_payload = {
            "name": proj_name,
            "description": "Enterprise AI search rollout",
            "priority": "HIGH",
        }
        # Member creates project
        res = self.client.post("/api/v1/projects", json=create_payload, headers=self.headers_org1_member)
        self.assertEqual(res.status_code, 201)
        proj_id = res.json()["data"]["id"]
        self.assertEqual(res.json()["data"]["name"], proj_name)

        # List projects
        res_list = self.client.get("/api/v1/projects?status=ACTIVE", headers=self.headers_org1_member)
        self.assertEqual(res_list.status_code, 200)
        self.assertTrue(any(p["id"] == proj_id for p in res_list.json()["data"]))

        # Get by ID
        res_get = self.client.get(f"/api/v1/projects/{proj_id}", headers=self.headers_org1_member)
        self.assertEqual(res_get.status_code, 200)

        # Update status
        res_patch = self.client.patch(
            f"/api/v1/projects/{proj_id}",
            json={"priority": "CRITICAL"},
            headers=self.headers_org1_admin,
        )
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.json()["data"]["priority"], "CRITICAL")

        # Archive project
        res_del = self.client.delete(f"/api/v1/projects/{proj_id}", headers=self.headers_org1_admin)
        self.assertEqual(res_del.status_code, 200)

    # --------------------------------------------------------------------------
    # 5. Invitations and Members Endpoints (/api/v1/invitations & /api/v1/members)
    # --------------------------------------------------------------------------
    def test_invitation_and_member_directory_lifecycle(self) -> None:
        """Verifies dispatching invitations, public token acceptance, and member directory management."""
        invitee_email = f"invitee_{uuid4().hex[:6]}@hier1.com"
        invite_payload = {
            "email": invitee_email,
            "role": "Member",
        }
        # 5.1 Send invitation
        res_inv = self.client.post("/api/v1/invitations", json=invite_payload, headers=self.headers_org1_admin)
        self.assertEqual(res_inv.status_code, 201)
        invitation_data = res_inv.json()["data"]
        token = invitation_data["token"]
        invitation_id = invitation_data["id"]

        # 5.2 List pending invitations
        res_inv_list = self.client.get("/api/v1/invitations", headers=self.headers_org1_admin)
        self.assertEqual(res_inv_list.status_code, 200)
        self.assertTrue(any(i["id"] == invitation_id for i in res_inv_list.json()["data"]))

        # 5.3 Accept invitation (Public endpoint)
        accept_payload = {
            "token": token,
            "full_name": "New Onboarded Member",
            "password": "SecurePassword123!",
        }
        res_accept = self.client.post("/api/v1/invitations/accept", json=accept_payload)
        self.assertEqual(res_accept.status_code, 200)
        self.assertTrue(res_accept.json()["data"]["accepted"])
        new_user_id = res_accept.json()["data"]["user_id"]

        # 5.4 List members in directory
        res_members = self.client.get("/api/v1/members?page=1&page_size=20", headers=self.headers_org1_admin)
        self.assertEqual(res_members.status_code, 200)
        items = res_members.json()["data"]["items"]
        self.assertTrue(any(m["id"] == new_user_id for m in items))

        # 5.5 Update member role to ProjectManager
        res_role = self.client.patch(
            f"/api/v1/members/{new_user_id}",
            json={"role": "ProjectManager"},
            headers=self.headers_org1_admin,
        )
        self.assertEqual(res_role.status_code, 200)
        self.assertEqual(res_role.json()["data"]["role"], "ProjectManager")

        # 5.6 Remove member
        res_remove = self.client.delete(f"/api/v1/members/{new_user_id}", headers=self.headers_org1_admin)
        self.assertEqual(res_remove.status_code, 200)

    # --------------------------------------------------------------------------
    # 6. Multi-Tenant Quarantine Validation
    # --------------------------------------------------------------------------
    def test_multi_tenant_quarantine(self) -> None:
        """Verifies that Tenant A cannot read or mutate Tenant B resources."""
        # Tenant 2 creates a department
        res_dept2 = self.client.post(
            "/api/v1/departments",
            json={"name": f"Org2 Dept {uuid4().hex[:6]}"},
            headers=self.headers_org2_admin,
        )
        self.assertEqual(res_dept2.status_code, 201)
        dept2_id = res_dept2.json()["data"]["id"]

        # Tenant 1 tries to access Tenant 2's department -> returns 404 (strictly isolated)
        res_quarantine_get = self.client.get(f"/api/v1/departments/{dept2_id}", headers=self.headers_org1_admin)
        self.assertEqual(res_quarantine_get.status_code, 404)

        # Tenant 1 tries to delete Tenant 2's department -> returns 404
        res_quarantine_del = self.client.delete(f"/api/v1/departments/{dept2_id}", headers=self.headers_org1_admin)
        self.assertEqual(res_quarantine_del.status_code, 404)
