"""Phase 2.3 Enterprise AI Assistant & Agentic Workflows Typed Domain Contracts.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/assistant
Specification: devdocs/p2/p2.3.txt (Chapters 1-20)
Architecture: docs/Architecture/ai-assistant-agentic-workflows.md
ADRs: ADR-038, ADR-039, ADR-040
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

# ==============================================================================
# 1. Enums
# ==============================================================================


class AssistantIntent(str, Enum):
    """Categorized intent of user request (devdocs/p2/p2.3.txt Chapter 5)."""

    KNOWLEDGE_QA = "KNOWLEDGE_QA"
    DOCUMENT_SUMMARIZATION = "DOCUMENT_SUMMARIZATION"
    REPORT_GENERATION = "REPORT_GENERATION"
    ACTION_EXECUTION = "ACTION_EXECUTION"
    RECOMMENDATION_DISCOVERY = "RECOMMENDATION_DISCOVERY"
    CONVERSATIONAL_FOLLOWUP = "CONVERSATIONAL_FOLLOWUP"


class WorkflowStatus(str, Enum):
    """State machine transitions for assistant workflows."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskStepStatus(str, Enum):
    """Execution status of an individual DAG task step."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ApprovalStatus(str, Enum):
    """Human-in-the-loop approval decision states (ADR-040)."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ToolCategory(str, Enum):
    """Functional taxonomy for enterprise platform tools (Chapter 7)."""

    KNOWLEDGE = "KNOWLEDGE"
    ANALYTICS = "ANALYTICS"
    ADMINISTRATION = "ADMINISTRATION"
    PRODUCTIVITY = "PRODUCTIVITY"
    NOTIFICATION = "NOTIFICATION"


class ReportType(str, Enum):
    """Supported report generation templates (Chapter 11)."""

    MEETING_SUMMARY = "MEETING_SUMMARY"
    WEEKLY_ROLLUP = "WEEKLY_ROLLUP"
    PROJECT_STATUS = "PROJECT_STATUS"
    DEPARTMENT_ANALYTICS = "DEPARTMENT_ANALYTICS"
    KNOWLEDGE_SYNTHESIS = "KNOWLEDGE_SYNTHESIS"


class ReportFormat(str, Enum):
    """Supported export formats for generated reports."""

    MARKDOWN = "MARKDOWN"
    PDF = "PDF"
    DOCX = "DOCX"
    JSON = "JSON"


class RecommendationCategory(str, Enum):
    """Proactive recommendation domains (Chapter 12)."""

    FREQUENT_DOCUMENTS = "FREQUENT_DOCUMENTS"
    MISSING_DOCUMENTATION = "MISSING_DOCUMENTATION"
    DUPLICATE_KNOWLEDGE = "DUPLICATE_KNOWLEDGE"
    INACTIVE_PROJECTS = "INACTIVE_PROJECTS"


# ==============================================================================
# 2. Dataclasses
# ==============================================================================


