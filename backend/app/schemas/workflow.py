"""Pydantic v2 Request/Response Validation Schemas for Workflow Automation & Notifications.

Phase: 3.4
Owner: Member 2 (Backend & Database Lead)
Domain: /backend/app/schemas/workflow.py
Specification: devdocs/p3/p3.4.txt & docs/api/api-contract.md (Section 16)
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Workflow Definition Schemas
# ============================================================================


class WorkflowStepCreate(BaseModel):
    """Schema for defining an individual step within a workflow creation request."""

    step_order: int = Field(default=1, ge=1, description="Sequential order in workflow execution")
    name: str | None = Field(default=None, description="Step name")
    action_type: str = Field(description="Action executor type, e.g. AI_SUMMARIZE, NOTIFY")
    configuration: dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")
    action_config: dict[str, Any] | None = Field(default=None, description="Alias for configuration")
    timeout_seconds: int = Field(default=300, ge=1, le=3600, description="Step execution timeout")

    model_config = ConfigDict(extra="ignore")

    def model_post_init(self, context: Any, /) -> None:
        if self.action_config and not self.configuration:
            self.configuration = self.action_config


class WorkflowCreateRequest(BaseModel):
    """Payload for registering a new enterprise workflow."""

    name: str = Field(min_length=1, max_length=255, description="Human-readable workflow name")
    description: str | None = Field(default=None, max_length=2000, description="Detailed operational objective")
    trigger_type: str = Field(default="EVENT", description="Trigger mechanism: EVENT, SCHEDULE, MANUAL")
    event_pattern: str | None = Field(default=None, max_length=120, description="Event topic pattern, e.g. document.uploaded")
    cron_expression: str | None = Field(default=None, max_length=60, description="Cron expression for SCHEDULE triggers")
    condition_rules: dict[str, Any] | list[dict[str, Any]] = Field(default_factory=dict, description="Predicate filter rules")
    is_active: bool = Field(default=True, description="Whether the workflow is active")
    steps: list[WorkflowStepCreate] = Field(default_factory=list, description="Ordered steps DAG")

    model_config = ConfigDict(extra="ignore")


class WorkflowStepResponse(BaseModel):
    """Step configuration response schema."""

    id: str
    name: str | None = None
    step_order: int
    action_type: str
    configuration: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 300

    model_config = ConfigDict(from_attributes=True)


class WorkflowItemResponse(BaseModel):
    """Workflow summary response schema."""

    id: str
    name: str
    description: str | None = None
    trigger_type: str
    event_pattern: str | None = None
    cron_expression: str | None = None
    condition_rules: dict[str, Any] | list[dict[str, Any]] = Field(default_factory=dict)
    is_active: bool
    step_count: int = 0
    steps: list[WorkflowStepResponse] = Field(default_factory=list)
    created_at: str

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Execution & Telemetry Schemas
# ============================================================================


class WorkflowExecuteRequest(BaseModel):
    """Payload to manually or programmatically invoke a workflow."""

    workflow_id: str = Field(description="UUID of workflow to execute")
    input_payload: dict[str, Any] = Field(default_factory=dict, description="Execution input context")

    model_config = ConfigDict(extra="ignore")


class WorkflowExecuteResponse(BaseModel):
    """Immediate acknowledgement returned upon triggering a workflow."""

    execution_id: str
    id: str | None = None
    status: str
    started_at: str

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, context: Any, /) -> None:
        if not self.id:
            self.id = self.execution_id


class WorkflowExecutionItemResponse(BaseModel):
    """Summary item for execution history audit trail."""

    id: str
    workflow_id: str
    workflow_name: str
    status: str
    duration_ms: float
    started_at: str
    completed_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Approvals Schemas
# ============================================================================


class WorkflowApprovalRequest(BaseModel):
    """Decision submitted by human reviewer gating workflow execution."""

    approval_id: str = Field(description="UUID of approval ticket")
    decision: str = Field(description="APPROVE or REJECT")
    comments: str | None = Field(default=None, max_length=2000, description="Review remarks")

    model_config = ConfigDict(extra="ignore")


class WorkflowApprovalItemResponse(BaseModel):
    """Approval ticket representation."""

    id: str
    execution_id: str
    workflow_name: str
    requester_name: str | None = None
    step_description: str | None = None
    status: str
    decision: str | None = None
    requested_at: str
    responded_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Notifications & Preferences Schemas
# ============================================================================


class NotificationItemResponse(BaseModel):
    """Notification inbox item representation."""

    id: str
    title: str
    message: str
    channel: str
    priority: str
    category: str
    is_read: bool
    link_url: str | None = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferenceItem(BaseModel):
    """User channel opt-in/opt-out configuration entry."""

    channel: str
    category: str
    is_enabled: bool

    model_config = ConfigDict(extra="ignore")


class NotificationPreferencesUpdateRequest(BaseModel):
    """Batch or single category preference update payload."""

    preferences: list[NotificationPreferenceItem] = Field(default_factory=list)
    category: str | None = None
    in_app: bool | None = None
    email: bool | None = None
    slack: bool | None = None
    teams: bool | None = None

    model_config = ConfigDict(extra="ignore")

    def model_post_init(self, context: Any, /) -> None:
        if self.category and not self.preferences:
            cat = self.category
            items: list[NotificationPreferenceItem] = []
            if self.in_app is not None:
                items.append(NotificationPreferenceItem(channel="in_app", category=cat, is_enabled=self.in_app))
            if self.email is not None:
                items.append(NotificationPreferenceItem(channel="email", category=cat, is_enabled=self.email))
            if self.slack is not None:
                items.append(NotificationPreferenceItem(channel="slack", category=cat, is_enabled=self.slack))
            if self.teams is not None:
                items.append(NotificationPreferenceItem(channel="teams", category=cat, is_enabled=self.teams))
            self.preferences = items


# ============================================================================
# Templates & Analytics Schemas
# ============================================================================


class WorkflowTemplateItemResponse(BaseModel):
    """Pre-configured enterprise workflow template."""

    id: str
    name: str
    description: str
    category: str
    trigger_type: str
    event_pattern: str | None = None
    cron_expression: str | None = None
    steps_preview: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class WorkflowAnalyticsResponse(BaseModel):
    """Operational KPI metrics and performance metrics."""

    total_workflows_executed: int
    success_rate: float
    avg_execution_time_ms: float
    failed_workflows: int
    pending_approvals: int
    notifications_delivered: int
    ai_automation_usage_count: int
    executions_by_day: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
