"""KEEP Phase 4.6 — Tool Calling Framework FastAPI Endpoints.

Exposes:
- `GET  /api/v1/tools`                     — List tools visible to caller
- `GET  /api/v1/tools/{tool_id}`           — Retrieve metadata & schema for a tool
- `POST /api/v1/tools/execute`             — Invoke a registered tool
- `POST /api/v1/tool-calls`                — Alias for tool invocation
- `GET  /api/v1/tools/calls/{call_id}`     — Inspect tool invocation status and outcome
- `GET  /api/v1/tool-calls/{call_id}`      — Alias for invocation outcome
- `GET  /api/v1/admin/tools`               — Administrative tool catalog (all tools)
- `POST /api/v1/admin/tools/{tool_id}/toggle` — Administrative enable/disable toggle

Specification Reference: devdocs/p4/p4.6.txt (Section 9) & docs/API/api-contract.md (Section 25)
Owner: Member 4 (LangGraph Integration, API, Persistence & QA)
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from backend.app.agents.errors import (
    ToolNotFoundError,
)
from backend.app.agents.tools.adapters.knowledge_search import KnowledgeSearchTool
from backend.app.agents.tools.adapters.report_draft import ReportDraftTool
from backend.app.agents.tools.audit import ToolAuditService
from backend.app.agents.tools.contracts import (
    ToolCallRequest,
    ToolCallResult,
    ToolContext,
)
from backend.app.agents.tools.executor import KeepToolExecutor
from backend.app.agents.tools.metadata import ToolMetadata
from backend.app.agents.tools.policies import ToolPolicyEngine
from backend.app.agents.tools.registry import ToolRegistry
from backend.app.agents.tools.repository import ToolRepository
from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.core.exceptions import AppException
from backend.app.schemas.envelope import ApiResponse
from backend.app.services.ai.interfaces import AIPermission
from fastapi import APIRouter, Depends, Header, Path, Request, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tools"])


# ============================================================================
# Schemas
# ============================================================================


class ExecuteToolPayload(BaseModel):
    """Payload for invoking an approved platform tool."""

    tool_id: str = Field(..., min_length=2, max_length=64, description="Target tool ID")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Input arguments")
    call_id: str | None = Field(default=None, description="Optional caller-supplied call ID")
    idempotency_key: str | None = Field(default=None, description="Optional deduplication key")


class ToggleToolPayload(BaseModel):
    """Payload for enabling or disabling a tool."""

    enabled: bool = Field(..., description="Target enablement status")


# ============================================================================
# Dependency Providers
# ============================================================================


def get_tool_registry(request: Request) -> ToolRegistry:
    """Retrieves or lazily initializes the ToolRegistry on app.state."""
    registry = getattr(request.app.state, "tool_registry", None)
    if registry is None:
        registry = ToolRegistry()
        # Register default platform tools
        registry.register(KnowledgeSearchTool())
        registry.register(ReportDraftTool())
        request.app.state.tool_registry = registry
    return registry


def get_tool_executor(request: Request) -> KeepToolExecutor:
    """Retrieves or lazily initializes KeepToolExecutor on app.state."""
    executor = getattr(request.app.state, "tool_executor", None)
    if executor is None:
        registry = get_tool_registry(request)
        policy_service = getattr(request.app.state, "tool_policy_engine", None)
        if policy_service is None:
            policy_service = ToolPolicyEngine()
            request.app.state.tool_policy_engine = policy_service

        audit_service = getattr(request.app.state, "tool_audit_service", None)
        if audit_service is None:
            audit_service = ToolAuditService()
            request.app.state.tool_audit_service = audit_service

        repository = getattr(request.app.state, "tool_repository", None)
        if repository is None:
            repository = ToolRepository()
            request.app.state.tool_repository = repository

        executor = KeepToolExecutor(
            registry=registry,
            policy_service=policy_service,
            audit_service=audit_service,
            repository=repository,
        )
        request.app.state.tool_executor = executor
    return executor


def get_tool_repository(request: Request) -> ToolRepository:
    """Retrieves or lazily initializes ToolRepository."""
    repo = getattr(request.app.state, "tool_repository", None)
    if repo is None:
        repo = ToolRepository()
        request.app.state.tool_repository = repo
    return repo


def _build_context(
    current_user: AuthenticatedUser,
    correlation_id: str | None = None,
) -> ToolContext:
    """Constructs server-side verified ToolContext from verified JWT."""
    role_name = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    return ToolContext(
        tenant_id=str(current_user.organization_id),
        user_id=str(current_user.id),
        roles=[role_name.lower()],
        correlation_id=correlation_id or f"corr_{uuid.uuid4().hex[:12]}",
    )


def _handle_tool_result_errors(result: ToolCallResult) -> None:
    """Converts structured failure codes into standardized HTTP exceptions."""
    if result.status == "succeeded" or result.status == "approval_required":
        return

    code = result.error_code or "TOOL_EXECUTION_FAILED"
    msg = result.error_message or "Tool execution failed."
    details = result.metadata

    if code == "TOOL_NOT_FOUND":
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code=code, message=msg, details=details)
    if code in ("TOOL_PERMISSION_DENIED", "AGENT_TENANT_ISOLATION_VIOLATION", "TOOL_PROMPT_INJECTION_BLOCKED", "TOOL_DISABLED"):
        raise AppException(status_code=status.HTTP_403_FORBIDDEN, code=code, message=msg, details=details)
    if code == "TOOL_ARGUMENT_INVALID":
        raise AppException(status_code=status.HTTP_400_BAD_REQUEST, code=code, message=msg, details=details)
    if code == "TOOL_TIMED_OUT":
        raise AppException(status_code=status.HTTP_408_REQUEST_TIMEOUT, code=code, message=msg, details=details)
    if code in ("TOOL_RATE_LIMITED", "TOOL_CONCURRENCY_LIMIT"):
        raise AppException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, code=code, message=msg, details=details)
    if code == "TOOL_OUTPUT_TOO_LARGE":
        raise AppException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, code=code, message=msg, details=details)

    raise AppException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, code=code, message=msg, details=details)


# ============================================================================
# Core Endpoints
# ============================================================================


@router.get("/tools", response_model=ApiResponse[list[ToolMetadata]], summary="List available tools")
async def list_tools(
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> ApiResponse[list[ToolMetadata]]:
    """Lists enabled tools accessible to the caller's role and tenant."""
    role_name = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    accessible = registry.list_for_role([role_name.lower()])
    return ApiResponse(data=accessible, message="Available tools retrieved successfully.")


