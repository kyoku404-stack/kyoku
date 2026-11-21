"""KEEP Phase 4.8 — Multi-Agent Collaboration FastAPI Endpoints.

Exposes:
- `POST   /api/v1/collaborations`                  — Start a new multi-agent collaboration session (HTTP 202)
- `GET    /api/v1/collaborations/{session_id}`     — Retrieve collaboration session details and status
- `GET    /api/v1/collaborations/{session_id}/tasks` — List assigned tasks and statuses
- `GET    /api/v1/collaborations/{session_id}/messages` — Query inter-agent messages
- `GET    /api/v1/collaborations/{session_id}/findings` — Retrieve verifiable agent findings
- `GET    /api/v1/collaborations/{session_id}/reviews` — View peer review evaluations
- `POST   /api/v1/collaborations/{session_id}/cancel`  — Abort/cancel an active session
- `POST   /api/v1/collaborations/{session_id}/resolve-conflict` — Submit supervisory conflict resolution

Specification: devdocs/p4/p4.8.txt (Section 10) & docs/API/api-contract.md (Section 27)
Owner: Member 4 (Persistence, LangGraph Integration, FastAPI Endpoints & Full QA)
"""

from __future__ import annotations

import logging

from backend.app.agents.collaboration.contracts import (
    CancelSessionRequest,
    CollaborationConflict,
    CollaborationFinding,
    CollaborationMessage,
    CollaborationRequest,
    CollaborationSecurityContext,
    CollaborationSession,
    CollaborationTask,
    ConflictResolutionRequest,
    ReviewResult,
)
from backend.app.agents.collaboration.repository import (
    SqlAlchemyCollaborationRepository,
)
from backend.app.agents.collaboration.service import CollaborationService
from backend.app.agents.errors import (
    AgentLayerError,
    CollaborationAccessDeniedError,
    CollaborationAgentCapabilityMismatchError,
    CollaborationAgentNotRegisteredError,
    CollaborationConflictDetectedError,
    CollaborationConflictUnresolvedError,
    CollaborationMaxRevisionsExceededError,
    CollaborationMessageInvalidError,
    CollaborationReviewFailedError,
    CollaborationSessionCancelledError,
    CollaborationSessionCompletedError,
    CollaborationSessionNotFoundError,
    CollaborationTaskDependencyFailedError,
    CollaborationTaskNotFoundError,
    CollaborationTenantIsolationViolationError,
)
from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.core.exceptions import AppException
from backend.app.schemas.envelope import ApiResponse
from backend.app.services.ai.interfaces import AIPermission
from fastapi import APIRouter, Depends, Query, Request, status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Multi-Agent Collaboration"])


def _get_collaboration_service(request: Request) -> CollaborationService:
    """Retrieves or lazily initializes CollaborationService on app.state."""
    service = getattr(request.app.state, "collaboration_service", None)
    if service is None:
        repo = getattr(request.app.state, "collaboration_repository", None)
        if repo is None:
            repo = SqlAlchemyCollaborationRepository()
            request.app.state.collaboration_repository = repo
        service = CollaborationService(repository=repo)
        request.app.state.collaboration_service = service
    return service


def _build_security_context(current_user: AuthenticatedUser) -> CollaborationSecurityContext:
    """Constructs server-side CollaborationSecurityContext from verified JWT."""
    role_name = (
        current_user.role.value
        if hasattr(current_user.role, "value")
        else str(current_user.role)
    )
    return CollaborationSecurityContext(
        tenant_id=str(current_user.organization_id),
        user_id=str(current_user.id),
        roles=[role_name.lower()],
        permissions=["agent.invoke", "agent.read"],
    )


