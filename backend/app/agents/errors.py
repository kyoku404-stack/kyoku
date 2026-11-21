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
    # Phase 4.4 Planning & Reasoning Engine error codes
    PLAN_NOT_FOUND = "PLAN_NOT_FOUND"
    PLAN_INVALID_GRAPH = "PLAN_INVALID_GRAPH"
    PLAN_CAPABILITY_UNAVAILABLE = "PLAN_CAPABILITY_UNAVAILABLE"
    PLAN_POLICY_REJECTED = "PLAN_POLICY_REJECTED"
    PLAN_APPROVAL_REQUIRED = "PLAN_APPROVAL_REQUIRED"
    PLAN_BUDGET_EXCEEDED = "PLAN_BUDGET_EXCEEDED"
    PLAN_REPLAN_LIMIT_EXCEEDED = "PLAN_REPLAN_LIMIT_EXCEEDED"
    PLAN_NOT_EXECUTABLE = "PLAN_NOT_EXECUTABLE"
    PLAN_CLARIFICATION_REQUIRED = "PLAN_CLARIFICATION_REQUIRED"
    # Phase 4.5 Research Agents error codes
    RESEARCH_NOT_FOUND = "RESEARCH_NOT_FOUND"
    RESEARCH_CITATION_INVALID = "RESEARCH_CITATION_INVALID"
    RESEARCH_RETRIEVAL_UNAVAILABLE = "RESEARCH_RETRIEVAL_UNAVAILABLE"
    RESEARCH_CANCELLED = "RESEARCH_CANCELLED"
    RESEARCH_REPORT_NOT_READY = "RESEARCH_REPORT_NOT_READY"
    RESEARCH_ACCESS_DENIED = "RESEARCH_ACCESS_DENIED"
    RESEARCH_IDEMPOTENCY_CONFLICT = "RESEARCH_IDEMPOTENCY_CONFLICT"
    # Phase 4.6 Tool-Calling Framework error codes
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_DISABLED = "TOOL_DISABLED"
    TOOL_ALREADY_REGISTERED = "TOOL_ALREADY_REGISTERED"
    TOOL_ARGUMENT_INVALID = "TOOL_ARGUMENT_INVALID"
    TOOL_OUTPUT_INVALID = "TOOL_OUTPUT_INVALID"
    TOOL_OUTPUT_TOO_LARGE = "TOOL_OUTPUT_TOO_LARGE"
    TOOL_PERMISSION_DENIED = "TOOL_PERMISSION_DENIED"
    TOOL_APPROVAL_REQUIRED = "TOOL_APPROVAL_REQUIRED"
    TOOL_EXECUTION_FAILED = "TOOL_EXECUTION_FAILED"
    TOOL_TIMED_OUT = "TOOL_TIMED_OUT"
    TOOL_RATE_LIMITED = "TOOL_RATE_LIMITED"
    TOOL_CONCURRENCY_LIMIT = "TOOL_CONCURRENCY_LIMIT"
    TOOL_IDEMPOTENCY_CONFLICT = "TOOL_IDEMPOTENCY_CONFLICT"
    TOOL_PROMPT_INJECTION_BLOCKED = "TOOL_PROMPT_INJECTION_BLOCKED"
    # Phase 4.7 Agent Memory System error codes
    MEMORY_NOT_FOUND = "MEMORY_NOT_FOUND"
    MEMORY_DISABLED = "MEMORY_DISABLED"
    MEMORY_ACCESS_DENIED = "MEMORY_ACCESS_DENIED"
    MEMORY_PROPOSAL_REJECTED = "MEMORY_PROPOSAL_REJECTED"
    MEMORY_PROPOSAL_NOT_FOUND = "MEMORY_PROPOSAL_NOT_FOUND"
    MEMORY_ALREADY_EXISTS = "MEMORY_ALREADY_EXISTS"
    MEMORY_INVALID_SCOPE = "MEMORY_INVALID_SCOPE"
    MEMORY_CONTENT_INVALID = "MEMORY_CONTENT_INVALID"
    MEMORY_RETENTION_EXPIRED = "MEMORY_RETENTION_EXPIRED"
    MEMORY_DELETED = "MEMORY_DELETED"
    MEMORY_POLICY_VIOLATION = "MEMORY_POLICY_VIOLATION"
    MEMORY_TENANT_ISOLATION_VIOLATION = "MEMORY_TENANT_ISOLATION_VIOLATION"
    MEMORY_PROMPT_INJECTION_BLOCKED = "MEMORY_PROMPT_INJECTION_BLOCKED"
    MEMORY_BUDGET_EXCEEDED = "MEMORY_BUDGET_EXCEEDED"
    MEMORY_CONFLICT_DETECTED = "MEMORY_CONFLICT_DETECTED"

    # Phase 4.8 Multi-Agent Collaboration error codes
    COLLABORATION_SESSION_NOT_FOUND = "COLLABORATION_SESSION_NOT_FOUND"
    COLLABORATION_SESSION_COMPLETED = "COLLABORATION_SESSION_COMPLETED"
    COLLABORATION_SESSION_CANCELLED = "COLLABORATION_SESSION_CANCELLED"
    COLLABORATION_TASK_NOT_FOUND = "COLLABORATION_TASK_NOT_FOUND"
    COLLABORATION_TASK_DEPENDENCY_FAILED = "COLLABORATION_TASK_DEPENDENCY_FAILED"
    COLLABORATION_MESSAGE_INVALID = "COLLABORATION_MESSAGE_INVALID"
    COLLABORATION_AGENT_NOT_REGISTERED = "COLLABORATION_AGENT_NOT_REGISTERED"
    COLLABORATION_AGENT_CAPABILITY_MISMATCH = "COLLABORATION_AGENT_CAPABILITY_MISMATCH"
    COLLABORATION_REVIEW_FAILED = "COLLABORATION_REVIEW_FAILED"
    COLLABORATION_CONFLICT_DETECTED = "COLLABORATION_CONFLICT_DETECTED"
    COLLABORATION_CONFLICT_UNRESOLVED = "COLLABORATION_CONFLICT_UNRESOLVED"
    COLLABORATION_MAX_REVISIONS_EXCEEDED = "COLLABORATION_MAX_REVISIONS_EXCEEDED"
    COLLABORATION_ACCESS_DENIED = "COLLABORATION_ACCESS_DENIED"
    COLLABORATION_TENANT_ISOLATION_VIOLATION = "COLLABORATION_TENANT_ISOLATION_VIOLATION"


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



