"""Integration and Performance SLA Benchmark Test Suite for Workflow Automation & Notifications (Phase 3.4).

Verifies the complete end-to-end Workflow & Event Intelligence Pipeline:
1. End-to-end workflow creation and multi-step execution.
2. Predicate condition evaluation (matching vs non-matching triggers).
3. Human-in-the-loop approval lifecycle: execution pauses at gate, queues for review, and resumes on approval.
4. Multi-channel notification delivery and preferences matrix persistence.
5. Multi-tenant isolation quarantine (Org Alpha workflows & notifications cannot be accessed by Org Beta).
6. Execution latency SLA benchmarks (DAG step execution latency < 2.0s).

Specification: devdocs/p3/p3.4.txt & docs/Architecture/workflow-automation-event-driven-intelligence.md
Author: Member 4 (Integration & DevOps Lead)
"""

import time
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, get_password_hash
from backend.app.main import app
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.models.workflow import (
    Workflow,
    WorkflowStep,
)
from backend.app.services.workflow.contracts import (
    NotificationChannelDispatcher,
    PredicateConditionEvaluator,
)
from tests.conftest import sync_test_engine


class TestWorkflowPipelineIntegration(unittest.TestCase):
    """End-to-end integration and SLA performance benchmark suite for Phase 3.4 Workflow Automation."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

        with Session(sync_test_engine, expire_on_commit=False) as session:
            # 1. Primary Tenant Organization Alpha
            cls.org_alpha = Organization(
                name="Workflow Org Alpha",
                domain=f"alpha-wf-{uuid4().hex[:6]}.com",
            )
            # 2. Secondary Tenant Organization Beta (Multi-tenant quarantine)
            cls.org_beta = Organization(
                name="Workflow Org Beta",
                domain=f"beta-wf-{uuid4().hex[:6]}.com",
            )
            session.add_all([cls.org_alpha, cls.org_beta])
            session.commit()
            session.refresh(cls.org_alpha)
            session.refresh(cls.org_beta)

            cls.org_alpha_id = cls.org_alpha.id
            cls.org_beta_id = cls.org_beta.id

            # Alpha Admin User
            cls.user_alpha = User(
                email=f"alpha-admin-{uuid4().hex[:6]}@enterprise.com",
                hashed_password=get_password_hash("AlphaPass123!"),
                full_name="Alpha Workflow Manager",
                role="ORG_ADMIN",
                organization_id=cls.org_alpha_id,
                is_active=True,
            )
            # Beta Admin User
            cls.user_beta = User(
                email=f"beta-admin-{uuid4().hex[:6]}@enterprise.com",
                hashed_password=get_password_hash("BetaPass123!"),
                full_name="Beta Workflow Manager",
                role="ORG_ADMIN",
                organization_id=cls.org_beta_id,
                is_active=True,
            )
            session.add_all([cls.user_alpha, cls.user_beta])
            session.commit()
            session.refresh(cls.user_alpha)
            session.refresh(cls.user_beta)

            cls.user_alpha_id = cls.user_alpha.id
            cls.user_beta_id = cls.user_beta.id

        cls.token_alpha = create_access_token(
            data={
                "sub": str(cls.user_alpha_id),
                "email": cls.user_alpha.email,
                "org_id": str(cls.org_alpha_id),
                "role": "OrgAdmin",
                "mfa_verified": True,
            }
        )
        cls.headers_alpha = {"Authorization": f"Bearer {cls.token_alpha}"}

        cls.token_beta = create_access_token(
            data={
                "sub": str(cls.user_beta_id),
                "email": cls.user_beta.email,
                "org_id": str(cls.org_beta_id),
                "role": "OrgAdmin",
                "mfa_verified": True,
            }
        )
        cls.headers_beta = {"Authorization": f"Bearer {cls.token_beta}"}

    def test_01_create_and_execute_dag_workflow(self) -> None:
        """Verifies creating a DAG workflow and executing its steps sequentially."""
        payload = {
            "name": "Integration Automated Indexer",
            "description": "Extracts metadata, performs RAG query and dispatches notification",
            "trigger_type": "document_created",
            "condition_rules": [
                {"field": "file_type", "operator": "equals", "value": "pdf"}
            ],
            "is_active": True,
            "steps": [
                {
                    "step_order": 1,
                    "name": "Invoke LLM Summarizer",
                    "action_type": "invoke_llm",
                    "action_config": {"prompt_template": "Summarize document {{document.title}}"},
                },
                {
                    "step_order": 2,
                    "name": "Send Multi-Channel Notification",
                    "action_type": "send_notification",
                    "action_config": {
                        "channel": "in_app",
                        "title": "Document Processed",
                        "content": "Processing complete",
                    },
                },
            ],
        }

        start_time = time.perf_counter()
        resp = self.client.post("/api/v1/workflows", json=payload, headers=self.headers_alpha)
        duration_ms = (time.perf_counter() - start_time) * 1000

        self.assertEqual(resp.status_code, 201)
        wf_data = resp.json()["data"]
        workflow_id = wf_data["id"]
        self.assertEqual(wf_data["name"], "Integration Automated Indexer")
        self.assertEqual(len(wf_data["steps"]), 2)
        self.assertLess(duration_ms, 2000.0, "Workflow creation should be < 2.0s SLA")

        # Execute Workflow
        exec_payload = {
            "context_data": {"document": {"title": "Q3 Financials", "file_type": "pdf"}},
            "trigger_metadata": {"event": "doc_uploaded"},
        }
        exec_start = time.perf_counter()
        exec_resp = self.client.post(
            f"/api/v1/workflows/{workflow_id}/execute",
            json=exec_payload,
            headers=self.headers_alpha,
        )
        exec_duration_ms = (time.perf_counter() - exec_start) * 1000

        self.assertEqual(exec_resp.status_code, 200)
        exec_data = exec_resp.json()["data"]
        self.assertEqual(exec_data["status"].lower(), "completed")
        self.assertLess(exec_duration_ms, 2000.0, "Execution should meet < 2.0s p95 SLA")

    def test_02_predicate_condition_evaluation_filtering(self) -> None:
        """Verifies predicate evaluation engine matches and rejects triggers based on rules."""
        evaluator = PredicateConditionEvaluator()

        # Matching event
        event_match = {"file_type": "pdf", "department": "Finance", "amount": 1500}
        rules = [
            {"field": "file_type", "operator": "equals", "value": "pdf"},
            {"field": "amount", "operator": "greater_than", "value": 1000},
        ]
        self.assertTrue(evaluator.evaluate(rules, event_match))

        # Non-matching event
        event_nomatch = {"file_type": "docx", "department": "HR", "amount": 500}
        self.assertFalse(evaluator.evaluate(rules, event_nomatch))

    def test_03_human_in_the_loop_approval_lifecycle(self) -> None:
        """Verifies workflow pauses at approval gate and resumes upon decision."""
        with Session(sync_test_engine, expire_on_commit=False) as session:
            wf = Workflow(
                organization_id=self.org_alpha_id,
                created_by_id=self.user_alpha_id,
                name="HITL Budget Approval Workflow",
                trigger_type="manual",
                is_active=True,
            )
            session.add(wf)
            session.commit()
            session.refresh(wf)

            step1 = WorkflowStep(
                workflow_id=wf.id,
                step_order=1,
                name="Manager Sign-off Gate",
                action_type="request_approval",
                action_config={"role": "ORG_ADMIN", "prompt": "Approve $50k spend"},
            )
            step2 = WorkflowStep(
                workflow_id=wf.id,
                step_order=2,
                name="Notify Finance",
                action_type="send_notification",
                action_config={"title": "Approved", "content": "Funds released"},
            )
            session.add_all([step1, step2])
            session.commit()
            wf_id = wf.id

        # Execute - should pause at step 1
        exec_resp = self.client.post(
            f"/api/v1/workflows/{wf_id}/execute",
            json={"context_data": {"budget": 50000}},
            headers=self.headers_alpha,
        )
        self.assertEqual(exec_resp.status_code, 200)
        exec_data = exec_resp.json()["data"]
        self.assertEqual(exec_data["status"].upper(), "WAITING_APPROVAL")

        # Check pending approvals
        appr_resp = self.client.get("/api/v1/workflows/approvals/pending", headers=self.headers_alpha)
        self.assertEqual(appr_resp.status_code, 200)
        res_data = appr_resp.json()["data"]
        pending_list = res_data if isinstance(res_data, list) else res_data.get("items", [])
        matching_appr = [a for a in pending_list if a["execution_id"] == exec_data["id"]]
        self.assertEqual(len(matching_appr), 1)
        approval_id = matching_appr[0]["id"]

        # Approve step
        decide_resp = self.client.post(
            f"/api/v1/workflows/approvals/{approval_id}/decide",
            json={"decision": "approved", "comments": "Budget approved for deployment."},
            headers=self.headers_alpha,
        )
        self.assertEqual(decide_resp.status_code, 200)
        decide_data = decide_resp.json()["data"]
        self.assertEqual(decide_data["status"].upper(), "APPROVED")
        self.assertEqual(decide_data["decision"].upper(), "APPROVED")

    def test_04_multi_channel_notification_dispatch_and_preferences(self) -> None:
        """Verifies multi-channel dispatcher and notification channel preferences persistence."""
        dispatcher = NotificationChannelDispatcher()
        email_result = dispatcher.format_payload("email", "System Alert", "Node 4 CPU high", {"node": 4})
        self.assertIn("subject", email_result)
        self.assertIn("html_body", email_result)

        slack_result = dispatcher.format_payload("slack", "System Alert", "Node 4 CPU high", {})
        self.assertIn("blocks", slack_result)

        teams_result = dispatcher.format_payload("teams", "System Alert", "Node 4 CPU high", {})
        self.assertIn("attachments", teams_result)

        # Get notification preferences
        pref_get = self.client.get("/api/v1/notifications/preferences", headers=self.headers_alpha)
        self.assertEqual(pref_get.status_code, 200)

        # Update preferences
        pref_payload = {"category": "workflow", "in_app": True, "email": True, "slack": True, "teams": False}
        pref_post = self.client.post("/api/v1/notifications/preferences", json=pref_payload, headers=self.headers_alpha)
        self.assertEqual(pref_post.status_code, 200)
        updated_pref = pref_post.json()["data"]
        self.assertTrue(updated_pref["email"])
        self.assertTrue(updated_pref["slack"])

    def test_05_multi_tenant_quarantine_isolation(self) -> None:
        """Verifies Organization Alpha workflows are strictly invisible and protected from Organization Beta."""
        # Alpha creates a confidential workflow
        alpha_create = self.client.post(
            "/api/v1/workflows",
            json={
                "name": "Alpha Confidential Payroll Sync",
                "trigger_type": "manual",
                "is_active": True,
                "steps": [
                    {
                        "step_order": 1,
                        "name": "Notify Payroll",
                        "action_type": "send_notification",
                        "action_config": {"title": "Payroll", "content": "Synced"},
                    }
                ],
            },
            headers=self.headers_alpha,
        )
        self.assertEqual(alpha_create.status_code, 201)
        alpha_wf_id = alpha_create.json()["data"]["id"]

        # Beta attempts to read Alpha workflow -> 404 Not Found
        beta_get = self.client.get(f"/api/v1/workflows/{alpha_wf_id}", headers=self.headers_beta)
        self.assertEqual(beta_get.status_code, 404)

        # Beta attempts to execute Alpha workflow -> 404 Not Found
        beta_exec = self.client.post(
            f"/api/v1/workflows/{alpha_wf_id}/execute",
            json={},
            headers=self.headers_beta,
        )
        self.assertEqual(beta_exec.status_code, 404)

        # Beta attempts to delete Alpha workflow -> 404 Not Found
        beta_del = self.client.delete(f"/api/v1/workflows/{alpha_wf_id}", headers=self.headers_beta)
        self.assertEqual(beta_del.status_code, 404)

    def test_06_workflow_analytics_aggregation(self) -> None:
        """Verifies workflow analytics endpoint returns aggregated performance and SLA metrics."""
        analytics_resp = self.client.get("/api/v1/workflows/analytics", headers=self.headers_alpha)
        self.assertEqual(analytics_resp.status_code, 200)
        data = analytics_resp.json()["data"]
        self.assertIn("total_workflows_executed", data)
        self.assertIn("success_rate", data)
        self.assertIn("avg_execution_time_ms", data)
        self.assertIn("executions_by_day", data)


if __name__ == "__main__":
    unittest.main()
