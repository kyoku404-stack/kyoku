from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AssistantChatRequest(BaseModel):
    """Request payload for conversing with the Enterprise AI Assistant."""

    model_config = ConfigDict(from_attributes=True)

    message: str = Field(..., min_length=1, max_length=4000, description="User instruction or prompt.")
    session_id: UUID | None = Field(default=None, description="Optional conversation session ID.")
    department_id: UUID | None = Field(default=None, description="Optional department scope.")
    project_id: UUID | None = Field(default=None, description="Optional project scope.")


class AssistantChatResponseData(BaseModel):
    """Response payload for assistant chat turn."""

    model_config = ConfigDict(from_attributes=True)

    session_id: UUID
    message_id: str
    reply: str
    detected_intent: str
    workflow_id: UUID | None = None
    tools_executed: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    approval_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TaskExecuteRequest(BaseModel):
    """Request payload for formulating and executing a multi-step AI task."""

    model_config = ConfigDict(from_attributes=True)

    instructions: str = Field(..., min_length=1, max_length=5000, description="Task instructions.")
    title: str | None = Field(default=None, description="Optional descriptive title for the task.")
    session_id: UUID | None = Field(default=None, description="Optional linked chat session.")
    context: dict[str, Any] = Field(default_factory=dict, description="Execution parameters and filters.")


class TaskStepResponse(BaseModel):
    """Execution state of an individual DAG task step."""

    model_config = ConfigDict(from_attributes=True)

    step_number: int
    tool_name: str
    description: str
    status: str
    latency_ms: float = 0.0
    output: dict[str, Any] | None = None
    error: str | None = None
    approval_id: UUID | None = None


class TaskExecuteResponseData(BaseModel):
    """Response payload for formulated and executed multi-step task."""

    model_config = ConfigDict(from_attributes=True)

    workflow_id: UUID
    title: str
    status: str
    total_steps: int
    completed_steps: int
    steps: list[TaskStepResponse] = Field(default_factory=list)
    result_summary: str | None = None
    pending_approval: dict[str, Any] | None = None


class ReportGenerateRequest(BaseModel):
    """Request payload for compiling structured organizational reports."""

    model_config = ConfigDict(from_attributes=True)

    report_type: str = Field(default="WEEKLY_ROLLUP", description="MEETING_SUMMARY, WEEKLY_ROLLUP, etc.")
    title: str = Field(..., min_length=1, max_length=255, description="Report title.")
    format: str = Field(default="MARKDOWN", description="MARKDOWN, PDF, DOCX, JSON.")
    filters: dict[str, Any] = Field(default_factory=dict, description="Reporting scope filters.")


class ReportGenerateResponseData(BaseModel):
    """Generated report payload."""

    model_config = ConfigDict(from_attributes=True)

    report_id: UUID
    report_type: str
    title: str
    format: str
    content: str
    created_at: datetime


class WorkflowItemResponse(BaseModel):
    """Summary of a workflow instance."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    trigger_type: str
    status: str
    total_steps: int
    completed_steps: int
    created_at: datetime
    completed_at: datetime | None = None


class WorkflowListResponseData(BaseModel):
    """Paginated list of assistant workflows."""

    model_config = ConfigDict(from_attributes=True)

    workflows: list[WorkflowItemResponse]
    total: int
    page: int
    page_size: int


class ApprovalActionRequest(BaseModel):
    """Human-in-the-loop decision request."""

    model_config = ConfigDict(from_attributes=True)

    approval_id: UUID
    decision: str = Field(..., description="APPROVED or REJECTED")
    reason: str | None = Field(default=None, description="Optional justification for the decision.")


class ApprovalActionResponseData(BaseModel):
    """Result of human-in-the-loop approval decision."""

    model_config = ConfigDict(from_attributes=True)

    approval_id: UUID
    workflow_id: UUID | None = None
    decision: str
    status: str
    executed_at: datetime


class ProactiveRecommendationItem(BaseModel):
    """Actionable insight surfaced by recommendation engine."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    title: str
    description: str
    suggested_action: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecommendationResponseData(BaseModel):
    """List of proactive enterprise recommendations."""

    model_config = ConfigDict(from_attributes=True)

    recommendations: list[ProactiveRecommendationItem]
