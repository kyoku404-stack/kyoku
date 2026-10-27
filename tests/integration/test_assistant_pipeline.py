"""Integration and Performance Benchmark Test Suite for KEEP AI Assistant & Workflows (Phase 2.3).

Verifies the end-to-end Agentic Workflow architecture across:
1. Multi-tenant isolation and session quarantine boundaries
2. DAG task planning, dependency resolution, and step execution
3. Dynamic tool registry invocation across categories
4. Two-phase commit Human-in-the-Loop (HITL) approval / rejection lifecycle
5. Multi-turn conversational memory with tool execution history
6. Automated report synthesis across organization knowledge bases
7. Proactive recommendation generation and relevance scoring
8. Task execution performance benchmark against < 3000ms SLA

Specification: devdocs/p2/p2.3.txt Chapters 1-20 & docs/Architecture/ai-assistant-agentic-workflows.md
Author: Member 4 (Integration & DevOps Lead)
"""

import time
import unittest
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.assistant import AssistantApproval, AssistantWorkflow
from backend.app.models.organization import Organization
from backend.app.models.user import User
from tests.conftest import sync_test_engine


class TestAssistantPipelineIntegration(unittest.TestCase):
    """End-to-end integration and security benchmark suite for Phase 2.3 AI Assistant."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Primary Tenant Organization Alpha
            cls.org_alpha = Organization(
                name="Assistant Alpha Tenant",
                domain=f"alpha-{uuid4().hex[:6]}.com",
            )
            # 2. Secondary Tenant Organization Beta (Cross-tenant boundary quarantine)
            cls.org_beta = Organization(
                name="Assistant Beta Tenant",
                domain=f"beta-{uuid4().hex[:6]}.com",
            )
            session.add_all([cls.org_alpha, cls.org_beta])
            session.commit()
            session.refresh(cls.org_alpha)
            session.refresh(cls.org_beta)

            cls.org_alpha_id = cls.org_alpha.id
            cls.org_beta_id = cls.org_beta.id

            # 3. Users for each organization
            cls.user_alpha = User(
                email=f"alice-{uuid4().hex[:6]}@alpha.com",
                hashed_password=get_password_hash("AlphaPass123!"),
                full_name="Alice Alpha Lead",
                role="OrgAdmin",
                organization_id=cls.org_alpha_id,
                is_active=True,
            )
            cls.user_beta = User(
                email=f"bob-{uuid4().hex[:6]}@beta.com",
                hashed_password=get_password_hash("BetaPass123!"),
                full_name="Bob Beta Member",
                role="Member",
                organization_id=cls.org_beta_id,
                is_active=True,
            )
            session.add_all([cls.user_alpha, cls.user_beta])
            session.commit()
            session.refresh(cls.user_alpha)
            session.refresh(cls.user_beta)

            cls.user_alpha_id = cls.user_alpha.id
            cls.user_alpha_email = cls.user_alpha.email
            cls.user_beta_id = cls.user_beta.id
            cls.user_beta_email = cls.user_beta.email

        # 4. Auth tokens
        cls.token_alpha = create_access_token(
            data={"sub": str(cls.user_alpha_id), "email": cls.user_alpha_email, "org_id": str(cls.org_alpha_id), "role": "OrgAdmin"}
        )
        cls.token_beta = create_access_token(
            data={"sub": str(cls.user_beta_id), "email": cls.user_beta_email, "org_id": str(cls.org_beta_id), "role": "Member"}
        )

        cls.headers_alpha = {"Authorization": f"Bearer {cls.token_alpha}"}
        cls.headers_beta = {"Authorization": f"Bearer {cls.token_beta}"}

    def test_01_conversational_chat_and_session_history(self) -> None:
        """Verify chat intent classification, multi-turn memory, and tool invocation chips."""
        # Turn 1: Knowledge query intent
        payload1 = {
            "message": "What is our company annual leave policy?",
            "session_id": None,
        }
        res1 = self.client.post("/api/v1/assistant/chat", json=payload1, headers=self.headers_alpha)
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()["data"]
        self.assertIn("reply", data1)
        self.assertEqual(data1["detected_intent"], "KNOWLEDGE_QA")
        self.assertGreater(len(data1["tools_executed"]), 0)
        session_id = data1["session_id"]
        self.assertIsNotNone(session_id)

        # Turn 2: Destructive action triggering HITL approval
        payload2 = {
            "message": "Invite user bob@company.com with role admin",
            "session_id": session_id,
        }
        res2 = self.client.post("/api/v1/assistant/chat", json=payload2, headers=self.headers_alpha)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()["data"]
        self.assertTrue(data2["requires_approval"])
        self.assertIsNotNone(data2["approval_id"])

        # Verify session history retrieval
        hist_res = self.client.get("/api/v1/assistant/history", headers=self.headers_alpha)
        self.assertEqual(hist_res.status_code, 200)
        history = hist_res.json()["data"]
        self.assertIn("sessions", history)
        self.assertGreaterEqual(history["total"], 1)

    def test_02_dag_task_execution_and_performance_benchmark(self) -> None:
        """Verify multi-step DAG task execution, dependency resolution, and < 3s latency SLA."""
        start_time = time.perf_counter()

        payload = {
            "title": "Pipeline Security Audit & Rollup",
            "instructions": "Audit document access policies, summarize findings, and compile weekly rollup",
            "context": {"priority": "HIGH", "category": "COMPLIANCE"},
        }
        response = self.client.post("/api/v1/assistant/task", json=payload, headers=self.headers_alpha)
        duration = time.perf_counter() - start_time

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertIn("workflow_id", data)
        self.assertEqual(data["status"], "COMPLETED")
        self.assertGreaterEqual(len(data["steps"]), 1)

        # Performance SLA check: DAG resolution and tool execution must complete in < 3.0s
        self.assertLess(duration, 3.0, f"Task execution took {duration:.3f}s, exceeding 3.0s SLA target")

    def test_03_hitl_approval_commit_flow(self) -> None:
        """Verify Two-Phase Commit HITL workflow: approving an action."""
        approval_id = uuid4()
        wf_id = uuid4()

        with Session(sync_test_engine) as session:
            wf = AssistantWorkflow(
                id=wf_id,
                organization_id=self.org_alpha_id,
                user_id=self.user_alpha_id,
                title="Alpha Protected Task",
                status="WAITING_APPROVAL",
                current_step=0,
                total_steps=1,
            )
            session.add(wf)

            expires_at = datetime.now(UTC) + timedelta(days=2)
            appr = AssistantApproval(
                id=approval_id,
                organization_id=self.org_alpha_id,
                user_id=self.user_alpha_id,
                workflow_id=wf_id,
                action_type="UserTool",
                description="Invite user",
                payload_json={"email": "contractor@alpha.com"},
                expires_at=expires_at,
                status="PENDING",
            )
            session.add(appr)
            session.commit()

        # Approve decision
        approve_payload = {
            "approval_id": str(approval_id),
            "decision": "APPROVED",
            "comments": "Authorized by security officer.",
        }
        approve_res = self.client.post("/api/v1/assistant/approve", json=approve_payload, headers=self.headers_alpha)
        self.assertEqual(approve_res.status_code, 200)
        approve_data = approve_res.json()["data"]
        self.assertEqual(approve_data["decision"], "APPROVED")
        self.assertEqual(approve_data["status"], "COMPLETED")

    def test_04_hitl_approval_reject_flow(self) -> None:
        """Verify HITL rejection transitions workflow and approval state to REJECTED."""
        approval_id = uuid4()
        wf_id = uuid4()

        with Session(sync_test_engine) as session:
            wf = AssistantWorkflow(
                id=wf_id,
                organization_id=self.org_alpha_id,
                user_id=self.user_alpha_id,
                title="Sensitive Action Task",
                status="WAITING_APPROVAL",
                current_step=0,
                total_steps=1,
            )
            session.add(wf)

            expires_at = datetime.now(UTC) + timedelta(days=2)
            appr = AssistantApproval(
                id=approval_id,
                organization_id=self.org_alpha_id,
                user_id=self.user_alpha_id,
                workflow_id=wf_id,
                action_type="UserTool",
                description="Elevate user permissions",
                payload_json={"email": "contractor@alpha.com"},
                expires_at=expires_at,
                status="PENDING",
            )
            session.add(appr)
            session.commit()

        # Reject decision
        reject_payload = {
            "approval_id": str(approval_id),
            "decision": "REJECTED",
            "comments": "Policy violation.",
        }
        reject_res = self.client.post("/api/v1/assistant/approve", json=reject_payload, headers=self.headers_alpha)
        self.assertEqual(reject_res.status_code, 200)
        reject_data = reject_res.json()["data"]
        self.assertEqual(reject_data["decision"], "REJECTED")
        self.assertEqual(reject_data["status"], "COMPLETED")

    def test_05_automated_report_synthesis(self) -> None:
        """Verify report generation across different types and markdown formatting."""
        report_payload = {
            "report_type": "WEEKLY_ROLLUP",
            "title": "Alpha Operations Weekly Rollup Brief",
            "format": "MARKDOWN",
        }
        res = self.client.post("/api/v1/assistant/report", json=report_payload, headers=self.headers_alpha)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertIn("report_id", data)
        self.assertEqual(data["title"], "Alpha Operations Weekly Rollup Brief")
        self.assertIn("# Alpha Operations Weekly Rollup Brief", data["content"])
        self.assertEqual(data["format"], "MARKDOWN")

    def test_06_proactive_recommendations(self) -> None:
        """Verify proactive recommendations generation and category taxonomy."""
        res = self.client.get("/api/v1/assistant/recommendations", headers=self.headers_alpha)
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        recs = data["recommendations"]
        self.assertIsInstance(recs, list)
        self.assertGreaterEqual(len(recs), 3)

        categories = {r["category"] for r in recs}
        self.assertIn("FREQUENT_DOCUMENTS", categories)
        self.assertIn("MISSING_DOCUMENTATION", categories)

    def test_07_tenant_boundary_quarantine_enforcement(self) -> None:
        """Verify strict tenant isolation: Tenant Beta cannot inspect or approve Tenant Alpha workflows."""
        approval_id = uuid4()
        wf_id = uuid4()

        with Session(sync_test_engine) as session:
            wf = AssistantWorkflow(
                id=wf_id,
                organization_id=self.org_alpha_id,
                user_id=self.user_alpha_id,
                title="Confidential Alpha Workflow",
                status="WAITING_APPROVAL",
                current_step=0,
                total_steps=1,
            )
            session.add(wf)

            expires_at = datetime.now(UTC) + timedelta(days=2)
            appr = AssistantApproval(
                id=approval_id,
                organization_id=self.org_alpha_id,
                user_id=self.user_alpha_id,
                workflow_id=wf_id,
                action_type="DocumentTool",
                description="Delete confidential documents",
                payload_json={},
                expires_at=expires_at,
                status="PENDING",
            )
            session.add(appr)
            session.commit()

        # Beta user attempts to approve Alpha's approval_id -> Expect 404 Not Found (tenant quarantine)
        hack_payload = {
            "approval_id": str(approval_id),
            "decision": "APPROVED",
            "comments": "Attempting cross-tenant privilege escalation",
        }
        hack_res = self.client.post("/api/v1/assistant/approve", json=hack_payload, headers=self.headers_beta)
        self.assertEqual(hack_res.status_code, 404)

        # Workflows listing for Beta must not include Alpha workflows
        beta_wf_res = self.client.get("/api/v1/assistant/workflows", headers=self.headers_beta)
        self.assertEqual(beta_wf_res.status_code, 200)
        beta_workflows = beta_wf_res.json()["data"]["workflows"]
        beta_wf_ids = [w["workflow_id"] for w in beta_workflows]
        self.assertNotIn(str(wf_id), beta_wf_ids)
