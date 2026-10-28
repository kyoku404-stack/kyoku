"""Typed AI and Domain Contracts for Workflow Automation, Notifications & Event-Driven Intelligence.

Phase: 3.4
Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/workflow/
Specification: devdocs/p3/p3.4.txt (Chapters 1-20)
"""

import asyncio
import fnmatch
import logging
import re
import uuid
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


# ============================================================================
# Enums & Domain Taxonomies
# ============================================================================


class WorkflowTriggerType(str, Enum):
    """Supported trigger types initiating workflow runs."""

    EVENT = "EVENT"
    SCHEDULE = "SCHEDULE"
    MANUAL = "MANUAL"


class WorkflowStatus(str, Enum):
    """Administrative status of a workflow definition."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class WorkflowExecutionStatus(str, Enum):
    """Lifecycle execution states of a workflow instance."""

    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowStepAction(str, Enum):
    """Executable action types for workflow DAG steps."""

    AI_SUMMARIZE = "AI_SUMMARIZE"
    AI_SUGGEST_REVIEWER = "AI_SUGGEST_REVIEWER"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    NOTIFY = "NOTIFY"
    DOCUMENT_ACTION = "DOCUMENT_ACTION"
    CUSTOM_SCRIPT = "CUSTOM_SCRIPT"


class ApprovalStatus(str, Enum):
    """Status of human-in-the-loop approval tickets."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ApprovalDecision(str, Enum):
    """Decisions submitted by human approvers."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"


class NotificationChannel(str, Enum):
    """Supported delivery channels for notifications."""

    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SLACK = "SLACK"
    TEAMS = "TEAMS"


class NotificationPriority(str, Enum):
    """Priority tiers determining visual prominence and routing."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NotificationCategory(str, Enum):
    """Functional categories for notifications."""

    WORKFLOW = "WORKFLOW"
    APPROVAL = "APPROVAL"
    DOCUMENT = "DOCUMENT"
    AI = "AI"
    SECURITY = "SECURITY"
    SYSTEM = "SYSTEM"


# ============================================================================
# Dataclasses & Event Envelopes
# ============================================================================


@dataclass
class EnterpriseEvent:
    """Standardized event envelope capturing enterprise platform occurrences."""

    event_type: str
    source: str
    organization_id: str
    actor_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "organization_id": self.organization_id,
            "actor_id": self.actor_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class WorkflowCondition:
    """Predicate condition rule evaluated against an event payload."""

    field: str
    operator: str  # equals, not_equals, contains, in, greater_than, less_than
    value: Any


@dataclass
class WorkflowStepConfig:
    """Configuration for an individual workflow DAG step."""

    step_order: int
    action_type: WorkflowStepAction
    configuration: dict[str, Any] = field(default_factory=dict)
    depends_on_step_order: int | None = None
    timeout_seconds: int = 300


@dataclass
class StepExecutionResult:
    """Result emitted after executing a workflow step."""

    step_order: int
    action_type: WorkflowStepAction
    status: str  # COMPLETED, FAILED, WAITING_APPROVAL, SKIPPED
    output_payload: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    duration_ms: float = 0.0


@dataclass
class NotificationPayload:
    """Payload dispatched through the notification engine."""

    user_id: str
    organization_id: str
    title: str
    message: str
    channel: NotificationChannel = NotificationChannel.IN_APP
    priority: NotificationPriority = NotificationPriority.NORMAL
    category: NotificationCategory = NotificationCategory.WORKFLOW
    link_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# ============================================================================
# Reference Engine 1: Predicate Condition Evaluator
# ============================================================================


class PredicateConditionEvaluator:
    """Evaluates JSON condition rules against event or workflow execution payloads."""

    @staticmethod
    def evaluate(condition_rules: dict[str, Any], payload: dict[str, Any]) -> bool:
        """Evaluates condition rules against payload.

        If condition_rules is empty, returns True.
        Supported operators:
          - 'equals': payload[field] == value
          - 'not_equals': payload[field] != value
          - 'contains': value in payload[field] (substring or element in list)
          - 'in': payload[field] in value
          - 'greater_than': payload[field] > value
          - 'less_than': payload[field] < value
        """
        if not condition_rules:
            return True

        if isinstance(condition_rules, list):
            return all(PredicateConditionEvaluator.evaluate(rule, payload) for rule in condition_rules)

        field_name = condition_rules.get("field")
        operator = condition_rules.get("operator", "equals").lower()
        target_value = condition_rules.get("value")

        if not field_name:
            return True

        actual_value = payload.get(field_name)

        if operator == "equals":
            return actual_value == target_value
        if operator == "not_equals":
            return actual_value != target_value
        if operator == "contains":
            if actual_value is None:
                return False
            if isinstance(actual_value, (list, tuple, set)):
                return target_value in actual_value
            return str(target_value).lower() in str(actual_value).lower()
        if operator == "in":
            if isinstance(target_value, (list, tuple, set)):
                return actual_value in target_value
            return False
        if operator == "greater_than":
            try:
                return float(actual_value) > float(target_value)
            except (ValueError, TypeError):
                return False
        if operator == "less_than":
            try:
                return float(actual_value) < float(target_value)
            except (ValueError, TypeError):
                return False

        return False


