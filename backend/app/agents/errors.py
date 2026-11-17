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
    # Phase 4.2 Agent Runtime & Execution Engine error codes
    EXECUTION_NOT_FOUND = "EXECUTION_NOT_FOUND"
    EXECUTION_INVALID_TRANSITION = "EXECUTION_INVALID_TRANSITION"
    EXECUTION_IDEMPOTENCY_CONFLICT = "EXECUTION_IDEMPOTENCY_CONFLICT"
    EXECUTION_TIMED_OUT = "EXECUTION_TIMED_OUT"
    EXECUTION_CANCELLED = "EXECUTION_CANCELLED"
    EXECUTION_CONCURRENCY_LIMIT = "EXECUTION_CONCURRENCY_LIMIT"
    EXECUTION_INPUT_TOO_LARGE = "EXECUTION_INPUT_TOO_LARGE"
    EXECUTION_NOT_RETRYABLE = "EXECUTION_NOT_RETRYABLE"
    EXECUTION_RESULT_NOT_READY = "EXECUTION_RESULT_NOT_READY"
    # Phase 4.3 Agent Orchestration Engine error codes
    WORKFLOW_NOT_FOUND = "WORKFLOW_NOT_FOUND"
    WORKFLOW_DISABLED = "WORKFLOW_DISABLED"
    WORKFLOW_ALREADY_REGISTERED = "WORKFLOW_ALREADY_REGISTERED"
    WORKFLOW_DEPENDENCY_MISSING = "WORKFLOW_DEPENDENCY_MISSING"
    WORKFLOW_EXECUTION_NOT_FOUND = "WORKFLOW_EXECUTION_NOT_FOUND"
    WORKFLOW_INVALID_TRANSITION = "WORKFLOW_INVALID_TRANSITION"
    WORKFLOW_IDEMPOTENCY_CONFLICT = "WORKFLOW_IDEMPOTENCY_CONFLICT"
    WORKFLOW_TIMEOUT = "WORKFLOW_TIMEOUT"
    WORKFLOW_CANCELLED = "WORKFLOW_CANCELLED"
    WORKFLOW_BUDGET_EXCEEDED = "WORKFLOW_BUDGET_EXCEEDED"
    WORKFLOW_RESULT_NOT_READY = "WORKFLOW_RESULT_NOT_READY"
    WORKFLOW_RECOVERY_NOT_ALLOWED = "WORKFLOW_RECOVERY_NOT_ALLOWED"
    WORKFLOW_STEP_FAILED = "WORKFLOW_STEP_FAILED"


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


class ExecutionNotFoundError(AgentLayerError, LookupError):
    """Raised when an execution_id does not exist or is concealed from a foreign tenant."""

    def __init__(self, execution_id: str) -> None:
        super().__init__(
            f"Execution not found: {execution_id}",
            code=AgentErrorCode.EXECUTION_NOT_FOUND,
            http_status=404,
            details={"execution_id": execution_id},
        )


class InvalidExecutionTransitionError(AgentLayerError, ValueError):
    """Raised when an illegal lifecycle state transition is attempted."""

    def __init__(self, execution_id: str, current_status: str, target_status: str) -> None:
        super().__init__(
            f"Invalid lifecycle transition for execution '{execution_id}': "
            f"{current_status} -> {target_status}.",
            code=AgentErrorCode.EXECUTION_INVALID_TRANSITION,
            http_status=409,
            details={
                "execution_id": execution_id,
                "current_status": current_status,
                "target_status": target_status,
            },
        )


class IdempotencyConflictError(AgentLayerError, ValueError):
    """Raised when an Idempotency-Key is reused with a different request payload."""

    def __init__(self, idempotency_key: str) -> None:
        super().__init__(
            f"Idempotency-Key '{idempotency_key}' was already used with a different request payload.",
            code=AgentErrorCode.EXECUTION_IDEMPOTENCY_CONFLICT,
            http_status=409,
            details={"idempotency_key": idempotency_key},
        )


