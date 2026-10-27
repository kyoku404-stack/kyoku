"""Unit tests for Phase 2.3 Enterprise AI Assistant & Agentic Workflow contracts.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/assistant
Specification: devdocs/p2/p2.3.txt
"""

from uuid import uuid4

import pytest

from backend.app.services.assistant.contracts import (
    ApprovalStatus,
    AssistantIntent,
    AssistantReportSpec,
    DefaultAssistantPlanner,
    DefaultRecommendationEngine,
    DefaultReportGenerator,
    DefaultToolRegistry,
    DefaultWorkflowOrchestrator,
    RecommendationCategory,
    ReportFormat,
    ReportType,
    ToolCategory,
    WorkflowExecutionContext,
    WorkflowStatus,
)


@pytest.fixture
def execution_context() -> WorkflowExecutionContext:
    return WorkflowExecutionContext(
        organization_id=uuid4(),
        user_id=uuid4(),
        user_roles=["ORG_ADMIN"],
        user_permissions={"assistant.chat", "assistant.task", "documents.read", "rag.query"},
        session_id=uuid4(),
    )


def test_intent_classification():
    planner = DefaultAssistantPlanner()

    assert planner.classify_intent("Generate a weekly report for engineering") == AssistantIntent.REPORT_GENERATION
    assert planner.classify_intent("Summarize all HR documents from last month") == AssistantIntent.DOCUMENT_SUMMARIZATION
    assert planner.classify_intent("Invite new user jane@corp.com with role admin") == AssistantIntent.ACTION_EXECUTION
    assert planner.classify_intent("Suggest recommendations for missing documentation") == AssistantIntent.RECOMMENDATION_DISCOVERY
    assert planner.classify_intent("What is our leave policy?") == AssistantIntent.KNOWLEDGE_QA
    assert planner.classify_intent("Tell me more about that") == AssistantIntent.CONVERSATIONAL_FOLLOWUP


def test_dag_task_planning_report_generation():
    planner = DefaultAssistantPlanner()
    plan = planner.plan("Generate a weekly rollup report", title="Weekly Engineering Report")

    assert plan.intent == AssistantIntent.REPORT_GENERATION
    assert plan.title == "Weekly Engineering Report"
    assert plan.total_steps == 3

    # Verify DAG dependencies
    step1, step2, step3 = plan.steps
    assert step1.tool_name == "DocumentTool"
    assert step1.dependencies == []

    assert step2.tool_name == "AnalyticsTool"
    assert 1 in step2.dependencies

    assert step3.tool_name == "ReportTool"
    assert 1 in step3.dependencies and 2 in step3.dependencies


def test_dag_task_planning_summarization():
    planner = DefaultAssistantPlanner()
    plan = planner.plan("Summarize the enterprise handbook policies")

    assert plan.intent == AssistantIntent.DOCUMENT_SUMMARIZATION
    assert plan.total_steps == 3
    assert plan.steps[0].tool_name == "DocumentTool"
    assert plan.steps[1].tool_name == "SearchTool"
    assert plan.steps[2].tool_name == "ReportTool"


def test_dag_task_planning_action_destructive_approval():
    planner = DefaultAssistantPlanner()
    plan = planner.plan("Invite user alex@corp.com as admin")

    assert plan.intent == AssistantIntent.ACTION_EXECUTION
    assert plan.has_approval_requirement is True
    assert plan.steps[0].requires_approval is True


def test_tool_registry():
    registry = DefaultToolRegistry()

    assert registry.get("DocumentTool") is not None
    assert registry.get("SearchTool") is not None
    assert registry.get("AnalyticsTool") is not None
    assert registry.get("ReportTool") is not None
    assert registry.get("UserTool") is not None
    assert registry.get("ProjectTool") is not None
    assert registry.get("NotificationTool") is not None

    knowledge_tools = registry.list_tools(ToolCategory.KNOWLEDGE)
    assert len(knowledge_tools) >= 2

    # Check destructive flags
    assert registry.get("UserTool").is_destructive is True
    assert registry.get("DocumentTool").is_destructive is False


@pytest.mark.asyncio
async def test_tool_executions(execution_context: WorkflowExecutionContext):
    registry = DefaultToolRegistry()

    doc_tool = registry.get("DocumentTool")
    doc_res = await doc_tool.execute({"category": "HR", "limit": 2}, execution_context)
    assert doc_res.success is True
    assert len(doc_res.data["documents"]) > 0

    search_tool = registry.get("SearchTool")
    search_res = await search_tool.execute({"query": "leave policy", "top_k": 3}, execution_context)
    assert search_res.success is True
    assert len(search_res.data["chunks"]) > 0

    analytics_tool = registry.get("AnalyticsTool")
    analytics_res = await analytics_tool.execute({}, execution_context)
    assert analytics_res.success is True
    assert "total_queries" in analytics_res.data


@pytest.mark.asyncio
async def test_workflow_orchestrator_execution(execution_context: WorkflowExecutionContext):
    planner = DefaultAssistantPlanner()
    orchestrator = DefaultWorkflowOrchestrator()

    plan = planner.plan("Generate weekly report for engineering")
    result = await orchestrator.execute_plan(plan, execution_context)

    assert result["status"] == WorkflowStatus.COMPLETED.value
    assert result["total_steps"] == 3
    assert result["completed_steps"] == 3
    assert len(result["steps"]) == 3
    assert result["pending_approval"] is None


@pytest.mark.asyncio
async def test_workflow_orchestrator_approval_pause(execution_context: WorkflowExecutionContext):
    planner = DefaultAssistantPlanner()
    orchestrator = DefaultWorkflowOrchestrator()

    plan = planner.plan("Invite user ops@corp.com")
    result = await orchestrator.execute_plan(plan, execution_context)

    # Workflow must pause at WAITING_APPROVAL (ADR-040)
    assert result["status"] == WorkflowStatus.WAITING_APPROVAL.value
    assert result["pending_approval"] is not None
    assert result["pending_approval"]["status"] == ApprovalStatus.PENDING.value
    assert result["pending_approval"]["action_type"] == "UserTool"


def test_report_generator():
    generator = DefaultReportGenerator()
    spec = AssistantReportSpec(
        report_type=ReportType.WEEKLY_ROLLUP,
        title="Weekly Executive Summary",
        format=ReportFormat.MARKDOWN,
    )
    content = generator.generate_report(spec, {"total_queries": 1500, "mean_confidence": 0.89})

    assert "# Weekly Executive Summary" in content
    assert "WEEKLY_ROLLUP" in content
    assert "Total Processed Queries" in content


def test_recommendation_engine():
    engine = DefaultRecommendationEngine()
    recs = engine.generate_recommendations({})

    assert len(recs) == 4
    categories = {r.category for r in recs}
    assert RecommendationCategory.FREQUENT_DOCUMENTS in categories
    assert RecommendationCategory.MISSING_DOCUMENTATION in categories
    assert RecommendationCategory.DUPLICATE_KNOWLEDGE in categories
    assert RecommendationCategory.INACTIVE_PROJECTS in categories
