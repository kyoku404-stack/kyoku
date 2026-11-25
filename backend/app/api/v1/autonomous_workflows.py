"""KEEP Phase 4.9 — Autonomous Workflow Engine FastAPI Endpoints.

Exposes:
- `GET    /api/v1/autonomous-workflows`             — List tenant autonomous workflows
- `POST   /api/v1/autonomous-workflows`             — Start an autonomous workflow (HTTP 202)
- `GET    /api/v1/autonomous-workflows/{id}`        — Inspect current state, budget & final result
- `GET    /api/v1/autonomous-workflows/{id}/steps`  — Inspect task execution history
- `GET    /api/v1/autonomous-workflows/{id}/events` — Inspect controller decisions & events
- `POST   /api/v1/autonomous-workflows/{id}/cancel` — Request cancellation
- `POST   /api/v1/autonomous-workflows/{id}/resume` — Resume paused workflow with permission revalidation

Specification: devdocs/p4/p4.9.txt (Section 7) & docs/API/api-contract.md (Section 28)
Owner: Member 4 (API, Persistence, Monitoring & Integration)
"""

from __future__ import annotations

import logging

from backend.app.agents.autonomy.contracts import (
    AutonomousStepRecord,
    AutonomousWorkflowRecord,
    AutonomousWorkflowRequest,
    AutonomySecurityContext,
    AutonomyStatus,
    AutonomyTimelineResponse,
    CancelWorkflowRequest,
    ResumeWorkflowRequest,
)
from backend.app.agents.autonomy.repository import SqlAlchemyAutonomyRepository
from backend.app.agents.autonomy.service import AutonomousWorkflowService
from backend.app.agents.errors import (
    AgentLayerError,
    AutonomousWorkflowAccessDeniedError,
    AutonomousWorkflowApprovalRequiredError,
    AutonomousWorkflowBudgetExhaustedError,
    AutonomousWorkflowCancelledError,
    AutonomousWorkflowDeadlineExceededError,
    AutonomousWorkflowIdempotencyConflictError,
    AutonomousWorkflowInvalidStateError,
    AutonomousWorkflowNotFoundError,
    AutonomousWorkflowPlanRejectedError,
    AutonomousWorkflowPolicyDeniedError,
    AutonomousWorkflowReplanLimitError,
    AutonomousWorkflowTenantViolationError,
    AutonomousWorkflowUnsupportedTypeError,
)
from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.core.exceptions import AppException
from backend.app.db.session import async_session_factory
from backend.app.schemas.envelope import ApiResponse
from backend.app.services.ai.interfaces import AIPermission
from fastapi import APIRouter, Body, Depends, Query, Request, status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Autonomous Workflows"])


def _get_autonomy_service(request: Request) -> AutonomousWorkflowService:
    """Retrieves or lazily initializes AutonomousWorkflowService on app.state."""
    service = getattr(request.app.state, "autonomy_service", None)
    if service is None:
        repo = getattr(request.app.state, "autonomy_repository", None)
        if repo is None:
            repo = SqlAlchemyAutonomyRepository(session_factory=async_session_factory)
            request.app.state.autonomy_repository = repo
        service = AutonomousWorkflowService(
            repository=repo,
            workflow_registry=getattr(request.app.state, "workflow_registry", None),
            agent_registry=getattr(request.app.state, "agent_registry", None),
            planning_service=getattr(request.app.state, "planning_service", None),
            runtime_service=getattr(request.app.state, "agent_runtime", None),
            orchestration_service=getattr(request.app.state, "orchestration_service", None),
            tool_executor=getattr(request.app.state, "tool_executor", None),
            memory_service=getattr(request.app.state, "memory_service", None),
            collaboration_service=getattr(request.app.state, "collaboration_service", None),
        )
        request.app.state.autonomy_service = service
    return service


def _build_security_context(
    current_user: AuthenticatedUser,
    request: Request,
) -> AutonomySecurityContext:
    """Constructs server-side AutonomySecurityContext strictly from verified JWT identity."""
    role_name = (
        current_user.role.value
        if hasattr(current_user.role, "value")
        else str(current_user.role)
    ).lower()
    perms = ["agent.read"]
    if role_name not in ("guest", "viewer"):
        perms.append("agent.invoke")
    if role_name in ("superadmin", "orgadmin", "admin", "manager", "lead"):
        perms.extend(["agent.manage", "agent.approve"])
    return AutonomySecurityContext(
        tenant_id=str(current_user.organization_id),
        user_id=str(current_user.id),
        roles=[role_name],
        permissions=perms,
        correlation_id=request.headers.get("X-Request-ID"),
    )


