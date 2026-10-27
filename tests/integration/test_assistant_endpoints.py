"""Integration Tests for Enterprise AI Assistant REST API Endpoints (Phase 2.3).

Verifies all 7 Assistant endpoints defined in docs/api/api-contract.md Section 10:
1. POST /api/v1/assistant/chat
2. POST /api/v1/assistant/task
3. GET  /api/v1/assistant/history
4. POST /api/v1/assistant/report
5. GET  /api/v1/assistant/workflows
6. POST /api/v1/assistant/approve
7. GET  /api/v1/assistant/recommendations

Specification: devdocs/p2/p2.3.txt Chapters 1-20 & docs/api/api-contract.md Section 10
Owner: Member 2 (Backend Lead)
"""

import unittest
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.assistant import (
    AssistantApproval,
    AssistantWorkflow,
)
from backend.app.models.document import Document
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestAssistantEndpointsIntegration(unittest.TestCase):
    """Integration test suite for Phase 2.3 Assistant REST APIs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Tenant organization
            cls.org = Organization(
                name="Assistant Test Org",
                domain=f"assistant-{uuid4().hex[:6]}.com",
            )
            session.add(cls.org)
            session.commit()
            session.refresh(cls.org)
            cls.org_id = cls.org.id

            # 2. Test user
            cls.user = User(
                email=f"assistant-user-{uuid4().hex[:6]}@test.com",
                hashed_password=get_password_hash("Pass123!"),
                full_name="Assistant Test User",
                organization_id=cls.org_id,
                role="Member",
            )
            session.add(cls.user)
            session.commit()
            session.refresh(cls.user)
            cls.user_id = cls.user.id
            cls.user_email = cls.user.email

            # 3. Sample document
            cls.doc = Document(
                id=uuid4(),
                organization_id=cls.org_id,
                uploader_id=cls.user_id,
                filename="handbook.pdf",
                original_filename="handbook.pdf",
                title="Company Employee Handbook",
                file_path="/tmp/handbook.pdf",
                file_type="pdf",
                mime_type="application/pdf",
                file_size=2048,
                status="PROCESSED",
            )
            session.add(cls.doc)
            session.commit()

        # JWT Token
        cls.token = create_access_token(
            {
                "sub": str(cls.user_id),
                "email": cls.user_email,
                "org_id": str(cls.org_id),
                "role": "Member",
            }
        )
        cls.auth_headers = {"Authorization": f"Bearer {cls.token}"}

    def test_01_chat_turn_knowledge_query(self):
        """Tests natural language conversational turn with knowledge question."""
        payload = {
            "message": "What is our company annual leave policy?",
            "session_id": None,
        }
        resp = self.client.post("/api/v1/assistant/chat", json=payload, headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]

        assert "session_id" in data
        assert "reply" in data
        assert data["detected_intent"] == "KNOWLEDGE_QA"
        assert len(data["tools_executed"]) > 0

    def test_02_chat_turn_destructive_action_approval_gating(self):
        """Tests that destructive instructions yield WAITING_APPROVAL status with approval_id."""
        payload = {
            "message": "Invite user bob@company.com with role admin",
            "session_id": None,
        }
        resp = self.client.post("/api/v1/assistant/chat", json=payload, headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]

        assert data["requires_approval"] is True
        assert data["approval_id"] is not None

    def test_03_execute_task_pipeline(self):
        """Tests multi-step DAG task plan formulation and execution."""
        payload = {
            "title": "Quarterly Document Rollup",
            "instructions": "Summarize HR policies and produce weekly rollup report",
            "context": {"category": "HR", "days_back": 14},
        }
        resp = self.client.post("/api/v1/assistant/task", json=payload, headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]

        assert data["workflow_id"] is not None
        assert data["title"] == "Quarterly Document Rollup"
        assert data["total_steps"] >= 1
        assert len(data["steps"]) >= 1

    def test_04_get_conversation_history(self):
        """Tests retrieving conversation history sessions."""
        resp = self.client.get("/api/v1/assistant/history", headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]

        assert "sessions" in data
        assert "total" in data
        assert isinstance(data["sessions"], list)

    def test_05_generate_report(self):
        """Tests automated structured report compilation and storage."""
        payload = {
            "report_type": "WEEKLY_ROLLUP",
            "title": "Engineering Knowledge Base Weekly Rollup",
            "format": "MARKDOWN",
            "filters": {"days_back": 7},
        }
        resp = self.client.post("/api/v1/assistant/report", json=payload, headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]

        assert data["report_id"] is not None
        assert data["report_type"] == "WEEKLY_ROLLUP"
        assert data["title"] == "Engineering Knowledge Base Weekly Rollup"
        assert "# Engineering Knowledge Base Weekly Rollup" in data["content"]

    def test_06_list_workflows(self):
        """Tests listing tenant assistant workflow execution history."""
        resp = self.client.get("/api/v1/assistant/workflows", headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]

        assert "workflows" in data
        assert "total" in data
        assert len(data["workflows"]) >= 1

    def test_07_approve_action(self):
        """Tests Human-in-the-Loop decision execution for sensitive actions."""
        approval_id = uuid4()
        wf_id = uuid4()

        # Seed pending approval record directly
        with Session(sync_test_engine) as session:
            wf = AssistantWorkflow(
                id=wf_id,
                organization_id=self.org_id,
                user_id=self.user_id,
                title="Pending Invite Task",
                status="WAITING_APPROVAL",
                current_step=0,
                total_steps=1,
            )
            session.add(wf)

            appr = AssistantApproval(
                id=approval_id,
                organization_id=self.org_id,
                user_id=self.user_id,
                workflow_id=wf_id,
                action_type="UserTool",
                description="Invite user",
                payload_json={"email": "alice@test.com"},
                status="PENDING",
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
            session.add(appr)
            session.commit()

        payload = {
            "approval_id": str(approval_id),
            "decision": "APPROVED",
            "reason": "Approved by verified admin",
        }
        resp = self.client.post("/api/v1/assistant/approve", json=payload, headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]

        assert data["approval_id"] == str(approval_id)
        assert data["decision"] == "APPROVED"
        assert data["status"] == "COMPLETED"

    def test_08_get_recommendations(self):
        """Tests proactive knowledge and workspace recommendations."""
        resp = self.client.get("/api/v1/assistant/recommendations", headers=self.auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]

        assert "recommendations" in data
        assert len(data["recommendations"]) == 4
        categories = [r["category"] for r in data["recommendations"]]
        assert "FREQUENT_DOCUMENTS" in categories
        assert "MISSING_DOCUMENTATION" in categories
