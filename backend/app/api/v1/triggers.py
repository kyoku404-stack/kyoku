"""KEEP Phase 4.10 — Trigger Management FastAPI Endpoints.

Exposes:
- `POST  /api/v1/triggers`
- `GET   /api/v1/triggers`
- `GET   /api/v1/triggers/{trigger_id}`
- `PATCH /api/v1/triggers/{trigger_id}`
- `POST  /api/v1/triggers/{trigger_id}/enable`
- `POST  /api/v1/triggers/{trigger_id}/disable`
- `GET   /api/v1/triggers/{trigger_id}/runs`
- `POST  /api/v1/triggers/{trigger_id}/schedules`

Specification: devdocs/p4/p4.10.txt (Section 10)
Owner: Member 4 (Workflow Dispatch, API & Integration)
"""

from __future__ import annotations

import logging

from backend.app.agents.errors import (
    AgentLayerError,
    EventTenantMismatchError,
    EventValidationError,
    TriggerAccessDeniedError,
    TriggerAlreadyExistsError,
    TriggerNotFoundError,
    TriggerPolicyDeniedError,
    TriggerRateLimitedError,
    TriggerWorkflowNotAllowedError,
)
from backend.app.agents.events.contracts import EventSecurityContext
from backend.app.agents.events.event_store import SqlAlchemyEventStore
from backend.app.agents.orchestration.graphs import (
    DOCUMENT_ENRICHMENT_DEFINITION,
    build_document_enrichment_graph,
)
from backend.app.agents.triggers.models import (
    ScheduleCreateRequest,
    TriggerCreateRequest,
    TriggerDispatchRecord,
    TriggerRule,
    TriggerSchedule,
    TriggerUpdateRequest,
)
from backend.app.agents.triggers.repository import SqlAlchemyTriggerRepository
from backend.app.agents.triggers.service import TriggerService
from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.core.exceptions import AppException
from backend.app.db.session import async_session_factory
from backend.app.schemas.envelope import ApiResponse
from backend.app.services.ai.interfaces import AIPermission
from fastapi import APIRouter, Depends, Query, Request, status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Event Triggers"])


def get_or_init_trigger_service(request: Request) -> TriggerService:
    """Retrieves or lazily binds lifespan TriggerService on app.state."""
    svc = getattr(request.app.state, "trigger_service", None)
    if svc is None:
        ev_store = getattr(request.app.state, "event_store", None)
        if ev_store is None:
            ev_store = SqlAlchemyEventStore(session_factory=async_session_factory)
            request.app.state.event_store = ev_store
        trg_repo = getattr(request.app.state, "trigger_repository", None)
        if trg_repo is None:
            trg_repo = SqlAlchemyTriggerRepository(session_factory=async_session_factory)
            request.app.state.trigger_repository = trg_repo
        wf_reg = getattr(request.app.state, "workflow_registry", None)
        if wf_reg is not None and not wf_reg.is_registered("document_enrichment"):
            wf_reg.register(
                DOCUMENT_ENRICHMENT_DEFINITION,
                build_document_enrichment_graph,
                validate_deps=False,
            )
        svc = TriggerService(
            event_store=ev_store,
            trigger_repository=trg_repo,
            workflow_registry=wf_reg,
            orchestration_service=getattr(request.app.state, "orchestration_service", None),
            autonomy_service=getattr(request.app.state, "autonomy_service", None),
        )
        request.app.state.trigger_service = svc
    return svc


def build_event_security_context(
    current_user: AuthenticatedUser,
    request: Request,
) -> EventSecurityContext:
    role_name = (
        current_user.role.value
        if hasattr(current_user.role, "value")
        else str(current_user.role)
    ).lower()
    perms = ["agent.read"]
    if role_name not in ("guest", "viewer"):
        perms.extend(["agent.invoke", "agent.manage"])
    return EventSecurityContext(
        tenant_id=str(current_user.organization_id),
        user_id=str(current_user.id),
        roles=[role_name],
        permissions=perms,
        correlation_id=request.headers.get("X-Request-ID"),
    )


def handle_trigger_error(exc: Exception) -> None:
    if isinstance(exc, TriggerNotFoundError):
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code=exc.code, message=str(exc))
    if isinstance(
        exc,
        (TriggerAccessDeniedError, TriggerPolicyDeniedError, EventTenantMismatchError),
    ):
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=exc.code if isinstance(exc, AgentLayerError) else "FORBIDDEN",
            message=str(exc),
        )
    if isinstance(exc, TriggerAlreadyExistsError):
        raise AppException(status_code=status.HTTP_409_CONFLICT, code=exc.code, message=str(exc))
    if isinstance(exc, TriggerRateLimitedError):
        raise AppException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, code=exc.code, message=str(exc)
        )
    if isinstance(exc, (EventValidationError, TriggerWorkflowNotAllowedError, ValueError)):
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=exc.code if isinstance(exc, AgentLayerError) else "VALIDATION_ERROR",
            message=str(exc),
        )
    if isinstance(exc, AppException):
        raise exc
    logger.exception("Unexpected error in triggers endpoint: %s", exc)
    raise AppException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred processing trigger request.",
    )