def _handle_autonomy_error(exc: Exception) -> None:
    """Maps Phase 4.9 domain exceptions to standardized AppException HTTP errors."""
    if isinstance(exc, AutonomousWorkflowNotFoundError):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=exc.code,
            message=str(exc),
        )
    if isinstance(
        exc,
        (
            AutonomousWorkflowAccessDeniedError,
            AutonomousWorkflowTenantViolationError,
            AutonomousWorkflowPolicyDeniedError,
            AutonomousWorkflowApprovalRequiredError,
        ),
    ):
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=exc.code if isinstance(exc, AgentLayerError) else "ACCESS_DENIED",
            message=str(exc),
        )
    if isinstance(
        exc,
        (
            AutonomousWorkflowInvalidStateError,
            AutonomousWorkflowCancelledError,
            AutonomousWorkflowIdempotencyConflictError,
        ),
    ):
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code=exc.code if isinstance(exc, AgentLayerError) else "CONFLICT",
            message=str(exc),
        )
    if isinstance(exc, AutonomousWorkflowBudgetExhaustedError):
        raise AppException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code=exc.code,
            message=str(exc),
        )
    if isinstance(exc, AutonomousWorkflowDeadlineExceededError):
        raise AppException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            code=exc.code,
            message=str(exc),
        )
    if isinstance(exc, AutonomousWorkflowReplanLimitError):
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=exc.code,
            message=str(exc),
        )
    if isinstance(
        exc,
        (
            AutonomousWorkflowUnsupportedTypeError,
            AutonomousWorkflowPlanRejectedError,
            ValueError,
        ),
    ):
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=exc.code if isinstance(exc, AgentLayerError) else "BAD_REQUEST",
            message=str(exc),
        )
    if isinstance(exc, AppException):
        raise exc
    logger.exception("Unexpected autonomous workflow error: %s", exc)
    raise AppException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred in the Autonomous Workflow Engine.",
    )


@router.get(
    "/autonomous-workflows",
    response_model=ApiResponse[list[AutonomousWorkflowRecord]],
    summary="List tenant autonomous workflows",
)
async def list_autonomous_workflows(
    request: Request,
    status_filter: AutonomyStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[list[AutonomousWorkflowRecord]]:
    service = _get_autonomy_service(request)
    sec_ctx = _build_security_context(current_user, request)
    try:
        items = await service.list_workflows(sec_ctx, status=status_filter, limit=limit)
        return ApiResponse(success=True, data=items)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        _handle_autonomy_error(exc)
        raise


@router.post(
    "/autonomous-workflows",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ApiResponse[AutonomousWorkflowRecord],
    summary="Start an autonomous workflow",
)
async def start_autonomous_workflow(
    request_body: AutonomousWorkflowRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[AutonomousWorkflowRecord]:
    service = _get_autonomy_service(request)
    sec_ctx = _build_security_context(current_user, request)
    try:
        record = await service.start_workflow(request_body, sec_ctx)
        return ApiResponse(success=True, data=record)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        _handle_autonomy_error(exc)
        raise


@router.get(
    "/autonomous-workflows/{execution_id}",
    response_model=ApiResponse[AutonomousWorkflowRecord],
    summary="Inspect autonomous workflow state",
)
async def get_autonomous_workflow(
    execution_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[AutonomousWorkflowRecord]:
    service = _get_autonomy_service(request)
    sec_ctx = _build_security_context(current_user, request)
    try:
        record = await service.get_workflow(execution_id, sec_ctx)
        return ApiResponse(success=True, data=record)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        _handle_autonomy_error(exc)
        raise


@router.get(
    "/autonomous-workflows/{execution_id}/steps",
    response_model=ApiResponse[list[AutonomousStepRecord]],
    summary="Inspect autonomous workflow step history",
)
async def list_autonomous_workflow_steps(
    execution_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[list[AutonomousStepRecord]]:
    service = _get_autonomy_service(request)
    sec_ctx = _build_security_context(current_user, request)
    try:
        steps = await service.list_steps(execution_id, sec_ctx)
        return ApiResponse(success=True, data=steps)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        _handle_autonomy_error(exc)
        raise


@router.get(
    "/autonomous-workflows/{execution_id}/events",
    response_model=ApiResponse[AutonomyTimelineResponse],
    summary="Inspect controller decisions and lifecycle events",
)
async def list_autonomous_workflow_events(
    execution_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[AutonomyTimelineResponse]:
    service = _get_autonomy_service(request)
    sec_ctx = _build_security_context(current_user, request)
    try:
        timeline = await service.get_timeline(execution_id, sec_ctx)
        return ApiResponse(success=True, data=timeline)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        _handle_autonomy_error(exc)
        raise


@router.post(
    "/autonomous-workflows/{execution_id}/cancel",
    response_model=ApiResponse[AutonomousWorkflowRecord],
    summary="Cancel an active or paused autonomous workflow",
)
async def cancel_autonomous_workflow(
    execution_id: str,
    request: Request,
    request_body: CancelWorkflowRequest | None = Body(default=None),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[AutonomousWorkflowRecord]:
    service = _get_autonomy_service(request)
    sec_ctx = _build_security_context(current_user, request)
    try:
        payload = request_body or CancelWorkflowRequest()
        record = await service.cancel_workflow(execution_id, payload, sec_ctx)
        return ApiResponse(success=True, data=record)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        _handle_autonomy_error(exc)
        raise


@router.post(
    "/autonomous-workflows/{execution_id}/resume",
    response_model=ApiResponse[AutonomousWorkflowRecord],
    summary="Resume a paused autonomous workflow with permission revalidation",
)
async def resume_autonomous_workflow(
    execution_id: str,
    request: Request,
    request_body: ResumeWorkflowRequest | None = Body(default=None),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[AutonomousWorkflowRecord]:
    service = _get_autonomy_service(request)
    sec_ctx = _build_security_context(current_user, request)
    try:
        payload = request_body or ResumeWorkflowRequest()
        record = await service.resume_workflow(execution_id, payload, sec_ctx)
        return ApiResponse(success=True, data=record)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        _handle_autonomy_error(exc)
        raise
