"""KEEP Phase 4.7 — Agent Memory System Data Contracts & Interfaces.

Defines memory records, scopes, lifecycle states, proposals, retrieval queries,
security context, and version tracking contracts.

Specification: devdocs/p4/p4.7.txt (Sections 2, 5, 7, 8)
Owner: Member 1 (Memory Contracts & Storage)
"""

from __future__ import annotations

import datetime
import hashlib
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

MemoryScope = Literal[
    "user",
    "organization",
    "workflow",
    "agent",
]

MemoryStatus = Literal[
    "proposed",
    "active",
    "expired",
    "deleted",
    "rejected",
]

ProposalStatus = Literal[
    "pending",
    "approved",
    "rejected",
]

MemoryType = Literal[
    "preference",
    "fact",
    "intermediate_result",
    "instruction",
    "observation",
]


def compute_content_hash(content: str) -> str:
    """Computes SHA-256 hash of normalized content for deduplication and integrity."""
    normalized = " ".join(content.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class MemorySecurityContext(BaseModel):
    """Trusted security context derived exclusively from verified JWT authentication."""

    tenant_id: str = Field(..., min_length=1, max_length=128)
    user_id: str = Field(..., min_length=1, max_length=128)
    roles: list[str] = Field(default_factory=list)
    is_admin: bool = Field(default=False)
    workflow_execution_id: str | None = Field(default=None, max_length=128)
    agent_execution_id: str | None = Field(default=None, max_length=128)
    correlation_id: str | None = Field(default=None, max_length=128)

    @field_validator("tenant_id", "user_id")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Identifier must not be empty or whitespace.")
        return stripped


class MemoryRecord(BaseModel):
    """Canonical active or historical memory entity."""

    memory_id: str = Field(..., min_length=1, max_length=128)
    scope: MemoryScope
    owner_id: str = Field(..., min_length=1, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=128)
    memory_type: str = Field(default="preference", min_length=1, max_length=64)
    content: str = Field(..., min_length=1, max_length=4000)
    content_hash: str = Field(default="")
    source_type: str = Field(default="user_input", max_length=64)
    source_reference: str | None = Field(default=None, max_length=128)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    status: MemoryStatus = Field(default="active")
    version: int = Field(default=1, ge=1)
    superseded_by: str | None = Field(default=None, max_length=128)
    meta_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    expires_at: datetime.datetime | None = None
    deleted_at: datetime.datetime | None = None

    def model_post_init(self, context: Any, /) -> None:
        if not self.content_hash:
            self.content_hash = compute_content_hash(self.content)

    @property
    def is_active(self) -> bool:
        """Determines if the memory record is currently active and unexpired."""
        if self.status != "active":
            return False
        if self.deleted_at is not None:
            return False
        return not (self.expires_at is not None and self.expires_at <= datetime.datetime.now(datetime.UTC))

    @property
    def estimated_tokens(self) -> int:
        """Rough token estimate (~4 chars per token)."""
        return max(1, len(self.content) // 4)


class MemoryProposal(BaseModel):
    """Candidate memory submitted by an agent or workflow awaiting policy review."""

    proposal_id: str = Field(..., min_length=1, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=128)
    scope: MemoryScope
    owner_id: str = Field(..., min_length=1, max_length=128)
    proposer_id: str = Field(..., min_length=1, max_length=128)
    proposer_type: Literal["agent", "workflow", "user"] = Field(default="agent")
    memory_type: str = Field(default="preference", min_length=1, max_length=64)
    content: str = Field(..., min_length=1, max_length=4000)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_reference: str | None = Field(default=None, max_length=128)
    status: ProposalStatus = Field(default="pending")
    rejection_reason: str | None = Field(default=None, max_length=256)
    approved_memory_id: str | None = Field(default=None, max_length=128)
    meta_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    reviewed_at: datetime.datetime | None = None


class MemoryVersionRecord(BaseModel):
    """Historical snapshot of an overwritten or superseded memory record."""

    version_id: str = Field(..., min_length=1, max_length=128)
    memory_id: str = Field(..., min_length=1, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=128)
    version: int = Field(..., ge=1)
    content: str = Field(..., min_length=1, max_length=4000)
    content_hash: str = Field(...)
    reason: str | None = Field(default=None, max_length=256)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )


class MemoryAccessEvent(BaseModel):
    """Audit log entry capturing retrieval, proposal, approval, or deletion events."""

    event_id: str = Field(..., min_length=1, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=128)
    user_id: str = Field(..., min_length=1, max_length=128)
    action: Literal["retrieve", "propose", "approve", "reject", "update", "expire", "delete"]
    memory_id: str | None = Field(default=None, max_length=128)
    scope: MemoryScope | None = None
    allowed: bool = Field(default=True)
    denial_reason: str | None = Field(default=None, max_length=64)
    query_summary: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = Field(default=None, max_length=128)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )


class MemoryQuery(BaseModel):
    """Search query parameters with scope boundaries and context token limit."""

    query: str = Field(..., min_length=1, max_length=1000)
    allowed_scopes: list[MemoryScope] = Field(
        default_factory=lambda: ["user", "organization"]
    )
    limit: int = Field(default=5, ge=1, le=50)
    max_tokens: int = Field(default=1000, ge=50, le=8000)
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    memory_types: list[str] | None = None
    workflow_execution_id: str | None = None
    agent_execution_id: str | None = None


class MemoryRetrievalResult(BaseModel):
    """Structured response for retrieved memories within budget."""

    memories: list[MemoryRecord]
    total_candidates: int
    returned_count: int
    total_estimated_tokens: int
    query: str


class MemoryWriteRequest(BaseModel):
    """Client or internal write/proposal request payload."""

    scope: MemoryScope = Field(default="user")
    memory_type: str = Field(default="preference", min_length=1, max_length=64)
    content: str = Field(..., min_length=1, max_length=4000)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_type: str = Field(default="user_input", max_length=64)
    source_reference: str | None = Field(default=None, max_length=128)
    owner_id: str | None = Field(default=None, max_length=128)
    meta_data: dict[str, Any] = Field(default_factory=dict)