class PlanNotFoundError(AgentLayerError, LookupError):
    """Raised when a plan_id does not exist or belongs to another tenant."""

    def __init__(self, plan_id: str) -> None:
        super().__init__(
            f"Execution plan not found: {plan_id}",
            code=AgentErrorCode.PLAN_NOT_FOUND,
            http_status=404,
            details={"plan_id": plan_id},
        )


class PlanGraphValidationError(AgentLayerError, ValueError):
    """Raised when a task dependency graph has cycles, missing references, or invalid I/O wiring."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            code=AgentErrorCode.PLAN_INVALID_GRAPH,
            http_status=422,
            details=details or {},
        )


class PlanCapabilityUnavailableError(AgentLayerError, LookupError):
    """Raised when no registered enabled agent satisfies a task's required capabilities."""

    def __init__(self, task_id: str, missing_capabilities: list[str]) -> None:
        super().__init__(
            f"Task '{task_id}' requires unavailable capabilities: {', '.join(missing_capabilities)}",
            code=AgentErrorCode.PLAN_CAPABILITY_UNAVAILABLE,
            http_status=422,
            details={"task_id": task_id, "missing_capabilities": missing_capabilities},
        )


class PlanPolicyRejectedError(AgentLayerError, PermissionError):
    """Raised when a plan violates KEEP security, tenant isolation, or authorization policy."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            code=AgentErrorCode.PLAN_POLICY_REJECTED,
            http_status=403,
            details=details or {},
        )


class PlanApprovalRequiredError(AgentLayerError, PermissionError):
    """Raised when attempting to execute a plan whose restricted actions await HITL approval."""

    def __init__(self, plan_id: str, reasons: list[str]) -> None:
        super().__init__(
            f"Plan '{plan_id}' requires human approval before execution: {'; '.join(reasons)}",
            code=AgentErrorCode.PLAN_APPROVAL_REQUIRED,
            http_status=409,
            details={"plan_id": plan_id, "approval_reasons": reasons},
        )


class PlanBudgetExceededError(AgentLayerError, ValueError):
    """Raised when a plan exceeds configured task, token, parallel-width, or duration budgets."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            code=AgentErrorCode.PLAN_BUDGET_EXCEEDED,
            http_status=422,
            details=details or {},
        )


