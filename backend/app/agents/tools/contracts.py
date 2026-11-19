"""KEEP Phase 4.6 — Tool Calling Contracts, Context & Protocol.

Specifies input/output models, trusted server-side context, and the BaseTool protocol.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal, Protocol, runtime_checkable

from backend.app.agents.errors import sanitize_error_message
from backend.app.agents.tools.metadata import ToolMetadata
from pydantic import BaseModel, Field, field_validator

ToolStatus = Literal[
    "succeeded",
    "failed",
    "timed_out",
    "denied",
    "approval_required",
]


class ToolContext(BaseModel):
    """Server-side verified security and execution context.
    
    Constructed exclusively by trusted backend middleware.
    Model-generated arguments can NEVER override these attributes.
    """

    tenant_id: str = Field(..., min_length=1, description="Tenant organization ID")
    user_id: str = Field(..., min_length=1, description="Authenticated calling user ID")
    roles: list[str] = Field(default_factory=list, description="Assigned principal roles")
    agent_execution_id: str | None = Field(default=None, description="Linked Phase 4.2 agent execution ID")
    workflow_execution_id: str | None = Field(default=None, description="Linked Phase 4.3 workflow execution ID")
    correlation_id: str = Field(
        default_factory=lambda: f"corr_{uuid.uuid4().hex[:12]}",
        description="Distributed correlation ID",
    )

    @property
    def is_admin(self) -> bool:
        """Helper to determine administrative privileges."""
        admin_roles = {"org_admin", "superadmin", "system_admin", "admin"}
        return any(role.lower() in admin_roles for role in self.roles)


class ToolCallRequest(BaseModel):
    """Standardized request envelope for invoking a registered platform tool."""

    tool_id: str = Field(..., min_length=2, max_length=64, description="Target tool ID")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Input arguments for the tool")
    call_id: str = Field(
        default_factory=lambda: f"call_{uuid.uuid4().hex[:12]}",
        description="Unique call tracking ID",
    )
    idempotency_key: str | None = Field(default=None, max_length=128, description="Optional deduplication key")


class ToolCallResult(BaseModel):
    """Standardized structured response envelope for tool invocations."""

    call_id: str = Field(..., description="Correlated call identifier")
    tool_id: str = Field(..., description="Target tool identifier")
    status: ToolStatus = Field(..., description="Execution outcome status")
    output: dict[str, Any] | None = Field(default=None, description="Output payload if succeeded")
    error_code: str | None = Field(default=None, description="Machine-readable error code if failed")
    error_message: str | None = Field(default=None, description="Sanitized human-readable error description")
    duration_ms: int = Field(default=0, ge=0, description="Execution duration in milliseconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Diagnostic and audit metadata")

    @field_validator("error_message")
    @classmethod
    def sanitize_err_msg(cls, v: str | None) -> str | None:
        if v is not None:
            return sanitize_error_message(v)
        return None

    @classmethod
    def success(
        cls,
        call_id: str,
        tool_id: str,
        output: dict[str, Any],
        duration_ms: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> ToolCallResult:
        return cls(
            call_id=call_id,
            tool_id=tool_id,
            status="succeeded",
            output=output,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

    @classmethod
    def denied(
        cls,
        call_id: str,
        tool_id: str,
        reason: str,
        error_code: str = "TOOL_PERMISSION_DENIED",
        duration_ms: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> ToolCallResult:
        return cls(
            call_id=call_id,
            tool_id=tool_id,
            status="denied",
            error_code=error_code,
            error_message=reason,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

    @classmethod
    def approval_required(
        cls,
        call_id: str,
        tool_id: str,
        reason: str = "Human approval required for this action.",
        duration_ms: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> ToolCallResult:
        return cls(
            call_id=call_id,
            tool_id=tool_id,
            status="approval_required",
            error_code="TOOL_APPROVAL_REQUIRED",
            error_message=reason,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

    @classmethod
    def timed_out(
        cls,
        call_id: str,
        tool_id: str,
        timeout_seconds: float,
        duration_ms: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> ToolCallResult:
        return cls(
            call_id=call_id,
            tool_id=tool_id,
            status="timed_out",
            error_code="TOOL_TIMED_OUT",
            error_message=f"Tool execution timed out after {timeout_seconds:.1f}s.",
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        call_id: str,
        tool_id: str,
        error_message: str,
        error_code: str = "TOOL_EXECUTION_FAILED",
        duration_ms: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> ToolCallResult:
        return cls(
            call_id=call_id,
            tool_id=tool_id,
            status="failed",
            error_code=error_code,
            error_message=error_message,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )


@runtime_checkable
class BaseTool(Protocol):
    """Common Protocol for all approved KEEP tools."""

    @property
    def metadata(self) -> ToolMetadata:
        """Declared metadata, schema, and capabilities for this tool."""
        ...

    def validate_arguments(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Validates and coerces input arguments against tool schema."""
        ...

    def validate_output(self, output: dict[str, Any]) -> dict[str, Any]:
        """Validates output payload against return schema before returning to agent."""
        ...

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> dict[str, Any]:
        """Executes the tool's underlying operation within the trusted server-side context."""
        ...
