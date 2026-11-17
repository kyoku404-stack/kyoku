"""KEEP Phase 4.1 — Agent Layer Error Contracts & Sanitized Exception Hierarchy.

Provides standardized error codes, secret-safe error sanitization, structured
Pydantic error representations, and typed exceptions compatible with both
Python built-in exception semantics and KEEP's FastAPI exception pipeline.

Owner: Member 2 (Agent Contracts & Communication)
Specification: devdocs/p4/p4.1.txt (Sections 3, 4.3)
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"(?i)(password|secret|api[_-]?key|token)\s*[:=]\s*['\"]?[^\s'\";,]+['\"]?"),
)

MAX_ERROR_MESSAGE_LENGTH = 512


def sanitize_error_message(message: str, *, max_length: int = MAX_ERROR_MESSAGE_LENGTH) -> str:
    """Redacts bearer tokens, JWTs, API keys, and inline secrets from error messages."""
    sanitized = message.strip()
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    if len(sanitized) > max_length:
        sanitized = sanitized[: max_length - 3].rstrip() + "..."
    return sanitized


class AgentErrorCode(str, Enum):
    """Canonical machine-readable error codes for KEEP's multi-agent layer."""

    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
    AGENT_DISABLED = "AGENT_DISABLED"
    AGENT_ALREADY_REGISTERED = "AGENT_ALREADY_REGISTERED"
    AGENT_CONTRACT_INVALID = "AGENT_CONTRACT_INVALID"
    AGENT_SCHEMA_VERSION_UNSUPPORTED = "AGENT_SCHEMA_VERSION_UNSUPPORTED"
    AGENT_UNTRUSTED_CONTEXT = "AGENT_UNTRUSTED_CONTEXT"
    AGENT_UNAUTHORIZED = "AGENT_UNAUTHORIZED"
    AGENT_CAPABILITY_DENIED = "AGENT_CAPABILITY_DENIED"
    AGENT_TENANT_ISOLATION_VIOLATION = "AGENT_TENANT_ISOLATION_VIOLATION"
    AGENT_PROMPT_INJECTION_BLOCKED = "AGENT_PROMPT_INJECTION_BLOCKED"
    AGENT_TOOL_UNAUTHORIZED = "AGENT_TOOL_UNAUTHORIZED"
    AGENT_EXECUTION_FAILED = "AGENT_EXECUTION_FAILED"


class AgentErrorDetail(BaseModel):
    """Structured, sanitized error payload embedded in failed AgentResults and messages."""

    code: AgentErrorCode
    message: str = Field(..., min_length=1, max_length=MAX_ERROR_MESSAGE_LENGTH)
    retryable: bool = Field(default=False)
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("message")
    @classmethod
    def redact_message(cls, value: str) -> str:
        return sanitize_error_message(value)


class AgentLayerError(Exception):
    """Base exception for all KEEP Phase 4 agent-layer errors."""

    def __init__(
        self,
        message: str,
        *,
        code: AgentErrorCode = AgentErrorCode.AGENT_EXECUTION_FAILED,
        http_status: int = 500,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.safe_message = sanitize_error_message(message)
        self.code = code
        self.http_status = http_status
        self.retryable = retryable
        self.details = details or {}
        super().__init__(self.safe_message)

    def to_error_detail(self) -> AgentErrorDetail:
        """Converts this exception into a safe, serializable AgentErrorDetail."""
        return AgentErrorDetail(
            code=self.code,
            message=self.safe_message,
            retryable=self.retryable,
            details=self.details,
        )


class AgentNotFoundError(AgentLayerError, LookupError):
    """Raised when a requested agent_id does not exist in the registry."""

    def __init__(self, agent_id: str) -> None:
        super().__init__(
            f"Unknown agent: {agent_id}",
            code=AgentErrorCode.AGENT_NOT_FOUND,
            http_status=404,
            details={"agent_id": agent_id},
        )


class AgentDisabledError(AgentLayerError, ValueError):
    """Raised when a caller attempts to invoke a disabled agent."""

    def __init__(self, agent_id: str) -> None:
        super().__init__(
            f"Agent is disabled: {agent_id}",
            code=AgentErrorCode.AGENT_DISABLED,
            http_status=409,
            details={"agent_id": agent_id},
        )


class AgentAlreadyRegisteredError(AgentLayerError, ValueError):
    """Raised when registering a duplicate agent_id."""

    def __init__(self, agent_id: str) -> None:
        super().__init__(
            f"Agent already registered: {agent_id}",
            code=AgentErrorCode.AGENT_ALREADY_REGISTERED,
            http_status=409,
            details={"agent_id": agent_id},
        )


class AgentContractValidationError(AgentLayerError, ValueError):
    """Raised when an agent request, result, or message fails contract validation."""

    def __init__(
        self,
        message: str,
        *,
        code: AgentErrorCode = AgentErrorCode.AGENT_CONTRACT_INVALID,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, http_status=422, details=details)


class AgentAuthorizationError(AgentLayerError, PermissionError):
    """Raised when an agent invocation or capability check is denied by policy."""

    def __init__(
        self,
        message: str,
        *,
        code: AgentErrorCode = AgentErrorCode.AGENT_CAPABILITY_DENIED,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, http_status=403, details=details)


class AgentTenantIsolationError(AgentAuthorizationError):
    """Raised on any cross-tenant access attempt or mismatched tenant context."""

    def __init__(self, message: str = "Cross-tenant agent access is strictly forbidden.") -> None:
        super().__init__(
            message,
            code=AgentErrorCode.AGENT_TENANT_ISOLATION_VIOLATION,
        )


class AgentPromptInjectionError(AgentAuthorizationError):
    """Raised when prompt injection or unsafe control instructions are detected."""

    def __init__(self, message: str = "Request blocked by agent prompt-injection guardrail.") -> None:
        super().__init__(
            message,
            code=AgentErrorCode.AGENT_PROMPT_INJECTION_BLOCKED,
        )