class PlanReplanLimitExceededError(AgentLayerError, ValueError):
    """Raised when revising a plan would exceed its configured `max_replans` budget."""

    def __init__(self, plan_id: str, max_replans: int) -> None:
        super().__init__(
            f"Plan '{plan_id}' reached its maximum replan limit ({max_replans}).",
            code=AgentErrorCode.PLAN_REPLAN_LIMIT_EXCEEDED,
            http_status=409,
            details={"plan_id": plan_id, "max_replans": max_replans},
        )


class PlanNotExecutableError(AgentLayerError, ValueError):
    """Raised when attempting to submit a non-validated plan (draft, rejected, clarification, submitted)."""

    def __init__(self, plan_id: str, status: str) -> None:
        super().__init__(
            f"Plan '{plan_id}' cannot be executed from status '{status}'.",
            code=AgentErrorCode.PLAN_NOT_EXECUTABLE,
            http_status=409,
            details={"plan_id": plan_id, "status": status},
        )


class ResearchNotFoundError(AgentLayerError, LookupError):
    """Raised when a research_id does not exist or belongs to another tenant."""

    def __init__(self, research_id: str) -> None:
        super().__init__(
            f"Research investigation not found: {research_id}",
            code=AgentErrorCode.RESEARCH_NOT_FOUND,
            http_status=404,
            details={"research_id": research_id},
        )


class ResearchCitationValidationError(AgentLayerError, ValueError):
    """Raised when synthesized research findings reference unknown or fabricated evidence IDs."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            code=AgentErrorCode.RESEARCH_CITATION_INVALID,
            http_status=422,
            details=details or {},
        )


class ResearchRetrievalUnavailableError(AgentLayerError, RuntimeError):
    """Raised when KEEP's underlying retrieval service is temporarily unavailable."""

    def __init__(self, message: str = "Knowledge retrieval service is currently unavailable.") -> None:
        super().__init__(
            message,
            code=AgentErrorCode.RESEARCH_RETRIEVAL_UNAVAILABLE,
            http_status=503,
            retryable=True,
        )


class ResearchCancelledError(AgentLayerError):
    """Raised when a research investigation is cooperatively cancelled."""

    def __init__(self, research_id: str) -> None:
        super().__init__(
            f"Research investigation '{research_id}' was cancelled.",
            code=AgentErrorCode.RESEARCH_CANCELLED,
            http_status=409,
            retryable=True,
            details={"research_id": research_id},
        )


class ResearchReportNotReadyError(AgentLayerError, ValueError):
    """Raised when requesting a report for an investigation that has not reached a report-ready state."""

    def __init__(self, research_id: str, status: str) -> None:
        super().__init__(
            f"Research report for '{research_id}' is not ready yet (current status: {status}).",
            code=AgentErrorCode.RESEARCH_REPORT_NOT_READY,
            http_status=409,
            details={"research_id": research_id, "status": status},
        )


