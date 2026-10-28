"""Unit tests for Phase 3.4 EnterpriseWorkflowService business logic.

Owner: Member 2 (Backend & Database Lead)
Domain: /backend/app/services/workflow/
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.schemas.workflow import (
    NotificationPreferenceItem,
    WorkflowApprovalRequest,
    WorkflowCreateRequest,
    WorkflowExecuteRequest,
    WorkflowStepCreate,
)
from backend.app.services.workflow.contracts import (
    ApprovalStatus,
    WorkflowExecutionStatus,
    WorkflowStepAction,
    WorkflowTriggerType,
)
from backend.app.services.workflow.service import EnterpriseWorkflowService


class TestEnterpriseWorkflowServiceUnit:
    """Unit test suite for EnterpriseWorkflowService orchestrator."""

    @pytest.mark.asyncio
    async def test_create_workflow_logic(self) -> None:
        """Verifies creating a workflow and registering DAG steps."""
        db = AsyncMock()
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()

        payload = WorkflowCreateRequest(
            name="Document Classification & Review",
            description="Auto-summarize and notify reviewer",
            trigger_type=WorkflowTriggerType.EVENT.value,
            event_pattern="document.uploaded",
            condition_rules={"field": "category", "operator": "equals", "value": "POLICY"},
            is_active=True,
            steps=[
                WorkflowStepCreate(
                    step_order=1,
                    action_type=WorkflowStepAction.AI_SUMMARIZE.value,
                    configuration={"max_sentences": 3},
                ),
                WorkflowStepCreate(
                    step_order=2,
                    action_type=WorkflowStepAction.NOTIFY.value,
                    configuration={"channel": "IN_APP", "priority": "HIGH"},
                ),
            ],
        )

        wf_res = await EnterpriseWorkflowService.create_workflow(db, org_id, user_id, payload)
        assert wf_res.name == "Document Classification & Review"
        assert wf_res.trigger_type == "EVENT"
        assert wf_res.step_count == 2
        assert wf_res.is_active is True
        assert db.commit.called

    @pytest.mark.asyncio
    async def test_list_workflows_with_filters(self) -> None:
        """Verifies listing workflows with active/trigger filters."""
        db = AsyncMock()
        org_id = uuid.uuid4()

        mock_wf = MagicMock()
        mock_wf.id = uuid.uuid4()
        mock_wf.name = "Policy Ingestion"
        mock_wf.description = "Auto summary"
        mock_wf.trigger_type = "EVENT"
        mock_wf.event_pattern = "document.*"
        mock_wf.cron_expression = None
        mock_wf.condition_rules = {}
        mock_wf.is_active = True
        mock_wf.created_at = MagicMock(isoformat=lambda: "2026-10-29T10:00:00Z")

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_wf]
        mock_res = MagicMock()
        mock_res.scalars.return_value = mock_scalars

        mock_count_res = MagicMock()
        mock_count_res.scalar.return_value = 2

        db.execute.side_effect = [mock_res, mock_count_res]

        items = await EnterpriseWorkflowService.list_workflows(db, org_id, is_active=True)
        assert len(items) == 1
        assert items[0].name == "Policy Ingestion"
        assert items[0].step_count == 2

    @pytest.mark.asyncio
    async def test_execute_workflow_lifecycle(self) -> None:
        """Verifies workflow execution, AI action dispatch, and state resolution."""
        db = AsyncMock()
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()
        wf_id = uuid.uuid4()

        mock_wf = MagicMock()
        mock_wf.id = wf_id
        mock_wf.name = "Automated Document Digest"

        mock_step1 = MagicMock()
        mock_step1.id = uuid.uuid4()
        mock_step1.step_order = 1
        mock_step1.action_type = WorkflowStepAction.AI_SUMMARIZE.value
        mock_step1.configuration = {"max_sentences": 2}

        mock_step2 = MagicMock()
        mock_step2.id = uuid.uuid4()
        mock_step2.step_order = 2
        mock_step2.action_type = WorkflowStepAction.NOTIFY.value
        mock_step2.configuration = {"channel": "IN_APP", "priority": "NORMAL"}

        mock_wf_res = MagicMock()
        mock_wf_res.scalar_one_or_none.return_value = mock_wf

        mock_steps_scalars = MagicMock()
        mock_steps_scalars.all.return_value = [mock_step1, mock_step2]
        mock_steps_res = MagicMock()
        mock_steps_res.scalars.return_value = mock_steps_scalars

        db.execute.side_effect = [mock_wf_res, mock_steps_res]

        payload = WorkflowExecuteRequest(
            workflow_id=str(wf_id),
            input_payload={"title": "Q3 Financial Plan", "content": "Company performance remains strong."},
        )

        exec_res = await EnterpriseWorkflowService.execute_workflow(db, org_id, user_id, payload)
        assert exec_res.execution_id is not None
        assert exec_res.status == WorkflowExecutionStatus.COMPLETED.value
        assert db.commit.called

    @pytest.mark.asyncio
    async def test_approval_decision_submission(self) -> None:
        """Verifies human-in-the-loop approval decision updates ticket and resumes execution."""
        db = AsyncMock()
        org_id = uuid.uuid4()
        approver_id = uuid.uuid4()
        approval_id = uuid.uuid4()
        execution_id = uuid.uuid4()

        mock_approval = MagicMock()
        mock_approval.id = approval_id
        mock_approval.execution_id = execution_id
        mock_approval.status = ApprovalStatus.PENDING.value
        mock_approval.requested_at = MagicMock(isoformat=lambda: "2026-10-29T10:00:00Z")
        mock_approval.responded_at = None

        mock_exec = MagicMock()
        mock_exec.id = execution_id
        mock_exec.status = WorkflowExecutionStatus.WAITING_APPROVAL.value

        mock_appr_res = MagicMock()
        mock_appr_res.scalar_one_or_none.return_value = mock_approval

        mock_exec_res = MagicMock()
        mock_exec_res.scalar_one_or_none.return_value = mock_exec

        db.execute.side_effect = [mock_appr_res, mock_exec_res]

        payload = WorkflowApprovalRequest(
            approval_id=str(approval_id),
            decision="APPROVE",
            comments="Approved by Security Lead",
        )

        appr_res = await EnterpriseWorkflowService.submit_approval_decision(db, org_id, approver_id, payload)
        assert appr_res.status == ApprovalStatus.APPROVED.value
        assert mock_exec.status == WorkflowExecutionStatus.COMPLETED.value
        assert db.commit.called

    @pytest.mark.asyncio
    async def test_notification_preferences_get_and_update(self) -> None:
        """Verifies querying default preferences and persisting user updates."""
        db = AsyncMock()
        user_id = uuid.uuid4()

        # Query defaults when DB returns empty
        mock_empty_scalars = MagicMock()
        mock_empty_scalars.all.return_value = []
        mock_empty_res = MagicMock()
        mock_empty_res.scalars.return_value = mock_empty_scalars
        db.execute.return_value = mock_empty_res

        default_prefs = await EnterpriseWorkflowService.get_notification_preferences(db, user_id)
        assert len(default_prefs) >= 4

        # Update preferences
        update_payload = [
            NotificationPreferenceItem(channel="SLACK", category="APPROVAL", is_enabled=True),
            NotificationPreferenceItem(channel="EMAIL", category="WORKFLOW", is_enabled=False),
        ]
        # Existing checks return None
        mock_none_res = MagicMock()
        mock_none_res.scalar_one_or_none.return_value = None
        db.execute.side_effect = [mock_none_res, mock_none_res]

        res = await EnterpriseWorkflowService.update_notification_preferences(db, user_id, update_payload)
        assert res is True
        assert db.commit.called

    def test_workflow_templates_listing(self) -> None:
        """Verifies template catalog retrieval."""
        templates = EnterpriseWorkflowService.list_templates()
        assert len(templates) >= 4
        assert any(t.id == "tpl-doc-approval" for t in templates)
        assert any(t.category == "AI" for t in templates)

    @pytest.mark.asyncio
    async def test_workflow_analytics_kpis(self) -> None:
        """Verifies analytics computation and timeseries synthesis."""
        db = AsyncMock()
        org_id = uuid.uuid4()

        # Count queries: total, failed, pending, notif
        res1 = MagicMock(scalar=lambda: 50)
        res2 = MagicMock(scalar=lambda: 2)
        res3 = MagicMock(scalar=lambda: 3)
        res4 = MagicMock(scalar=lambda: 120)

        db.execute.side_effect = [res1, res2, res3, res4]

        analytics = await EnterpriseWorkflowService.get_workflow_analytics(db, org_id, days=7)
        assert analytics.total_workflows_executed >= 50
        assert analytics.success_rate > 90.0
        assert analytics.failed_workflows == 2
        assert analytics.pending_approvals == 3
        assert len(analytics.executions_by_day) == 8
