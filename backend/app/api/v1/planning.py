"""KEEP Phase 4.4 — Planning & Reasoning Engine FastAPI Endpoints.

Exposes:
- `POST /api/v1/plans`                      — Parse goal, generate & validate execution plan
- `GET  /api/v1/plans`                      — List tenant-scoped execution plans
- `GET  /api/v1/plans/{plan_id}`            — Retrieve persisted plan & tasks
- `GET  /api/v1/plans/{plan_id}/validation` — Retrieve validation findings, revisions & audit events
- `POST /api/v1/plans/{plan_id}/revise`     — Revise/replan within bounded replan limit
- `POST /api/v1/plans/{plan_id}/execute`    — Submit validated plan to Phase 4.3 orchestrator

Owner: Member 4 (FastAPI, Persistence & Integration Testing)
Specification: devdocs/p4/p4.4.txt (Section 9) & docs/API/api-contract.md (Section 23)
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.errors import AgentLayerError
from backend.app.agents.persistence.plan_repository import SQLAlchemyPlanRepository
from backend.app.agents.planning.contracts import (
    ExecutionPlan,
    PlanCreateRequest,
    PlanEventRecord,
    PlanExecuteRequest,
    PlanReviseRequest,
    PlanRevisionSnapshot,
    PlanStatus,
    ValidationFinding,
)
from backend.app.agents.planning.orchestrator_bridge import PlanOrchestrationBridge
from backend.app.agents.planning.policies import KeepPlanningPolicyEngine
from backend.app.agents.planning.service import KeepPlanningService
from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.api.v1.agent_workflows import get_orchestration_service
from backend.app.core.exceptions import AppException
from backend.app.db.session import async_session_factory
from backend.app.services.ai.interfaces import AIPermission
from backend.app.services.security.agent_permissions import build_trusted_agent_context
from backend.app.services.security.agent_policy import KeepAgentPolicyEngine
from fastapi import APIRouter, Depends, Query, Request, Response, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/plans", tags=["Agent Planning"])


# ============================================================================
# Dependency Injection Provider
# ============================================================================


def get_planning_service(request: Request) -> KeepPlanningService:
    """Retrieves lifespan-initialized KeepPlanningService from `app.state` (lazy fallback for tests)."""
    service = getattr(request.app.state, "planning_service", None)
    if service is not None:
        return service

    orch_service = get_orchestration_service(request)
    sec_policy = getattr(request.app.state, "agent_policy", None) or KeepAgentPolicyEngine()
    request.app.state.agent_policy = sec_policy

    plan_repo = getattr(request.app.state, "plan_repository", None)
    if plan_repo is None:
        plan_repo = SQLAlchemyPlanRepository(async_session_factory)
        request.app.state.plan_repository = plan_repo

    bridge = getattr(request.app.state, "plan_orchestration_bridge", None)
    if bridge is None:
        bridge = PlanOrchestrationBridge(orch_service)
        request.app.state.plan_orchestration_bridge = bridge

    plan_policy = getattr(request.app.state, "planning_policy", None)
    if plan_policy is None:
        plan_policy = KeepPlanningPolicyEngine(security_policy=sec_policy)
        request.app.state.planning_policy = plan_policy

    service = KeepPlanningService(
        agent_registry=orch_service.runtime.registry,
        plan_repository=plan_repo,
        orchestrator_bridge=bridge,
        policy_engine=plan_policy,
    )
    request.app.state.planning_service = service
    return service


# ============================================================================
# Response Envelopes
# ============================================================================


class PlanSingleResponse(BaseModel):
    success: bool = True
    message: str
    data: ExecutionPlan


class PlanListData(BaseModel):
    items: list[ExecutionPlan]
    total: int


class PlanListResponse(BaseModel):
    success: bool = True
    message: str
    data: PlanListData


class PlanValidationData(BaseModel):
    plan_id: str
    version: int
    status: PlanStatus
    policy_version: str
    approval_required: bool
    approval_reasons: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    validation_findings: list[ValidationFinding] = Field(default_factory=list)
    revisions: list[PlanRevisionSnapshot] = Field(default_factory=list)
    events: list[PlanEventRecord] = Field(default_factory=list)


class PlanValidationResponse(BaseModel):
    success: bool = True
    message: str
    data: PlanValidationData


class PlanExecuteData(BaseModel):
    plan_id: str
    plan_version: int
    plan_status: str
    workflow_execution_id: str
    workflow_status: str
    correlation_id: str
    execution_ids: list[str] = Field(default_factory=list)
    status_url: str
    result_url: str
    steps_url: str
    output: dict[str, Any] = Field(default_factory=dict)


class PlanExecuteResponse(BaseModel):
    success: bool = True
    message: str
    data: PlanExecuteData


def _raise_app_exception(exc: AgentLayerError) -> None:
    detail = exc.to_error_detail()
    raise AppException(
        message=detail.message,
        code=detail.code.value,
        status_code=exc.http_status,
        details=detail.details,
    ) from exc


# ============================================================================
# REST Endpoints
# ============================================================================


@router.post(
    "",
    response_model=PlanSingleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate and validate a multi-agent execution plan",
)
async def create_execution_plan(
    payload: PlanCreateRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    service: KeepPlanningService = Depends(get_planning_service),
) -> PlanSingleResponse:
    req_id = request.headers.get("X-Request-ID")
    context = build_trusted_agent_context(
        current_user,
        correlation_id=payload.correlation_id or req_id,
    )
    try:
        plan = await service.create_plan(payload, context, source_request_id=req_id)
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    return PlanSingleResponse(
        success=plan.status in (PlanStatus.VALIDATED, PlanStatus.APPROVAL_REQUIRED),
        message=f"Plan '{plan.plan_id}' v{plan.version} generated with status '{plan.status.value}'.",
        data=plan,
    )


@router.get(
    "",
    response_model=PlanListResponse,
    status_code=status.HTTP_200_OK,
    summary="List tenant-scoped execution plans",
)
async def list_execution_plans(
    request: Request,
    status_filter: PlanStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepPlanningService = Depends(get_planning_service),
) -> PlanListResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=request.headers.get("X-Request-ID"),
    )
    items = await service.list_plans(context, status=status_filter, limit=limit)
    return PlanListResponse(
        success=True,
        message="Execution plans retrieved successfully.",
        data=PlanListData(items=items, total=len(items)),
    )


@router.get(
    "/{plan_id}",
    response_model=PlanSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a tenant-scoped execution plan",
)
async def get_execution_plan(
    plan_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepPlanningService = Depends(get_planning_service),
) -> PlanSingleResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=request.headers.get("X-Request-ID"),
    )
    try:
        plan = await service.get_plan(plan_id, context)
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    return PlanSingleResponse(
        success=True,
        message="Execution plan retrieved successfully.",
        data=plan,
    )


@router.get(
    "/{plan_id}/validation",
    response_model=PlanValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve validation findings, immutable revisions, and audit events for a plan",
)
async def get_plan_validation(
    plan_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepPlanningService = Depends(get_planning_service),
) -> PlanValidationResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=request.headers.get("X-Request-ID"),
    )
    try:
        plan, revisions, events = await service.get_validation_details(plan_id, context)
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    return PlanValidationResponse(
        success=True,
        message="Plan validation details retrieved successfully.",
        data=PlanValidationData(
            plan_id=plan.plan_id,
            version=plan.version,
            status=plan.status,
            policy_version=plan.policy_version,
            approval_required=plan.approval_required,
            approval_reasons=list(plan.approval_reasons),
            clarification_questions=list(plan.clarification_questions),
            validation_findings=list(plan.validation_findings),
            revisions=revisions,
            events=events,
        ),
    )


@router.post(
    "/{plan_id}/revise",
    response_model=PlanSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Request a bounded plan revision with fresh policy validation",
)
async def revise_execution_plan(
    plan_id: str,
    payload: PlanReviseRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    service: KeepPlanningService = Depends(get_planning_service),
) -> PlanSingleResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=request.headers.get("X-Request-ID"),
    )
    try:
        revised = await service.revise_plan(plan_id, payload, context)
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    return PlanSingleResponse(
        success=revised.status in (PlanStatus.VALIDATED, PlanStatus.APPROVAL_REQUIRED),
        message=f"Plan '{revised.plan_id}' revised to v{revised.version} (status='{revised.status.value}').",
        data=revised,
    )


@router.post(
    "/{plan_id}/execute",
    response_model=PlanExecuteResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a validated execution plan to KEEP's Phase 4.3 Orchestration Engine",
)
async def execute_validated_plan(
    plan_id: str,
    request: Request,
    response: Response,
    payload: PlanExecuteRequest | None = None,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    service: KeepPlanningService = Depends(get_planning_service),
) -> PlanExecuteResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=request.headers.get("X-Request-ID"),
    )
    req_body = payload or PlanExecuteRequest()
    try:
        submitted_plan, wf_record = await service.execute_plan(plan_id, req_body, context)
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    if req_body.mode == "async":
        response.status_code = status.HTTP_202_ACCEPTED
    else:
        response.status_code = status.HTTP_200_OK

    output_payload = wf_record.result.output if wf_record.result is not None else {}
    return PlanExecuteResponse(
        success=True,
        message=f"Plan '{submitted_plan.plan_id}' submitted as workflow '{wf_record.workflow_execution_id}'.",
        data=PlanExecuteData(
            plan_id=submitted_plan.plan_id,
            plan_version=submitted_plan.version,
            plan_status=submitted_plan.status.value,
            workflow_execution_id=wf_record.workflow_execution_id,
            workflow_status=wf_record.status.value,
            correlation_id=wf_record.correlation_id,
            execution_ids=list(wf_record.execution_ids),
            status_url=wf_record.status_url,
            result_url=wf_record.result_url,
            steps_url=wf_record.steps_url,
            output=output_payload,
        ),
    )