class ExecutionTimeoutError(AgentLayerError, TimeoutError):
    """Raised when an agent execution exceeds its enforced deadline."""

    def __init__(self, execution_id: str, timeout_seconds: float) -> None:
        super().__init__(
            f"Execution '{execution_id}' exceeded deadline ({timeout_seconds:.1f}s).",
            code=AgentErrorCode.EXECUTION_TIMED_OUT,
            http_status=504,
            retryable=True,
            details={"execution_id": execution_id, "timeout_seconds": timeout_seconds},
        )


class ExecutionCancelledError(AgentLayerError):
    """Raised when an execution is cooperatively cancelled."""

    def __init__(self, execution_id: str) -> None:
        super().__init__(
            f"Execution '{execution_id}' was cancelled.",
            code=AgentErrorCode.EXECUTION_CANCELLED,
            http_status=409,
            retryable=True,
            details={"execution_id": execution_id},
        )


class ConcurrencyLimitExceededError(AgentLayerError):
    """Raised when global, per-agent, or per-tenant active execution limits are saturated."""

    def __init__(self, scope: str, limit: int) -> None:
        super().__init__(
            f"Active execution concurrency limit exceeded for {scope} (limit={limit}).",
            code=AgentErrorCode.EXECUTION_CONCURRENCY_LIMIT,
            http_status=429,
            retryable=True,
            details={"scope": scope, "limit": limit},
        )


class ExecutionNotRetryableError(AgentLayerError, ValueError):
    """Raised when a caller requests a retry on an ineligible execution."""

    def __init__(self, execution_id: str, reason: str) -> None:
        super().__init__(
            f"Execution '{execution_id}' cannot be retried: {reason}",
            code=AgentErrorCode.EXECUTION_NOT_RETRYABLE,
            http_status=409,
            details={"execution_id": execution_id, "reason": reason},
        )


class ExecutionResultNotReadyError(AgentLayerError, ValueError):
    """Raised when requesting a result for an execution that has not reached a terminal state."""

    def __init__(self, execution_id: str, status: str) -> None:
        super().__init__(
            f"Execution '{execution_id}' result is not available yet (current status: {status}).",
            code=AgentErrorCode.EXECUTION_RESULT_NOT_READY,
            http_status=409,
            details={"execution_id": execution_id, "status": status},
        )



class WorkflowNotFoundError(AgentLayerError, LookupError):
    """Raised when a workflow definition or version is not registered."""

    def __init__(self, workflow_id: str, version: str | None = None) -> None:
        suffix = f" (version={version})" if version else ""
        super().__init__(
            f"Workflow not found: {workflow_id}{suffix}",
            code=AgentErrorCode.WORKFLOW_NOT_FOUND,
            http_status=404,
            details={"workflow_id": workflow_id, **({"version": version} if version else {})},
        )


class WorkflowDisabledError(AgentLayerError, PermissionError):
    """Raised when attempting to submit a disabled workflow definition."""

    def __init__(self, workflow_id: str, version: str) -> None:
        super().__init__(
            f"Workflow '{workflow_id}' v{version} is currently disabled.",
            code=AgentErrorCode.WORKFLOW_DISABLED,
            http_status=409,
            details={"workflow_id": workflow_id, "version": version},
        )


class WorkflowAlreadyRegisteredError(AgentLayerError, ValueError):
    """Raised on duplicate (workflow_id, version) registration."""

    def __init__(self, workflow_id: str, version: str) -> None:
        super().__init__(
            f"Workflow already registered: {workflow_id}@{version}",
            code=AgentErrorCode.WORKFLOW_ALREADY_REGISTERED,
            http_status=409,
            details={"workflow_id": workflow_id, "version": version},
        )


class WorkflowDependencyMissingError(AgentLayerError, ValueError):
    """Raised when a workflow requires agent capabilities or agent IDs absent from AgentRegistry."""

    def __init__(self, workflow_id: str, missing: list[str]) -> None:
        super().__init__(
            f"Workflow '{workflow_id}' has unresolved agent dependencies: {', '.join(missing)}",
            code=AgentErrorCode.WORKFLOW_DEPENDENCY_MISSING,
            http_status=422,
            details={"workflow_id": workflow_id, "missing": missing},
        )


