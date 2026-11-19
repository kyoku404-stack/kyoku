"""KEEP Phase 4.7 — Agent Memory System FastAPI Endpoints.

Exposes:
- `POST   /api/v1/memory/search`              — Search accessible memories within context budget
- `GET    /api/v1/memory/{memory_id}`         — Retrieve an authorized memory record
- `POST   /api/v1/memory/proposals`           — Submit a candidate memory proposal
- `POST   /api/v1/memory/{memory_id}/approve` — Approve a memory proposal
- `POST   /api/v1/memory/{memory_id}/reject`  — Reject a memory proposal
- `DELETE /api/v1/memory/{memory_id}`         — Soft-delete a memory record

Specification Reference: devdocs/p4/p4.7.txt (Section 10) & docs/API/api-contract.md (Section 26)
Owner: Member 4 (LangGraph Integration, API, Persistence & QA)
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from backend.app.agents.errors import (
    AgentLayerError,
    MemoryAccessDeniedError,
    MemoryConflictDetectedError,
    MemoryContentInvalidError,
    MemoryNotFoundError,
    MemoryPromptInjectionBlockedError,
    MemoryProposalNotFoundError,
    MemoryTenantIsolationViolationError,
)
from backend.app.agents.memory.contracts import (
    MemoryQuery,
    MemorySecurityContext,
    MemoryWriteRequest,
)
from backend.app.agents.memory.repository import SqlAlchemyMemoryRepository
from backend.app.agents.memory.service import MemoryService
from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.core.exceptions import AppException
from backend.app.schemas.envelope import ApiResponse
from backend.app.services.ai.interfaces import AIPermission
from fastapi import APIRouter, Depends, Header, Path, Request, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Memory"])


# ============================================================================
# Request / Response Schemas
# ============================================================================


class RejectProposalPayload(BaseModel):
    """Optional rejection reason payload."""

    reason: str = Field(default="Rejected by policy or human reviewer.", max_length=256)


# ============================================================================
# Helpers
# ============================================================================


def _get_memory_service(request: Request) -> MemoryService:
    """Retrieves or lazily initializes MemoryService on app.state."""
    service = getattr(request.app.state, "memory_service", None)
    if service is None:
        repo = getattr(request.app.state, "memory_repository", None)
        if repo is None:
            repo = SqlAlchemyMemoryRepository()
            request.app.state.memory_repository = repo
        service = MemoryService(repository=repo)
        request.app.state.memory_service = service
    return service


def _build_security_context(
    current_user: AuthenticatedUser,
    correlation_id: str | None = None,
) -> MemorySecurityContext:
    """Constructs trusted server-side MemorySecurityContext from verified JWT."""
    role_name = (
        current_user.role.value
        if hasattr(current_user.role, "value")
        else str(current_user.role)
    )
    is_admin = role_name.lower().replace("-", "_") in {
        "orgadmin",
        "org_admin",
        "superadmin",
        "admin",
        "system_admin",
    }
    return MemorySecurityContext(
        tenant_id=str(current_user.organization_id),
        user_id=str(current_user.id),
        roles=[role_name.lower()],
        is_admin=is_admin,
        correlation_id=correlation_id or f"corr_{uuid.uuid4().hex[:12]}",
    )


def _handle_memory_error(exc: Exception) -> None:
    """Translates domain exceptions into standardized FastAPI AppExceptions."""
    if isinstance(exc, (MemoryNotFoundError, MemoryProposalNotFoundError)):
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=exc.code if hasattr(exc, "code") else "MEMORY_NOT_FOUND",
            message=exc.safe_message if hasattr(exc, "safe_message") else str(exc),
            details=getattr(exc, "details", {}),
        )
    if isinstance(
        exc,
        (
            MemoryAccessDeniedError,
            MemoryTenantIsolationViolationError,
            MemoryPromptInjectionBlockedError,
        ),
    ):
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=exc.code if hasattr(exc, "code") else "MEMORY_ACCESS_DENIED",
            message=exc.safe_message if hasattr(exc, "safe_message") else str(exc),
            details=getattr(exc, "details", {}),
        )
    if isinstance(exc, MemoryConflictDetectedError):
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code=exc.code if hasattr(exc, "code") else "MEMORY_CONFLICT_DETECTED",
            message=exc.safe_message if hasattr(exc, "safe_message") else str(exc),
            details=getattr(exc, "details", {}),
        )
    if isinstance(exc, MemoryContentInvalidError):
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=exc.code if hasattr(exc, "code") else "MEMORY_CONTENT_INVALID",
            message=exc.safe_message if hasattr(exc, "safe_message") else str(exc),
            details=getattr(exc, "details", {}),
        )
    if isinstance(exc, AgentLayerError):
        raise AppException(
            status_code=getattr(exc, "http_status", status.HTTP_500_INTERNAL_SERVER_ERROR),
            code=exc.code,
            message=exc.safe_message,
            details=getattr(exc, "details", {}),
        )
    raise exc


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/memory/search",
    response_model=ApiResponse[dict[str, Any]],
    summary="Search accessible memories",
)
async def search_memories(
    payload: MemoryQuery,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    x_correlation_id: str | None = Header(default=None),
) -> ApiResponse[dict[str, Any]]:
    """Retrieves and ranks active memories within context budget."""
    service = _get_memory_service(request)
    sec_ctx = _build_security_context(current_user, x_correlation_id)

    try:
        result = await service.retrieve(payload, sec_ctx)
        return ApiResponse(
            data=result.model_dump(),
            message="Memories retrieved successfully",
        )
    except Exception as exc:
        _handle_memory_error(exc)
        raise


@router.get(
    "/memory/{memory_id}",
    response_model=ApiResponse[dict[str, Any]],
    summary="Get memory record by ID",
)
async def get_memory_record(
    request: Request,
    memory_id: str = Path(..., min_length=1, max_length=128),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_VIEW)),
    x_correlation_id: str | None = Header(default=None),
) -> ApiResponse[dict[str, Any]]:
    """Retrieves an authorized memory record."""
    service = _get_memory_service(request)
    sec_ctx = _build_security_context(current_user, x_correlation_id)

    try:
        record = await service.get_memory(memory_id, sec_ctx)
        return ApiResponse(
            data=record.model_dump(),
            message="Memory retrieved successfully",
        )
    except Exception as exc:
        _handle_memory_error(exc)
        raise


@router.post(
    "/memory/proposals",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse[dict[str, Any]],
    summary="Submit a memory proposal",
)
async def submit_memory_proposal(
    payload: MemoryWriteRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    x_correlation_id: str | None = Header(default=None),
) -> ApiResponse[dict[str, Any]]:
    """Submits a candidate memory proposal for policy governance."""
    service = _get_memory_service(request)
    sec_ctx = _build_security_context(current_user, x_correlation_id)

    try:
        saved_proposal = await service.propose(payload, sec_ctx)
        return ApiResponse(
            data=saved_proposal.model_dump(),
            message="Memory proposal created successfully",
        )
    except Exception as exc:
        _handle_memory_error(exc)
        raise


@router.post(
    "/memory/{memory_id}/approve",
    response_model=ApiResponse[dict[str, Any]],
    summary="Approve a memory proposal",
)
async def approve_memory_proposal(
    request: Request,
    memory_id: str = Path(..., min_length=1, max_length=128),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    x_correlation_id: str | None = Header(default=None),
) -> ApiResponse[dict[str, Any]]:
    """Approves a proposal and consolidates it into active memory."""
    service = _get_memory_service(request)
    sec_ctx = _build_security_context(current_user, x_correlation_id)

    try:
        activated = await service.approve_proposal(memory_id, sec_ctx)
        return ApiResponse(
            data=activated.model_dump(),
            message="Memory approved and activated successfully",
        )
    except Exception as exc:
        _handle_memory_error(exc)
        raise


@router.post(
    "/memory/{memory_id}/reject",
    response_model=ApiResponse[dict[str, Any]],
    summary="Reject a memory proposal",
)
async def reject_memory_proposal(
    request: Request,
    memory_id: str = Path(..., min_length=1, max_length=128),
    payload: RejectProposalPayload | None = None,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    x_correlation_id: str | None = Header(default=None),
) -> ApiResponse[dict[str, Any]]:
    """Rejects a pending memory proposal."""
    service = _get_memory_service(request)
    sec_ctx = _build_security_context(current_user, x_correlation_id)
    reason = payload.reason if payload else "Rejected by reviewer"

    try:
        rejected = await service.reject_proposal(memory_id, reason, sec_ctx)
        return ApiResponse(
            data=rejected.model_dump(),
            message="Memory proposal rejected successfully",
        )
    except Exception as exc:
        _handle_memory_error(exc)
        raise


@router.delete(
    "/memory/{memory_id}",
    response_model=ApiResponse[dict[str, Any]],
    summary="Soft-delete a memory record",
)
async def delete_memory_record(
    request: Request,
    memory_id: str = Path(..., min_length=1, max_length=128),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.AGENT_INVOKE)),
    x_correlation_id: str | None = Header(default=None),
) -> ApiResponse[dict[str, Any]]:
    """Soft-deletes a memory record with audit trail."""
    service = _get_memory_service(request)
    sec_ctx = _build_security_context(current_user, x_correlation_id)

    try:
        deleted = await service.delete_memory(memory_id, sec_ctx)
        return ApiResponse(
            data={"memory_id": memory_id, "deleted": deleted},
            message="Memory deleted successfully",
        )
    except Exception as exc:
        _handle_memory_error(exc)
        raise
