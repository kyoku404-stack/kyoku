"""KEEP Phase 4.11 — Proactive Enterprise Intelligence FastAPI Endpoints.

Exposes:
- `GET  /api/v1/intelligence/insights`
- `GET  /api/v1/intelligence/insights/{insight_id}`
- `GET  /api/v1/intelligence/insights/{insight_id}/evidence`
- `POST /api/v1/intelligence/insights/{insight_id}/feedback`
- `POST /api/v1/intelligence/insights/{insight_id}/dismiss`
- `POST /api/v1/intelligence/insights/{insight_id}/resolve`
- `POST /api/v1/intelligence/insights/{insight_id}/investigate`
- `GET  /api/v1/intelligence/runs/{run_id}`
- `POST /api/v1/intelligence/scans`
- `GET  /api/v1/intelligence/metrics`
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import AgentLayerError
from backend.app.agents.intelligence.contracts import (
    DetectionRunRecord,
    EvidenceReference,
    InsightCategory,
    InsightDismissRequest,
    InsightFeedbackRecord,
    InsightFeedbackRequest,
    InsightInvestigateRequest,
    InsightResolveRequest,
    InsightStatus,
    IntelligenceInsight,
    IntelligenceSecurityContext,
    OperationalMetrics,
    ScanRequest,
)
from backend.app.agents.intelligence.repository import SqlAlchemyIntelligenceRepository
from backend.app.agents.intelligence.service import IntelligenceService
from backend.app.agents.intelligence_detectors import build_default_detectors
from backend.app.agents.orchestration.workflow_contracts import WorkflowRequest
from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.core.exceptions import AppException
from backend.app.db.session import async_session_factory
from backend.app.schemas.envelope import ApiResponse
from backend.app.services.ai.interfaces import AIPermission
from fastapi import APIRouter, Depends, Query, Request, status

router = APIRouter(tags=["Proactive Intelligence"])


def _to_security_context(user: AuthenticatedUser) -> IntelligenceSecurityContext:
    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
    perms = sorted(str(p.value if hasattr(p, "value") else p) for p in getattr(user, "permissions", ()))
    return IntelligenceSecurityContext(
        tenant_id=str(user.organization_id),
        user_id=str(user.id),
        roles=[role_val],
        permissions=perms,
    )


def _raise_http(exc: AgentLayerError) -> None:
    raise AppException(
        message=str(exc),
        code=exc.code.value,
        status_code=exc.http_status,
        details=exc.details,
    ) from exc


def _build_orchestration_dispatcher(
    request: Request,
) -> Callable[[IntelligenceInsight, str, IntelligenceSecurityContext, str | None], Awaitable[str | None]]:
    async def _dispatch(
        insight: IntelligenceInsight,
        workflow_id: str,
        ctx: IntelligenceSecurityContext,
        notes: str | None,
    ) -> str | None:
        orch = getattr(request.app.state, "orchestration_service", None)
        if orch is None:
            from backend.app.agents.orchestration.service import (
                KeepOrchestrationService,
            )

            orch = KeepOrchestrationService()
            request.app.state.orchestration_service = orch
        agent_ctx = AgentContext(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            roles=ctx.roles,
            permissions=ctx.permissions,
        )
        wf_req = WorkflowRequest(
            workflow_id=workflow_id,
            goal=f"Investigate proactive insight '{insight.title}': {insight.summary}",
            inputs={
                "insight_id": insight.insight_id,
                "category": insight.category,
                "evidence_refs": insight.evidence_refs,
                "notes": notes or "",
            },
            max_steps=8,
        )
        record = await orch.submit_workflow(
            workflow_id=workflow_id,
            request=wf_req,
            context=agent_ctx,
            idempotency_key=f"intel_inv:{ctx.tenant_id}:{insight.insight_id}:{workflow_id}",
        )
        return getattr(record, "workflow_execution_id", None) or getattr(record, "execution_id", None)

    return _dispatch


def get_or_init_intelligence_service(request: Request) -> IntelligenceService:
    svc = getattr(request.app.state, "intelligence_service", None)
    if svc is None:
        svc = IntelligenceService(
            repository=SqlAlchemyIntelligenceRepository(session_factory=async_session_factory),
            detectors=build_default_detectors(),
            orchestration_dispatcher=_build_orchestration_dispatcher(request),
        )
        request.app.state.intelligence_service = svc
    elif svc.orchestration_dispatcher is None:
        svc.orchestration_dispatcher = _build_orchestration_dispatcher(request)
    return svc


@router.get(
    "/intelligence/insights",
    response_model=ApiResponse[list[IntelligenceInsight]],
    summary="List published insights visible to the authenticated user",
)
async def list_insights(
    request: Request,
    category: InsightCategory | None = Query(default=None),
    insight_status: InsightStatus | None = Query(default="published", alias="status"),
    min_priority: float | None = Query(default=None, ge=0.0, le=100.0),
    limit: int = Query(default=50, ge=1, le=200),
    user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[list[IntelligenceInsight]]:
    svc = get_or_init_intelligence_service(request)
    try:
        items = await svc.list_insights(
            _to_security_context(user),
            category=category,
            status=insight_status,
            min_priority=min_priority,
            limit=limit,
        )
        return ApiResponse(success=True, data=items)
    except AgentLayerError as exc:
        _raise_http(exc)


@router.get(
    "/intelligence/insights/{insight_id}",
    response_model=ApiResponse[IntelligenceInsight],
    summary="View insight details and authorized evidence",
)
async def get_insight(
    insight_id: str,
    request: Request,
    user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[IntelligenceInsight]:
    svc = get_or_init_intelligence_service(request)
    try:
        item = await svc.get_insight(insight_id, _to_security_context(user))
        return ApiResponse(success=True, data=item)
    except AgentLayerError as exc:
        _raise_http(exc)


@router.get(
    "/intelligence/insights/{insight_id}/evidence",
    response_model=ApiResponse[list[EvidenceReference]],
    summary="Retrieve authorized supporting source references for an insight",
)
async def get_insight_evidence(
    insight_id: str,
    request: Request,
    user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[list[EvidenceReference]]:
    svc = get_or_init_intelligence_service(request)
    try:
        evidence = await svc.get_insight_evidence(insight_id, _to_security_context(user))
        return ApiResponse(success=True, data=evidence)
    except AgentLayerError as exc:
        _raise_http(exc)


@router.post(
    "/intelligence/insights/{insight_id}/feedback",
    response_model=ApiResponse[InsightFeedbackRecord],
    status_code=status.HTTP_201_CREATED,
    summary="Submit user feedback on an intelligence insight",
)
async def submit_feedback(
    insight_id: str,
    body: InsightFeedbackRequest,
    request: Request,
    user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[InsightFeedbackRecord]:
    svc = get_or_init_intelligence_service(request)
    try:
        rec = await svc.submit_feedback(insight_id, body, _to_security_context(user))
        return ApiResponse(success=True, data=rec)
    except AgentLayerError as exc:
        _raise_http(exc)


@router.post(
    "/intelligence/insights/{insight_id}/dismiss",
    response_model=ApiResponse[IntelligenceInsight],
    summary="Dismiss an insight for user feed or organization-wide",
)
async def dismiss_insight(
    insight_id: str,
    body: InsightDismissRequest,
    request: Request,
    user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[IntelligenceInsight]:
    svc = get_or_init_intelligence_service(request)
    try:
        ins = await svc.dismiss_insight(insight_id, body, _to_security_context(user))
        return ApiResponse(success=True, data=ins)
    except AgentLayerError as exc:
        _raise_http(exc)


@router.post(
    "/intelligence/insights/{insight_id}/resolve",
    response_model=ApiResponse[IntelligenceInsight],
    summary="Mark an insight resolved",
)
async def resolve_insight(
    insight_id: str,
    body: InsightResolveRequest,
    request: Request,
    user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[IntelligenceInsight]:
    svc = get_or_init_intelligence_service(request)
    try:
        ins = await svc.resolve_insight(insight_id, body, _to_security_context(user))
        return ApiResponse(success=True, data=ins)
    except AgentLayerError as exc:
        _raise_http(exc)


@router.post(
    "/intelligence/insights/{insight_id}/investigate",
    response_model=ApiResponse[IntelligenceInsight],
    summary="Launch an approved KEEP workflow to investigate an insight",
)
async def investigate_insight(
    insight_id: str,
    body: InsightInvestigateRequest,
    request: Request,
    user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[IntelligenceInsight]:
    svc = get_or_init_intelligence_service(request)
    try:
        ins = await svc.investigate_insight(insight_id, body, _to_security_context(user))
        return ApiResponse(success=True, data=ins)
    except AgentLayerError as exc:
        _raise_http(exc)


@router.get(
    "/intelligence/runs/{run_id}",
    response_model=ApiResponse[DetectionRunRecord],
    summary="Inspect a proactive detection run",
)
async def get_run(
    run_id: str,
    request: Request,
    user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[DetectionRunRecord]:
    svc = get_or_init_intelligence_service(request)
    try:
        run = await svc.get_run(run_id, _to_security_context(user))
        return ApiResponse(success=True, data=run)
    except AgentLayerError as exc:
        _raise_http(exc)


@router.post(
    "/intelligence/scans",
    response_model=ApiResponse[DetectionRunRecord],
    status_code=status.HTTP_201_CREATED,
    summary="Request an authorized proactive intelligence scan",
)
async def request_scan(
    body: ScanRequest,
    request: Request,
    user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
) -> ApiResponse[DetectionRunRecord]:
    svc = get_or_init_intelligence_service(request)
    try:
        run = await svc.run_scan(body, _to_security_context(user))
        return ApiResponse(success=True, data=run)
    except AgentLayerError as exc:
        _raise_http(exc)


@router.get(
    "/intelligence/metrics",
    response_model=ApiResponse[OperationalMetrics],
    summary="View authorized operational metrics for proactive intelligence",
)
async def get_metrics(
    request: Request,
    user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
) -> ApiResponse[OperationalMetrics]:
    svc = get_or_init_intelligence_service(request)
    try:
        metrics = await svc.get_metrics(_to_security_context(user))
        return ApiResponse(success=True, data=metrics)
    except AgentLayerError as exc:
        _raise_http(exc)


async def handle_proactive_event(
    service: IntelligenceService,
    observation: dict[str, Any],
    ctx: IntelligenceSecurityContext,
    source_event_id: str | None = None,
) -> DetectionRunRecord:
    """Bridges Phase 4.10 events/schedules to Phase 4.11 proactive scan execution."""
    return await service.run_scan(
        ScanRequest(
            observations=[observation],
            trigger_source="event" if source_event_id else "schedule",
            source_event_id=source_event_id,
        ),
        ctx,
    )