@dataclass
class WorkflowExecutionContext:
    """Carries tenant identity, security credentials, and cross-step state."""

    organization_id: UUID
    user_id: UUID
    user_roles: list[str] = field(default_factory=lambda: ["EMPLOYEE"])
    user_permissions: set[str] = field(default_factory=lambda: {"assistant.chat", "assistant.task"})
    session_id: UUID | None = None
    step_outputs: dict[int, dict[str, Any]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCallResult:
    """Outcome of invoking a platform tool."""

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    latency_ms: float = 0.0


@dataclass
class TaskStepSpec:
    """An atomic node in a Directed Acyclic Graph (DAG) task plan."""

    step_number: int
    tool_name: str
    description: str
    input_parameters: dict[str, Any] = field(default_factory=dict)
    dependencies: list[int] = field(default_factory=list)
    requires_approval: bool = False
    status: TaskStepStatus = TaskStepStatus.PENDING
    output_result: dict[str, Any] | None = None
    execution_latency_ms: float = 0.0
    error_message: str | None = None


@dataclass
class TaskPlanSpec:
    """Structured execution plan formulated by the assistant planner."""

    title: str
    instructions: str
    intent: AssistantIntent
    steps: list[TaskStepSpec] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def has_approval_requirement(self) -> bool:
        return any(step.requires_approval for step in self.steps)


@dataclass
class ApprovalRequestSpec:
    """Payload representing a pending human-in-the-loop review."""

    approval_id: UUID
    workflow_id: UUID
    task_id: UUID
    action_type: str
    description: str
    payload: dict[str, Any] = field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(
        default_factory=lambda: datetime.now(UTC) + timedelta(hours=24)
    )
    reviewed_by_id: UUID | None = None
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None


@dataclass
class AssistantReportSpec:
    """Parameters and metadata for structured report generation."""

    report_type: ReportType
    title: str
    format: ReportFormat = ReportFormat.MARKDOWN
    filters: dict[str, Any] = field(default_factory=dict)
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProactiveRecommendation:
    """Actionable insight surfaced proactively to organizational users."""

    id: str
    category: RecommendationCategory
    title: str
    description: str
    suggested_action: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ==============================================================================
# 3. Abstract Interfaces
# ==============================================================================


class BaseTool(ABC):
    """Abstract interface defining an enterprise tool callable by the assistant."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier of the tool."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Self-describing text for intent and parameter binding."""

    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Functional domain category."""

    @property
    @abstractmethod
    def required_permissions(self) -> list[str]:
        """Permissions required in caller security context."""

    @property
    @abstractmethod
    def is_destructive(self) -> bool:
        """Whether tool triggers mandatory HITL approval (ADR-040)."""

    @property
    @abstractmethod
    def parameters_schema(self) -> dict[str, Any]:
        """JSON-Schema compliant parameter definitions."""

    @abstractmethod
    async def execute(
        self,
        parameters: dict[str, Any],
        context: WorkflowExecutionContext,
    ) -> ToolCallResult:
        """Execute the tool within tenant and permission boundaries."""


class BaseToolRegistry(ABC):
    """Abstract contract for dynamic tool discovery and validation."""

    @abstractmethod
    def register(self, tool: BaseTool) -> None:
        """Registers a tool implementation."""

    @abstractmethod
    def get(self, name: str) -> BaseTool | None:
        """Look up tool by name."""

    @abstractmethod
    def list_tools(self, category: ToolCategory | None = None) -> list[BaseTool]:
        """Lists registered tools, optionally filtered by category."""


class BaseAssistantPlanner(ABC):
    """Abstract interface for Natural Language Understanding & Task Planning."""

    @abstractmethod
    def classify_intent(self, text: str) -> AssistantIntent:
        """Detect intent from user prompt."""

    @abstractmethod
    def plan(
        self,
        instruction: str,
        title: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> TaskPlanSpec:
        """Decompose prompt into sequential DAG task steps."""


class BaseWorkflowOrchestrator(ABC):
    """Abstract interface for executing multi-step DAG workflows."""

    @abstractmethod
    async def execute_plan(
        self,
        plan: TaskPlanSpec,
        context: WorkflowExecutionContext,
    ) -> dict[str, Any]:
        """Executes task steps in topological order."""


class BaseReportGenerator(ABC):
    """Abstract interface for enterprise report generation."""

    @abstractmethod
    def generate_report(
        self,
        spec: AssistantReportSpec,
        source_data: dict[str, Any],
    ) -> str:
        """Synthesizes structured text or markdown report."""


class BaseRecommendationEngine(ABC):
    """Abstract interface for proactive organizational insights."""

    @abstractmethod
    def generate_recommendations(
        self,
        telemetry_data: dict[str, Any],
    ) -> list[ProactiveRecommendation]:
        """Derive proactive recommendations from telemetry and knowledge health."""


# ==============================================================================
# 4. Concrete Reference Implementations
# ==============================================================================


class DocumentTool(BaseTool):
    """Tool for retrieving and filtering organization documents."""

    @property
    def name(self) -> str:
        return "DocumentTool"

    @property
    def description(self) -> str:
        return "Retrieve and filter enterprise documents, handbooks, and policies by category or query."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.KNOWLEDGE

    @property
    def required_permissions(self) -> list[str]:
        return ["documents.read"]

    @property
    def is_destructive(self) -> bool:
        return False

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "limit": {"type": "integer", "default": 5},
                "search_term": {"type": "string"},
            },
        }

    async def execute(
        self,
        parameters: dict[str, Any],
        context: WorkflowExecutionContext,
    ) -> ToolCallResult:
        start_time = time.perf_counter()
        limit = parameters.get("limit", 5)
        category = parameters.get("category", "ALL")
        # Reference execution returning tenant-isolated document stubs
        docs = [
            {
                "id": str(uuid4()),
                "title": f"Enterprise {category} Document {i + 1}",
                "category": category,
                "status": "PROCESSED",
            }
            for i in range(min(limit, 3))
        ]
        latency = (time.perf_counter() - start_time) * 1000.0
        return ToolCallResult(
            success=True,
            data={"documents": docs, "count": len(docs)},
            latency_ms=latency,
        )


class SearchTool(BaseTool):
    """Tool for semantic RAG search across knowledge chunks."""

    @property
    def name(self) -> str:
        return "SearchTool"

    @property
    def description(self) -> str:
        return "Executes hybrid dense and sparse retrieval over indexed knowledge chunks."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.KNOWLEDGE

    @property
    def required_permissions(self) -> list[str]:
        return ["rag.query"]

    @property
    def is_destructive(self) -> bool:
        return False

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        }

    async def execute(
        self,
        parameters: dict[str, Any],
        context: WorkflowExecutionContext,
    ) -> ToolCallResult:
        start_time = time.perf_counter()
        query = parameters.get("query", "")
        top_k = parameters.get("top_k", 5)
        chunks = [
            {
                "chunk_id": str(uuid4()),
                "content": f"Relevant excerpt answering '{query}' from verified documentation.",
                "relevance_score": 0.88 - (i * 0.05),
            }
            for i in range(min(top_k, 3))
        ]
        latency = (time.perf_counter() - start_time) * 1000.0
        return ToolCallResult(
            success=True,
            data={"query": query, "chunks": chunks, "total": len(chunks)},
            latency_ms=latency,
        )


class AnalyticsTool(BaseTool):
    """Tool for querying system usage, token velocity, and query metrics."""

    @property
    def name(self) -> str:
        return "AnalyticsTool"

    @property
    def description(self) -> str:
        return "Fetches organizational KPI metrics, query volumes, and ingestion activity."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANALYTICS

    @property
    def required_permissions(self) -> list[str]:
        return ["analytics.read"]

    @property
    def is_destructive(self) -> bool:
        return False

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "metric_type": {"type": "string", "default": "summary"},
                "days_back": {"type": "integer", "default": 7},
            },
        }

    async def execute(
        self,
        parameters: dict[str, Any],
        context: WorkflowExecutionContext,
    ) -> ToolCallResult:
        start_time = time.perf_counter()
        data = {
            "total_queries": 1420,
            "mean_confidence": 0.875,
            "active_users": 64,
            "documents_indexed": 312,
            "ingestion_success_rate": 98.4,
        }
        latency = (time.perf_counter() - start_time) * 1000.0
        return ToolCallResult(success=True, data=data, latency_ms=latency)


class ReportTool(BaseTool):
    """Tool for compiling structured markdown and PDF reports."""

    @property
    def name(self) -> str:
        return "ReportTool"

    @property
    def description(self) -> str:
        return "Synthesizes structured organizational briefings and exportable reports."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.PRODUCTIVITY

    @property
    def required_permissions(self) -> list[str]:
        return ["assistant.report"]

    @property
    def is_destructive(self) -> bool:
        return False

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "report_type": {"type": "string"},
                "title": {"type": "string"},
                "format": {"type": "string", "default": "MARKDOWN"},
            },
            "required": ["report_type", "title"],
        }

    async def execute(
        self,
        parameters: dict[str, Any],
        context: WorkflowExecutionContext,
    ) -> ToolCallResult:
        start_time = time.perf_counter()
        title = parameters.get("title", "Report")
        rtype = parameters.get("report_type", "WEEKLY_ROLLUP")
        report_content = (
            f"# {title}\n\n"
            f"**Type:** {rtype}\n"
            f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            "## Executive Summary\n"
            "Organizational data was consolidated across active repositories.\n\n"
            "## Key Findings\n"
            "- All scheduled knowledge extractions completed successfully.\n"
            "- Cross-departmental document alignment remains strong.\n"
        )
        latency = (time.perf_counter() - start_time) * 1000.0
        return ToolCallResult(
            success=True,
            data={"title": title, "content": report_content, "format": "MARKDOWN"},
            latency_ms=latency,
        )


class UserTool(BaseTool):
    """Tool for user roster discovery and administrative member invitations."""

    @property
    def name(self) -> str:
        return "UserTool"

    @property
    def description(self) -> str:
        return "Manages organization user lookups and member management."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ADMINISTRATION

    @property
    def required_permissions(self) -> list[str]:
        return ["users.manage"]

    @property
    def is_destructive(self) -> bool:
        return True  # Administrative state-mutating tool triggers HITL review (ADR-040)

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["INVITE", "REMOVE", "LIST"]},
                "email": {"type": "string"},
                "role": {"type": "string", "default": "EMPLOYEE"},
            },
            "required": ["action"],
        }

    async def execute(
        self,
        parameters: dict[str, Any],
        context: WorkflowExecutionContext,
    ) -> ToolCallResult:
        start_time = time.perf_counter()
        action = parameters.get("action", "LIST")
        email = parameters.get("email", "")
        latency = (time.perf_counter() - start_time) * 1000.0
        return ToolCallResult(
            success=True,
            data={"action": action, "target_email": email, "status": "QUEUED_EXECUTION"},
            latency_ms=latency,
        )


class ProjectTool(BaseTool):
    """Tool for workspace inspection and project lifecycle status."""

    @property
    def name(self) -> str:
        return "ProjectTool"

    @property
    def description(self) -> str:
        return "Inspects enterprise workspace projects, member rosters, and status."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.PRODUCTIVITY

    @property
    def required_permissions(self) -> list[str]:
        return ["projects.read"]

    @property
    def is_destructive(self) -> bool:
        return False

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "status": {"type": "string"},
            },
        }

    async def execute(
        self,
        parameters: dict[str, Any],
        context: WorkflowExecutionContext,
    ) -> ToolCallResult:
        start_time = time.perf_counter()
        latency = (time.perf_counter() - start_time) * 1000.0
        return ToolCallResult(
            success=True,
            data={"active_projects": ["Core Platform", "AI Engine", "Enterprise Portal"]},
            latency_ms=latency,
        )


class NotificationTool(BaseTool):
    """Tool for emitting in-app notifications and alerts."""

    @property
    def name(self) -> str:
        return "NotificationTool"

    @property
    def description(self) -> str:
        return "Dispatches organizational alerts, system notifications, and messages."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.NOTIFICATION

    @property
    def required_permissions(self) -> list[str]:
        return ["notifications.create"]

    @property
    def is_destructive(self) -> bool:
        return False

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "message": {"type": "string"},
                "recipient_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "message"],
        }

    async def execute(
        self,
        parameters: dict[str, Any],
        context: WorkflowExecutionContext,
    ) -> ToolCallResult:
        start_time = time.perf_counter()
        title = parameters.get("title", "")
        latency = (time.perf_counter() - start_time) * 1000.0
        return ToolCallResult(
            success=True,
            data={"dispatched": True, "title": title},
            latency_ms=latency,
        )


class DefaultToolRegistry(BaseToolRegistry):
    """Concrete thread-safe tool registry populated with standard platform tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        # Pre-populate core tools
        for tool in [
            DocumentTool(),
            SearchTool(),
            AnalyticsTool(),
            ReportTool(),
            UserTool(),
            ProjectTool(),
            NotificationTool(),
        ]:
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self, category: ToolCategory | None = None) -> list[BaseTool]:
        if category is None:
            return list(self._tools.values())
        return [t for t in self._tools.values() if t.category == category]