def _handle_collaboration_error(exc: Exception) -> None:
    """Translates domain collaboration exceptions into standardized HTTP responses."""
    if isinstance(exc, (CollaborationSessionNotFoundError, CollaborationTaskNotFoundError)):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=exc.code if isinstance(exc, AgentLayerError) else "NOT_FOUND",
            message=str(exc),
        )
    if isinstance(exc, (CollaborationAccessDeniedError, CollaborationTenantIsolationViolationError)):
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=exc.code if isinstance(exc, AgentLayerError) else "ACCESS_DENIED",
            message=str(exc),
        )
    if isinstance(exc, (CollaborationConflictDetectedError, CollaborationConflictUnresolvedError)):
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code=exc.code if isinstance(exc, AgentLayerError) else "CONFLICT",
            message=str(exc),
        )
    if isinstance(exc, (CollaborationReviewFailedError, CollaborationMaxRevisionsExceededError)):
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=exc.code if isinstance(exc, AgentLayerError) else "UNPROCESSABLE_ENTITY",
            message=str(exc),
        )
    if isinstance(
        exc,
        (
            CollaborationSessionCompletedError,
            CollaborationSessionCancelledError,
            CollaborationMessageInvalidError,
            CollaborationAgentNotRegisteredError,
            CollaborationAgentCapabilityMismatchError,
            CollaborationTaskDependencyFailedError,
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

    logger.exception("Unexpected error in collaboration endpoint: %s", exc)
    raise AppException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred during collaboration processing.",
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/collaborations",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ApiResponse[CollaborationSession],
    summary="Start a multi-agent collaboration session",
)
async def start_collaboration(
    request_body: CollaborationRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[CollaborationSession]:
    """Initiates a collaboration session and registers initial subtasks."""
    service = _get_collaboration_service(request)
    sec_ctx = _build_security_context(current_user)
    try:
        session = await service.start_session(request_body, sec_ctx)
        return ApiResponse(success=True, data=session)
    except Exception as exc:
        _handle_collaboration_error(exc)
        raise


@router.get(
    "/collaborations/{session_id}",
    response_model=ApiResponse[CollaborationSession],
    summary="Get collaboration session details",
)
async def get_collaboration(
    session_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[CollaborationSession]:
    """Retrieves session status, metadata, and final synthesis report."""
    service = _get_collaboration_service(request)
    sec_ctx = _build_security_context(current_user)
    try:
        session = await service.get_session(session_id, sec_ctx)
        return ApiResponse(success=True, data=session)
    except Exception as exc:
        _handle_collaboration_error(exc)
        raise


@router.get(
    "/collaborations/{session_id}/tasks",
    response_model=ApiResponse[list[CollaborationTask]],
    summary="List tasks assigned in collaboration session",
)
async def list_collaboration_tasks(
    session_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[list[CollaborationTask]]:
    """Lists subtasks, assigned agents, statuses, and outputs."""
    service = _get_collaboration_service(request)
    sec_ctx = _build_security_context(current_user)
    try:
        tasks = await service.list_tasks(session_id, sec_ctx)
        return ApiResponse(success=True, data=tasks)
    except Exception as exc:
        _handle_collaboration_error(exc)
        raise


@router.get(
    "/collaborations/{session_id}/messages",
    response_model=ApiResponse[list[CollaborationMessage]],
    summary="Query inter-agent messages",
)
async def list_collaboration_messages(
    session_id: str,
    request: Request,
    task_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[list[CollaborationMessage]]:
    """Lists messages exchanged between agents in a session."""
    service = _get_collaboration_service(request)
    sec_ctx = _build_security_context(current_user)
    try:
        messages = await service.list_messages(
            session_id=session_id,
            security_context=sec_ctx,
            task_id=task_id,
            limit=limit,
        )
        return ApiResponse(success=True, data=messages)
    except Exception as exc:
        _handle_collaboration_error(exc)
        raise


@router.get(
    "/collaborations/{session_id}/findings",
    response_model=ApiResponse[list[CollaborationFinding]],
    summary="Retrieve agent findings with evidence",
)
async def list_collaboration_findings(
    session_id: str,
    request: Request,
    task_id: str | None = Query(default=None),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[list[CollaborationFinding]]:
    """Retrieves verifiable findings and evidence references."""
    service = _get_collaboration_service(request)
    sec_ctx = _build_security_context(current_user)
    try:
        findings = await service.list_findings(
            session_id=session_id,
            security_context=sec_ctx,
            task_id=task_id,
        )
        return ApiResponse(success=True, data=findings)
    except Exception as exc:
        _handle_collaboration_error(exc)
        raise


@router.get(
    "/collaborations/{session_id}/reviews",
    response_model=ApiResponse[list[ReviewResult]],
    summary="View peer review evaluations",
)
async def list_collaboration_reviews(
    session_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[list[ReviewResult]]:
    """Lists peer review outcomes and critique justifications."""
    service = _get_collaboration_service(request)
    sec_ctx = _build_security_context(current_user)
    try:
        reviews = await service.list_reviews(session_id, sec_ctx)
        return ApiResponse(success=True, data=reviews)
    except Exception as exc:
        _handle_collaboration_error(exc)
        raise


@router.post(
    "/collaborations/{session_id}/cancel",
    response_model=ApiResponse[CollaborationSession],
    summary="Cancel a collaboration session",
)
async def cancel_collaboration(
    session_id: str,
    request: Request,
    request_body: CancelSessionRequest | None = None,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[CollaborationSession]:
    """Cancels an ongoing session and marks active tasks cancelled."""
    service = _get_collaboration_service(request)
    sec_ctx = _build_security_context(current_user)
    try:
        cancel_req = request_body or CancelSessionRequest()
        session = await service.cancel_session(session_id, cancel_req, sec_ctx)
        return ApiResponse(success=True, data=session)
    except Exception as exc:
        _handle_collaboration_error(exc)
        raise


@router.post(
    "/collaborations/{session_id}/resolve-conflict",
    response_model=ApiResponse[CollaborationConflict],
    summary="Submit conflict resolution",
)
async def resolve_collaboration_conflict(
    session_id: str,
    request_body: ConflictResolutionRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[CollaborationConflict]:
    """Submits a supervisory resolution for an escalated conflict."""
    service = _get_collaboration_service(request)
    sec_ctx = _build_security_context(current_user)
    try:
        resolved = await service.resolve_conflict(session_id, request_body, sec_ctx)
        return ApiResponse(success=True, data=resolved)
    except Exception as exc:
        _handle_collaboration_error(exc)
        raise
