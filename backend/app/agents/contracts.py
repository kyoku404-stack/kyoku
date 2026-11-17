"""KEEP Phase 4.1 — Shared Agent Request, Context & Result Contracts (Initial Baseline).

Agreed shared contract baseline between Member 1 and Member 2.
Extended and hardened in Stage 2 (Member 2 — Agent Contracts & Communication).

Specification: devdocs/p4/p4.1.txt (Section 4.3)
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

AGENT_CONTRACT_SCHEMA_VERSION = "1.0"


class AgentRequest(BaseModel):
    """Standard request payload passed to any KEEP BaseAgent."""

    request_id: str = Field(..., min_length=1, max_length=128)
    task_id: str = Field(..., min_length=1, max_length=128)
    goal: str = Field(..., min_length=1, max_length=4096)
    input: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = Field(default=None, max_length=128)
    schema_version: str = Field(default=AGENT_CONTRACT_SCHEMA_VERSION)


class AgentContext(BaseModel):
    """Trusted backend execution context populated strictly from verified KEEP auth."""

    user_id: str = Field(..., min_length=1, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=128)
    correlation_id: str = Field(..., min_length=1, max_length=128)
    roles: list[str] = Field(default_factory=list)
    permissions: set[str] = Field(default_factory=set)
    deadline_seconds: int = Field(default=60, ge=1, le=3600)
    trusted_source: str = Field(default="keep_jwt_auth")


class EvidenceReference(BaseModel):
    """Traceable source reference returned by knowledge or research agents."""

    source_id: str = Field(..., min_length=1, max_length=256)
    source_type: str = Field(default="document", max_length=64)
    title: str | None = Field(default=None, max_length=512)
    excerpt: str | None = Field(default=None, max_length=2000)
    score: float | None = Field(default=None, ge=0.0, le=1.0)


class AgentResult(BaseModel):
    """Standard structured outcome returned by every KEEP BaseAgent."""

    status: Literal["succeeded", "failed"]
    output: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = Field(default=None, max_length=128)
    error_message: str | None = Field(default=None, max_length=1024)
    schema_version: str = Field(default=AGENT_CONTRACT_SCHEMA_VERSION)