# ============================================================================
# Reference Engine 2: Decoupled Publish-Subscribe Enterprise Event Bus
# ============================================================================

EventHandlerType = Callable[[EnterpriseEvent], Coroutine[Any, Any, None]]


class EnterpriseEventBus:
    """Asynchronous in-memory event bus supporting wildcard subscriptions and decoupled dispatch."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandlerType]] = {}
        self._event_history: list[EnterpriseEvent] = []
        self._max_history: int = 1000

    def subscribe(self, event_pattern: str, handler: EventHandlerType) -> None:
        """Registers an asynchronous subscriber handler for an event pattern (e.g.

        'document.*' or 'user.login').
        """
        if event_pattern not in self._subscribers:
            self._subscribers[event_pattern] = []
        if handler not in self._subscribers[event_pattern]:
            self._subscribers[event_pattern].append(handler)
        logger.info(f"Subscribed handler to event pattern: {event_pattern}")

    def unsubscribe(self, event_pattern: str, handler: EventHandlerType) -> None:
        """Unsubscribes a handler from a pattern."""
        if event_pattern in self._subscribers and handler in self._subscribers[event_pattern]:
            self._subscribers[event_pattern].remove(handler)

    async def publish(self, event: EnterpriseEvent) -> int:
        """Publishes an enterprise event and dispatches to all matching subscribers.

        Returns the number of handlers invoked.
        """
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        matching_handlers: list[EventHandlerType] = []
        for pattern, handlers in self._subscribers.items():
            if pattern == "*" or pattern == event.event_type or fnmatch.fnmatch(event.event_type, pattern):
                matching_handlers.extend(handlers)

        # Deduplicate handlers
        unique_handlers = list(dict.fromkeys(matching_handlers))

        for handler in unique_handlers:
            try:
                # Dispatch non-blocking
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)  # type: ignore
            except Exception:
                logger.exception(f"Error executing event handler for {event.event_type}")

        return len(unique_handlers)

    def get_recent_events(self, limit: int = 50) -> list[EnterpriseEvent]:
        """Returns the most recent dispatched events."""
        return self._event_history[-limit:]


# Global singleton event bus instance
default_event_bus = EnterpriseEventBus()


# ============================================================================
# Reference Engine 3: AI Workflow Actions Engine
# ============================================================================


class AIWorkflowActionsEngine:
    """Executes native AI-powered workflow automation steps."""

    @staticmethod
    def execute_ai_summarize(
        document_text: str,
        max_sentences: int = 3,
    ) -> dict[str, Any]:
        """Generates an autonomous extraction-based executive summary for document workflows."""
        if not document_text or not document_text.strip():
            return {
                "summary": "Document contains no readable text content.",
                "key_points": [],
                "sentence_count": 0,
            }

        # Clean and split into sentences
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", document_text) if len(s.strip()) > 15]

        if not sentences:
            sentences = [document_text[:200]]

        selected = sentences[:max_sentences]
        summary = " ".join(selected)

        # Extract simulated high-frequency keywords
        words = re.findall(r"\b[A-Za-z]{4,}\b", document_text.lower())
        word_freq: dict[str, int] = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1

        top_keywords = sorted(word_freq.keys(), key=lambda k: word_freq[k], reverse=True)[:5]

        return {
            "summary": summary,
            "key_points": selected,
            "keywords": top_keywords,
            "sentence_count": len(selected),
        }

    @staticmethod
    def execute_ai_suggest_reviewer(
        document_type: str,
        content_snippet: str,
        available_reviewers: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Analyzes document taxonomy and suggests the ideal domain reviewer."""
        doc_type_normalized = (document_type or "GENERAL").upper()

        role_mapping = {
            "POLICY": "LegalManager",
            "CONTRACT": "LegalCounsel",
            "FINANCIAL": "FinanceDirector",
            "HR": "HRManager",
            "TECHNICAL": "LeadArchitect",
            "SECURITY": "SecurityOfficer",
        }

        suggested_role = role_mapping.get(doc_type_normalized, "ProjectManager")
        match_confidence = 0.92 if doc_type_normalized in role_mapping else 0.75

        # Pick candidate reviewer if provided
        candidate_name = "Assigned Domain Lead"
        candidate_id = "default-reviewer-id"
        if available_reviewers:
            for rev in available_reviewers:
                if rev.get("role") == suggested_role:
                    candidate_name = rev.get("name", candidate_name)
                    candidate_id = rev.get("id", candidate_id)
                    break

        return {
            "suggested_role": suggested_role,
            "suggested_reviewer_name": candidate_name,
            "suggested_reviewer_id": candidate_id,
            "match_confidence": match_confidence,
            "reasoning": f"Document classified as {doc_type_normalized}, mapping to organizational domain {suggested_role}.",
        }