class ResearchAccessDeniedError(AgentLayerError, PermissionError):
    """Raised when caller permissions deny access to a research run, report, or evidence tier."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            code=AgentErrorCode.RESEARCH_ACCESS_DENIED,
            http_status=403,
            details=details or {},
        )


class ResearchIdempotencyConflictError(AgentLayerError, ValueError):
    """Raised when an Idempotency-Key is reused for a different research request payload."""

    def __init__(self, idempotency_key: str) -> None:
        super().__init__(
            f"Research Idempotency-Key '{idempotency_key}' was already used with a different request payload.",
            code=AgentErrorCode.RESEARCH_IDEMPOTENCY_CONFLICT,
            http_status=409,
            details={"idempotency_key": idempotency_key},
        )


# ============================================================================
# Phase 4.6 Tool-Calling Framework Exceptions
# ============================================================================


class ToolNotFoundError(AgentLayerError, LookupError):
    """Raised when an agent attempts to invoke or inspect an unregistered tool."""

    def __init__(self, tool_id: str) -> None:
        super().__init__(
            f"Tool '{tool_id}' is not registered in the platform catalog.",
            code=AgentErrorCode.TOOL_NOT_FOUND,
            http_status=404,
            details={"tool_id": tool_id},
        )


class ToolDisabledError(AgentLayerError, ValueError):
    """Raised when an agent attempts to invoke a tool that is currently disabled."""

    def __init__(self, tool_id: str) -> None:
        super().__init__(
            f"Tool '{tool_id}' is currently disabled by administrative policy.",
            code=AgentErrorCode.TOOL_DISABLED,
            http_status=400,
            details={"tool_id": tool_id},
        )


class ToolAlreadyRegisteredError(AgentLayerError, ValueError):
    """Raised when attempting to register a tool with an identifier that already exists."""

    def __init__(self, tool_id: str) -> None:
        super().__init__(
            f"Tool with ID '{tool_id}' is already registered.",
            code=AgentErrorCode.TOOL_ALREADY_REGISTERED,
            http_status=409,
            details={"tool_id": tool_id},
        )


class ToolArgumentValidationError(AgentLayerError, ValueError):
    """Raised when tool input arguments fail schema validation."""

    def __init__(self, message: str, *, tool_id: str, details: dict[str, Any] | None = None) -> None:
        combined_details = {"tool_id": tool_id}
        if details:
            combined_details.update(details)
        super().__init__(
            message,
            code=AgentErrorCode.TOOL_ARGUMENT_INVALID,
            http_status=400,
            details=combined_details,
        )


class ToolOutputValidationError(AgentLayerError, ValueError):
    """Raised when tool execution output fails schema validation."""

    def __init__(self, message: str, *, tool_id: str, details: dict[str, Any] | None = None) -> None:
        combined_details = {"tool_id": tool_id}
        if details:
            combined_details.update(details)
        super().__init__(
            message,
            code=AgentErrorCode.TOOL_OUTPUT_INVALID,
            http_status=500,
            details=combined_details,
        )


class ToolOutputTooLargeError(AgentLayerError, ValueError):
    """Raised when tool execution output exceeds configured maximum size limits."""

    def __init__(self, message: str, *, tool_id: str, size_bytes: int, max_bytes: int) -> None:
        super().__init__(
            message,
            code=AgentErrorCode.TOOL_OUTPUT_TOO_LARGE,
            http_status=413,
            details={"tool_id": tool_id, "size_bytes": size_bytes, "max_bytes": max_bytes},
        )


class ToolPermissionDeniedError(AgentLayerError, PermissionError):
    """Raised when caller lacks required role, tenant, or capability permissions for a tool."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            code=AgentErrorCode.TOOL_PERMISSION_DENIED,
            http_status=403,
            details=details or {},
        )


class ToolApprovalRequiredError(AgentLayerError):
    """Raised when a tool action requires human or administrative approval before execution."""

    def __init__(self, message: str, *, tool_id: str, details: dict[str, Any] | None = None) -> None:
        combined_details = {"tool_id": tool_id}
        if details:
            combined_details.update(details)
        super().__init__(
            message,
            code=AgentErrorCode.TOOL_APPROVAL_REQUIRED,
            http_status=409,
            details=combined_details,
        )


