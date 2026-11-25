"""KEEP Phase 4.10 — Event Ingestion, Inspection, DLQ & Webhook FastAPI Endpoints.

Exposes:
- `POST /api/v1/events`
- `GET  /api/v1/events/dead-letter`
- `GET  /api/v1/events/{event_id}`
- `POST /api/v1/events/deliveries/{delivery_id}/replay`
- `POST /api/v1/webhooks/{source_id}`

Specification: devdocs/p4/p4.10.txt (Section 10)
Owner: Member 4 (Workflow Dispatch, API & Integration)
"""

from __future__ import annotations

import logging
from typing import Any

from backend.app.agents.errors import (
    AgentLayerError,
    EventDuplicateError,
    EventNotFoundError,
    EventTenantMismatchError,
    EventValidationError,
    WebhookAuthenticationError,
    WebhookReplayDetectedError,
)
from backend.app.agents.events.adapters.webhook import (
    WebhookIngestionAdapter,
    WebhookSourceRegistry,
)
from backend.app.agents.events.contracts import (
    EventDeliveryRecord,
    EventInspectionResponse,
    EventPublishRequest,
    WebhookReceipt,
)
from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.api.v1.triggers import (
    build_event_security_context,
    get_or_init_trigger_service,
)
from backend.app.core.exceptions import AppException
from backend.app.schemas.envelope import ApiResponse
from backend.app.services.ai.interfaces import AIPermission
from fastapi import APIRouter, Depends, Header, Query, Request, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Events & Webhooks"])


class EventPublishReceipt(BaseModel):
    event_id: str
    delivery_id: str
    status: str
    deduplicated: bool = False
    dispatches: list[dict[str, Any]] = []


def _get_webhook_adapter(request: Request) -> WebhookIngestionAdapter:
    adapter = getattr(request.app.state, "webhook_adapter", None)
    if adapter is None:
        svc = get_or_init_trigger_service(request)
        src_reg = getattr(request.app.state, "webhook_source_registry", None)
        if src_reg is None:
            src_reg = WebhookSourceRegistry()
            request.app.state.webhook_source_registry = src_reg
        adapter = WebhookIngestionAdapter(svc.ingestion_service, src_reg)
        request.app.state.webhook_adapter = adapter
    return adapter


def _handle_event_error(exc: Exception) -> None:
    if isinstance(exc, EventNotFoundError):
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code=exc.code, message=str(exc))
    if isinstance(exc, WebhookAuthenticationError):
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED, code=exc.code, message=str(exc)
        )
    if isinstance(exc, EventTenantMismatchError):
        raise AppException(status_code=status.HTTP_403_FORBIDDEN, code=exc.code, message=str(exc))
    if isinstance(exc, (EventDuplicateError, WebhookReplayDetectedError)):
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code=exc.code if isinstance(exc, AgentLayerError) else "CONFLICT",
            message=str(exc),
        )
    if isinstance(exc, (EventValidationError, ValueError)):
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=exc.code if isinstance(exc, AgentLayerError) else "VALIDATION_ERROR",
            message=str(exc),
        )
    if isinstance(exc, AppException):
        raise exc
    logger.exception("Unexpected error in events endpoint: %s", exc)
    raise AppException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred processing event request.",
    )


@router.post(
    "/events",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ApiResponse[EventPublishReceipt],
    summary="Accept and enqueue an authenticated internal KEEP event",
)
async def publish_event(
    body: EventPublishRequest,
    request: Request,
    process_sync: bool = Query(default=True),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[EventPublishReceipt]:
    svc = get_or_init_trigger_service(request)
    ctx = build_event_security_context(current_user, request)
    try:
        event, delivery, dispatches, deduplicated = await svc.publish_and_process(
            body, ctx, process_immediately=process_sync
        )
        return ApiResponse(
            success=True,
            data=EventPublishReceipt(
                event_id=event.event_id,
                delivery_id=delivery.delivery_id,
                status=event.status,
                deduplicated=deduplicated,
                dispatches=[d.model_dump(mode="json") for d in dispatches],
            ),
        )
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        _handle_event_error(exc)
        raise


@router.get(
    "/events/dead-letter",
    response_model=ApiResponse[list[EventDeliveryRecord]],
    summary="List dead-lettered event deliveries for tenant inspection",
)
async def list_dead_letter_deliveries(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[list[EventDeliveryRecord]]:
    svc = get_or_init_trigger_service(request)
    ctx = build_event_security_context(current_user, request)
    try:
        items = await svc.list_dead_letters(ctx, limit=limit)
        return ApiResponse(success=True, data=items)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        _handle_event_error(exc)
        raise


@router.get(
    "/events/{event_id}",
    response_model=ApiResponse[EventInspectionResponse],
    summary="Inspect event processing status, deliveries, and workflow dispatches",
)
async def inspect_event(
    event_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[EventInspectionResponse]:
    svc = get_or_init_trigger_service(request)
    ctx = build_event_security_context(current_user, request)
    try:
        info = await svc.inspect_event(event_id, ctx)
        return ApiResponse(success=True, data=info)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        _handle_event_error(exc)
        raise


@router.post(
    "/events/deliveries/{delivery_id}/replay",
    response_model=ApiResponse[EventDeliveryRecord],
    summary="Safely replay a dead-lettered event delivery",
)
async def replay_dead_letter_delivery(
    delivery_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[EventDeliveryRecord]:
    svc = get_or_init_trigger_service(request)
    ctx = build_event_security_context(current_user, request)
    try:
        replayed = await svc.replay_dead_letter(delivery_id, ctx)
        return ApiResponse(success=True, data=replayed)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        _handle_event_error(exc)
        raise


@router.post(
    "/webhooks/{source_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ApiResponse[WebhookReceipt],
    summary="Receive an HMAC-authenticated external webhook event",
)
async def receive_external_webhook(
    source_id: str,
    request: Request,
    x_keep_signature: str | None = Header(default=None, alias="X-KEEP-Signature"),
    x_keep_timestamp: str | None = Header(default=None, alias="X-KEEP-Timestamp"),
) -> ApiResponse[WebhookReceipt]:
    adapter = _get_webhook_adapter(request)
    svc = get_or_init_trigger_service(request)
    raw_body = await request.body()
    try:
        receipt = await adapter.handle_webhook(
            source_id=source_id,
            raw_body=raw_body,
            signature_header=x_keep_signature,
            timestamp_header=x_keep_timestamp,
            correlation_id=request.headers.get("X-Request-ID"),
        )
        # Dispatch due delivery immediately if synchronous processing succeeded
        if not receipt.deduplicated:
            src_cfg = adapter.source_registry.get(source_id)
            if src_cfg is not None:
                await svc.worker.process_delivery(receipt.delivery_id, src_cfg.tenant_id)
        return ApiResponse(success=True, data=receipt)
    except (AgentLayerError, ValueError, RuntimeError, AppException) as exc:
        _handle_event_error(exc)
        raise