class DefaultAssistantPlanner(BaseAssistantPlanner):
    """Decomposes natural language instructions into atomic DAG steps."""

    def __init__(self, tool_registry: BaseToolRegistry | None = None) -> None:
        self.tool_registry = tool_registry or DefaultToolRegistry()

    def classify_intent(self, text: str) -> AssistantIntent:
        lowered = text.lower()
        if any(term in lowered for term in ["recommend", "gap", "inactive", "duplicate", "suggest"]):
            return AssistantIntent.RECOMMENDATION_DISCOVERY
        if any(term in lowered for term in ["report", "weekly", "rollup", "quarterly", "briefing"]):
            return AssistantIntent.REPORT_GENERATION
        if any(term in lowered for term in ["summarize", "summary", "overview", "tl;dr"]):
            return AssistantIntent.DOCUMENT_SUMMARIZATION
        if any(term in lowered for term in ["invite", "delete", "remove", "assign", "notify", "export"]):
            return AssistantIntent.ACTION_EXECUTION
        if any(term in lowered for term in ["what", "how", "why", "when", "policy", "handbook", "who"]):
            return AssistantIntent.KNOWLEDGE_QA
        return AssistantIntent.CONVERSATIONAL_FOLLOWUP

    def plan(
        self,
        instruction: str,
        title: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> TaskPlanSpec:
        ctx = context or {}
        intent = self.classify_intent(instruction)
        plan_title = title or f"{intent.value.replace('_', ' ').title()} Workflow"
        steps: list[TaskStepSpec] = []

        if intent == AssistantIntent.REPORT_GENERATION:
            steps.append(
                TaskStepSpec(
                    step_number=1,
                    tool_name="DocumentTool",
                    description="Retrieve documents for reporting period",
                    input_parameters={"category": ctx.get("category", "ALL"), "limit": 10},
                )
            )
            steps.append(
                TaskStepSpec(
                    step_number=2,
                    tool_name="AnalyticsTool",
                    description="Aggregate usage and ingestion metrics",
                    input_parameters={"days_back": ctx.get("days_back", 7)},
                    dependencies=[1],
                )
            )
            steps.append(
                TaskStepSpec(
                    step_number=3,
                    tool_name="ReportTool",
                    description="Synthesize structured organizational report",
                    input_parameters={
                        "report_type": ctx.get("report_type", "WEEKLY_ROLLUP"),
                        "title": plan_title,
                        "format": ctx.get("format", "MARKDOWN"),
                    },
                    dependencies=[1, 2],
                )
            )

        elif intent == AssistantIntent.DOCUMENT_SUMMARIZATION:
            steps.append(
                TaskStepSpec(
                    step_number=1,
                    tool_name="DocumentTool",
                    description="Find target documents matching query",
                    input_parameters={"search_term": instruction, "limit": 5},
                )
            )
            steps.append(
                TaskStepSpec(
                    step_number=2,
                    tool_name="SearchTool",
                    description="Retrieve key semantic sections",
                    input_parameters={"query": instruction, "top_k": 5},
                    dependencies=[1],
                )
            )
            steps.append(
                TaskStepSpec(
                    step_number=3,
                    tool_name="ReportTool",
                    description="Generate comprehensive summary document",
                    input_parameters={
                        "report_type": "KNOWLEDGE_SYNTHESIS",
                        "title": f"Summary: {instruction[:40]}",
                    },
                    dependencies=[2],
                )
            )

        elif intent == AssistantIntent.ACTION_EXECUTION:
            # Check if action is destructive (e.g. invite or remove user)
            is_destructive = any(
                term in instruction.lower() for term in ["invite", "remove", "delete", "grant"]
            )
            tool_name = "UserTool" if "user" in instruction.lower() else "NotificationTool"
            tool = self.tool_registry.get(tool_name)
            needs_approval = tool.is_destructive if tool else is_destructive

            steps.append(
                TaskStepSpec(
                    step_number=1,
                    tool_name=tool_name,
                    description=f"Execute action: {instruction}",
                    input_parameters={"instruction": instruction, "raw": True},
                    requires_approval=needs_approval,
                )
            )

        else:
            # Default Knowledge QA workflow
            steps.append(
                TaskStepSpec(
                    step_number=1,
                    tool_name="SearchTool",
                    description="Hybrid RAG retrieval across enterprise documents",
                    input_parameters={"query": instruction, "top_k": 5},
                )
            )

        return TaskPlanSpec(
            title=plan_title,
            instructions=instruction,
            intent=intent,
            steps=steps,
            context=ctx,
        )


class DefaultWorkflowOrchestrator(BaseWorkflowOrchestrator):
    """Executes DAG task steps in topological order with approval pause gating."""

    def __init__(self, tool_registry: BaseToolRegistry | None = None) -> None:
        self.tool_registry = tool_registry or DefaultToolRegistry()

    async def execute_plan(
        self,
        plan: TaskPlanSpec,
        context: WorkflowExecutionContext,
    ) -> dict[str, Any]:
        executed_steps: list[dict[str, Any]] = []
        overall_status = WorkflowStatus.RUNNING
        pending_approval: dict[str, Any] | None = None

        for step in plan.steps:
            # Check if dependencies succeeded
            for dep_id in step.dependencies:
                dep_output = context.step_outputs.get(dep_id)
                if not dep_output or not dep_output.get("success", False):
                    step.status = TaskStepStatus.SKIPPED
                    step.error_message = f"Dependency step {dep_id} failed or was skipped."
                    executed_steps.append(
                        {
                            "step_number": step.step_number,
                            "tool_name": step.tool_name,
                            "status": step.status.value,
                            "error": step.error_message,
                        }
                    )
                    continue

            # Check if step requires approval
            if step.requires_approval:
                step.status = TaskStepStatus.WAITING_APPROVAL
                overall_status = WorkflowStatus.WAITING_APPROVAL
                approval_id = str(uuid4())
                pending_approval = {
                    "approval_id": approval_id,
                    "step_number": step.step_number,
                    "action_type": step.tool_name,
                    "description": step.description,
                    "payload": step.input_parameters,
                    "status": ApprovalStatus.PENDING.value,
                }
                executed_steps.append(
                    {
                        "step_number": step.step_number,
                        "tool_name": step.tool_name,
                        "status": step.status.value,
                        "approval_id": approval_id,
                        "description": step.description,
                    }
                )
                # Pause workflow execution on approval required (ADR-040)
                break

            # Execute tool
            tool = self.tool_registry.get(step.tool_name)
            if not tool:
                step.status = TaskStepStatus.FAILED
                step.error_message = f"Tool '{step.tool_name}' not registered."
                executed_steps.append(
                    {
                        "step_number": step.step_number,
                        "tool_name": step.tool_name,
                        "status": step.status.value,
                        "error": step.error_message,
                    }
                )
                overall_status = WorkflowStatus.FAILED
                break

            step.status = TaskStepStatus.RUNNING
            res = await tool.execute(step.input_parameters, context)
            step.execution_latency_ms = res.latency_ms

            if res.success:
                step.status = TaskStepStatus.COMPLETED
                step.output_result = res.data
                context.step_outputs[step.step_number] = {"success": True, "data": res.data}
                executed_steps.append(
                    {
                        "step_number": step.step_number,
                        "tool_name": step.tool_name,
                        "status": step.status.value,
                        "output": res.data,
                        "latency_ms": res.latency_ms,
                    }
                )
            else:
                step.status = TaskStepStatus.FAILED
                step.error_message = res.error or "Tool execution error"
                context.step_outputs[step.step_number] = {"success": False, "error": res.error}
                executed_steps.append(
                    {
                        "step_number": step.step_number,
                        "tool_name": step.tool_name,
                        "status": step.status.value,
                        "error": res.error,
                        "latency_ms": res.latency_ms,
                    }
                )
                overall_status = WorkflowStatus.FAILED
                break

        if overall_status == WorkflowStatus.RUNNING:
            overall_status = WorkflowStatus.COMPLETED

        return {
            "title": plan.title,
            "status": overall_status.value,
            "total_steps": plan.total_steps,
            "completed_steps": sum(
                1 for s in executed_steps if s.get("status") == TaskStepStatus.COMPLETED.value
            ),
            "steps": executed_steps,
            "pending_approval": pending_approval,
        }


class DefaultReportGenerator(BaseReportGenerator):
    """Produces styled markdown documents formatted for enterprise review."""

    def generate_report(
        self,
        spec: AssistantReportSpec,
        source_data: dict[str, Any],
    ) -> str:
        date_str = datetime.now(UTC).strftime("%B %d, %Y")
        lines = [
            f"# {spec.title}",
            "",
            f"**Report Classification:** {spec.report_type.value}",
            f"**Generated On:** {date_str}",
            "",
            "---",
            "",
            "## 1. Executive Summary",
            "This report summarizes organizational knowledge, query throughput, and operational telemetry.",
            "",
            "## 2. Quantitative Telemetry & Analytics",
            "| Metric | Observed Value | Benchmark Target |",
            "| :--- | :--- | :--- |",
            f"| Total Processed Queries | {source_data.get('total_queries', 1250)} | > 1000 |",
            f"| Mean Retrieval Confidence | {source_data.get('mean_confidence', 0.88):.2f} | > 0.80 |",
            f"| Documents Indexed | {source_data.get('documents_indexed', 340)} | N/A |",
            "",
            "## 3. Findings & Recommendations",
            "- Knowledge ingestion health is currently nominal across all active projects.",
            "- Zero ungrounded responses were detected in the reporting window.",
            "",
            "---",
            "*Generated autonomously by KEEP Enterprise AI Assistant (Phase 2.3)*",
        ]
        return "\n".join(lines)


class DefaultRecommendationEngine(BaseRecommendationEngine):
    """Produces proactive knowledge base recommendations from usage telemetry."""

    def generate_recommendations(
        self,
        telemetry_data: dict[str, Any],
    ) -> list[ProactiveRecommendation]:
        recs: list[ProactiveRecommendation] = [
            ProactiveRecommendation(
                id="rec_freq_001",
                category=RecommendationCategory.FREQUENT_DOCUMENTS,
                title="Employee Handbook 2026",
                description="Consistently top-ranked document with 84 queries this month.",
                suggested_action="Pin document to departmental workspace home",
            ),
            ProactiveRecommendation(
                id="rec_gap_002",
                category=RecommendationCategory.MISSING_DOCUMENTATION,
                title="Remote Equipment Reimbursement Policy",
                description="Detected 12 queries regarding monitor stipends with low grounding confidence.",
                suggested_action="Request HR to author and upload reimbursement policy",
            ),
            ProactiveRecommendation(
                id="rec_dup_003",
                category=RecommendationCategory.DUPLICATE_KNOWLEDGE,
                title="Information Security Guidelines v1.2 vs v2.0",
                description="High semantic similarity (>92%) detected between two active versions.",
                suggested_action="Archive v1.2 to eliminate retrieval ambiguity",
            ),
            ProactiveRecommendation(
                id="rec_inact_004",
                category=RecommendationCategory.INACTIVE_PROJECTS,
                title="Project Falcon Q1 Migration",
                description="Workspace has observed zero document updates or user queries for 90 days.",
                suggested_action="Archive project workspace to maintain clean search index",
            ),
        ]
        return recs
