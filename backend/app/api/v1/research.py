"""KEEP Phase 4.5 — Research Agents FastAPI Endpoints.

Exposes:
- `POST /api/v1/research`                         — Launch sync (`200`) or async (`202`) research run
- `GET  /api/v1/research`                         — List tenant-scoped research investigations
- `GET  /api/v1/research/{research_id}`           — Retrieve investigation status, metrics & events
- `GET  /api/v1/research/{research_id}/report`    — Retrieve re-authorized ResearchReport
- `GET  /api/v1/research/{research_id}/evidence`  — Retrieve re-authorized EvidenceItem provenance
- `POST /api/v1/research/{research_id}/cancel`    — Cooperatively cancel an active investigation

Owner: Member 4 (Research Graph, Persistence, API & QA)
Specification: devdocs/p4/p4.5.txt (Section 8) & docs/API/api-contract.md (Section 24)
"""

from __future__ import annotations

from typing import Any, Literal

from backend.app.agents.errors import AgentLayerError
from backend.app.agents.research.agent import KeepResearchAgent
from backend.app.agents.research.contracts import (
    EvidenceItem,
    RequiredOutputType,
    ResearchEventRecord,
    ResearchReport,
    ResearchRequest,
    ResearchRunRecord,
    ResearchStatus,
)
from backend.app.agents.research.graph import build_default_research_agent
from backend.app.agents.research.repository import SQLAlchemyResearchRepository
from backend.app.agents.research.research_service import KeepResearchService
from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.api.v1.agent_executions import get_agent_runtime
from backend.app.core.exceptions import AppException
from backend.app.db.session import async_session_factory
from backend.app.services.ai.interfaces import AIPermission
from backend.app.services.security.agent_permissions import build_trusted_agent_context
from backend.app.services.security.agent_policy import KeepAgentPolicyEngine
from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/research", tags=["Research Agents"])


# ============================================================================
# Dependency Injection Provider
# ============================================================================


def get_research_service(request: Request) -> KeepResearchService:
    """Retrieves lifespan-initialized KeepResearchService from `app.state` (lazy fallback)."""
    service = getattr(request.app.state, "research_service", None)
    if service is not None:
        return service

    sec_policy = getattr(request.app.state, "agent_policy", None) or KeepAgentPolicyEngine()
    request.app.state.agent_policy = sec_policy

    repo = getattr(request.app.state, "research_repository", None)
    if repo is None:
        repo = SQLAlchemyResearchRepository(async_session_factory)
        request.app.state.research_repository = repo

    runtime = get_agent_runtime(request)
    research_agent: KeepResearchAgent
    if runtime.registry.is_registered("research_agent"):
        candidate = runtime.registry.get("research_agent")
        if isinstance(candidate, KeepResearchAgent):
            research_agent = candidate
        else:
            research_agent = build_default_research_agent(policy=sec_policy)
    else:
        research_agent = build_default_research_agent(policy=sec_policy)
        runtime.registry.register(research_agent)

    worker = getattr(request.app.state, "research_worker", None)
    service = KeepResearchService(
        repository=repo,
        research_agent=research_agent,
        agent_runtime=runtime,
        policy=sec_policy,
        worker=worker,
    )
    request.app.state.research_service = service
    return service


# ============================================================================
# Request / Response Schemas
# ============================================================================


class StartResearchPayload(BaseModel):
    """Request payload for `POST /api/v1/research`."""

    question: str = Field(..., min_length=3, max_length=2000)
    scope: str | None = Field(default=None, max_length=1000)
    max_sources: int = Field(default=12, ge=1, le=30)
    required_output: RequiredOutputType = Field(default="detailed_report")
    mode: Literal["sync", "async"] = Field(default="sync")
    filters: dict[str, Any] = Field(default_factory=dict)
    plan_id: str | None = Field(default=None, max_length=128)
    workflow_execution_id: str | None = Field(default=None, max_length=128)


class ResearchLaunchData(BaseModel):
    research_id: str
    status: ResearchStatus
    question: str
    scope: str | None = None
    required_output: RequiredOutputType
    max_sources: int
    agent_execution_id: str | None = None
    correlation_id: str
    status_url: str
    report_url: str
    evidence_url: str
    report: ResearchReport | None = None


class ResearchLaunchResponse(BaseModel):
    success: bool = True
    message: str
    data: ResearchLaunchData


class ResearchRunDetailData(BaseModel):
    run: ResearchRunRecord
    events: list[ResearchEventRecord] = Field(default_factory=list)


class ResearchRunDetailResponse(BaseModel):
    success: bool = True
    message: str
    data: ResearchRunDetailData


class ResearchListData(BaseModel):
    items: list[ResearchRunRecord]
    total: int


class ResearchListResponse(BaseModel):
    success: bool = True
    message: str
    data: ResearchListData


class ResearchReportResponse(BaseModel):
    success: bool = True
    message: str
    data: ResearchReport


class ResearchEvidenceData(BaseModel):
    research_id: str
    items: list[EvidenceItem]
    total: int
    redacted_count: int = 0


class ResearchEvidenceResponse(BaseModel):
    success: bool = True
    message: str
    data: ResearchEvidenceData