@router.post(
    "/triggers",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse[TriggerRule],
    summary="Create a declarative trigger rule",
)
async def create_trigger(
    body: TriggerCreateRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[TriggerRule]:
    svc = get_or_init_trigger_service(request)
    ctx = build_event_security_context(current_user, request)
    try:
        rule = await svc.create_trigger(body, ctx)
        return ApiResponse(success=True, data=rule)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        handle_trigger_error(exc)
        raise


@router.get(
    "/triggers",
    response_model=ApiResponse[list[TriggerRule]],
    summary="List authorized trigger rules",
)
async def list_triggers(
    request: Request,
    event_type: str | None = Query(default=None),
    enabled_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[list[TriggerRule]]:
    svc = get_or_init_trigger_service(request)
    ctx = build_event_security_context(current_user, request)
    try:
        items = await svc.list_triggers(
            ctx, event_type=event_type, enabled_only=enabled_only, limit=limit
        )
        return ApiResponse(success=True, data=items)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        handle_trigger_error(exc)
        raise


@router.get(
    "/triggers/{trigger_id}",
    response_model=ApiResponse[TriggerRule],
    summary="Retrieve trigger rule configuration",
)
async def get_trigger(
    trigger_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[TriggerRule]:
    svc = get_or_init_trigger_service(request)
    ctx = build_event_security_context(current_user, request)
    try:
        rule = await svc.get_trigger(trigger_id, ctx)
        return ApiResponse(success=True, data=rule)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        handle_trigger_error(exc)
        raise


@router.patch(
    "/triggers/{trigger_id}",
    response_model=ApiResponse[TriggerRule],
    summary="Update an authorized trigger rule",
)
async def update_trigger(
    trigger_id: str,
    body: TriggerUpdateRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[TriggerRule]:
    svc = get_or_init_trigger_service(request)
    ctx = build_event_security_context(current_user, request)
    try:
        rule = await svc.update_trigger(trigger_id, body, ctx)
        return ApiResponse(success=True, data=rule)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        handle_trigger_error(exc)
        raise


@router.post(
    "/triggers/{trigger_id}/enable",
    response_model=ApiResponse[TriggerRule],
    summary="Enable a trigger rule",
)
async def enable_trigger(
    trigger_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[TriggerRule]:
    svc = get_or_init_trigger_service(request)
    ctx = build_event_security_context(current_user, request)
    try:
        rule = await svc.set_trigger_enabled(trigger_id, enabled=True, security_context=ctx)
        return ApiResponse(success=True, data=rule)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        handle_trigger_error(exc)
        raise


@router.post(
    "/triggers/{trigger_id}/disable",
    response_model=ApiResponse[TriggerRule],
    summary="Disable a trigger rule",
)
async def disable_trigger(
    trigger_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[TriggerRule]:
    svc = get_or_init_trigger_service(request)
    ctx = build_event_security_context(current_user, request)
    try:
        rule = await svc.set_trigger_enabled(trigger_id, enabled=False, security_context=ctx)
        return ApiResponse(success=True, data=rule)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        handle_trigger_error(exc)
        raise


@router.get(
    "/triggers/{trigger_id}/runs",
    response_model=ApiResponse[list[TriggerDispatchRecord]],
    summary="Inspect trigger dispatch and execution history",
)
async def list_trigger_runs(
    trigger_id: str,
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[list[TriggerDispatchRecord]]:
    svc = get_or_init_trigger_service(request)
    ctx = build_event_security_context(current_user, request)
    try:
        runs = await svc.list_trigger_runs(trigger_id, ctx, limit=limit)
        return ApiResponse(success=True, data=runs)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        handle_trigger_error(exc)
        raise


@router.post(
    "/triggers/{trigger_id}/schedules",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse[TriggerSchedule],
    summary="Attach a persistent cron or interval schedule to a trigger",
)
async def attach_trigger_schedule(
    trigger_id: str,
    body: ScheduleCreateRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[TriggerSchedule]:
    svc = get_or_init_trigger_service(request)
    ctx = build_event_security_context(current_user, request)
    try:
        sch = await svc.create_schedule(trigger_id, body, ctx)
        return ApiResponse(success=True, data=sch)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        handle_trigger_error(exc)
        raise
