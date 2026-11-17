"""KEEP Phase 4.1 — Multi-Agent Discovery & Reference Contract Verification API.

Mounts under `/api/v1/agents`. Initializes `AgentRegistry` via FastAPI lifespan
(`app.state.agent_registry`) and injects `KeepAgentService` per request.
Full asynchronous execution lifecycle, timeouts, cancellation, and retries are
deferred to Phase 4.2 (`devdocs/p4/p4.2.txt`).

Owner: Member 4 (KEEP Integration, Reference Agent & QA)
Specification: devdocs/p4/p4.1.txt (Sections 5, 7, 9) & docs/api/api-contract.md (Section 20)
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.contracts import AgentRequest, EvidenceReference
from backend.app.agents.errors import (
    AgentAuthorizationError,
    AgentContractValidationError,
    AgentDisabledError,
    AgentErrorDetail,
    AgentLayerError,
    AgentNotFoundError,
)
from backend.app.agents.metadata import AgentMetadata
from backend.app.agents.registry import AgentRegistry
from backend.app.agents.service import KeepAgentService, build_default_agent_registry
from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.core.exceptions import AppException
from backend.app.services.ai.interfaces import AIPermission
from backend.app.services.security.agent_permissions import build_trusted_agent_context
from backend.app.services.security.agent_policy import KeepAgentPolicyEngine
from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/agents", tags=["Agents"])


# ============================================================================
# Dependency Injection Providers
# ============================================================================


def get_agent_registry(request: Request) -> AgentRegistry:
    """Retrieves the lifespan-initialized AgentRegistry from FastAPI `app.state`."""
    registry = getattr(request.app.state, "agent_registry", None)
    if registry is None:
        registry = build_default_agent_registry()
        request.app.state.agent_registry = registry
    return registry


def get_agent_policy(request: Request) -> KeepAgentPolicyEngine:
    """Retrieves or initializes the shared KeepAgentPolicyEngine from `app.state`."""
    policy = getattr(request.app.state, "agent_policy", None)
    if policy is None:
        policy = KeepAgentPolicyEngine()
        request.app.state.agent_policy = policy
    return policy


def get_agent_service(
    registry: AgentRegistry = Depends(get_agent_registry),
    policy: KeepAgentPolicyEngine = Depends(get_agent_policy),
) -> KeepAgentService:
    """Provides a KeepAgentService bound to the application's AgentRegistry and policy engine."""
    return KeepAgentService(registry=registry, policy=policy)


# ============================================================================
# Request / Response Envelopes
# ============================================================================


class AgentListData(BaseModel):
    items: list[dict[str, Any]]
    total: int


class AgentListResponse(BaseModel):
    success: bool = True
    message: str
    data: AgentListData


class AgentDetailResponse(BaseModel):
    success: bool = True
    message: str
    data: AgentMetadata


class AgentInvokeResponseData(BaseModel):
    agent_id: str
    request_id: str
    task_id: str
    correlation_id: str
    status: str
    output: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    error: AgentErrorDetail | None = None
    schema_version: str


class AgentInvokeResponse(BaseModel):
    success: bool = True
    message: str
    data: AgentInvokeResponseData


class AgentStatusUpdateRequest(BaseModel):
    enabled: bool


def _raise_http_from_agent_error(exc: Exception) -> None:
    """Translates typed AgentLayerError exceptions into KEEP's canonical AppException envelope."""
    if isinstance(exc, AgentLayerError):
        detail = exc.to_error_detail()
        raise AppException(
            message=detail.message,
            code=detail.code.value,
            status_code=exc.http_status,
            details=detail.details,
        ) from exc
    raise exc


# ============================================================================
# REST Endpoints
# ============================================================================


@router.get(
    "",
    response_model=AgentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List registered KEEP agents",
    description="Discovers available KEEP agents. Disabled agents are only returned to authorized OrgAdmin/SuperAdmin callers.",
)
async def list_registered_agents(
    request: Request,
    capability: str | None = Query(default=None, description="Optional capability name filter."),
    include_disabled: bool = Query(
        default=False,
        description="Include disabled agents (honored for OrgAdmin/SuperAdmin only).",
    ),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepAgentService = Depends(get_agent_service),
) -> AgentListResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=request.headers.get("X-Request-ID"),
    )
    items = service.list_agents(
        context,
        include_disabled=include_disabled,
        capability=capability,
    )
    return AgentListResponse(
        success=True,
        message="Registered agents retrieved successfully.",
        data=AgentListData(items=items, total=len(items)),
    )


@router.get(
    "/{agent_id}",
    response_model=AgentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect a registered agent's metadata and capabilities",
)
async def get_registered_agent(
    agent_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    service: KeepAgentService = Depends(get_agent_service),
) -> AgentDetailResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=request.headers.get("X-Request-ID"),
    )
    try:
        metadata = service.get_agent_metadata(agent_id, context)
    except (AgentNotFoundError, AgentAuthorizationError) as exc:
        _raise_http_from_agent_error(exc)
        raise  # pragma: no cover

    return AgentDetailResponse(
        success=True,
        message=f"Agent '{metadata.agent_id}' metadata retrieved successfully.",
        data=metadata,
    )


@router.post(
    "/{agent_id}/invoke",
    response_model=AgentInvokeResponse,
    status_code=status.HTTP_200_OK,
    summary="Invoke a registered agent (Phase 4.1 contract validation)",
    description="Builds a trusted AgentContext from KEEP JWT authentication, enforces security policies, and invokes the registered agent.",
)
async def invoke_registered_agent(
    agent_id: str,
    payload: AgentRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    service: KeepAgentService = Depends(get_agent_service),
) -> AgentInvokeResponse:
    correlation_id = payload.correlation_id or request.headers.get("X-Request-ID")
    context = build_trusted_agent_context(current_user, correlation_id=correlation_id)

    try:
        result = await service.invoke_agent(agent_id, payload, context)
    except (
        AgentNotFoundError,
        AgentDisabledError,
        AgentAuthorizationError,
        AgentContractValidationError,
    ) as exc:
        _raise_http_from_agent_error(exc)
        raise  # pragma: no cover

    return AgentInvokeResponse(
        success=result.status == "succeeded",
        message="Agent invocation completed." if result.status == "succeeded" else "Agent invocation failed.",
        data=AgentInvokeResponseData(
            agent_id=agent_id.strip().lower(),
            request_id=payload.request_id,
            task_id=payload.task_id,
            correlation_id=context.correlation_id,
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


@router.patch(
    "/{agent_id}/status",
    response_model=AgentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Enable or disable a registered agent (Admin)",
)
async def update_agent_status(
    agent_id: str,
    payload: AgentStatusUpdateRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_MANAGE)),
    service: KeepAgentService = Depends(get_agent_service),
) -> AgentDetailResponse:
    context = build_trusted_agent_context(
        current_user,
        correlation_id=request.headers.get("X-Request-ID"),
    )
    try:
        metadata = service.set_agent_enabled(agent_id, payload.enabled, context)
    except (AgentNotFoundError, AgentAuthorizationError) as exc:
        _raise_http_from_agent_error(exc)
        raise  # pragma: no cover

    state_word = "enabled" if metadata.enabled else "disabled"
    return AgentDetailResponse(
        success=True,
        message=f"Agent '{metadata.agent_id}' {state_word} successfully.",
        data=metadata,
    )
