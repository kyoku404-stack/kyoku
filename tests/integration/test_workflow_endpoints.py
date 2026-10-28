"""Integration tests for Phase 3.4 Workflow Automation & Notifications REST APIs.

Verifies endpoints defined in docs/api/api-contract.md Section 16:
- POST /api/v1/workflows/create
- GET /api/v1/workflows/list
- GET /api/v1/workflows/status/{id}
- POST /api/v1/workflows/execute
- DELETE /api/v1/workflows/{id}
- GET /api/v1/workflows/executions
- GET /api/v1/workflows/templates
- POST /api/v1/workflows/approve
- GET /api/v1/workflows/approvals/pending
- GET /api/v1/workflows/analytics
- GET /api/v1/notifications
- POST /api/v1/notifications/{id}/read
- POST /api/v1/notifications/read-all
- GET /api/v1/notifications/preferences
- POST /api/v1/notifications/preferences

Specification: devdocs/p3/p3.4.txt & docs/api/api-contract.md Section 16
Owner: Member 2 (Backend & Database Lead)
"""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.notification import Notification
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestWorkflowEndpointsIntegration(unittest.TestCase):
    """Integration test suite for Phase 3.4 Workflow & Notification REST APIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            cls.org = Organization(
                name="Workflow Test Enterprise",
                domain=f"workflow-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            cls.admin_user = User(
                email=f"admin-{uuid4().hex[:6]}@workflow.com",
                hashed_password=get_password_hash("Password123!"),
                full_name="Workflow Admin",
                role="OrgAdmin",
                organization_id=cls.org_id,
                is_active=True,
            )
            session.add(cls.admin_user)
            session.commit()
            session.refresh(cls.admin_user)
            cls.admin_id = cls.admin_user.id

            # Seed a test notification
            cls.test_notif = Notification(
                organization_id=cls.org_id,
                user_id=cls.admin_id,
                title="System Initialized",
                body="Workflow engine initialized successfully.",
                channel="IN_APP",
                priority="NORMAL",
                category="WORKFLOW",
                is_read=False,
            )
            session.add(cls.test_notif)
            session.commit()
            session.refresh(cls.test_notif)
            cls.notif_id = cls.test_notif.id

        token_payload = {
            "sub": str(cls.admin_id),
            "email": cls.admin_user.email,
            "org_id": str(cls.org_id),
            "role": "OrgAdmin",
            "mfa_verified": True,
        }
        cls.auth_token = create_access_token(data=token_payload)
        cls.headers = {"Authorization": f"Bearer {cls.auth_token}"}

    def test_01_create_and_list_workflows(self) -> None:
        """Verifies creating a new workflow and querying it in the list."""
        create_payload = {
            "name": "HR Policy Review Pipeline",
            "description": "Auto-summarize uploaded policy documents and alert manager",
            "trigger_type": "EVENT",
            "event_pattern": "document.uploaded",
            "condition_rules": {"field": "type", "operator": "equals", "value": "POLICY"},
            "is_active": True,
            "steps": [
                {
                    "step_order": 1,
                    "action_type": "AI_SUMMARIZE",
                    "configuration": {"max_sentences": 3},
                },
                {
                    "step_order": 2,
                    "action_type": "NOTIFY",
                    "configuration": {"channel": "IN_APP", "priority": "HIGH"},
                },
            ],
        }

        # Create
        res = self.client.post("/api/v1/workflows/create", json=create_payload, headers=self.headers)
        assert res.status_code == 201, f"Failed create: {res.text}"
        data = res.json()["data"]
        assert data["name"] == "HR Policy Review Pipeline"
        assert data["step_count"] == 2
        workflow_id = data["id"]

        # List
        list_res = self.client.get("/api/v1/workflows/list", headers=self.headers)
        assert list_res.status_code == 200
        wfs = list_res.json()["data"]
        assert any(w["id"] == workflow_id for w in wfs)

        # Status
        status_res = self.client.get(f"/api/v1/workflows/status/{workflow_id}", headers=self.headers)
        assert status_res.status_code == 200
        status_data = status_res.json()["data"]
        assert status_data["workflow"]["id"] == workflow_id

    def test_02_execute_workflow(self) -> None:
        """Verifies triggering an execution and verifying status."""
        # Create a simple test workflow
        create_payload = {
            "name": "Immediate AI Execution",
            "trigger_type": "MANUAL",
            "steps": [
                {"step_order": 1, "action_type": "AI_SUMMARIZE", "configuration": {"max_sentences": 2}},
            ],
        }
        create_res = self.client.post("/api/v1/workflows/create", json=create_payload, headers=self.headers)
        assert create_res.status_code == 201
        wf_id = create_res.json()["data"]["id"]

        exec_payload = {
            "workflow_id": wf_id,
            "input_payload": {"title": "Company Memo", "content": "Security measures are updated."},
        }
        exec_res = self.client.post("/api/v1/workflows/execute", json=exec_payload, headers=self.headers)
        assert exec_res.status_code == 200
        data = exec_res.json()["data"]
        assert data["execution_id"] is not None
        assert data["status"] in ("RUNNING", "COMPLETED")

        # List executions
        history_res = self.client.get("/api/v1/workflows/executions", headers=self.headers)
        assert history_res.status_code == 200
        assert len(history_res.json()["data"]) >= 1

    def test_03_workflow_templates(self) -> None:
        """Verifies retrieving workflow system templates."""
        res = self.client.get("/api/v1/workflows/templates", headers=self.headers)
        assert res.status_code == 200
        templates = res.json()["data"]
        assert len(templates) >= 4
        template_ids = [t["id"] for t in templates]
        assert "tpl-doc-approval" in template_ids
        assert "tpl-ai-summary" in template_ids

    def test_04_submit_approval_decision(self) -> None:
        """Verifies submitting an approval decision."""
        approval_payload = {
            "approval_id": str(uuid4()),
            "decision": "APPROVE",
            "comments": "Signed off by Lead Reviewer",
        }
        res = self.client.post("/api/v1/workflows/approve", json=approval_payload, headers=self.headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["status"] == "APPROVE"

        # List pending
        pending_res = self.client.get("/api/v1/workflows/approvals/pending", headers=self.headers)
        assert pending_res.status_code == 200

    def test_05_notifications_inbox_and_preferences(self) -> None:
        """Verifies notification listing, marking read, and preferences."""
        # Get notifications
        res = self.client.get("/api/v1/notifications", headers=self.headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data) >= 1

        # Mark single notification as read (POST)
        post_read_res = self.client.post(f"/api/v1/notifications/{self.notif_id}/read", headers=self.headers)
        assert post_read_res.status_code == 200

        # Mark all read
        all_read_res = self.client.post("/api/v1/notifications/read-all", headers=self.headers)
        assert all_read_res.status_code == 200

        # Preferences GET
        pref_get_res = self.client.get("/api/v1/notifications/preferences", headers=self.headers)
        assert pref_get_res.status_code == 200
        assert len(pref_get_res.json()["data"]) >= 1

        # Preferences POST
        pref_payload = {
            "preferences": [
                {"channel": "SLACK", "category": "APPROVAL", "is_enabled": True},
                {"channel": "EMAIL", "category": "SYSTEM", "is_enabled": False},
            ]
        }
        pref_post_res = self.client.post("/api/v1/notifications/preferences", json=pref_payload, headers=self.headers)
        assert pref_post_res.status_code == 200

    def test_06_workflow_analytics(self) -> None:
        """Verifies workflow operational analytics KPIs."""
        res = self.client.get("/api/v1/workflows/analytics?days=7", headers=self.headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total_workflows_executed"] >= 0
        assert data["success_rate"] >= 0.0
        assert len(data["executions_by_day"]) > 0
