"""Unit tests for Phase 3.4 Workflow Automation, Notifications & Event-Driven Intelligence contracts.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/workflow/
"""

import pytest

from backend.app.services.ai.interfaces import (
    EMPLOYEE_PERMISSIONS,
    ORG_ADMIN_PERMISSIONS,
    PROJECT_MANAGER_PERMISSIONS,
    VIEWER_PERMISSIONS,
    AIPermission,
)
from backend.app.services.workflow.contracts import (
    AIWorkflowActionsEngine,
    EnterpriseEvent,
    EnterpriseEventBus,
    NotificationCategory,
    NotificationChannel,
    NotificationChannelDispatcher,
    NotificationPayload,
    NotificationPriority,
    PredicateConditionEvaluator,
    WorkflowTemplateRegistry,
)


class TestWorkflowContractsUnit:
    """Test suite for Phase 3.4 typed contracts, event bus, and AI engines."""

    def test_enterprise_event_envelope(self) -> None:
        """Verifies EnterpriseEvent creation, UUID generation, and serialization."""
        event = EnterpriseEvent(
            event_type="document.uploaded",
            source="storage_service",
            organization_id="org-123",
            actor_id="user-456",
            payload={"document_id": "doc-999", "title": "Security Policy.pdf"},
        )
        assert event.event_id is not None
        assert len(event.event_id) == 36
        assert event.event_type == "document.uploaded"
        assert event.payload["title"] == "Security Policy.pdf"

        event_dict = event.to_dict()
        assert event_dict["event_type"] == "document.uploaded"
        assert event_dict["source"] == "storage_service"
        assert event_dict["organization_id"] == "org-123"
        assert "timestamp" in event_dict

    def test_predicate_condition_evaluator_equals_and_not_equals(self) -> None:
        """Verifies equals and not_equals condition evaluations."""
        payload = {"department": "Legal", "priority": "HIGH", "file_size_mb": 15}

        # Equals
        assert PredicateConditionEvaluator.evaluate(
            {"field": "department", "operator": "equals", "value": "Legal"}, payload
        ) is True
        assert PredicateConditionEvaluator.evaluate(
            {"field": "department", "operator": "equals", "value": "Engineering"}, payload
        ) is False

        # Not equals
        assert PredicateConditionEvaluator.evaluate(
            {"field": "department", "operator": "not_equals", "value": "Engineering"}, payload
        ) is True
        assert PredicateConditionEvaluator.evaluate(
            {"field": "department", "operator": "not_equals", "value": "Legal"}, payload
        ) is False

        # Empty rules
        assert PredicateConditionEvaluator.evaluate({}, payload) is True

    def test_predicate_condition_evaluator_contains_and_in(self) -> None:
        """Verifies contains and in operators."""
        payload = {"filename": "annual_financial_audit_2026.pdf", "tags": ["finance", "confidential", "board"]}

        # String contains
        assert PredicateConditionEvaluator.evaluate(
            {"field": "filename", "operator": "contains", "value": "financial"}, payload
        ) is True
        assert PredicateConditionEvaluator.evaluate(
            {"field": "filename", "operator": "contains", "value": "marketing"}, payload
        ) is False

        # List contains
        assert PredicateConditionEvaluator.evaluate(
            {"field": "tags", "operator": "contains", "value": "confidential"}, payload
        ) is True

        # In list
        payload2 = {"region": "US"}
        assert PredicateConditionEvaluator.evaluate(
            {"field": "region", "operator": "in", "value": ["US", "EU", "APAC"]}, payload2
        ) is True
        assert PredicateConditionEvaluator.evaluate(
            {"field": "region", "operator": "in", "value": ["LATAM", "AFRICA"]}, payload2
        ) is False

    def test_predicate_condition_evaluator_comparisons(self) -> None:
        """Verifies greater_than and less_than operators."""
        payload = {"risk_score": 85, "threshold": 50}

        assert PredicateConditionEvaluator.evaluate(
            {"field": "risk_score", "operator": "greater_than", "value": 75}, payload
        ) is True
        assert PredicateConditionEvaluator.evaluate(
            {"field": "risk_score", "operator": "less_than", "value": 90}, payload
        ) is True
        assert PredicateConditionEvaluator.evaluate(
            {"field": "risk_score", "operator": "less_than", "value": 50}, payload
        ) is False

    @pytest.mark.asyncio
    async def test_enterprise_event_bus_exact_and_wildcard(self) -> None:
        """Verifies event bus pub/sub with exact matching and wildcard patterns."""
        bus = EnterpriseEventBus()
        received_events: list[str] = []

        async def doc_handler(evt: EnterpriseEvent) -> None:
            received_events.append(f"doc:{evt.event_type}")

        async def all_handler(evt: EnterpriseEvent) -> None:
            received_events.append(f"all:{evt.event_type}")

        bus.subscribe("document.uploaded", doc_handler)
        bus.subscribe("document.*", doc_handler)
        bus.subscribe("*", all_handler)

        event1 = EnterpriseEvent(
            event_type="document.uploaded",
            source="doc_service",
            organization_id="org-1",
            actor_id="user-1",
        )
        invoked_count = await bus.publish(event1)
        assert invoked_count == 2  # doc_handler (deduplicated) + all_handler
        assert "doc:document.uploaded" in received_events
        assert "all:document.uploaded" in received_events

        # Publish document.deleted -> matched by document.* and *
        received_events.clear()
        event2 = EnterpriseEvent(
            event_type="document.deleted",
            source="doc_service",
            organization_id="org-1",
            actor_id="user-1",
        )
        invoked_count2 = await bus.publish(event2)
        assert invoked_count2 == 2
        assert "doc:document.deleted" in received_events

        # Unsubscribe
        bus.unsubscribe("*", all_handler)
        received_events.clear()
        await bus.publish(event2)
        assert "all:document.deleted" not in received_events

    @pytest.mark.asyncio
    async def test_enterprise_event_bus_error_boundary(self) -> None:
        """Verifies event bus isolates faulty subscriber exceptions without crashing."""
        bus = EnterpriseEventBus()

        async def faulty_handler(evt: EnterpriseEvent) -> None:
            raise RuntimeError("Intentional subscriber crash")

        bus.subscribe("test.error", faulty_handler)
        event = EnterpriseEvent(
            event_type="test.error",
            source="test",
            organization_id="org-1",
            actor_id="user-1",
        )
        # Must not raise RuntimeError
        count = await bus.publish(event)
        assert count == 1
        assert len(bus.get_recent_events()) == 1

    def test_ai_workflow_actions_summarize(self) -> None:
        """Verifies autonomous AI summarizer action step."""
        text = (
            "Enterprise knowledge platforms require strict data governance. "
            "Automated workflows decrease human operational overhead by 40 percent. "
            "Event-driven architectures enable immediate reaction to document modifications. "
            "Continuous compliance guarantees audit readiness across all business units."
        )
        result = AIWorkflowActionsEngine.execute_ai_summarize(text, max_sentences=2)
        assert result["sentence_count"] == 2
        assert len(result["key_points"]) == 2
        assert len(result["keywords"]) > 0
        assert "Enterprise knowledge platforms" in result["summary"]

        # Empty text fallback
        empty_res = AIWorkflowActionsEngine.execute_ai_summarize("")
        assert empty_res["sentence_count"] == 0

    def test_ai_workflow_actions_suggest_reviewer(self) -> None:
        """Verifies AI reviewer recommendation logic."""
        reviewers = [
            {"id": "usr-legal-1", "name": "Counsel Sarah", "role": "LegalManager"},
            {"id": "usr-fin-1", "name": "Director Dave", "role": "FinanceDirector"},
        ]

        # Policy document
        res1 = AIWorkflowActionsEngine.execute_ai_suggest_reviewer("POLICY", "Acceptable Use Policy", reviewers)
        assert res1["suggested_role"] == "LegalManager"
        assert res1["suggested_reviewer_name"] == "Counsel Sarah"
        assert res1["suggested_reviewer_id"] == "usr-legal-1"
        assert res1["match_confidence"] > 0.9

        # Financial document
        res2 = AIWorkflowActionsEngine.execute_ai_suggest_reviewer("FINANCIAL", "Q3 Balance Sheet", reviewers)
        assert res2["suggested_role"] == "FinanceDirector"
        assert res2["suggested_reviewer_name"] == "Director Dave"

        # General document fallback
        res3 = AIWorkflowActionsEngine.execute_ai_suggest_reviewer("GENERAL", "Misc notes", reviewers)
        assert res3["suggested_role"] == "ProjectManager"

    def test_notification_channel_dispatcher_formatting(self) -> None:
        """Verifies notification payload formatting for Email, Slack, and Teams."""
        payload = NotificationPayload(
            user_id="usr-123",
            organization_id="org-456",
            title="Approval Required: Corporate Policy",
            message="Please review and sign off on the 2026 AI Governance Policy.",
            channel=NotificationChannel.IN_APP,
            priority=NotificationPriority.HIGH,
            category=NotificationCategory.APPROVAL,
            link_url="https://keep.enterprise.com/workflows/approvals/123",
        )

        # Email
        email_data = NotificationChannelDispatcher.format_email_payload(payload)
        assert "[HIGH] Approval Required: Corporate Policy" in email_data["subject"]
        assert "View in KEEP" in email_data["html_body"]
        assert email_data["recipient_user_id"] == "usr-123"

        # Slack
        slack_data = NotificationChannelDispatcher.format_slack_webhook_payload(payload)
        assert len(slack_data["blocks"]) >= 2
        assert "Approval Required: Corporate Policy" in slack_data["text"]

        # Teams
        teams_data = NotificationChannelDispatcher.format_teams_adaptive_card(payload)
        assert teams_data["type"] == "message"
        card = teams_data["attachments"][0]["content"]
        assert card["type"] == "AdaptiveCard"
        assert len(card["body"]) >= 2

    def test_workflow_template_registry(self) -> None:
        """Verifies system templates in WorkflowTemplateRegistry."""
        templates = WorkflowTemplateRegistry.get_system_templates()
        assert len(templates) >= 4

        template_ids = [t["id"] for t in templates]
        assert "tpl-doc-approval" in template_ids
        assert "tpl-ai-summary" in template_ids
        assert "tpl-scheduled-report" in template_ids
        assert "tpl-knowledge-audit" in template_ids

        for t in templates:
            assert "name" in t
            assert "description" in t
            assert "category" in t
            assert "steps_definition" in t
            assert len(t["steps_definition"]) > 0

    def test_rbac_workflow_permissions_integration(self) -> None:
        """Verifies Phase 3.4 permissions are defined in AIPermission and assigned to role hierarchies."""
        # Enum definitions
        assert AIPermission.WORKFLOW_VIEW.value == "workflow.view"
        assert AIPermission.WORKFLOW_MANAGE.value == "workflow.manage"
        assert AIPermission.WORKFLOW_EXECUTE.value == "workflow.execute"
        assert AIPermission.WORKFLOW_APPROVE.value == "workflow.approve"
        assert AIPermission.NOTIFICATION_VIEW.value == "notification.view"
        assert AIPermission.NOTIFICATION_MANAGE.value == "notification.manage"

        # Role mappings
        assert AIPermission.WORKFLOW_VIEW.value in VIEWER_PERMISSIONS
        assert AIPermission.NOTIFICATION_VIEW.value in VIEWER_PERMISSIONS

        assert AIPermission.WORKFLOW_EXECUTE.value in EMPLOYEE_PERMISSIONS
        assert AIPermission.NOTIFICATION_MANAGE.value in EMPLOYEE_PERMISSIONS

        assert AIPermission.WORKFLOW_APPROVE.value in PROJECT_MANAGER_PERMISSIONS

        assert AIPermission.WORKFLOW_MANAGE.value in ORG_ADMIN_PERMISSIONS
