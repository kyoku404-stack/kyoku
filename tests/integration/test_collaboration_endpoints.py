"""Integration Tests for Real-Time Collaboration & Team Workspaces REST APIs (Phase 3.2).

Verifies endpoints defined in docs/api/api-contract.md Section 14:
- POST /api/v1/workspaces/create
- GET /api/v1/workspaces/list
- GET /api/v1/workspaces/{id}
- POST /api/v1/workspaces/{id}/members
- GET /api/v1/workspaces/{id}/dashboard
- POST /api/v1/projects/create
- POST /api/v1/comments/create
- POST /api/v1/comments/reply
- GET /api/v1/comments/document/{document_id}
- POST /api/v1/comments/{id}/resolve
- POST /api/v1/presence/heartbeat
- GET /api/v1/presence/{workspace_id}
- GET /api/v1/activity/feed
- POST /api/v1/version/create
- GET /api/v1/version/history/{document_id}
- POST /api/v1/version/rollback
- POST /api/v1/collaboration/discussions/{document_id}/summary

Specification: devdocs/p3/p3.2.txt & docs/api/api-contract.md Section 14
Owner: Member 2 (Backend & Database Lead)
"""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.document import Document
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestCollaborationEndpointsIntegration(unittest.TestCase):
    """Integration test suite for Phase 3.2 Collaboration REST APIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Organization
            cls.org = Organization(
                name="Collaboration Test Org",
                domain=f"collab-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            # 2. OrgAdmin User
            cls.user = User(
                email=f"collab-lead-{uuid4().hex[:6]}@test.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Lead Architect",
                organization_id=cls.org_id,
                role="OrgAdmin",
            )
            session.add(cls.user)

            # 3. Colleague User for mentions/membership
            cls.colleague = User(
                email=f"colleague-{uuid4().hex[:6]}@test.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Sarah Connor",
                organization_id=cls.org_id,
                role="Member",
            )
            session.add(cls.colleague)

            # 4. Enterprise Document
            cls.document = Document(
                organization_id=cls.org_id,
                uploader_id=cls.user.id,
                filename="handbook.pdf",
                title="Employee Handbook.pdf",
                file_path="/storage/test/handbook.pdf",
                file_type="pdf",
                mime_type="application/pdf",
                file_size=1048576,
                status="READY",
            )
            session.add(cls.document)

            session.commit()
            session.refresh(cls.user)
            session.refresh(cls.colleague)
            session.refresh(cls.document)

            cls.user_id = cls.user.id
            cls.colleague_id = cls.colleague.id
            cls.document_id = cls.document.id

        # Auth Token
        cls.token = create_access_token(
            data={
                "sub": str(cls.user_id),
                "email": cls.user.email,
                "org_id": str(cls.org_id),
                "role": "OrgAdmin",
            }
        )
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    def test_01_workspace_lifecycle(self):
        """Test workspace creation, retrieval, listing, and membership."""
        slug = f"eng-core-{uuid4().hex[:4]}"
        create_payload = {
            "name": "Engineering Core",
            "slug": slug,
            "description": "Core engineering workspace",
            "avatar_color": "#4F46E5",
            "is_private": False,
        }
        resp = self.client.post("/api/v1/workspaces/create", json=create_payload, headers=self.headers)
        assert resp.status_code == 201, resp.text
        data = resp.json()["data"]
        workspace_id = data["id"]
        assert data["slug"] == slug
        assert data["member_count"] == 1
        assert data["current_user_role"] == "ADMIN"

        # List workspaces
        list_resp = self.client.get("/api/v1/workspaces/list", headers=self.headers)
        assert list_resp.status_code == 200
        w_list = list_resp.json()["data"]["workspaces"]
        assert any(w["id"] == workspace_id for w in w_list)

        # Get workspace by ID
        get_resp = self.client.get(f"/api/v1/workspaces/{workspace_id}", headers=self.headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["id"] == workspace_id

        # Add colleague as MEMBER
        add_member_payload = {
            "user_id": str(self.colleague_id),
            "role": "MEMBER",
        }
        m_resp = self.client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json=add_member_payload,
            headers=self.headers,
        )
        assert m_resp.status_code == 200
        assert m_resp.json()["data"]["role"] == "MEMBER"

        # Workspace dashboard
        dash_resp = self.client.get(f"/api/v1/workspaces/{workspace_id}/dashboard", headers=self.headers)
        assert dash_resp.status_code == 200
        dash_data = dash_resp.json()["data"]
        assert dash_data["active_members_count"] >= 2

    def test_02_shared_project_creation(self):
        """Test shared project creation under a workspace."""
        # Create temporary workspace
        slug = f"proj-ws-{uuid4().hex[:4]}"
        w_resp = self.client.post(
            "/api/v1/workspaces/create",
            json={"name": "Projects Hub", "slug": slug},
            headers=self.headers,
        )
        w_id = w_resp.json()["data"]["id"]

        proj_payload = {
            "workspace_id": w_id,
            "name": "Cloud Native Architecture",
            "description": "Migration to multi-region cloud cluster",
        }
        p_resp = self.client.post("/api/v1/projects/create", json=proj_payload, headers=self.headers)
        assert p_resp.status_code == 201
        assert p_resp.json()["data"]["name"] == "Cloud Native Architecture"

    def test_03_threaded_comments_and_mentions(self):
        """Test comment creation, replies, mentions, and resolution."""
        # Post root comment with mention
        comment_payload = {
            "document_id": str(self.document_id),
            "content": f"Please verify the compliance policy with @{self.colleague.email.split('@')[0]} before the audit.",
            "page_number": 2,
            "highlight_text": "All data must be encrypted at rest.",
        }
        c_resp = self.client.post("/api/v1/comments/create", json=comment_payload, headers=self.headers)
        assert c_resp.status_code == 201
        c_data = c_resp.json()["data"]
        comment_id = c_data["id"]
        assert c_data["status"] == "OPEN"
        assert len(c_data["mentions"]) >= 1

        # Reply to comment
        reply_payload = {
            "parent_comment_id": comment_id,
            "content": "Verified and approved per ISO-27001 requirements.",
        }
        r_resp = self.client.post("/api/v1/comments/reply", json=reply_payload, headers=self.headers)
        assert r_resp.status_code == 201
        assert r_resp.json()["data"]["parent_comment_id"] == comment_id

        # Get all document comments
        doc_comms_resp = self.client.get(f"/api/v1/comments/document/{self.document_id}", headers=self.headers)
        assert doc_comms_resp.status_code == 200
        comments_list = doc_comms_resp.json()["data"]["comments"]
        assert len(comments_list) >= 1
        # Root comment should nest reply
        root = [c for c in comments_list if c["id"] == comment_id][0]
        assert len(root["replies"]) == 1

        # Resolve comment
        res_resp = self.client.post(f"/api/v1/comments/{comment_id}/resolve", headers=self.headers)
        assert res_resp.status_code == 200
        assert res_resp.json()["data"]["status"] == "RESOLVED"

    def test_04_presence_and_activity_feed(self):
        """Test heartbeat presence updates and activity feed queries."""
        slug = f"presence-ws-{uuid4().hex[:4]}"
        w_resp = self.client.post(
            "/api/v1/workspaces/create",
            json={"name": "Presence Hub", "slug": slug},
            headers=self.headers,
        )
        w_id = w_resp.json()["data"]["id"]

        # Send presence heartbeat
        hb_payload = {
            "workspace_id": w_id,
            "status": "EDITING",
            "document_id": str(self.document_id),
        }
        hb_resp = self.client.post("/api/v1/presence/heartbeat", json=hb_payload, headers=self.headers)
        assert hb_resp.status_code == 200
        assert hb_resp.json()["data"]["received"] is True

        # Query presence roster
        pres_resp = self.client.get(f"/api/v1/presence/{w_id}", headers=self.headers)
        assert pres_resp.status_code == 200
        collaborators = pres_resp.json()["data"]["collaborators"]
        assert any(c["user_id"] == str(self.user_id) for c in collaborators)

        # Activity feed
        feed_resp = self.client.get(f"/api/v1/activity/feed?workspace_id={w_id}", headers=self.headers)
        assert feed_resp.status_code == 200
        assert "activities" in feed_resp.json()["data"]

    def test_05_version_history_and_rollback(self):
        """Test version checkpoint creation, retrieval, and rollback."""
        # Create version checkpoint 1
        v1_payload = {
            "document_id": str(self.document_id),
            "change_summary": "Initial draft of employee handbook",
            "file_size_bytes": 1048576,
            "checksum": "a1b2c3d4e5f6...",
            "approval_status": "APPROVED",
        }
        v1_resp = self.client.post("/api/v1/version/create", json=v1_payload, headers=self.headers)
        assert v1_resp.status_code == 201
        v1_num = v1_resp.json()["data"]["version_number"]

        # Create version checkpoint 2
        v2_payload = {
            "document_id": str(self.document_id),
            "change_summary": "Updated annual leave to 20 days",
            "file_size_bytes": 1050000,
            "checksum": "f6e5d4c3b2a1...",
            "approval_status": "APPROVED",
        }
        v2_resp = self.client.post("/api/v1/version/create", json=v2_payload, headers=self.headers)
        assert v2_resp.status_code == 201
        v2_num = v2_resp.json()["data"]["version_number"]
        assert v2_num > v1_num

        # Get version history
        hist_resp = self.client.get(f"/api/v1/version/history/{self.document_id}", headers=self.headers)
        assert hist_resp.status_code == 200
        versions = hist_resp.json()["data"]["versions"]
        assert len(versions) >= 2

        # Roll back to version 1
        rb_payload = {
            "document_id": str(self.document_id),
            "target_version_number": v1_num,
        }
        rb_resp = self.client.post("/api/v1/version/rollback", json=rb_payload, headers=self.headers)
        assert rb_resp.status_code == 200
        rb_data = rb_resp.json()["data"]
        assert "Rolled back to Version 1" in rb_data["change_summary"]

    def test_06_ai_discussion_summary(self):
        """Test AI discussion summarization and recommendation endpoint."""
        summary_resp = self.client.post(
            f"/api/v1/collaboration/discussions/{self.document_id}/summary",
            headers=self.headers,
        )
        assert summary_resp.status_code == 200
        data = summary_resp.json()["data"]
        assert data["document_id"] == str(self.document_id)
        assert "executive_summary" in data
        assert isinstance(data["key_decisions"], list)
        assert isinstance(data["action_items"], list)
        assert isinstance(data["suggested_documents"], list)