class WorkflowExecutionNotFoundError(AgentLayerError, LookupError):
    """Raised when a workflow_execution_id does not exist or belongs to another tenant."""

    def __init__(self, workflow_execution_id: str) -> None:
        super().__init__(
            f"Workflow execution not found: {workflow_execution_id}",
            code=AgentErrorCode.WORKFLOW_EXECUTION_NOT_FOUND,
            http_status=404,
            details={"workflow_execution_id": workflow_execution_id},
        )


class InvalidWorkflowTransitionError(AgentLayerError, ValueError):
    """Raised on an illegal workflow execution lifecycle transition."""

    def __init__(self, workflow_execution_id: str, current_status: str, target_status: str) -> None:
        super().__init__(
            f"Invalid lifecycle transition for workflow '{workflow_execution_id}': "
            f"{current_status} -> {target_status}.",
            code=AgentErrorCode.WORKFLOW_INVALID_TRANSITION,
            http_status=409,
            details={
                "workflow_execution_id": workflow_execution_id,
                "current_status": current_status,
                "target_status": target_status,
            },
        )


class WorkflowIdempotencyConflictError(AgentLayerError, ValueError):
    """Raised when a workflow Idempotency-Key is reused with a different request fingerprint."""

    def __init__(self, idempotency_key: str) -> None:
        super().__init__(
            f"Workflow Idempotency-Key '{idempotency_key}' was already used with a different request payload.",
            code=AgentErrorCode.WORKFLOW_IDEMPOTENCY_CONFLICT,
            http_status=409,
            details={"idempotency_key": idempotency_key},
        )


class WorkflowTimeoutError(AgentLayerError, TimeoutError):
    """Raised when a multi-agent workflow exceeds its overall deadline."""

    def __init__(self, workflow_execution_id: str, timeout_seconds: float) -> None:
        super().__init__(
            f"Workflow '{workflow_execution_id}' exceeded deadline ({timeout_seconds:.1f}s).",
            code=AgentErrorCode.WORKFLOW_TIMEOUT,
            http_status=504,
            retryable=True,
            details={
                "workflow_execution_id": workflow_execution_id,
                "timeout_seconds": timeout_seconds,
            },
        )


class WorkflowCancelledError(AgentLayerError):
    """Raised when a workflow execution is cooperatively cancelled."""

    def __init__(self, workflow_execution_id: str) -> None:
        super().__init__(
            f"Workflow '{workflow_execution_id}' was cancelled.",
            code=AgentErrorCode.WORKFLOW_CANCELLED,
            http_status=409,
            retryable=True,
            details={"workflow_execution_id": workflow_execution_id},
        )


class WorkflowBudgetExceededError(AgentLayerError):
    """Raised when a workflow exceeds agent invocation budget or tenant concurrency cap."""

    def __init__(self, reason: str, *, limit: int | None = None) -> None:
        super().__init__(
            reason,
            code=AgentErrorCode.WORKFLOW_BUDGET_EXCEEDED,
            http_status=429,
            retryable=True,
            details={"limit": limit} if limit is not None else {},
        )


class WorkflowResultNotReadyError(AgentLayerError, ValueError):
    """Raised when requesting results for a non-terminal workflow execution."""

    def __init__(self, workflow_execution_id: str, status: str) -> None:
        super().__init__(
            f"Workflow '{workflow_execution_id}' result is not available yet (current status: {status}).",
            code=AgentErrorCode.WORKFLOW_RESULT_NOT_READY,
            http_status=409,
            details={"workflow_execution_id": workflow_execution_id, "status": status},
        )


class WorkflowRecoveryNotAllowedError(AgentLayerError, ValueError):
    """Raised when checkpoint resume is blocked due to terminal state or unsafe side effects."""

    def __init__(self, workflow_execution_id: str, reason: str) -> None:
        super().__init__(
            f"Workflow '{workflow_execution_id}' cannot be resumed: {reason}",
            code=AgentErrorCode.WORKFLOW_RECOVERY_NOT_ALLOWED,
            http_status=409,
            details={"workflow_execution_id": workflow_execution_id, "reason": reason},
        )
