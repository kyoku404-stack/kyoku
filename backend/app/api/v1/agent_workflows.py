"""KEEP Phase 4.3 — Multi-Agent Workflow Orchestration FastAPI Endpoints.

Exposes:
- `GET   /api/v1/orchestration/workflows`                   — List approved workflows
- `GET   /api/v1/orchestration/workflows/{workflow_id}`     — Inspect workflow definition
- `PATCH /api/v1/orchestration/workflows/{workflow_id}/status` — Admin enable/disable workflow
- `POST  /api/v1/workflows/{workflow_id}/executions`        — Submit workflow execution (sync/async)
- `GET   /api/v1/workflow-executions`                       — List tenant workflow executions
- `GET   /api/v1/workflow-executions/metrics`               — Workflow observability metrics
- `GET   /api/v1/workflow-executions/{id}`                  — Retrieve workflow status
- `GET   /api/v1/workflow-executions/{id}/result`           — Retrieve validated/partial result
- `GET   /api/v1/workflow-executions/{id}/steps`            — View participating agent executions
- `POST  /api/v1/workflow-executions/{id}/cancel`           — Request workflow cancellation
- `POST  /api/v1/workflow-executions/{id}/resume`           — Resume from checkpoint (re-authorized)

Owner: Member 4 (FastAPI Integration, Persistence & End-to-End QA)
Specification: devdocs/p4/p4.3.txt (Sections 10, 12, 13) & docs/API/api-contract.md (Section 22)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.app.agents.contracts import EvidenceReference
from backend.app.agents.errors import AgentLayerError
from backend.app.agents.observability.workflow_tracing import WorkflowMetricsCollector
from backend.app.agents.orchestration.graphs import build_default_workflow_registry
from backend.app.agents.orchestration.policies import KeepWorkflowPolicyEngine
from backend.app.agents.orchestration.service import KeepOrchestrationService
from backend.app.agents.orchestration.workflow_contracts import (
    WorkflowDefinition,
    WorkflowExecutionRecord,
    WorkflowMode,
    WorkflowRequest,
    WorkflowStatus,
    WorkflowStepLink,
)
from backend.app.agents.persistence.checkpoints import KeepCheckpointStore
from backend.app.agents.persistence.graph_checkpoints import KeepGraphCheckpointStore
from backend.app.agents.persistence.workflow_repository import (
    SQLAlchemyWorkflowRepository,
)
from backend.app.agents.workers.execution_worker import DurableExecutionWorker
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

router = APIRouter(tags=["Agent Orchestration"])


# ============================================================================
# Dependency Injection Providers
# ============================================================================


def get_workflow_metrics(request: Request) -> WorkflowMetricsCollector:
    collector = getattr(request.app.state, "workflow_metrics", None)
    if collector is None:
        collector = WorkflowMetricsCollector()
        request.app.state.workflow_metrics = collector
    return collector


def get_orchestration_service(request: Request) -> KeepOrchestrationService:
    """Retrieves lifespan-initialized KeepOrchestrationService from `app.state` (lazy fallback for tests)."""
    service = getattr(request.app.state, "orchestration_service", None)
    if service is not None:
        return service

    runtime = get_agent_runtime(request)
    security_policy = getattr(request.app.state, "agent_policy", None) or KeepAgentPolicyEngine()
    request.app.state.agent_policy = security_policy

    wf_registry = getattr(request.app.state, "workflow_registry", None)
    if wf_registry is None:
        wf_registry = build_default_workflow_registry(
            runtime.registry,
            validate_deps=False,
        )
        request.app.state.workflow_registry = wf_registry

    wf_repo = getattr(request.app.state, "workflow_repository", None)
    if wf_repo is None:
        wf_repo = SQLAlchemyWorkflowRepository(async_session_factory)
        request.app.state.workflow_repository = wf_repo

    base_chk = getattr(request.app.state, "agent_checkpoints", None) or KeepCheckpointStore(
        session_factory=async_session_factory,
        policy=security_policy,
    )
    graph_chk = getattr(request.app.state, "graph_checkpoints", None)
    if graph_chk is None:
        graph_chk = KeepGraphCheckpointStore(base_chk)
        request.app.state.graph_checkpoints = graph_chk

    wf_policy = getattr(request.app.state, "workflow_policy", None)
    if wf_policy is None:
        wf_policy = KeepWorkflowPolicyEngine(security_policy=security_policy)
        request.app.state.workflow_policy = wf_policy

    wf_worker = getattr(request.app.state, "workflow_worker", None)
    if wf_worker is None:
        wf_worker = DurableExecutionWorker()
        request.app.state.workflow_worker = wf_worker

    wf_metrics = get_workflow_metrics(request)

    service = KeepOrchestrationService(
        workflow_registry=wf_registry,
        repository=wf_repo,
        runtime=runtime,
        policy=wf_policy,
        security_policy=security_policy,
        checkpoint_store=graph_chk,
        dispatcher=wf_worker,
        observer=wf_metrics,
    )
    wf_worker.bind_handler(service.execute_from_worker)
    request.app.state.orchestration_service = service
    return service


# ============================================================================
# Request / Response Schemas
# ============================================================================


class SubmitWorkflowExecutionRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=4096)
    input: dict[str, Any] = Field(default_factory=dict)
    version: str | None = Field(default=None, max_length=32)
    mode: WorkflowMode = Field(default="async")
    timeout_seconds: float | None = Field(default=None, gt=0.0)
    idempotency_key: str | None = Field(default=None, max_length=128)
    correlation_id: str | None = Field(default=None, max_length=128)


class WorkflowStatusToggleRequest(BaseModel):
    enabled: bool
    version: str | None = Field(default=None, max_length=32)


class WorkflowDefinitionListData(BaseModel):
    items: list[dict[str, Any]]
    total: int


class WorkflowDefinitionListResponse(BaseModel):
    success: bool = True
    message: str
    data: WorkflowDefinitionListData


class WorkflowDefinitionSingleResponse(BaseModel):
    success: bool = True
    message: str
    data: WorkflowDefinition


class WorkflowExecutionResponseData(BaseModel):
    workflow_execution_id: str
    workflow_id: str
    workflow_version: str
    tenant_id: str
    requested_by: str
    status: str
    mode: str
    goal: str
    correlation_id: str
    idempotency_key: str | None = None
    execution_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    checkpoint_ref: str | None = None
    cancel_requested: bool = False
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    deadline_at: datetime | None = None
    duration_ms: int | None = None
    status_url: str
    result_url: str
    steps_url: str


class WorkflowExecutionSingleResponse(BaseModel):
    success: bool = True
    message: str
    data: WorkflowExecutionResponseData


class WorkflowExecutionListData(BaseModel):
    items: list[WorkflowExecutionResponseData]
    total: int


class WorkflowExecutionListResponse(BaseModel):
    success: bool = True
    message: str
    data: WorkflowExecutionListData


class WorkflowResultResponseData(BaseModel):
    workflow_execution_id: str
    workflow_id: str
    workflow_version: str
    status: str
    output: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    execution_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    failed_optional_steps: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    schema_version: str = "1.0"


class WorkflowResultResponse(BaseModel):
    success: bool = True
    message: str
    data: WorkflowResultResponseData


class WorkflowStepsListData(BaseModel):
    workflow_execution_id: str
    items: list[WorkflowStepLink]
    total: int


class WorkflowStepsListResponse(BaseModel):
    success: bool = True
    message: str
    data: WorkflowStepsListData


class WorkflowMetricsResponse(BaseModel):
    success: bool = True
    message: str
    data: dict[str, Any]


def _to_response_data(rec: WorkflowExecutionRecord) -> WorkflowExecutionResponseData:
    return WorkflowExecutionResponseData(
        workflow_execution_id=rec.workflow_execution_id,
        workflow_id=rec.workflow_id,
        workflow_version=rec.workflow_version,
        tenant_id=rec.tenant_id,
        requested_by=rec.requested_by,
        status=rec.status.value,
        mode=rec.mode,
        goal=rec.goal,
        correlation_id=rec.correlation_id,
        idempotency_key=rec.idempotency_key,
        execution_ids=list(rec.execution_ids),
        warnings=list(rec.warnings),
        error_code=rec.error_code,
        error_message=rec.error_message,
        checkpoint_ref=rec.checkpoint_ref,
        cancel_requested=rec.cancel_requested,
        created_at=rec.created_at,
        started_at=rec.started_at,
        completed_at=rec.completed_at,
        deadline_at=rec.deadline_at,
        duration_ms=rec.duration_ms,
        status_url=rec.status_url,
        result_url=rec.result_url,
        steps_url=rec.steps_url,
    )


def _raise_app_exception(exc: AgentLayerError) -> None:
    detail = exc.to_error_detail()
    raise AppException(
        message=detail.message,
        code=detail.code.value,
        status_code=exc.http_status,
        details=detail.details,
    ) from exc


# ============================================================================
# Workflow Registry Endpoints
# ============================================================================


@router.get(
    "/orchestration/workflows",
    response_model=WorkflowDefinitionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List approved multi-agent workflows",
)
async def list_approved_workflows(
    request: Request,
    task_type: str | None = Query(default=None),
    include_disabled: bool = Query(default=False),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepOrchestrationService = Depends(get_orchestration_service),
) -> WorkflowDefinitionListResponse:
    context = build_trusted_agent_context(
        current_user, correlation_id=request.headers.get("X-Request-ID")
    )
    items = service.list_workflows(
        context, include_disabled=include_disabled, task_type=task_type
    )
    return WorkflowDefinitionListResponse(
        success=True,
        message="Approved multi-agent workflows retrieved successfully.",
        data=WorkflowDefinitionListData(items=items, total=len(items)),
    )


@router.get(
    "/orchestration/workflows/{workflow_id}",
    response_model=WorkflowDefinitionSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect an approved workflow definition",
)
async def inspect_approved_workflow(
    workflow_id: str,
    request: Request,
    version: str | None = Query(default=None),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepOrchestrationService = Depends(get_orchestration_service),
) -> WorkflowDefinitionSingleResponse:
    context = build_trusted_agent_context(
        current_user, correlation_id=request.headers.get("X-Request-ID")
    )
    try:
        defn = service.get_workflow_definition(workflow_id, context, version=version)
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    return WorkflowDefinitionSingleResponse(
        success=True,
        message=f"Workflow '{defn.workflow_id}' v{defn.version} retrieved successfully.",
        data=defn,
    )


@router.patch(
    "/orchestration/workflows/{workflow_id}/status",
    response_model=WorkflowDefinitionSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Enable or disable an approved workflow (Admin)",
)
async def toggle_approved_workflow_status(
    workflow_id: str,
    payload: WorkflowStatusToggleRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_MANAGE)),
    service: KeepOrchestrationService = Depends(get_orchestration_service),
) -> WorkflowDefinitionSingleResponse:
    context = build_trusted_agent_context(
        current_user, correlation_id=request.headers.get("X-Request-ID")
    )
    try:
        updated = service.set_workflow_enabled(
            workflow_id, payload.enabled, context, version=payload.version
        )
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    word = "enabled" if updated.enabled else "disabled"
    return WorkflowDefinitionSingleResponse(
        success=True,
        message=f"Workflow '{updated.workflow_id}' v{updated.version} {word} successfully.",
        data=updated,
    )


# ============================================================================
# Workflow Execution Endpoints (Section 10 Spec)
# ============================================================================


@router.post(
    "/workflows/{workflow_id}/executions",
    response_model=WorkflowExecutionSingleResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a multi-agent workflow execution (sync or async)",
)
async def submit_workflow_execution(
    workflow_id: str,
    payload: SubmitWorkflowExecutionRequest,
    request: Request,
    response: Response,
    idempotency_key_header: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    service: KeepOrchestrationService = Depends(get_orchestration_service),
) -> WorkflowExecutionSingleResponse:
    correlation_id = payload.correlation_id or request.headers.get("X-Request-ID")
    context = build_trusted_agent_context(current_user, correlation_id=correlation_id)
    effective_idem = idempotency_key_header or payload.idempotency_key

    wf_req = WorkflowRequest(
        goal=payload.goal,
        input=payload.input,
        version=payload.version,
        mode=payload.mode,
        timeout_seconds=payload.timeout_seconds,
        idempotency_key=effective_idem,
        correlation_id=context.correlation_id,
    )
    try:
        record = await service.submit_workflow(
            workflow_id,
            wf_req,
            context,
            idempotency_key=effective_idem,
        )
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    if payload.mode == "sync":
        response.status_code = status.HTTP_200_OK
        msg = f"Workflow '{record.workflow_execution_id}' finished with status {record.status.value}."
    else:
        response.status_code = status.HTTP_202_ACCEPTED
        msg = f"Workflow '{record.workflow_execution_id}' accepted for orchestration."

    return WorkflowExecutionSingleResponse(
        success=True,
        message=msg,
        data=_to_response_data(record),
    )


@router.get(
    "/workflow-executions",
    response_model=WorkflowExecutionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List tenant-scoped workflow executions",
)
async def list_workflow_executions(
    request: Request,
    workflow_id: str | None = Query(default=None),
    status_filter: WorkflowStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepOrchestrationService = Depends(get_orchestration_service),
) -> WorkflowExecutionListResponse:
    context = build_trusted_agent_context(
        current_user, correlation_id=request.headers.get("X-Request-ID")
    )
    records = await service.list_workflow_executions(
        context, workflow_id=workflow_id, status=status_filter, limit=limit
    )
    items = [_to_response_data(r) for r in records]
    return WorkflowExecutionListResponse(
        success=True,
        message="Workflow executions retrieved successfully.",
        data=WorkflowExecutionListData(items=items, total=len(items)),
    )


@router.get(
    "/workflow-executions/metrics",
    response_model=WorkflowMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve workflow orchestration observability metrics",
)
async def get_workflow_execution_metrics(
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    metrics: WorkflowMetricsCollector = Depends(get_workflow_metrics),
) -> WorkflowMetricsResponse:
    return WorkflowMetricsResponse(
        success=True,
        message="Workflow orchestration metrics retrieved successfully.",
        data=metrics.snapshot(),
    )


@router.get(
    "/workflow-executions/{workflow_execution_id}",
    response_model=WorkflowExecutionSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve multi-agent workflow execution status",
)
async def get_workflow_execution_status(
    workflow_execution_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepOrchestrationService = Depends(get_orchestration_service),
) -> WorkflowExecutionSingleResponse:
    context = build_trusted_agent_context(
        current_user, correlation_id=request.headers.get("X-Request-ID")
    )
    try:
        record = await service.get_workflow_execution(workflow_execution_id, context)
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    return WorkflowExecutionSingleResponse(
        success=True,
        message="Workflow execution status retrieved successfully.",
        data=_to_response_data(record),
    )


@router.get(
    "/workflow-executions/{workflow_execution_id}/result",
    response_model=WorkflowResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve final or permitted partial workflow result",
)
async def get_workflow_execution_result(
    workflow_execution_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepOrchestrationService = Depends(get_orchestration_service),
) -> WorkflowResultResponse:
    context = build_trusted_agent_context(
        current_user, correlation_id=request.headers.get("X-Request-ID")
    )
    try:
        result = await service.get_workflow_result(workflow_execution_id, context)
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    ok = result.status in (WorkflowStatus.SUCCEEDED.value, WorkflowStatus.PARTIALLY_SUCCEEDED.value)
    return WorkflowResultResponse(
        success=ok,
        message="Workflow execution result retrieved successfully.",
        data=WorkflowResultResponseData(**result.model_dump()),
    )


@router.get(
    "/workflow-executions/{workflow_execution_id}/steps",
    response_model=WorkflowStepsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List participating Phase 4.2 agent executions for a workflow",
)
async def get_workflow_execution_steps(
    workflow_execution_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepOrchestrationService = Depends(get_orchestration_service),
) -> WorkflowStepsListResponse:
    context = build_trusted_agent_context(
        current_user, correlation_id=request.headers.get("X-Request-ID")
    )
    try:
        steps = await service.get_workflow_steps(workflow_execution_id, context)
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    return WorkflowStepsListResponse(
        success=True,
        message="Workflow execution steps retrieved successfully.",
        data=WorkflowStepsListData(
            workflow_execution_id=workflow_execution_id,
            items=steps,
            total=len(steps),
        ),
    )


@router.post(
    "/workflow-executions/{workflow_execution_id}/cancel",
    response_model=WorkflowExecutionSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Request cooperative workflow cancellation",
)
async def cancel_workflow_execution(
    workflow_execution_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    service: KeepOrchestrationService = Depends(get_orchestration_service),
) -> WorkflowExecutionSingleResponse:
    context = build_trusted_agent_context(
        current_user, correlation_id=request.headers.get("X-Request-ID")
    )
    try:
        record = await service.cancel_workflow(workflow_execution_id, context)
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    return WorkflowExecutionSingleResponse(
        success=True,
        message=f"Cancellation processed for workflow '{record.workflow_execution_id}' (status={record.status.value}).",
        data=_to_response_data(record),
    )


@router.post(
    "/workflow-executions/{workflow_execution_id}/resume",
    response_model=WorkflowExecutionSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Resume a failed or interrupted workflow from persisted checkpoint",
)
async def resume_workflow_execution(
    workflow_execution_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    service: KeepOrchestrationService = Depends(get_orchestration_service),
) -> WorkflowExecutionSingleResponse:
    context = build_trusted_agent_context(
        current_user, correlation_id=request.headers.get("X-Request-ID")
    )
    try:
        record = await service.resume_workflow(workflow_execution_id, context)
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    return WorkflowExecutionSingleResponse(
        success=True,
        message=f"Workflow '{record.workflow_execution_id}' resumed and completed with status {record.status.value}.",
        data=_to_response_data(record),
    )