@router.get("/tools/{tool_id}", response_model=ApiResponse[ToolMetadata], summary="Retrieve tool schema and metadata")
async def get_tool(
    tool_id: str = Path(..., description="Tool ID"),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> ApiResponse[ToolMetadata]:
    """Retrieves full specification and schemas for a registered tool."""
    try:
        tool = registry.get(tool_id, check_enabled=False)
        return ApiResponse(data=tool.metadata, message=f"Tool '{tool_id}' retrieved.")
    except (ToolNotFoundError, KeyError) as err:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="TOOL_NOT_FOUND",
            message=f"Tool '{tool_id}' is not registered in the platform catalog.",
            details={"tool_id": tool_id},
        ) from err


@router.post("/tools/execute", response_model=ApiResponse[ToolCallResult], summary="Execute a tool call")
@router.post("/tool-calls", response_model=ApiResponse[ToolCallResult], summary="Alias to execute tool call")
async def execute_tool(
    payload: ExecuteToolPayload,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    executor: KeepToolExecutor = Depends(get_tool_executor),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
) -> ApiResponse[ToolCallResult]:
    """Executes a tool call through the verified security and validation pipeline."""
    context = _build_context(current_user, correlation_id=x_correlation_id)
    cid = payload.call_id or f"call_{uuid.uuid4().hex[:12]}"
    idem = payload.idempotency_key or idempotency_key

    req = ToolCallRequest(
        tool_id=payload.tool_id,
        arguments=payload.arguments,
        call_id=cid,
        idempotency_key=idem,
    )

    result = await executor.invoke(req, context)
    _handle_tool_result_errors(result)

    return ApiResponse(data=result, message=f"Tool '{payload.tool_id}' executed with status: {result.status}.")


@router.get("/tools/calls/{call_id}", response_model=ApiResponse[dict[str, Any]], summary="Get invocation status")
@router.get("/tool-calls/{call_id}", response_model=ApiResponse[dict[str, Any]], summary="Alias to get invocation status")
async def get_invocation_outcome(
    call_id: str = Path(..., description="Unique call ID"),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    repository: ToolRepository = Depends(get_tool_repository),
) -> ApiResponse[dict[str, Any]]:
    """Retrieves an invocation record strictly scoped to caller's tenant."""
    record = await repository.get_invocation(tenant_id=str(current_user.organization_id), call_id=call_id)
    if record is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="TOOL_INVOCATION_NOT_FOUND",
            message=f"Tool invocation '{call_id}' not found for tenant.",
            details={"call_id": call_id},
        )

    return ApiResponse(
        data={
            "call_id": record.call_id,
            "tool_id": record.tool_id,
            "tool_version": record.tool_version,
            "tenant_id": record.tenant_id,
            "requested_by": record.requested_by,
            "agent_execution_id": record.agent_execution_id,
            "workflow_execution_id": record.workflow_execution_id,
            "status": record.status,
            "duration_ms": record.duration_ms,
            "error_code": record.error_code,
            "input_summary": record.input_summary,
            "output_summary": record.output_summary,
        },
        message=f"Tool invocation '{call_id}' retrieved.",
    )


# ============================================================================
# Admin Endpoints
# ============================================================================


@router.get("/admin/tools", response_model=ApiResponse[list[ToolMetadata]], summary="Admin tool catalog")
async def admin_list_tools(
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_MANAGE)),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> ApiResponse[list[ToolMetadata]]:
    """Administrative tool catalog showing all tools including disabled ones."""
    all_tools = registry.list_tools(include_disabled=True)
    return ApiResponse(data=all_tools, message="Admin tool catalog retrieved.")


@router.post("/admin/tools/{tool_id}/toggle", response_model=ApiResponse[ToolMetadata], summary="Admin toggle tool")
async def admin_toggle_tool(
    payload: ToggleToolPayload,
    tool_id: str = Path(..., description="Tool ID"),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_MANAGE)),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> ApiResponse[ToolMetadata]:
    """Enables or disables a platform tool."""
    try:
        if payload.enabled:
            meta = registry.enable(tool_id)
        else:
            meta = registry.disable(tool_id)
        return ApiResponse(data=meta, message=f"Tool '{tool_id}' enabled={payload.enabled}.")
    except (ToolNotFoundError, KeyError) as err:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="TOOL_NOT_FOUND",
            message=f"Tool '{tool_id}' is not registered in the platform catalog.",
            details={"tool_id": tool_id},
        ) from err