def _translate_error(exc: AgentLayerError) -> AppException:
    detail = exc.to_error_detail()
    return AppException(
        message=detail.message,
        code=detail.code.value,
        status_code=exc.http_status,
        details=detail.details,
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "",
    response_model=ResearchLaunchResponse,
    summary="Start a multi-source research investigation",
)
async def start_research(
    payload: StartResearchPayload,
    request: Request,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    service: KeepResearchService = Depends(get_research_service),
) -> ResearchLaunchResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=getattr(request.state, "request_id", None),
    )
    research_req = ResearchRequest(
        question=payload.question,
        scope=payload.scope,
        max_sources=payload.max_sources,
        required_output=payload.required_output,
        filters=payload.filters,
        plan_id=payload.plan_id,
        workflow_execution_id=payload.workflow_execution_id,
    )
    try:
        run, report = await service.start_research(
            research_req,
            context,
            mode=payload.mode,
            idempotency_key=idempotency_key,
        )
    except AgentLayerError as exc:
        raise _translate_error(exc) from exc

    if payload.mode == "async" and report is None:
        response.status_code = status.HTTP_202_ACCEPTED
        msg = "Research investigation queued for asynchronous execution."
    else:
        response.status_code = status.HTTP_200_OK
        msg = f"Research investigation finished with status '{run.status.value}'."

    base = f"/api/v1/research/{run.research_id}"
    return ResearchLaunchResponse(
        message=msg,
        data=ResearchLaunchData(
            research_id=run.research_id,
            status=run.status,
            question=run.question,
            scope=run.scope,
            required_output=run.required_output,
            max_sources=run.max_sources,
            agent_execution_id=run.agent_execution_id,
            correlation_id=run.correlation_id,
            status_url=base,
            report_url=f"{base}/report",
            evidence_url=f"{base}/evidence",
            report=report,
        ),
    )


@router.get(
    "",
    response_model=ResearchListResponse,
    summary="List tenant-scoped research investigations",
)
async def list_research(
    request: Request,
    status_filter: ResearchStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepResearchService = Depends(get_research_service),
) -> ResearchListResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=getattr(request.state, "request_id", None),
    )
    try:
        runs = await service.list_runs(context, status=status_filter, limit=limit)
    except AgentLayerError as exc:
        raise _translate_error(exc) from exc

    return ResearchListResponse(
        message=f"Retrieved {len(runs)} research investigation(s).",
        data=ResearchListData(items=runs, total=len(runs)),
    )


@router.get(
    "/{research_id}",
    response_model=ResearchRunDetailResponse,
    summary="Retrieve research investigation status, metadata, and audit events",
)
async def get_research(
    research_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepResearchService = Depends(get_research_service),
) -> ResearchRunDetailResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=getattr(request.state, "request_id", None),
    )
    try:
        run = await service.get_run(research_id, context)
        events = await service.get_events(research_id, context)
    except AgentLayerError as exc:
        raise _translate_error(exc) from exc

    return ResearchRunDetailResponse(
        message="Research investigation retrieved successfully.",
        data=ResearchRunDetailData(run=run, events=events),
    )


@router.get(
    "/{research_id}/report",
    response_model=ResearchReportResponse,
    summary="Retrieve re-authorized evidence-backed research report",
)
async def get_research_report(
    research_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepResearchService = Depends(get_research_service),
) -> ResearchReportResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=getattr(request.state, "request_id", None),
    )
    try:
        report = await service.get_report(research_id, context)
    except AgentLayerError as exc:
        raise _translate_error(exc) from exc

    return ResearchReportResponse(
        message="Research report retrieved successfully.",
        data=report,
    )


@router.get(
    "/{research_id}/evidence",
    response_model=ResearchEvidenceResponse,
    summary="Retrieve re-authorized evidence passages and source provenance",
)
async def get_research_evidence(
    research_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepResearchService = Depends(get_research_service),
) -> ResearchEvidenceResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=getattr(request.state, "request_id", None),
    )
    try:
        items, redacted = await service.get_evidence(research_id, context)
    except AgentLayerError as exc:
        raise _translate_error(exc) from exc

    return ResearchEvidenceResponse(
        message=f"Retrieved {len(items)} authorized evidence passage(s).",
        data=ResearchEvidenceData(
            research_id=research_id,
            items=items,
            total=len(items),
            redacted_count=redacted,
        ),
    )


@router.post(
    "/{research_id}/cancel",
    response_model=ResearchRunDetailResponse,
    summary="Cooperatively cancel a pending or running research investigation",
)
async def cancel_research(
    research_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    service: KeepResearchService = Depends(get_research_service),
) -> ResearchRunDetailResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=getattr(request.state, "request_id", None),
    )
    try:
        run = await service.cancel_research(research_id, context)
        events = await service.get_events(research_id, context)
    except AgentLayerError as exc:
        raise _translate_error(exc) from exc

    return ResearchRunDetailResponse(
        message=f"Cancellation recorded for research investigation '{research_id}'.",
        data=ResearchRunDetailData(run=run, events=events),
    )
