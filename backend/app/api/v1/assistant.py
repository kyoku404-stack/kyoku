"""KEEP Enterprise Platform — AI Assistant & Agentic Workflows Router (Phase 2.3).

Exposes RESTful endpoints for conversational assistant chat, multi-step task execution,
human-in-the-loop approvals, structured report generation, workflow history,
and proactive organizational recommendations.
Specification: docs/api/api-contract.md Section 10 & devdocs/p2/p2.3.txt Chapters 1-20
Owner: Member 2 (Backend Lead)
"""

from typing import Any
from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
)
from backend.app.api.dependencies.database import get_db
from backend.app.api.dependencies.tenant import TenantContext, get_tenant_context
from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import NotFoundException
from backend.app.schemas.assistant import (
    ApprovalActionRequest,
    ApprovalActionResponseData,
    AssistantChatRequest,
    AssistantChatResponseData,
    ProactiveRecommendationItem,
    RecommendationResponseData,
    ReportGenerateRequest,
    ReportGenerateResponseData,
    TaskExecuteRequest,
    TaskExecuteResponseData,
    WorkflowItemResponse,
    WorkflowListResponseData,
)
from backend.app.schemas.envelope import ApiResponse
from backend.app.services.assistant.service import AssistantService
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/assistant", tags=["Enterprise AI Assistant"])
assistant_service = AssistantService()


@router.post(
    "/chat",
    response_model=ApiResponse[AssistantChatResponseData],
    status_code=status.HTTP_200_OK,
    summary="Chat with Enterprise AI Assistant",
    description="Processes user instruction through NLU, plans workflow, executes tools, and maintains conversation context.",
)
async def assistant_chat(
    request: AssistantChatRequest,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> ApiResponse[AssistantChatResponseData]:
    """Conversational assistant turn with intent classification and tool dispatching."""
    result = await assistant_service.chat(
        db=db,
        user_id=current_user.id,
        organization_id=tenant.organization_id,
        payload=request,
    )
    return ApiResponse(
        success=True,
        message="Assistant message processed successfully.",
        data=result,
    )


@router.post(
    "/task",
    response_model=ApiResponse[TaskExecuteResponseData],
    status_code=status.HTTP_200_OK,
    summary="Execute Multi-Step AI Task",
    description="Formulates and executes an explicit Directed Acyclic Graph (DAG) task plan with tool orchestration.",
)
async def execute_task(
    request: TaskExecuteRequest,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> ApiResponse[TaskExecuteResponseData]:
    """Executes multi-step task workflow."""
    result = await assistant_service.execute_task(
        db=db,
        user_id=current_user.id,
        organization_id=tenant.organization_id,
        payload=request,
    )
    return ApiResponse(
        success=True,
        message="Task plan formulated and execution initiated.",
        data=result,
    )


@router.get(
    "/history",
    response_model=ApiResponse[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Retrieve Conversation History",
    description="Lists chat sessions and chronological message exchanges.",
)
async def get_history(
    session_id: UUID | None = Query(default=None, description="Optional chat session ID filter."),
    page: int = Query(default=1, ge=1, description="Page number."),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size limit."),
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> ApiResponse[dict[str, Any]]:
    """Retrieves conversational memory and sessions."""
    sessions, total = await assistant_service.get_conversation_history(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(
        success=True,
        message="Conversation history retrieved successfully.",
        data={
            "sessions": sessions,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    )


@router.post(
    "/report",
    response_model=ApiResponse[ReportGenerateResponseData],
    status_code=status.HTTP_200_OK,
    summary="Generate Structured Enterprise Report",
    description="Compiles organizational briefings (Meeting summaries, weekly rollups, project audits).",
)
async def generate_report(
    request: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> ApiResponse[ReportGenerateResponseData]:
    """Generates structured markdown/exportable report."""
    report = await assistant_service.generate_report(
        db=db,
        user_id=current_user.id,
        organization_id=tenant.organization_id,
        payload=request,
    )
    return ApiResponse(
        success=True,
        message="Report generated successfully.",
        data=ReportGenerateResponseData(
            report_id=report.id,
            report_type=report.report_type,
            title=report.title,
            format=report.format,
            content=report.content,
            created_at=report.created_at,
        ),
    )


@router.get(
    "/workflows",
    response_model=ApiResponse[WorkflowListResponseData],
    status_code=status.HTTP_200_OK,
    summary="List & Inspect Workflows",
    description="Inspects active, waiting approval, completed, or failed workflow states.",
)
async def list_workflows(
    status_filter: str | None = Query(default=None, alias="status", description="Optional workflow status filter."),
    page: int = Query(default=1, ge=1, description="Page number."),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size limit."),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> ApiResponse[WorkflowListResponseData]:
    """Lists organization workflows."""
    workflows, total = await assistant_service.list_workflows(
        db=db,
        organization_id=tenant.organization_id,
        status=status_filter,
        page=page,
        page_size=page_size,
    )
    items = [
        WorkflowItemResponse(
            id=w.id,
            title=w.title,
            trigger_type=w.trigger_type,
            status=w.status,
            total_steps=w.total_steps,
            completed_steps=w.current_step,
            created_at=w.created_at,
            completed_at=w.completed_at,
        )
        for w in workflows
    ]
    return ApiResponse(
        success=True,
        message="Workflows retrieved successfully.",
        data=WorkflowListResponseData(
            workflows=items,
            total=total,
            page=page,
            page_size=page_size,
        ),
    )


@router.post(
    "/approve",
    response_model=ApiResponse[ApprovalActionResponseData],
    status_code=status.HTTP_200_OK,
    summary="Human-in-the-Loop Action Approval",
    description="Reviews and commits or rejects a pending destructive/sensitive operation.",
)
async def process_approval(
    request: ApprovalActionRequest,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> ApiResponse[ApprovalActionResponseData]:
    """Reviews and resolves pending human-in-the-loop approval."""
    res = await assistant_service.process_approval(
        db=db,
        user_id=current_user.id,
        organization_id=tenant.organization_id,
        payload=request,
    )
    if "error" in res and res.get("status") == "NOT_FOUND":
        raise NotFoundException(
            message=res["error"],
            code=ErrorCode.NOT_FOUND,
        )

    return ApiResponse(
        success=True,
        message="Approval processed and action executed successfully.",
        data=ApprovalActionResponseData(
            approval_id=res["approval_id"],
            workflow_id=res.get("workflow_id"),
            decision=res["decision"],
            status=res["status"],
            executed_at=res["executed_at"],
        ),
    )


@router.get(
    "/recommendations",
    response_model=ApiResponse[RecommendationResponseData],
    status_code=status.HTTP_200_OK,
    summary="Get Proactive Recommendations",
    description="Discovers organizational knowledge gaps, trending documents, and inactive workspaces.",
)
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> ApiResponse[RecommendationResponseData]:
    """Surfaces proactive recommendations."""
    recs = await assistant_service.get_recommendations(
        db=db,
        organization_id=tenant.organization_id,
    )
    items = [
        ProactiveRecommendationItem(
            id=r.id,
            category=r.category.value,
            title=r.title,
            description=r.description,
            suggested_action=r.suggested_action,
            metadata=r.metadata,
        )
        for r in recs
    ]
    return ApiResponse(
        success=True,
        message="Proactive recommendations retrieved successfully.",
        data=RecommendationResponseData(recommendations=items),
    )
