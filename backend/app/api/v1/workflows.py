"""KEEP Enterprise Platform — Workflow Automation & Event-Driven Intelligence Endpoints.

Specification: devdocs/p3/p3.4.txt & docs/api/api-contract.md Section 16
Author: Member 2 (Backend & Database Lead)
"""

from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
)
from backend.app.api.dependencies.database import get_db
from backend.app.schemas.envelope import ApiResponse
from backend.app.schemas.workflow import (
    WorkflowAnalyticsResponse,
    WorkflowApprovalItemResponse,
    WorkflowApprovalRequest,
    WorkflowCreateRequest,
    WorkflowExecuteRequest,
    WorkflowExecuteResponse,
    WorkflowExecutionItemResponse,
    WorkflowItemResponse,
    WorkflowTemplateItemResponse,
)
from backend.app.services.workflow.service import EnterpriseWorkflowService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/workflows", tags=["Workflows"])


# =============================================================================
# 16.2 Workflow Creation & Listing
# =============================================================================


@router.post(
    "",
    response_model=ApiResponse[WorkflowItemResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create workflow (REST alias)",
    include_in_schema=False,
)
@router.post(
    "/create",
    response_model=ApiResponse[WorkflowItemResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create workflow",
    description="Registers a new enterprise workflow with ordered DAG steps and trigger rules.",
)
async def create_workflow(
    payload: WorkflowCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[WorkflowItemResponse]:
    """Registers a new workflow definition."""
    workflow = await EnterpriseWorkflowService.create_workflow(
        db=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        payload=payload,
    )
    return ApiResponse(
        success=True,
        message="Workflow created successfully.",
        data=workflow,
    )


@router.get(
    "",
    response_model=ApiResponse[list[WorkflowItemResponse]],
    status_code=status.HTTP_200_OK,
    summary="List workflows (REST alias)",
    include_in_schema=False,
)
@router.get(
    "/list",
    response_model=ApiResponse[list[WorkflowItemResponse]],
    status_code=status.HTTP_200_OK,
    summary="List workflows",
    description="Returns all active or configured workflows for the user's organization.",
)
async def list_workflows(
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    trigger_type: str | None = Query(default=None, description="Filter by trigger mechanism (EVENT, SCHEDULE, MANUAL)"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[WorkflowItemResponse]]:
    """Lists organization workflows."""
    workflows = await EnterpriseWorkflowService.list_workflows(
        db=db,
        organization_id=current_user.organization_id,
        is_active=is_active,
        trigger_type=trigger_type,
    )
    return ApiResponse(
        success=True,
        message="Workflows retrieved successfully.",
        data=workflows,
    )


# =============================================================================
# Execution, Executions History, Templates, Approvals, Analytics (Static Routes)
# =============================================================================


@router.post(
    "/execute",
    response_model=ApiResponse[WorkflowExecuteResponse],
    status_code=status.HTTP_200_OK,
    summary="Execute workflow",
    description="Manually or programmatically triggers workflow execution across DAG steps.",
)
async def execute_workflow(
    payload: WorkflowExecuteRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[WorkflowExecuteResponse]:
    """Triggers execution of a workflow."""
    execution = await EnterpriseWorkflowService.execute_workflow(
        db=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        payload=payload,
    )
    return ApiResponse(
        success=True,
        message="Workflow execution triggered successfully.",
        data=execution,
    )


@router.get(
    "/executions",
    response_model=ApiResponse[list[WorkflowExecutionItemResponse]],
    status_code=status.HTTP_200_OK,
    summary="List workflow executions",
    description="Retrieves execution history audit trail with pagination and status filters.",
)
async def list_workflow_executions(
    workflow_id: UUID | None = Query(default=None, description="Optional workflow ID filter"),
    status_filter: str | None = Query(default=None, alias="status", description="Optional execution status filter"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[WorkflowExecutionItemResponse]]:
    """Retrieves paginated executions."""
    executions, total = await EnterpriseWorkflowService.list_workflow_executions(
        db=db,
        organization_id=current_user.organization_id,
        workflow_id=workflow_id,
        status=status_filter,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(
        success=True,
        message=f"Retrieved {len(executions)} execution records (total: {total}).",
        data=executions,
    )


@router.get(
    "/templates",
    response_model=ApiResponse[list[WorkflowTemplateItemResponse]],
    status_code=status.HTTP_200_OK,
    summary="List workflow templates",
    description="Returns pre-configured enterprise workflow templates matching Chapter 13.",
)
async def list_workflow_templates(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> ApiResponse[list[WorkflowTemplateItemResponse]]:
    """Lists system templates."""
    templates = EnterpriseWorkflowService.list_templates()
    return ApiResponse(
        success=True,
        message="Workflow templates retrieved successfully.",
        data=templates,
    )


@router.get(
    "/approvals/pending",
    response_model=ApiResponse[list[WorkflowApprovalItemResponse]],
    status_code=status.HTTP_200_OK,
    summary="List pending approvals",
    description="Lists all pending approval tickets awaiting decision in the organization.",
)
async def list_pending_approvals(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[WorkflowApprovalItemResponse]]:
    """Lists pending approvals."""
    approvals = await EnterpriseWorkflowService.list_pending_approvals(
        db=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        message="Pending approvals retrieved successfully.",
        data=approvals,
    )


@router.post(
    "/approvals/{id}/decide",
    response_model=ApiResponse[WorkflowApprovalItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Decide workflow approval by ID (REST alias)",
    include_in_schema=False,
)
async def decide_approval_by_id(
    id: UUID,
    payload: dict,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[WorkflowApprovalItemResponse]:
    """Decides a pending approval by path ID."""
    req = WorkflowApprovalRequest(
        approval_id=str(id),
        decision=payload.get("decision", "approved"),
        comments=payload.get("comments"),
    )
    return await approve_workflow(payload=req, current_user=current_user, db=db)


@router.post(
    "/approve",
    response_model=ApiResponse[WorkflowApprovalItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Approve or reject workflow",
    description="Submits a human reviewer decision for a pending workflow execution step.",
)
async def approve_workflow(
    payload: WorkflowApprovalRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[WorkflowApprovalItemResponse]:
    """Submits approval decision."""
    decision_result = await EnterpriseWorkflowService.submit_approval_decision(
        db=db,
        organization_id=current_user.organization_id,
        approver_id=current_user.id,
        payload=payload,
    )
    return ApiResponse(
        success=True,
        message=f"Workflow step decision '{payload.decision}' recorded successfully.",
        data=decision_result,
    )


@router.get(
    "/analytics",
    response_model=ApiResponse[WorkflowAnalyticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Workflow analytics",
    description="Calculates automation throughput, success rates, duration, and AI usage metrics.",
)
async def get_workflow_analytics(
    days: int = Query(default=30, ge=1, le=365, description="Rolling time window in days"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[WorkflowAnalyticsResponse]:
    """Retrieves operational automation KPIs."""
    analytics = await EnterpriseWorkflowService.get_workflow_analytics(
        db=db,
        organization_id=current_user.organization_id,
        days=days,
    )
    return ApiResponse(
        success=True,
        message="Workflow analytics retrieved successfully.",
        data=analytics,
    )


# =============================================================================
# Parameterized ID Routes (Declared after static routes to avoid path collisions)
# =============================================================================


@router.post(
    "/{id}/execute",
    response_model=ApiResponse[WorkflowExecuteResponse],
    status_code=status.HTTP_200_OK,
    summary="Execute workflow by ID (REST alias)",
    include_in_schema=False,
)
async def execute_workflow_by_id(
    id: UUID,
    payload: dict | None = None,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[WorkflowExecuteResponse]:
    """Triggers execution of a workflow by path ID."""
    req = WorkflowExecuteRequest(
        workflow_id=str(id),
        context_data=(payload or {}).get("context_data", {}),
        trigger_metadata=(payload or {}).get("trigger_metadata", {}),
    )
    return await execute_workflow(payload=req, current_user=current_user, db=db)


@router.get(
    "/{id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Get workflow status (REST alias)",
    include_in_schema=False,
)
@router.get(
    "/status/{id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Get workflow status",
    description="Retrieves a workflow's configuration and recent execution runs.",
)
async def get_workflow_status(
    id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    """Retrieves workflow status by ID."""
    status_data = await EnterpriseWorkflowService.get_workflow_status(
        db=db,
        organization_id=current_user.organization_id,
        workflow_id=id,
    )
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{id}' not found.",
        )
    return ApiResponse(
        success=True,
        message="Workflow status retrieved successfully.",
        data=status_data,
    )


@router.delete(
    "/{id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete workflow",
    description="Deletes or archives a workflow definition.",
)
async def delete_workflow(
    id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    """Deletes a workflow."""
    deleted = await EnterpriseWorkflowService.delete_workflow(
        db=db,
        organization_id=current_user.organization_id,
        workflow_id=id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{id}' not found or already deleted.",
        )
    return ApiResponse(
        success=True,
        message="Workflow deleted successfully.",
        data={"deleted": True},
    )
