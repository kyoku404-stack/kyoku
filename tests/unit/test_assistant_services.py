"""Unit tests for Phase 2.3 Assistant Backend Service.

Owner: Member 2 (Backend & Database Lead)
Domain: /tests/unit
Specification: devdocs/p2/p2.3.txt
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.app.models.assistant import AssistantApproval, AssistantWorkflow
from backend.app.schemas.assistant import (
    ApprovalActionRequest,
    AssistantChatRequest,
    ReportGenerateRequest,
    TaskExecuteRequest,
)
from backend.app.services.assistant.service import AssistantService


@pytest.fixture
def mock_db() -> AsyncMock:
    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_res.scalar.return_value = 10
    mock_res.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_res
    return db


class TestAssistantServiceUnit:
    """Unit test suite for AssistantService core orchestration workflows."""

    @pytest.mark.asyncio
    async def test_chat_knowledge_query(self, mock_db: AsyncMock):
        service = AssistantService()
        user_id = uuid4()
        org_id = uuid4()

        req = AssistantChatRequest(
            message="What is our employee parental leave policy?",
            session_id=None,
        )

        res = await service.chat(
            db=mock_db,
            user_id=user_id,
            organization_id=org_id,
            payload=req,
        )

        assert res.session_id is not None
        assert res.reply is not None
        assert res.detected_intent == "KNOWLEDGE_QA"
        assert res.requires_approval is False
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_chat_action_approval_gating(self, mock_db: AsyncMock):
        service = AssistantService()
        user_id = uuid4()
        org_id = uuid4()

        req = AssistantChatRequest(
            message="Invite new user alex@company.com with role admin",
            session_id=None,
        )

        res = await service.chat(
            db=mock_db,
            user_id=user_id,
            organization_id=org_id,
            payload=req,
        )

        assert res.requires_approval is True
        assert res.approval_id is not None
        assert "explicit approval is required" in res.reply

    @pytest.mark.asyncio
    async def test_execute_task(self, mock_db: AsyncMock):
        service = AssistantService()
        user_id = uuid4()
        org_id = uuid4()

        req = TaskExecuteRequest(
            title="HR Policy Rollup",
            instructions="Summarize HR policy documents and report metrics",
            context={"days_back": 14},
        )

        res = await service.execute_task(
            db=mock_db,
            user_id=user_id,
            organization_id=org_id,
            payload=req,
        )

        assert res.workflow_id is not None
        assert res.title == "HR Policy Rollup"
        assert res.total_steps == 3
        assert len(res.steps) == 3

    @pytest.mark.asyncio
    async def test_generate_report(self, mock_db: AsyncMock):
        service = AssistantService()
        user_id = uuid4()
        org_id = uuid4()

        req = ReportGenerateRequest(
            report_type="WEEKLY_ROLLUP",
            title="Weekly Operations Summary",
            format="MARKDOWN",
            filters={"category": "OPERATIONS"},
        )

        report = await service.generate_report(
            db=mock_db,
            user_id=user_id,
            organization_id=org_id,
            payload=req,
        )

        assert report.title == "Weekly Operations Summary"
        assert report.format == "MARKDOWN"
        assert "# Weekly Operations Summary" in report.content

    @pytest.mark.asyncio
    async def test_process_approval_approved(self, mock_db: AsyncMock):
        service = AssistantService()
        user_id = uuid4()
        org_id = uuid4()
        approval_id = uuid4()
        workflow_id = uuid4()

        mock_approval = AssistantApproval(
            id=approval_id,
            organization_id=org_id,
            user_id=user_id,
            workflow_id=workflow_id,
            action_type="UserTool",
            description="Invite user",
            status="PENDING",
            expires_at=None,
        )
        mock_wf = AssistantWorkflow(
            id=workflow_id,
            organization_id=org_id,
            user_id=user_id,
            title="Task",
            status="WAITING_APPROVAL",
        )

        # Mock execute returning approval and workflow
        mock_exec_res = MagicMock()
        mock_exec_res.scalar_one_or_none.side_effect = [mock_approval, mock_wf, None]
        mock_db.execute.return_value = mock_exec_res

        req = ApprovalActionRequest(
            approval_id=approval_id,
            decision="APPROVED",
            reason="Approved by HR Admin",
        )

        res = await service.process_approval(
            db=mock_db,
            user_id=user_id,
            organization_id=org_id,
            payload=req,
        )

        assert res["decision"] == "APPROVED"
        assert res["status"] == "COMPLETED"
        assert mock_approval.status == "APPROVED"
        assert mock_wf.status == "COMPLETED"

    @pytest.mark.asyncio
    async def test_get_recommendations(self, mock_db: AsyncMock):
        service = AssistantService()
        org_id = uuid4()

        recs = await service.get_recommendations(
            db=mock_db,
            organization_id=org_id,
        )

        assert len(recs) == 4
        assert recs[0].category.value == "FREQUENT_DOCUMENTS"