# ============================================================================
# Reference Engine 4: Multi-Channel Notification Dispatcher
# ============================================================================


class NotificationChannelDispatcher:
    """Formats and dispatches notifications across in-app, email, Slack, and Teams channels."""

    @staticmethod
    def format_payload(
        channel: str,
        title: str,
        message: str,
        metadata: dict[str, Any] | None = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        category: NotificationCategory = NotificationCategory.SYSTEM,
    ) -> dict[str, Any]:
        """Generic payload formatter routing to channel-specific formatting engine."""
        channel_enum = NotificationChannel.IN_APP
        try:
            channel_enum = NotificationChannel(channel.lower())
        except (ValueError, AttributeError):
            pass

        payload = NotificationPayload(
            id=str(uuid.uuid4()),
            user_id="default-user",
            organization_id="default-org",
            title=title,
            message=message,
            channel=channel_enum,
            priority=priority,
            category=category,
            link_url=(metadata or {}).get("link_url"),
            metadata=metadata or {},
        )
        if channel.lower() == "email":
            return NotificationChannelDispatcher.format_email_payload(payload)
        elif channel.lower() == "slack":
            return NotificationChannelDispatcher.format_slack_webhook_payload(payload)
        elif channel.lower() == "teams":
            return NotificationChannelDispatcher.format_teams_adaptive_card(payload)
        else:
            return {
                "title": title,
                "message": message,
                "channel": channel,
                "priority": priority.value,
                "category": category.value,
            }

    @staticmethod
    def format_email_payload(payload: NotificationPayload) -> dict[str, Any]:
        """Formats an HTML/plain email notification with call to action."""
        action_button = (
            f'<a href="{payload.link_url}" style="background-color: #2563EB; color: #FFFFFF; padding: 10px 18px; text-decoration: none; border-radius: 4px;">View in KEEP</a>'
            if payload.link_url
            else ""
        )
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #E5E7EB; border-radius: 8px;">
            <h2 style="color: #1F2937; margin-top: 0;">{payload.title}</h2>
            <p style="color: #4B5563; font-size: 15px; line-height: 1.5;">{payload.message}</p>
            <div style="margin: 25px 0;">
                {action_button}
            </div>
            <p style="color: #9CA3AF; font-size: 12px; margin-bottom: 0;">Priority: {payload.priority.value} | Category: {payload.category.value}</p>
        </div>
        """
        return {
            "recipient_user_id": payload.user_id,
            "subject": f"[{payload.priority.value}] {payload.title}",
            "html_body": html_body.strip(),
            "plain_text": f"{payload.title}\n\n{payload.message}\n\nPriority: {payload.priority.value}",
        }

    @staticmethod
    def format_slack_webhook_payload(payload: NotificationPayload) -> dict[str, Any]:
        """Formats a Slack Block Kit rich card message."""
        blocks: list[dict[str, Any]] = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🔔 {payload.title}", "emoji": True},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": payload.message},
                "fields": [
                    {"type": "mrkdwn", "text": f"*Priority:*\n{payload.priority.value}"},
                    {"type": "mrkdwn", "text": f"*Category:*\n{payload.category.value}"},
                ],
            },
        ]
        if payload.link_url:
            blocks.append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Open Details", "emoji": True},
                            "url": payload.link_url,
                            "style": "primary" if payload.priority in (NotificationPriority.HIGH, NotificationPriority.CRITICAL) else "default",
                        }
                    ],
                }
            )
        return {"text": f"{payload.title}: {payload.message}", "blocks": blocks}

    @staticmethod
    def format_teams_adaptive_card(payload: NotificationPayload) -> dict[str, Any]:
        """Formats a Microsoft Teams Adaptive Card webhook payload."""
        body: list[dict[str, Any]] = [
            {"type": "TextBlock", "size": "Medium", "weight": "Bolder", "text": payload.title},
            {"type": "TextBlock", "text": payload.message, "wrap": True},
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Priority", "value": payload.priority.value},
                    {"title": "Category", "value": payload.category.value},
                ],
            },
        ]
        actions = []
        if payload.link_url:
            actions.append({"type": "Action.OpenUrl", "title": "Open in KEEP", "url": payload.link_url})

        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": body,
                        "actions": actions,
                    },
                }
            ],
        }


# ============================================================================
# Reference Engine 5: Reusable Workflow Templates Registry
# ============================================================================


class WorkflowTemplateRegistry:
    """Pre-configured enterprise workflow templates matching Chapter 13."""

    @staticmethod
    def get_system_templates() -> list[dict[str, Any]]:
        return [
            {
                "id": "tpl-doc-approval",
                "name": "Document Approval Pipeline",
                "description": "Multi-tier manager review and sign-off for newly uploaded policies and contracts.",
                "category": "GOVERNANCE",
                "trigger_type": "EVENT",
                "event_pattern": "document.uploaded",
                "steps_definition": [
                    {
                        "step_order": 1,
                        "action_type": WorkflowStepAction.AI_SUMMARIZE.value,
                        "configuration": {"max_sentences": 3},
                    },
                    {
                        "step_order": 2,
                        "action_type": WorkflowStepAction.AI_SUGGEST_REVIEWER.value,
                        "configuration": {"default_role": "LegalReviewer"},
                    },
                    {
                        "step_order": 3,
                        "action_type": WorkflowStepAction.REQUIRE_APPROVAL.value,
                        "configuration": {"approver_role": "ProjectManager"},
                    },
                    {
                        "step_order": 4,
                        "action_type": WorkflowStepAction.NOTIFY.value,
                        "configuration": {"channel": "IN_APP", "priority": "HIGH"},
                    },
                ],
            },
            {
                "id": "tpl-ai-summary",
                "name": "Autonomous AI Ingestion",
                "description": "Automatically extract keywords, generate executive summaries, and update knowledge vector index.",
                "category": "AI",
                "trigger_type": "EVENT",
                "event_pattern": "document.uploaded",
                "steps_definition": [
                    {
                        "step_order": 1,
                        "action_type": WorkflowStepAction.AI_SUMMARIZE.value,
                        "configuration": {"max_sentences": 4},
                    },
                    {
                        "step_order": 2,
                        "action_type": WorkflowStepAction.NOTIFY.value,
                        "configuration": {"channel": "IN_APP", "priority": "NORMAL"},
                    },
                ],
            },
            {
                "id": "tpl-scheduled-report",
                "name": "Weekly Executive Digest",
                "description": "Synthesizes weekly knowledge usage metrics and delivers executive briefing.",
                "category": "REPORTING",
                "trigger_type": "SCHEDULE",
                "cron_expression": "0 9 * * 1",
                "steps_definition": [
                    {
                        "step_order": 1,
                        "action_type": WorkflowStepAction.NOTIFY.value,
                        "configuration": {"channel": "EMAIL", "priority": "NORMAL"},
                    }
                ],
            },
            {
                "id": "tpl-knowledge-audit",
                "name": "Quarterly Knowledge Review",
                "description": "Scans outdated documents, flags stale content, and assigns review tickets to department owners.",
                "category": "GOVERNANCE",
                "trigger_type": "SCHEDULE",
                "cron_expression": "0 0 1 */3 *",
                "steps_definition": [
                    {
                        "step_order": 1,
                        "action_type": WorkflowStepAction.REQUIRE_APPROVAL.value,
                        "configuration": {"approver_role": "OrgAdmin"},
                    },
                    {
                        "step_order": 2,
                        "action_type": WorkflowStepAction.NOTIFY.value,
                        "configuration": {"channel": "IN_APP", "priority": "HIGH"},
                    },
                ],
            },
        ]