class ToolExecutionFailedError(AgentLayerError, RuntimeError):
    """Raised when tool execution fails unexpectedly during adapter invocation."""

    def __init__(
        self,
        message: str,
        *,
        tool_id: str,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        combined_details = {"tool_id": tool_id}
        if details:
            combined_details.update(details)
        super().__init__(
            message,
            code=AgentErrorCode.TOOL_EXECUTION_FAILED,
            http_status=500,
            retryable=retryable,
            details=combined_details,
        )


class ToolTimedOutError(AgentLayerError, TimeoutError):
    """Raised when a tool invocation exceeds its timeout limit."""

    def __init__(self, tool_id: str, timeout_seconds: float) -> None:
        super().__init__(
            f"Tool '{tool_id}' execution timed out after {timeout_seconds:.1f}s.",
            code=AgentErrorCode.TOOL_TIMED_OUT,
            http_status=408,
            retryable=False,
            details={"tool_id": tool_id, "timeout_seconds": timeout_seconds},
        )


class ToolRateLimitedError(AgentLayerError):
    """Raised when tool invocation rate exceeds tenant or agent burst limits."""

    def __init__(self, tool_id: str, *, tenant_id: str, limit: int, window_seconds: int) -> None:
        super().__init__(
            f"Tool '{tool_id}' rate limit exceeded for tenant '{tenant_id}' ({limit} calls per {window_seconds}s).",
            code=AgentErrorCode.TOOL_RATE_LIMITED,
            http_status=429,
            retryable=True,
            details={"tool_id": tool_id, "tenant_id": tenant_id, "limit": limit, "window_seconds": window_seconds},
        )


class ToolConcurrencyLimitError(AgentLayerError):
    """Raised when concurrent tool invocations exceed maximum allowed semaphore slots."""

    def __init__(self, tool_id: str, *, max_concurrency: int) -> None:
        super().__init__(
            f"Tool '{tool_id}' maximum concurrency limit ({max_concurrency}) reached.",
            code=AgentErrorCode.TOOL_CONCURRENCY_LIMIT,
            http_status=429,
            retryable=True,
            details={"tool_id": tool_id, "max_concurrency": max_concurrency},
        )


class ToolIdempotencyConflictError(AgentLayerError, ValueError):
    """Raised when an Idempotency-Key is reused with differing arguments."""

    def __init__(self, idempotency_key: str) -> None:
        super().__init__(
            f"Tool Idempotency-Key '{idempotency_key}' was already used with a different request payload.",
            code=AgentErrorCode.TOOL_IDEMPOTENCY_CONFLICT,
            http_status=409,
            details={"idempotency_key": idempotency_key},
        )


class ToolPromptInjectionBlockedError(AgentLayerError, PermissionError):
    """Raised when malicious prompt injection or instruction override patterns are detected in tool arguments."""

    def __init__(self, tool_id: str, *, pattern_matched: str | None = None) -> None:
        super().__init__(
            f"Tool '{tool_id}' execution blocked due to prompt injection attempt.",
            code=AgentErrorCode.TOOL_PROMPT_INJECTION_BLOCKED,
            http_status=403,
            details={"tool_id": tool_id, "pattern_matched": pattern_matched or "detected"},
        )


# ============================================================================
# Phase 4.7 Agent Memory System Typed Exceptions
# ============================================================================


class MemoryNotFoundError(AgentLayerError, LookupError):
    """Raised when an authorized memory record cannot be found or is soft-deleted."""

    def __init__(self, memory_id: str) -> None:
        super().__init__(
            f"Memory record '{memory_id}' was not found.",
            code=AgentErrorCode.MEMORY_NOT_FOUND,
            http_status=404,
            details={"memory_id": memory_id},
        )


class MemoryProposalNotFoundError(AgentLayerError, LookupError):
    """Raised when a memory proposal cannot be found."""

    def __init__(self, proposal_id: str) -> None:
        super().__init__(
            f"Memory proposal '{proposal_id}' was not found.",
            code=AgentErrorCode.MEMORY_PROPOSAL_NOT_FOUND,
            http_status=404,
            details={"proposal_id": proposal_id},
        )


class MemoryAccessDeniedError(AgentLayerError, PermissionError):
    """Raised when a caller or agent attempts to access, approve, or delete a memory outside their authorized scope."""

    def __init__(self, message: str = "Memory access denied", *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            code=AgentErrorCode.MEMORY_ACCESS_DENIED,
            http_status=403,
            details=details or {},
        )


class MemoryTenantIsolationViolationError(AgentLayerError, PermissionError):
    """Raised when a memory query or proposal attempts cross-tenant boundary breach."""

    def __init__(self, *, tenant_id: str, target_tenant_id: str) -> None:
        super().__init__(
            f"Cross-tenant memory access attempt detected: caller '{tenant_id}' cannot access target '{target_tenant_id}'.",
            code=AgentErrorCode.MEMORY_TENANT_ISOLATION_VIOLATION,
            http_status=403,
            details={"caller_tenant_id": tenant_id, "target_tenant_id": target_tenant_id},
        )


class MemoryInvalidScopeError(AgentLayerError, ValueError):
    """Raised when an invalid memory scope is specified."""

    def __init__(self, scope: str) -> None:
        super().__init__(
            f"Invalid memory scope '{scope}'. Allowed scopes: 'user', 'organization', 'workflow', 'agent'.",
            code=AgentErrorCode.MEMORY_INVALID_SCOPE,
            http_status=400,
            details={"scope": scope},
        )


class MemoryContentInvalidError(AgentLayerError, ValueError):
    """Raised when memory content fails length, format, or sanitization constraints."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            f"Memory content validation failed: {reason}",
            code=AgentErrorCode.MEMORY_CONTENT_INVALID,
            http_status=400,
            details={"reason": reason},
        )


class MemoryProposalRejectedError(AgentLayerError, ValueError):
    """Raised when a memory proposal is rejected by policy or human reviewer."""

    def __init__(self, proposal_id: str, reason: str) -> None:
        super().__init__(
            f"Memory proposal '{proposal_id}' was rejected: {reason}",
            code=AgentErrorCode.MEMORY_PROPOSAL_REJECTED,
            http_status=400,
            details={"proposal_id": proposal_id, "reason": reason},
        )


class MemoryRetentionExpiredError(AgentLayerError, ValueError):
    """Raised when an expired memory record is queried or operated on."""

    def __init__(self, memory_id: str) -> None:
        super().__init__(
            f"Memory record '{memory_id}' has expired under retention policy.",
            code=AgentErrorCode.MEMORY_RETENTION_EXPIRED,
            http_status=410,
            details={"memory_id": memory_id},
        )


class MemoryDeletedError(AgentLayerError, ValueError):
    """Raised when an operation targets a deleted memory record."""

    def __init__(self, memory_id: str) -> None:
        super().__init__(
            f"Memory record '{memory_id}' has been deleted.",
            code=AgentErrorCode.MEMORY_DELETED,
            http_status=410,
            details={"memory_id": memory_id},
        )


class MemoryPromptInjectionBlockedError(AgentLayerError, PermissionError):
    """Raised when prompt injection payload is detected in proposed memory content."""

    def __init__(self, *, pattern_matched: str | None = None) -> None:
        super().__init__(
            "Memory write proposal rejected due to prompt injection screening.",
            code=AgentErrorCode.MEMORY_PROMPT_INJECTION_BLOCKED,
            http_status=403,
            details={"pattern_matched": pattern_matched or "detected"},
        )


class MemoryConflictDetectedError(AgentLayerError, ValueError):
    """Raised when a memory write conflicts with an existing verified memory."""

    def __init__(self, memory_id: str, conflict_details: str) -> None:
        super().__init__(
            f"Memory conflict detected against record '{memory_id}': {conflict_details}",
            code=AgentErrorCode.MEMORY_CONFLICT_DETECTED,
            http_status=409,
            details={"conflicting_memory_id": memory_id, "conflict_details": conflict_details},
        )


class MemoryBudgetExceededError(AgentLayerError, ValueError):
    """Raised when memory retrieval or storage exceeds configured context budget."""

    def __init__(self, tokens: int, max_tokens: int) -> None:
        super().__init__(
            f"Memory token budget exceeded: {tokens} tokens requested, maximum {max_tokens}.",
            code=AgentErrorCode.MEMORY_BUDGET_EXCEEDED,
            http_status=400,
            details={"tokens": tokens, "max_tokens": max_tokens},
        )


# ==============================================================================
# Phase 4.8 Multi-Agent Collaboration Typed Exceptions
# ==============================================================================


class CollaborationSessionNotFoundError(AgentLayerError, LookupError):
    """Raised when a collaboration session does not exist."""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            f"Collaboration session '{session_id}' was not found.",
            code=AgentErrorCode.COLLABORATION_SESSION_NOT_FOUND,
            http_status=404,
            details={"session_id": session_id},
        )


class CollaborationSessionCompletedError(AgentLayerError, ValueError):
    """Raised when an operation cannot be performed on a completed collaboration session."""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            f"Collaboration session '{session_id}' has already completed.",
            code=AgentErrorCode.COLLABORATION_SESSION_COMPLETED,
            http_status=400,
            details={"session_id": session_id},
        )


class CollaborationSessionCancelledError(AgentLayerError, ValueError):
    """Raised when an operation cannot be performed on a cancelled collaboration session."""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            f"Collaboration session '{session_id}' has been cancelled.",
            code=AgentErrorCode.COLLABORATION_SESSION_CANCELLED,
            http_status=400,
            details={"session_id": session_id},
        )


class CollaborationTaskNotFoundError(AgentLayerError, LookupError):
    """Raised when a collaboration task does not exist."""

    def __init__(self, task_id: str) -> None:
        super().__init__(
            f"Collaboration task '{task_id}' was not found.",
            code=AgentErrorCode.COLLABORATION_TASK_NOT_FOUND,
            http_status=404,
            details={"task_id": task_id},
        )


class CollaborationTaskDependencyFailedError(AgentLayerError, RuntimeError):
    """Raised when a task cannot proceed because predecessor dependencies failed."""

    def __init__(self, task_id: str, failed_dependencies: list[str]) -> None:
        super().__init__(
            f"Collaboration task '{task_id}' dependencies failed: {failed_dependencies}",
            code=AgentErrorCode.COLLABORATION_TASK_DEPENDENCY_FAILED,
            http_status=400,
            details={"task_id": task_id, "failed_dependencies": failed_dependencies},
        )


class CollaborationMessageInvalidError(AgentLayerError, ValueError):
    """Raised when an agent collaboration message is malformed or invalid."""

    def __init__(self, reason: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            f"Collaboration message validation failed: {reason}",
            code=AgentErrorCode.COLLABORATION_MESSAGE_INVALID,
            http_status=400,
            details=details or {},
        )


class CollaborationAgentNotRegisteredError(AgentLayerError, LookupError):
    """Raised when a participant agent is not registered or found in the registry."""

    def __init__(self, agent_id: str) -> None:
        super().__init__(
            f"Collaboration agent '{agent_id}' is not registered.",
            code=AgentErrorCode.COLLABORATION_AGENT_NOT_REGISTERED,
            http_status=400,
            details={"agent_id": agent_id},
        )


class CollaborationAgentCapabilityMismatchError(AgentLayerError, ValueError):
    """Raised when an agent lacks the required capability for a collaboration task."""

    def __init__(self, agent_id: str, required_capability: str) -> None:
        super().__init__(
            f"Agent '{agent_id}' lacks required capability '{required_capability}'.",
            code=AgentErrorCode.COLLABORATION_AGENT_CAPABILITY_MISMATCH,
            http_status=400,
            details={"agent_id": agent_id, "required_capability": required_capability},
        )


class CollaborationReviewFailedError(AgentLayerError, RuntimeError):
    """Raised when a peer review rejects findings without a recoverable path."""

    def __init__(self, reason: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            f"Collaboration peer review failed: {reason}",
            code=AgentErrorCode.COLLABORATION_REVIEW_FAILED,
            http_status=422,
            details=details or {},
        )


class CollaborationConflictDetectedError(AgentLayerError, ValueError):
    """Raised when contradictory claims are detected across collaboration agents."""

    def __init__(self, conflict_id: str, finding_ids: list[str], reason: str) -> None:
        super().__init__(
            f"Collaboration conflict '{conflict_id}' detected across findings {finding_ids}: {reason}",
            code=AgentErrorCode.COLLABORATION_CONFLICT_DETECTED,
            http_status=409,
            details={"conflict_id": conflict_id, "finding_ids": finding_ids, "reason": reason},
        )


class CollaborationConflictUnresolvedError(AgentLayerError, RuntimeError):
    """Raised when an escalated conflict cannot be automatically reconciled."""

    def __init__(self, conflict_id: str) -> None:
        super().__init__(
            f"Collaboration conflict '{conflict_id}' remains unresolved and requires intervention.",
            code=AgentErrorCode.COLLABORATION_CONFLICT_UNRESOLVED,
            http_status=409,
            details={"conflict_id": conflict_id},
        )


class CollaborationMaxRevisionsExceededError(AgentLayerError, RuntimeError):
    """Raised when review revision loops exceed the configured maximum threshold."""

    def __init__(self, session_id: str, max_revisions: int) -> None:
        super().__init__(
            f"Collaboration session '{session_id}' exceeded max revisions ({max_revisions}).",
            code=AgentErrorCode.COLLABORATION_MAX_REVISIONS_EXCEEDED,
            http_status=422,
            details={"session_id": session_id, "max_revisions": max_revisions},
        )


class CollaborationAccessDeniedError(AgentLayerError, PermissionError):
    """Raised when caller lacks required permissions to access collaboration resources."""

    def __init__(self, message: str = "Access to collaboration session or resource denied.") -> None:
        super().__init__(
            message,
            code=AgentErrorCode.COLLABORATION_ACCESS_DENIED,
            http_status=403,
        )


class CollaborationTenantIsolationViolationError(AgentLayerError, PermissionError):
    """Raised when a cross-tenant collaboration access is attempted."""

    def __init__(self, tenant_id: str, target_tenant_id: str) -> None:
        super().__init__(
            f"Cross-tenant collaboration access attempt: caller '{tenant_id}' cannot access target '{target_tenant_id}'.",
            code=AgentErrorCode.COLLABORATION_TENANT_ISOLATION_VIOLATION,
            http_status=403,
            details={"caller_tenant_id": tenant_id, "target_tenant_id": target_tenant_id},
        )



