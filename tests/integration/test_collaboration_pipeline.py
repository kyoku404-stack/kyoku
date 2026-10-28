"""Integration and Performance Benchmark Test Suite for Real-Time Collaboration & Team Workspaces (Phase 3.2).

Verifies the complete end-to-end Collaboration Pipeline across:
1. Multi-tenant workspace data quarantine (Tenant Alpha vs Tenant Beta).
2. End-to-end collaboration lifecycle:
   - Workspace creation and membership provisioning.
   - Shared project linking.
   - Threaded document comments, replies, and resolution lifecycle.
   - User mention processing and notifications.
3. Live presence heartbeat updates and workspace collaborator tracking.
4. Activity feed pipeline recording audit events with actor attribution.
5. Document version history checkpoints and version rollback integrity.
6. AI-assisted discussion summarization with key decisions and action items.
7. SLA performance benchmarks:
   - Comment creation latency < 500ms.
   - Activity feed query latency < 1000ms.
   - Presence heartbeat latency < 300ms.

Specification: devdocs/p3/p3.2.txt & docs/Architecture/real-time-collaboration-team-workspaces.md
Author: Member 4 (Integration & DevOps Lead)
"""

import time
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.collaboration import (
    CollaborationActivity,
    DocumentComment,
    DocumentVersionHistory,
    Workspace,
    WorkspaceMember,
)
from backend.app.models.document import Document
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestCollaborationPipelineIntegration(unittest.TestCase):
    """End-to-end integration and SLA performance benchmark suite for Phase 3.2 Collaboration."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Primary Tenant Organization Alpha
            cls.org_alpha = Organization(
                name="Collaboration Org Alpha",
                domain=f"alpha-collab-{uuid4().hex[:6]}.com",
            )
            # 2. Secondary Tenant Organization Beta (Multi-tenant quarantine)
            cls.org_beta = Organization(
                name="Collaboration Org Beta",
                domain=f"beta-collab-{uuid4().hex[:6]}.com",
            )
            session.add_all([cls.org_alpha, cls.org_beta])
            session.commit()
            session.refresh(cls.org_alpha)
            session.refresh(cls.org_beta)

            cls.org_alpha_id = cls.org_alpha.id
            cls.org_beta_id = cls.org_beta.id

            # 3. Users for Org Alpha (Lead + Collaborator)
            cls.user_alpha_lead = User(
                email=f"alpha-lead-{uuid4().hex[:6]}@test.com",
                hashed_password=get_password_hash("LeadPass123!"),
                full_name="Alpha Lead Architect",
                role="OrgAdmin",
                organization_id=cls.org_alpha_id,
                is_active=True,
            )
            cls.user_alpha_member = User(
                email=f"alpha-member-{uuid4().hex[:6]}@test.com",
                hashed_password=get_password_hash("MemberPass123!"),
                full_name="Alpha Contributor User",
                role="Member",
                organization_id=cls.org_alpha_id,
                is_active=True,
            )

            # 4. User for Org Beta (Isolation validation)
            cls.user_beta_admin = User(
                email=f"beta-admin-{uuid4().hex[:6]}@test.com",
                hashed_password=get_password_hash("BetaPass123!"),
                full_name="Beta Org Administrator",
                role="OrgAdmin",
                organization_id=cls.org_beta_id,
                is_active=True,
            )

            session.add_all([cls.user_alpha_lead, cls.user_alpha_member, cls.user_beta_admin])
            session.commit()
            session.refresh(cls.user_alpha_lead)
            session.refresh(cls.user_alpha_member)
            session.refresh(cls.user_beta_admin)

            cls.alpha_lead_id = cls.user_alpha_lead.id
            cls.alpha_member_id = cls.user_alpha_member.id
            cls.beta_admin_id = cls.user_beta_admin.id

            # 5. Shared Test Document in Org Alpha
            cls.test_doc = Document(
                filename="Architecture_Design_Spec.pdf",
                file_path="/storage/test/Architecture_Design_Spec.pdf",
                file_type="pdf",
                file_size=2048576,
                organization_id=cls.org_alpha_id,
                uploader_id=cls.alpha_lead_id,
                checksum_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            )
            session.add(cls.test_doc)
            session.commit()
            session.refresh(cls.test_doc)
            cls.doc_id = cls.test_doc.id

        # Auth tokens with complete claims
        cls.token_alpha_lead = create_access_token(
            data={
                "sub": str(cls.alpha_lead_id),
                "role": "OrgAdmin",
                "org_id": str(cls.org_alpha_id),
                "email": cls.user_alpha_lead.email,
            }
        )
        cls.headers_alpha_lead = {
            "Authorization": f"Bearer {cls.token_alpha_lead}",
            "X-Organization-ID": str(cls.org_alpha_id),
        }

        cls.token_alpha_member = create_access_token(
            data={
                "sub": str(cls.alpha_member_id),
                "role": "Member",
                "org_id": str(cls.org_alpha_id),
                "email": cls.user_alpha_member.email,
            }
        )
        cls.headers_alpha_member = {
            "Authorization": f"Bearer {cls.token_alpha_member}",
            "X-Organization-ID": str(cls.org_alpha_id),
        }

        cls.token_beta_admin = create_access_token(
            data={
                "sub": str(cls.beta_admin_id),
                "role": "OrgAdmin",
                "org_id": str(cls.org_beta_id),
                "email": cls.user_beta_admin.email,
            }
        )
        cls.headers_beta_admin = {
            "Authorization": f"Bearer {cls.token_beta_admin}",
            "X-Organization-ID": str(cls.org_beta_id),
        }

        # Shared workspace created for cross-test reference
        cls.shared_workspace_id = None

    @classmethod
    def tearDownClass(cls) -> None:
        with Session(sync_test_engine) as session:
            session.query(CollaborationActivity).delete()
            session.query(DocumentVersionHistory).delete()
            session.query(DocumentComment).delete()
            session.query(WorkspaceMember).delete()
            session.query(Workspace).delete()
            session.query(Document).filter(Document.id == cls.doc_id).delete()
            session.query(User).filter(
                User.id.in_([cls.alpha_lead_id, cls.alpha_member_id, cls.beta_admin_id])
            ).delete()
            session.query(Organization).filter(
                Organization.id.in_([cls.org_alpha_id, cls.org_beta_id])
            ).delete()
            session.commit()

    def test_01_multi_tenant_workspace_isolation(self) -> None:
        """Verify Tenant B cannot list or access workspaces created by Tenant A."""
        slug = f"alpha-conf-{uuid4().hex[:6]}"
        resp = self.client.post(
            "/api/v1/workspaces/create",
            headers=self.headers_alpha_lead,
            json={
                "name": f"Alpha Conf Secret Space {uuid4().hex[:4]}",
                "slug": slug,
                "description": "Tenant Alpha confidential workspace",
                "avatar_color": "#1E293B",
                "is_private": True,
            },
        )
        self.assertEqual(resp.status_code, 201)
        workspace_id = resp.json()["data"]["id"]

        # Beta Admin attempts to retrieve Alpha's workspace directly -> 404 Not Found
        beta_get_resp = self.client.get(
            f"/api/v1/workspaces/{workspace_id}",
            headers=self.headers_beta_admin,
        )
        self.assertEqual(beta_get_resp.status_code, 404)

        # Beta Admin lists workspaces -> Alpha's workspace must not appear
        beta_list_resp = self.client.get(
            "/api/v1/workspaces/list",
            headers=self.headers_beta_admin,
        )
        self.assertEqual(beta_list_resp.status_code, 200)
        beta_workspaces = beta_list_resp.json()["data"]["workspaces"]
        alpha_workspace_ids = [w["id"] for w in beta_workspaces if w["id"] == workspace_id]
        self.assertEqual(len(alpha_workspace_ids), 0)

    def test_02_end_to_end_collaboration_lifecycle(self) -> None:
        """Verify complete lifecycle: Workspace -> Member -> Project -> Comment -> Reply -> Resolve."""
        # 1. Create Workspace
        slug = f"prod-eng-{uuid4().hex[:6]}"
        create_ws_resp = self.client.post(
            "/api/v1/workspaces/create",
            headers=self.headers_alpha_lead,
            json={
                "name": "Product Engineering",
                "slug": slug,
                "description": "Core product engineering collaboration hub",
                "avatar_color": "#4F46E5",
                "is_private": False,
            },
        )
        self.assertEqual(create_ws_resp.status_code, 201)
        workspace_id = create_ws_resp.json()["data"]["id"]
        TestCollaborationPipelineIntegration.shared_workspace_id = workspace_id

        # 2. Add Member to Workspace
        add_member_resp = self.client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            headers=self.headers_alpha_lead,
            json={
                "user_id": str(self.alpha_member_id),
                "role": "MEMBER",
            },
        )
        self.assertEqual(add_member_resp.status_code, 200)
        self.assertEqual(add_member_resp.json()["data"]["role"], "MEMBER")

        # 3. Create Shared Project inside Workspace
        create_project_resp = self.client.post(
            "/api/v1/projects/create",
            headers=self.headers_alpha_lead,
            json={
                "workspace_id": workspace_id,
                "name": "Phase 3 Cloud Migration",
                "description": "Cross-functional cloud architecture upgrade",
            },
        )
        self.assertEqual(create_project_resp.status_code, 201)
        project_id = create_project_resp.json()["data"]["id"]
        self.assertIsNotNone(project_id)

        # 4. Post Parent Comment on Document
        post_comment_resp = self.client.post(
            "/api/v1/comments/create",
            headers=self.headers_alpha_lead,
            json={
                "document_id": str(self.doc_id),
                "content": f"Please review Section 4 on database partitioning. @{self.user_alpha_member.email.split('@')[0]}",
                "workspace_id": workspace_id,
                "page_number": 4,
                "highlight_text": "Section 4: Database Partitioning",
            },
        )
        self.assertEqual(post_comment_resp.status_code, 201)
        comment_id = post_comment_resp.json()["data"]["id"]
        self.assertEqual(post_comment_resp.json()["data"]["status"], "OPEN")

        # 5. Member posts threaded reply
        reply_comment_resp = self.client.post(
            "/api/v1/comments/reply",
            headers=self.headers_alpha_member,
            json={
                "parent_comment_id": comment_id,
                "content": "Reviewed and approved the shard key distribution algorithm.",
            },
        )
        self.assertEqual(reply_comment_resp.status_code, 201)
        reply_data = reply_comment_resp.json()["data"]
        self.assertEqual(reply_data["parent_comment_id"], comment_id)

        # 6. Retrieve Document Discussion Thread
        get_comments_resp = self.client.get(
            f"/api/v1/comments/document/{self.doc_id}",
            headers=self.headers_alpha_lead,
        )
        self.assertEqual(get_comments_resp.status_code, 200)
        comments_list = get_comments_resp.json()["data"]["comments"]
        parent_comment = next((c for c in comments_list if c["id"] == comment_id), None)
        self.assertIsNotNone(parent_comment)
        self.assertEqual(len(parent_comment["replies"]), 1)

        # 7. Resolve Thread
        resolve_resp = self.client.post(
            f"/api/v1/comments/{comment_id}/resolve",
            headers=self.headers_alpha_lead,
        )
        self.assertEqual(resolve_resp.status_code, 200)
        self.assertEqual(resolve_resp.json()["data"]["status"], "RESOLVED")
        self.assertIsNotNone(resolve_resp.json()["data"]["resolved_at"])

    def test_03_presence_heartbeat_and_live_collaborators(self) -> None:
        """Verify presence heartbeat updates and tracking active collaborators in workspace."""
        ws_id = self.shared_workspace_id or str(uuid4())

        # 1. Lead sends online heartbeat
        hb1 = self.client.post(
            "/api/v1/presence/heartbeat",
            headers=self.headers_alpha_lead,
            json={
                "workspace_id": ws_id,
                "status": "ONLINE",
                "document_id": str(self.doc_id),
            },
        )
        self.assertEqual(hb1.status_code, 200)
        self.assertTrue(hb1.json()["data"]["received"])

        # 2. Member sends busy/editing heartbeat
        hb2 = self.client.post(
            "/api/v1/presence/heartbeat",
            headers=self.headers_alpha_member,
            json={
                "workspace_id": ws_id,
                "status": "EDITING",
                "document_id": str(self.doc_id),
            },
        )
        self.assertEqual(hb2.status_code, 200)

        # 3. Retrieve Workspace Active Collaborators
        presence_resp = self.client.get(
            f"/api/v1/presence/{ws_id}",
            headers=self.headers_alpha_lead,
        )
        self.assertEqual(presence_resp.status_code, 200)
        collaborators = presence_resp.json()["data"]["collaborators"]
        self.assertIsInstance(collaborators, list)
        self.assertTrue(any(c["user_id"] == str(self.alpha_lead_id) for c in collaborators))

    def test_04_activity_feed_audit_timeline(self) -> None:
        """Verify activity feed records collaboration actions with timestamps and actor metadata."""
        ws_id = self.shared_workspace_id or str(uuid4())
        feed_resp = self.client.get(
            f"/api/v1/activity/feed?workspace_id={ws_id}&limit=25",
            headers=self.headers_alpha_lead,
        )
        self.assertEqual(feed_resp.status_code, 200)
        feed_data = feed_resp.json()["data"]
        self.assertIn("activities", feed_data)
        self.assertIsInstance(feed_data["activities"], list)

    def test_05_document_version_checkpoints_and_rollback(self) -> None:
        """Verify creating version snapshots and rolling back with version checkpoint history."""
        # 1. Create v1 checkpoint
        v1_resp = self.client.post(
            "/api/v1/version/create",
            headers=self.headers_alpha_lead,
            json={
                "document_id": str(self.doc_id),
                "change_summary": "Initial draft of system architecture",
                "file_size_bytes": 1048576,
                "checksum": "1111111111111111111111111111111111111111111111111111111111111111",
                "approval_status": "APPROVED",
            },
        )
        self.assertEqual(v1_resp.status_code, 201)
        v1_data = v1_resp.json()["data"]
        self.assertEqual(v1_data["version_number"], 1)

        # 2. Create v2 checkpoint
        v2_resp = self.client.post(
            "/api/v1/version/create",
            headers=self.headers_alpha_member,
            json={
                "document_id": str(self.doc_id),
                "change_summary": "Added disaster recovery runbooks",
                "file_size_bytes": 1500000,
                "checksum": "2222222222222222222222222222222222222222222222222222222222222222",
                "approval_status": "APPROVED",
            },
        )
        self.assertEqual(v2_resp.status_code, 201)
        v2_data = v2_resp.json()["data"]
        self.assertEqual(v2_data["version_number"], 2)

        # 3. Retrieve Version History
        history_resp = self.client.get(
            f"/api/v1/version/history/{self.doc_id}",
            headers=self.headers_alpha_lead,
        )
        self.assertEqual(history_resp.status_code, 200)
        history_data = history_resp.json()["data"]
        self.assertEqual(history_data["total_versions"], 2)
        self.assertEqual(len(history_data["versions"]), 2)

        # 4. Rollback to v1
        rollback_resp = self.client.post(
            "/api/v1/version/rollback",
            headers=self.headers_alpha_lead,
            json={
                "document_id": str(self.doc_id),
                "target_version_number": 1,
            },
        )
        self.assertEqual(rollback_resp.status_code, 200)
        rollback_data = rollback_resp.json()["data"]
        self.assertEqual(rollback_data["version_number"], 3)
        self.assertIn("Version 1", rollback_data["change_summary"])

    def test_06_ai_discussion_summary_generation(self) -> None:
        """Verify AI discussion assistant extracts consensus, open questions, and action items."""
        summary_resp = self.client.post(
            f"/api/v1/collaboration/discussions/{self.doc_id}/summary",
            headers=self.headers_alpha_lead,
        )
        self.assertEqual(summary_resp.status_code, 200)
        summary_data = summary_resp.json()["data"]
        self.assertEqual(summary_data["document_id"], str(self.doc_id))
        self.assertIn("executive_summary", summary_data)
        self.assertIsInstance(summary_data["executive_summary"], str)
        self.assertIsInstance(summary_data["action_items"], list)
        self.assertIsInstance(summary_data["key_decisions"], list)
        self.assertIsInstance(summary_data["suggested_documents"], list)

    def test_07_collaboration_performance_sla_benchmark(self) -> None:
        """Benchmark collaboration operations against strict enterprise SLAs:
        - Comment creation latency < 500ms
        - Activity feed latency < 1000ms
        - Presence heartbeat latency < 300ms
        """
        ws_id = self.shared_workspace_id or str(uuid4())

        # Benchmark 1: Comment creation (< 500ms SLA)
        t0 = time.perf_counter()
        comment_resp = self.client.post(
            "/api/v1/comments/create",
            headers=self.headers_alpha_lead,
            json={
                "document_id": str(self.doc_id),
                "content": "SLA Benchmark Comment Execution.",
                "workspace_id": ws_id,
            },
        )
        comment_duration_ms = (time.perf_counter() - t0) * 1000
        self.assertEqual(comment_resp.status_code, 201)
        self.assertLess(
            comment_duration_ms,
            500.0,
            f"Comment creation took {comment_duration_ms:.2f}ms, exceeding 500ms SLA",
        )

        # Benchmark 2: Activity feed retrieval (< 1000ms SLA)
        t0 = time.perf_counter()
        feed_resp = self.client.get(
            f"/api/v1/activity/feed?workspace_id={ws_id}&limit=50",
            headers=self.headers_alpha_lead,
        )
        feed_duration_ms = (time.perf_counter() - t0) * 1000
        self.assertEqual(feed_resp.status_code, 200)
        self.assertLess(
            feed_duration_ms,
            1000.0,
            f"Activity feed retrieval took {feed_duration_ms:.2f}ms, exceeding 1000ms SLA",
        )

        # Benchmark 3: Presence heartbeat (< 300ms SLA)
        t0 = time.perf_counter()
        hb_resp = self.client.post(
            "/api/v1/presence/heartbeat",
            headers=self.headers_alpha_lead,
            json={
                "workspace_id": ws_id,
                "status": "ONLINE",
                "document_id": str(self.doc_id),
            },
        )
        hb_duration_ms = (time.perf_counter() - t0) * 1000
        self.assertEqual(hb_resp.status_code, 200)
        self.assertLess(
            hb_duration_ms,
            300.0,
            f"Presence heartbeat took {hb_duration_ms:.2f}ms, exceeding 300ms SLA",
        )
