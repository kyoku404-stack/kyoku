"""KEEP Phase 4.1 — Hardened Agent Request, Context, Evidence & Result Contracts.

Defines canonical Pydantic v2 models, contract schema versioning rules,
traceable evidence references, warning representations, and helper factories
governing all interactions across KEEP's multi-agent layer.

Owner: Member 2 (Agent Contracts & Communication)
Specification: devdocs/p4/p4.1.txt (Sections 3, 4.3, 9)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from backend.app.agents.errors import (
    AgentErrorCode,
    AgentErrorDetail,
    sanitize_error_message,
)
from pydantic import BaseModel, Field, field_validator, model_validator

AGENT_CONTRACT_SCHEMA_VERSION = "1.0"
SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1.0"})

AgentStatus = Literal["succeeded", "failed"]


def generate_request_id() -> str:
    """Generates a unique, traceable agent request identifier."""
    return f"req_{uuid4().hex}"


def generate_task_id() -> str:
    """Generates a unique task identifier for agent invocations."""
    return f"task_{uuid4().hex}"


def generate_correlation_id() -> str:
    """Generates a unique correlation identifier for end-to-end tracing."""
    return f"corr_{uuid4().hex}"


def validate_contract_schema_version(version: str) -> str:
    """Validates that a payload declares a supported KEEP agent contract schema version."""
    cleaned = version.strip()
    if cleaned not in SUPPORTED_SCHEMA_VERSIONS:
        supported = ", ".join(sorted(SUPPORTED_SCHEMA_VERSIONS))
        raise ValueError(
            f"Unsupported agent contract schema_version '{version}'. Supported versions: {supported}."
        )
    return cleaned


class AgentRequest(BaseModel):
    """Canonical validated request contract submitted to a KEEP BaseAgent."""

    request_id: str = Field(default_factory=generate_request_id, min_length=1, max_length=128)
    task_id: str = Field(default_factory=generate_task_id, min_length=1, max_length=128)
    goal: str = Field(..., min_length=1, max_length=4096)
    input: dict[str, Any] = Field(default_factory=dict)
    requested_capabilities: list[str] = Field(
        default_factory=list,
        description="Optional subset of declared agent capabilities requested for this call.",
    )
    correlation_id: str | None = Field(default=None, max_length=128)
    schema_version: str = Field(default=AGENT_CONTRACT_SCHEMA_VERSION)

    @field_validator("request_id", "task_id", "goal")
    @classmethod
    def strip_non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or whitespace-only.")
        return cleaned

    @field_validator("correlation_id")
    @classmethod
    def strip_optional_correlation(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("requested_capabilities")
    @classmethod
    def normalize_capabilities(cls, caps: list[str]) -> list[str]:
        return [c.strip().lower() for c in caps if c and c.strip()]

    @field_validator("schema_version")
    @classmethod
    def check_schema_version(cls, value: str) -> str:
        return validate_contract_schema_version(value)


class AgentContext(BaseModel):
    """Trusted backend execution context populated strictly from verified KEEP authentication.

    Security invariant: `user_id`, `tenant_id`, `roles`, and `permissions` MUST be
    constructed by trusted KEEP backend code (`build_trusted_agent_context`) and
    NEVER populated from untrusted client payloads.
    """

    user_id: str = Field(..., min_length=1, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=128)
    correlation_id: str = Field(default_factory=generate_correlation_id, min_length=1, max_length=128)
    roles: list[str] = Field(default_factory=list)
    permissions: set[str] = Field(default_factory=set)
    deadline_seconds: int = Field(default=60, ge=1, le=3600)
    trusted_source: Literal["keep_jwt_auth", "keep_internal_system"] = Field(
        default="keep_jwt_auth",
        description="Provenance marker proving context originated from trusted KEEP auth.",
    )
    issued_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("user_id", "tenant_id", "correlation_id")
    @classmethod
    def strip_required_ids(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Trusted context identifiers cannot be empty.")
        return cleaned

    def has_permission(self, permission: str) -> bool:
        """Returns True if the trusted principal holds the given KEEP permission."""
        return permission in self.permissions


class EvidenceReference(BaseModel):
    """Traceable source reference returned by knowledge, document, or research agents."""

    source_id: str = Field(..., min_length=1, max_length=256)
    source_type: Literal["document", "chunk", "graph_entity", "connector", "system"] = Field(
        default="document"
    )
    title: str | None = Field(default=None, max_length=512)
    excerpt: str | None = Field(default=None, max_length=2000)
    uri: str | None = Field(default=None, max_length=1024)
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    chunk_index: int | None = Field(default=None, ge=0)
    tenant_id: str | None = Field(default=None, max_length=128)

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("EvidenceReference.source_id cannot be blank.")
        return cleaned


class AgentResult(BaseModel):
    """Canonical structured result returned by every KEEP BaseAgent implementation."""

    status: AgentStatus
    output: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = Field(default=None, max_length=128)
    error_message: str | None = Field(default=None, max_length=512)
    error: AgentErrorDetail | None = Field(default=None)
    schema_version: str = Field(default=AGENT_CONTRACT_SCHEMA_VERSION)

    @field_validator("schema_version")
    @classmethod
    def check_schema_version(cls, value: str) -> str:
        return validate_contract_schema_version(value)

    @field_validator("error_message")
    @classmethod
    def sanitize_result_error_message(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return sanitize_error_message(value)

    @model_validator(mode="after")
    def validate_status_consistency(self) -> AgentResult:
        """Enforces consistency between `status`, `error_code`, and `error`."""
        if self.status == "succeeded":
            if self.error_code is not None or self.error is not None:
                raise ValueError("A succeeded AgentResult must not include error_code or error details.")
        else:
            # Failed result: synchronize error_code and structured error cleanly
            if self.error is not None and self.error_code is None:
                self.error_code = self.error.code.value
            if self.error is not None and self.error_message is None:
                self.error_message = self.error.message
            if self.error_code is None:
                self.error_code = AgentErrorCode.AGENT_EXECUTION_FAILED.value
        return self

    @classmethod
    def failure(
        cls,
        *,
        code: AgentErrorCode,
        message: str,
        warnings: list[str] | None = None,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> AgentResult:
        """Factory for constructing a sanitized, contract-compliant failed AgentResult."""
        error_detail = AgentErrorDetail(
            code=code,
            message=message,
            retryable=retryable,
            details=details or {},
        )
        return cls(
            status="failed",
            output={},
            warnings=warnings or [],
            error_code=error_detail.code.value,
            error_message=error_detail.message,
            error=error_detail,
        )


EXAMPLE_AGENT_REQUEST: dict[str, Any] = {
    "request_id": "req_example_001",
    "task_id": "task_example_001",
    "goal": "Summarize KEEP Phase 4.1 multi-agent boundaries.",
    "input": {"topic": "multi-agent-architecture"},
    "correlation_id": "corr_example_001",
    "schema_version": AGENT_CONTRACT_SCHEMA_VERSION,
}

EXAMPLE_AGENT_RESULT: dict[str, Any] = {
    "status": "succeeded",
    "output": {"message": "Agent contract integration is working."},
    "evidence": [
        {
            "source_id": "doc_phase4_arch",
            "source_type": "document",
            "title": "KEEP Phase 4.1 Architecture",
            "excerpt": "KEEP owns agent identity, registry, contracts, and security policies.",
            "score": 0.96,
        }
    ],
    "warnings": [],
    "error_code": None,
    "error_message": None,
    "error": None,
    "schema_version": AGENT_CONTRACT_SCHEMA_VERSION,
}
