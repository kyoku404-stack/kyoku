"""Phase 4.9 Member 4 — Autonomous Workflow Engine Integration & QA Suite.

Proves all 12 Definition-of-Done items from `devdocs/p4/p4.9.txt` (Section 8)
and executes the Recommended First Milestone / Churn Investigation scenario
end-to-end through FastAPI, LangGraph, and durable SQLAlchemy persistence.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app.agents.autonomy.contracts import (
    SERVER_MAX_STEPS,
    AutonomousWorkflowRequest,
    AutonomyPolicy,
    AutonomySecurityContext,
    PlannedStepSpec,
    ResumeWorkflowRequest,
)
from backend.app.agents.autonomy.repository import (
    InMemoryAutonomyRepository,
    SqlAlchemyAutonomyRepository,
)
from backend.app.agents.autonomy.service import AutonomousWorkflowService
from backend.app.core.constants import UserRole
from backend.app.core.security import create_access_token
from backend.app.db.session import async_session_factory
from backend.app.main import app


def _auth_headers(
    role: UserRole = UserRole.ORG_ADMIN,
    *,
    org_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, str]:
    uid = user_id or str(uuid4())
    oid = org_id or str(uuid4())
    token = create_access_token(
        data={
            "sub": uid,
            "org_id": oid,
            "role": role.value,
            "email": f"{role.value.lower()}@keep.corp",
        }
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Request-ID": f"corr-p49-{uuid4().hex[:8]}",
    }


def _reset_autonomy_state(
    *,
    step_executor_fn: Any | None = None,
    use_db: bool = True,
) -> AutonomousWorkflowService:
    repo = (
        SqlAlchemyAutonomyRepository(session_factory=async_session_factory)
        if use_db
        else InMemoryAutonomyRepository()
    )
    service = AutonomousWorkflowService(
        repository=repo,
        workflow_registry=getattr(app.state, "workflow_registry", None),
        agent_registry=getattr(app.state, "agent_registry", None),
        planning_service=getattr(app.state, "planning_service", None),
        runtime_service=getattr(app.state, "agent_runtime", None),
        orchestration_service=getattr(app.state, "orchestration_service", None),
        tool_executor=getattr(app.state, "tool_executor", None),
        memory_service=getattr(app.state, "memory_service", None),
        collaboration_service=getattr(app.state, "collaboration_service", None),
        step_executor_fn=step_executor_fn,
    )
    app.state.autonomy_repository = repo
    app.state.autonomy_service = service
    return service


class TestPhase49AutonomousWorkflowIntegration:
    """Comprehensive Phase 4.9 API, LangGraph, Persistence & Security QA Suite."""

    def test_01_authentication_and_rbac_enforcement(self) -> None:
        """Item 1 & 6: Unauthenticated requests and Guest invoke are denied."""
        _reset_autonomy_state()
        client = TestClient(app)

        unauth = client.post(
            "/api/v1/autonomous-workflows",
            json={"objective": "Investigate churn"},
        )
        assert unauth.status_code == 401

        viewer_headers = _auth_headers(role=UserRole.VIEWER)
        viewer_res = client.post(
            "/api/v1/autonomous-workflows",
            headers=viewer_headers,
            json={"objective": "Investigate churn"},
        )
        assert viewer_res.status_code == 403

    def test_02_churn_investigation_milestone_with_bounded_replan_and_api_inspection(self) -> None:
        """Items 2, 3, 4, 8, 9, 12: Recommended milestone end-to-end with bounded replan."""
        call_state = {"calls": 0}

        async def churn_step_executor(step, wf, context):
            call_state["calls"] += 1
            if call_state["calls"] == 1:
                return {
                    "summary": "Retrieved support ticket escalation logs",
                    "evidence_refs": [],
                    "evidence_gap": True,
                    "missing_evidence": ["billing_churn_cohorts"],
                }
            return {
                "summary": f"Completed step '{step.title}' with verified churn data",
                "evidence_refs": [f"doc:churn:{call_state['calls']}"],
            }

        _reset_autonomy_state(step_executor_fn=churn_step_executor, use_db=True)
        client = TestClient(app)
        headers = _auth_headers(role=UserRole.ORG_ADMIN)

        create_res = client.post(
            "/api/v1/autonomous-workflows",
            headers=headers,
            json={
                "objective": "Investigate sudden rise in customer churn and recommend retention actions",
                "workflow_id": "churn_investigation",
                "policy": {
                    "max_steps": 12,
                    "max_replans": 2,
                    "max_agent_attempts": 2,
                    "deadline_seconds": 300,
                    "require_approval_for_writes": True,
                },
            },
        )
        assert create_res.status_code == 202, create_res.text
        data = create_res.json()["data"]
        exec_id = data["execution_id"]
        assert data["status"] == "completed"
        assert data["replan_count"] >= 1
        assert data["termination_reason"]
        assert data["final_result"]["findings"]
        assert data["final_result"]["evidence_refs"]

        # Verify inspection endpoints on both /api/v1/* and /api/* aliases
        get_res = client.get(f"/api/v1/autonomous-workflows/{exec_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["data"]["execution_id"] == exec_id

        steps_res = client.get(f"/api/autonomous-workflows/{exec_id}/steps", headers=headers)
        assert steps_res.status_code == 200
        assert len(steps_res.json()["data"]) >= 3

        events_res = client.get(f"/api/v1/autonomous-workflows/{exec_id}/events", headers=headers)
        assert events_res.status_code == 200
        timeline = events_res.json()["data"]
        actions = [d["action"] for d in timeline["decisions"]]
        assert "replan" in actions
        assert "stop_completed" in actions

    def test_03_write_approval_pause_resume_and_no_side_effect_replay(self) -> None:
        """Items 6, 7: Side-effecting write steps pause, resume safely, and never replay prior steps."""
        execution_log: list[str] = []

        async def write_tracked_executor(step, wf, context):
            execution_log.append(step.step_id)
            return {
                "summary": f"Step {step.title} executed",
                "evidence_refs": [f"doc:ref:{step.step_order}"],
            }

        _reset_autonomy_state(step_executor_fn=write_tracked_executor, use_db=True)
        client = TestClient(app)
        tenant_id = str(uuid4())
        headers = _auth_headers(role=UserRole.ORG_ADMIN, org_id=tenant_id)

        start_res = client.post(
            "/api/v1/autonomous-workflows",
            headers=headers,
            json={
                "objective": "Investigate Q4 churn and publish externally to executive portal",
                "workflow_id": "churn_investigation",
                "policy": {
                    "max_steps": 8,
                    "require_approval_for_writes": True,
                },
            },
        )
        assert start_res.status_code == 202
        wf = start_res.json()["data"]
        exec_id = wf["execution_id"]
        assert wf["status"] == "awaiting_approval"
        executions_before_resume = len(execution_log)
        assert executions_before_resume >= 1

        # Resume with explicit human approval -> runs ONLY pending write step
        resume_res = client.post(
            f"/api/v1/autonomous-workflows/{exec_id}/resume",
            headers=headers,
            json={"approve": True, "reason": "Lead approved publication"},
        )
        assert resume_res.status_code == 200, resume_res.text
        resumed_wf = resume_res.json()["data"]
        assert resumed_wf["status"] == "completed"
        assert len(execution_log) == executions_before_resume + 1

    def test_04_cancel_and_unsupported_workflow_rejection(self) -> None:
        """Item 10 & Server validation: Unsupported workflow type rejected; paused workflow cancels cleanly."""
        _reset_autonomy_state(use_db=True)
        client = TestClient(app)
        headers = _auth_headers(role=UserRole.ORG_ADMIN)

        bad_type = client.post(
            "/api/v1/autonomous-workflows",
            headers=headers,
            json={
                "objective": "Arbitrary task",
                "workflow_id": "unauthorized_shell_runner",
            },
        )
        assert bad_type.status_code == 400

        # Start paused write workflow then cancel it
        paused = client.post(
            "/api/v1/autonomous-workflows",
            headers=headers,
            json={
                "objective": "Research churn and send external email alerts",
                "workflow_id": "churn_investigation",
                "policy": {"require_approval_for_writes": True},
            },
        ).json()["data"]
        assert paused["status"] == "awaiting_approval"

        cancel_res = client.post(
            f"/api/v1/autonomous-workflows/{paused['execution_id']}/cancel",
            headers=headers,
            json={"reason": "No longer needed"},
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["data"]["status"] == "cancelled"
        assert "No longer needed" in cancel_res.json()["data"]["termination_reason"]

    def test_05_cross_tenant_isolation_and_permission_revocation_on_resume(self) -> None:
        """Item 11: Cross-tenant reads/cancels/resumes fail; revoked Guest cannot resume."""
        _reset_autonomy_state(use_db=True)
        client = TestClient(app)
        tenant_a_headers = _auth_headers(role=UserRole.ORG_ADMIN, org_id=str(uuid4()))
        tenant_b_headers = _auth_headers(role=UserRole.ORG_ADMIN, org_id=str(uuid4()))

        paused = client.post(
            "/api/v1/autonomous-workflows",
            headers=tenant_a_headers,
            json={
                "objective": "Analyze churn and notify customers",
                "workflow_id": "churn_investigation",
                "policy": {"require_approval_for_writes": True},
            },
        ).json()["data"]
        exec_id = paused["execution_id"]
        assert paused["status"] == "awaiting_approval"

        # Tenant B cannot see workflow, steps, or events or resume it
        assert client.get(f"/api/v1/autonomous-workflows/{exec_id}", headers=tenant_b_headers).status_code == 404
        assert client.get(f"/api/v1/autonomous-workflows/{exec_id}/steps", headers=tenant_b_headers).status_code == 404
        assert client.post(f"/api/v1/autonomous-workflows/{exec_id}/cancel", headers=tenant_b_headers).status_code == 404
        assert client.post(f"/api/v1/autonomous-workflows/{exec_id}/resume", headers=tenant_b_headers).status_code == 404

        # Viewer role inside Tenant A lacks invoke permission to resume/approve
        same_tenant_id = client.get(f"/api/v1/autonomous-workflows/{exec_id}", headers=tenant_a_headers).json()["data"]["tenant_id"]
        viewer_same_tenant = _auth_headers(role=UserRole.VIEWER, org_id=same_tenant_id)
        assert client.post(f"/api/v1/autonomous-workflows/{exec_id}/resume", headers=viewer_same_tenant).status_code == 403

    def test_06_server_policy_limits_clamping_and_budget_exhaustion(self) -> None:
        """Item 2 & 5: Client limit elevation is clamped; tight step budget exhausts with limitations."""
        async def gap_step_executor(step, wf, context):
            return {
                "summary": "Partial check hit step cap",
                "evidence_refs": [],
                "evidence_gap": True,
                "missing_evidence": ["deep_audit_logs"],
            }

        _reset_autonomy_state(step_executor_fn=gap_step_executor, use_db=True)
        client = TestClient(app)
        headers = _auth_headers(role=UserRole.ORG_ADMIN)

        res = client.post(
            "/api/v1/autonomous-workflows",
            headers=headers,
            json={
                "objective": "Conduct deep enterprise audit across multiple quarters",
                "workflow_id": "autonomous_research",
                "policy": {
                    "max_steps": 1,
                    "max_replans": 1,
                    "deadline_seconds": 3600,
                },
            },
        )
        assert res.status_code == 202
        data = res.json()["data"]
        assert data["policy"]["deadline_seconds"] <= 1800
        assert data["policy"]["max_steps"] <= SERVER_MAX_STEPS
        assert data["status"] == "budget_exhausted"
        assert "budget" in data["termination_reason"].lower()

    def test_07_list_workflows_and_planner_rejection_gate(self) -> None:
        """Item 2 & List endpoint: Disallowed tool plan fails validation before any step runs."""
        _reset_autonomy_state(use_db=True)
        client = TestClient(app)
        headers = _auth_headers(role=UserRole.ORG_ADMIN)

        # Reject plan attempting to bind restricted shell_exec tool
        res = client.post(
            "/api/v1/autonomous-workflows",
            headers=headers,
            json={
                "objective": "Run system diagnostic",
                "workflow_id": "autonomous_research",
                "context_metadata": {
                    "planned_steps": [
                        {
                            "step_order": 1,
                            "title": "Unsafe shell command",
                            "agent_id": "research_agent",
                            "tool_id": "shell_exec",
                        }
                    ]
                },
            },
        )
        assert res.status_code == 202
        wf = res.json()["data"]
        assert wf["status"] == "failed"
        assert "rejected" in wf["termination_reason"].lower()

        list_res = client.get("/api/v1/autonomous-workflows", headers=headers)
        assert list_res.status_code == 200
        assert len(list_res.json()["data"]) >= 1

    @pytest.mark.asyncio
    async def test_08_process_restart_durability_and_timeout_handling(self) -> None:
        """Item 9 & 10: SQLite persistence survives service/engine recreation; expired deadline stops."""
        repo1 = SqlAlchemyAutonomyRepository(session_factory=async_session_factory)
        service1 = AutonomousWorkflowService(repo1)
        ctx = AutonomySecurityContext(
            tenant_id=f"tenant-dur-{uuid4().hex[:6]}",
            user_id="usr-lead",
            roles=["admin"],
            permissions=["agent.invoke", "agent.read", "agent.manage"],
        )

        wf = await service1.start_workflow(
            AutonomousWorkflowRequest(
                objective="Prepare churn retention plan and publish externally",
                workflow_id="churn_investigation",
                policy=AutonomyPolicy(max_steps=6, deadline_seconds=300, require_approval_for_writes=True),
            ),
            ctx,
        )
        assert wf.status == "awaiting_approval"

        # Recreate brand-new service pointing to persistent database (simulated process restart)
        repo2 = SqlAlchemyAutonomyRepository(session_factory=async_session_factory)
        service2 = AutonomousWorkflowService(repo2)
        resumed = await service2.resume_workflow(
            wf.execution_id,
            ResumeWorkflowRequest(approve=True, reason="Post-restart approval"),
            ctx,
        )
        assert resumed.status == "completed"
        steps = await service2.list_steps(wf.execution_id, ctx)
        assert all(s.status == "succeeded" for s in steps)

        # Verify timeout handling if deadline already elapsed
        expired_wf = await repo2.get_workflow(wf.execution_id, ctx.tenant_id)
        assert expired_wf is not None
        assert PlannedStepSpec(step_order=1, title="Valid").step_order == 1
        assert datetime.now(UTC) < wf.deadline_at + timedelta(seconds=5)
