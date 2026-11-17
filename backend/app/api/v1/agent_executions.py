"""KEEP Phase 4.2 — Agent Runtime & Execution Engine FastAPI Endpoints.

Exposes:
- `POST /api/v1/agents/{agent_id}/executions`  — Submit sync (`200`) or async (`202`) execution
- `GET  /api/v1/executions`                    — List caller's tenant-scoped executions
- `GET  /api/v1/executions/metrics`            — Runtime observability metrics snapshot
- `GET  /api/v1/executions/{execution_id}`     — Retrieve execution lifecycle status
- `GET  /api/v1/executions/{execution_id}/result` — Retrieve completed validated result
- `POST /api/v1/executions/{execution_id}/cancel` — Request atomic/cooperative cancellation
- `POST /api/v1/executions/{execution_id}/retry`  — Create linked retry attempt

Owner: Member 4 (FastAPI Integration, Monitoring & End-to-End QA)
Specification: devdocs/p4/p4.2.txt (Sections 7, 10, 13) & docs/api/api-contract.md (Section 21)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.app.agents.contracts import AgentRequest, EvidenceReference
from backend.app.agents.errors import AgentErrorDetail, AgentLayerError
from backend.app.agents.observability.telemetry import RuntimeMetricsCollector
from backend.app.agents.persistence.checkpoints import KeepCheckpointStore
from backend.app.agents.persistence.execution_repository import (
    SQLAlchemyExecutionRepository,
)
from backend.app.agents.runtime.executor import AgentRuntime
from backend.app.agents.runtime.lifecycle import (
    ExecutionMode,
    ExecutionRecord,
    ExecutionStatus,
)
from backend.app.agents.runtime.policies import KeepExecutionPolicy
from backend.app.agents.service import build_runtime_agent_registry
from backend.app.agents.workers.execution_worker import DurableExecutionWorker
from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.core.exceptions import AppException
from backend.app.db.session import async_session_factory
from backend.app.services.ai.interfaces import AIPermission
from backend.app.services.security.agent_permissions import build_trusted_agent_context
from backend.app.services.security.agent_policy import KeepAgentPolicyEngine
from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["Agent Executions"])


# ============================================================================
# Dependency Injection Providers
# ============================================================================


def get_runtime_metrics(request: Request) -> RuntimeMetricsCollector:
    collector = getattr(request.app.state, "runtime_metrics", None)
    if collector is None:
        collector = RuntimeMetricsCollector()
        request.app.state.runtime_metrics = collector
    return collector


def get_agent_runtime(request: Request) -> AgentRuntime:
    """Retrieves lifespan-initialized AgentRuntime from `app.state` (lazy fallback for minimal test apps)."""
    runtime = getattr(request.app.state, "agent_runtime", None)
    if runtime is not None:
        return runtime

    security_policy = getattr(request.app.state, "agent_policy", None) or KeepAgentPolicyEngine()
    request.app.state.agent_policy = security_policy

    checkpoints = getattr(request.app.state, "agent_checkpoints", None)
    if checkpoints is None:
        checkpoints = KeepCheckpointStore(
            session_factory=async_session_factory,
            policy=security_policy,
        )
        request.app.state.agent_checkpoints = checkpoints

    registry = getattr(request.app.state, "agent_registry", None)
    if registry is None:
        registry = build_runtime_agent_registry(
            checkpoint_store=checkpoints,
            policy=security_policy,
        )
        request.app.state.agent_registry = registry

    repo = getattr(request.app.state, "execution_repository", None)
    if repo is None:
        repo = SQLAlchemyExecutionRepository(async_session_factory)
        request.app.state.execution_repository = repo

    exec_policy = getattr(request.app.state, "execution_policy", None)
    if exec_policy is None:
        exec_policy = KeepExecutionPolicy(security_policy=security_policy)
        request.app.state.execution_policy = exec_policy

    worker = getattr(request.app.state, "execution_worker", None)
    if worker is None:
        worker = DurableExecutionWorker()
        request.app.state.execution_worker = worker

    metrics = get_runtime_metrics(request)

    runtime = AgentRuntime(
        registry=registry,
        repository=repo,
        policy=exec_policy,
        dispatcher=worker,
        observer=metrics,
    )
    worker.bind_handler(runtime.execute_existing)
    request.app.state.agent_runtime = runtime
    return runtime


# ============================================================================
# Request / Response Schemas
# ============================================================================


class SubmitExecutionRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=4096)
    input: dict[str, Any] = Field(default_factory=dict)
    mode: ExecutionMode = Field(default="async")
    timeout_seconds: float | None = Field(default=None, gt=0.0)
    idempotency_key: str | None = Field(default=None, max_length=128)
    requested_capabilities: list[str] = Field(default_factory=list)
    correlation_id: str | None = Field(default=None, max_length=128)


class RetryExecutionRequest(BaseModel):
    mode: ExecutionMode | None = None
    timeout_seconds: float | None = Field(default=None, gt=0.0)


class ExecutionRecordResponseData(BaseModel):
    execution_id: str
    task_id: str
    agent_id: str
    agent_version: str
    tenant_id: str
    requested_by: str
    status: str
    mode: str
    goal: str
    correlation_id: str
    attempt_number: int
    parent_execution_id: str | None = None
    idempotency_key: str | None = None
    cancel_requested: bool = False
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    deadline_at: datetime | None = None
    duration_ms: int | None = None
    queue_wait_ms: int | None = None
    status_url: str
    result_url: str


class ExecutionSingleResponse(BaseModel):
    success: bool = True
    message: str
    data: ExecutionRecordResponseData


class ExecutionListData(BaseModel):
    items: list[ExecutionRecordResponseData]
    total: int


class ExecutionListResponse(BaseModel):
    success: bool = True
    message: str
    data: ExecutionListData


class ExecutionResultData(BaseModel):
    execution_id: str
    agent_id: str
    execution_status: str
    status: str
    output: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    error: AgentErrorDetail | None = None
    schema_version: str


class ExecutionResultResponse(BaseModel):
    success: bool = True
    message: str
    data: ExecutionResultData


class RuntimeMetricsResponse(BaseModel):
    success: bool = True
    message: str
    data: dict[str, Any]


def _to_response_data(rec: ExecutionRecord) -> ExecutionRecordResponseData:
    return ExecutionRecordResponseData(
        execution_id=rec.execution_id,
        task_id=rec.task_id,
        agent_id=rec.agent_id,
        agent_version=rec.agent_version,
        tenant_id=rec.tenant_id,
        requested_by=rec.requested_by,
        status=rec.status.value,
        mode=rec.mode,
        goal=rec.goal,
        correlation_id=rec.correlation_id,
        attempt_number=rec.attempt_number,
        parent_execution_id=rec.parent_execution_id,
        idempotency_key=rec.idempotency_key,
        cancel_requested=rec.cancel_requested,
        error_code=rec.error_code,
        error_message=rec.error_message,
        created_at=rec.created_at,
        started_at=rec.started_at,
        completed_at=rec.completed_at,
        deadline_at=rec.deadline_at,
        duration_ms=rec.duration_ms,
        queue_wait_ms=rec.queue_wait_ms,
        status_url=rec.status_url,
        result_url=rec.result_url,
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
# REST Endpoints
# ============================================================================


@router.post(
    "/agents/{agent_id}/executions",
    response_model=ExecutionSingleResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit an agent execution (sync or async)",
)
async def submit_agent_execution(
    agent_id: str,
    payload: SubmitExecutionRequest,
    request: Request,
    response: Response,
    idempotency_key_header: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> ExecutionSingleResponse:
    correlation_id = payload.correlation_id or request.headers.get("X-Request-ID")
    context = build_trusted_agent_context(current_user, correlation_id=correlation_id)
    effective_idem_key = idempotency_key_header or payload.idempotency_key

    agent_req = AgentRequest(
        goal=payload.goal,
        input=payload.input,
        requested_capabilities=payload.requested_capabilities,
        correlation_id=context.correlation_id,
    )
    try:
        record = await runtime.submit(
            agent_id,
            agent_req,
            context,
            mode=payload.mode,
            idempotency_key=effective_idem_key,
            timeout_seconds=payload.timeout_seconds,
        )
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    if payload.mode == "sync":
        response.status_code = status.HTTP_200_OK
        msg = f"Execution '{record.execution_id}' completed with status {record.status.value}."
    else:
        response.status_code = status.HTTP_202_ACCEPTED
        msg = f"Execution '{record.execution_id}' accepted for background processing."

    return ExecutionSingleResponse(
        success=True,
        message=msg,
        data=_to_response_data(record),
    )


@router.get(
    "/executions",
    response_model=ExecutionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List tenant-scoped agent executions",
)
async def list_agent_executions(
    request: Request,
    agent_id: str | None = Query(default=None),
    status_filter: ExecutionStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> ExecutionListResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=request.headers.get("X-Request-ID"),
    )
    records = await runtime.list_executions(
        context,
        agent_id=agent_id,
        status=status_filter,
        limit=limit,
    )
    items = [_to_response_data(r) for r in records]
    return ExecutionListResponse(
        success=True,
        message="Agent executions retrieved successfully.",
        data=ExecutionListData(items=items, total=len(items)),
    )


@router.get(
    "/executions/metrics",
    response_model=RuntimeMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve agent runtime observability metrics",
)
async def get_execution_metrics(
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    metrics: RuntimeMetricsCollector = Depends(get_runtime_metrics),
) -> RuntimeMetricsResponse:
    return RuntimeMetricsResponse(
        success=True,
        message="Agent runtime metrics retrieved successfully.",
        data=metrics.snapshot(),
    )


@router.get(
    "/executions/{execution_id}",
    response_model=ExecutionSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve agent execution status and lifecycle metadata",
)
async def get_execution_status(
    execution_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> ExecutionSingleResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=request.headers.get("X-Request-ID"),
    )
    try:
        record = await runtime.get_execution(execution_id, context)
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    return ExecutionSingleResponse(
        success=True,
        message="Execution status retrieved successfully.",
        data=_to_response_data(record),
    )


@router.get(
    "/executions/{execution_id}/result",
    response_model=ExecutionResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve validated result for a completed agent execution",
)
async def get_execution_result(
    execution_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> ExecutionResultResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=request.headers.get("X-Request-ID"),
    )
    try:
        record = await runtime.get_execution(execution_id, context)
        result = await runtime.get_result(execution_id, context)
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    return ExecutionResultResponse(
        success=result.status == "succeeded",
        message="Execution result retrieved successfully.",
        data=ExecutionResultData(
            execution_id=record.execution_id,
            agent_id=record.agent_id,
            execution_status=record.status.value,
            status=result.status,
            output=result.output,
            evidence=result.evidence,
            warnings=result.warnings,
            error_code=result.error_code,
            error_message=result.error_message,
            error=result.error,
            schema_version=result.schema_version,
        ),
    )


@router.post(
    "/executions/{execution_id}/cancel",
    response_model=ExecutionSingleResponse,
    status_code=status.HTTP_200_OK,
    summary="Request cancellation for a pending or running execution",
)
async def cancel_agent_execution(
    execution_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> ExecutionSingleResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=request.headers.get("X-Request-ID"),
    )
    try:
        record = await runtime.cancel_execution(execution_id, context)
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    return ExecutionSingleResponse(
        success=True,
        message=f"Cancellation processed for execution '{record.execution_id}' (status={record.status.value}).",
        data=_to_response_data(record),
    )


@router.post(
    "/executions/{execution_id}/retry",
    response_model=ExecutionSingleResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a new linked retry attempt for an eligible terminal execution",
)
async def retry_agent_execution(
    execution_id: str,
    request: Request,
    response: Response,
    payload: RetryExecutionRequest | None = None,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> ExecutionSingleResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=request.headers.get("X-Request-ID"),
    )
    req_body = payload or RetryExecutionRequest()
    try:
        record = await runtime.retry_execution(
            execution_id,
            context,
            mode=req_body.mode,
            timeout_seconds=req_body.timeout_seconds,
        )
    except AgentLayerError as exc:
        _raise_app_exception(exc)
        raise  # pragma: no cover

    if record.mode == "sync":
        response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_202_ACCEPTED

    return ExecutionSingleResponse(
        success=True,
        message=f"Retry attempt #{record.attempt_number} created as '{record.execution_id}'.",
        data=_to_response_data(record),
    )
