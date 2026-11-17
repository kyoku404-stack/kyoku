"""KEEP Phase 4.1 — Agent Metadata & Capability Contracts.

Defines structured metadata and capability declarations for KEEP agents.
Note: Capabilities declare what an agent supports — they are NOT authorization
by themselves. The security layer (`backend/app/services/security/agent_policy.py`)
independently enforces permissions for every requested action.

Owner: Member 1 (Architecture & Agent Registry)
Specification: devdocs/p4/p4.1.txt (Sections 3, 4.2)
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

CapabilityAccess = Literal["read", "write", "sensitive"]

_AGENT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
_CAPABILITY_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{1,63}$")


class AgentCapability(BaseModel):
    """Describes a single capability declared by a KEEP agent."""

    name: str = Field(..., min_length=2, max_length=64, description="Canonical dot-delimited capability identifier.")
    description: str = Field(default="", max_length=512)
    access: CapabilityAccess = Field(
        default="read",
        description="Access tier governing required authorization level: read, write, or sensitive.",
    )
    requires_approval: bool = Field(
        default=False,
        description="Hint for future Phase 4.12 HITL approval gating on sensitive/write actions.",
    )

    @field_validator("name")
    @classmethod
    def validate_capability_name(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _CAPABILITY_NAME_PATTERN.match(normalized):
            raise ValueError(
                f"Invalid capability name '{value}'. Must match ^[a-z][a-z0-9_.-]{{1,63}}$."
            )
        return normalized


class AgentMetadata(BaseModel):
    """Canonical identity, version, and capability descriptor for a KEEP agent."""

    agent_id: str = Field(..., min_length=1, max_length=64, description="Unique stable agent identifier.")
    name: str = Field(..., min_length=1, max_length=128, description="Human-readable agent display name.")
    version: str = Field(..., description="Semantic version (e.g., 1.0.0).")
    description: str = Field(default="", max_length=1024)
    capabilities: list[AgentCapability] = Field(default_factory=list)
    enabled: bool = Field(default=True, description="Whether this agent is currently enabled for discovery/invocation.")
    tags: list[str] = Field(default_factory=list, description="Optional classification tags.")
    schema_version: str = Field(default="1.0", description="Metadata contract schema version.")

    @field_validator("agent_id")
    @classmethod
    def validate_agent_id(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _AGENT_ID_PATTERN.match(normalized):
            raise ValueError(
                f"Invalid agent_id '{value}'. Must match ^[a-z0-9][a-z0-9._-]{{0,63}}$."
            )
        return normalized

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        cleaned = value.strip()
        if not _SEMVER_PATTERN.match(cleaned):
            raise ValueError(f"Invalid semantic version '{value}'. Expected MAJOR.MINOR.PATCH.")
        return cleaned

    @field_validator("capabilities")
    @classmethod
    def validate_unique_capabilities(cls, capabilities: list[AgentCapability]) -> list[AgentCapability]:
        seen: set[str] = set()
        for cap in capabilities:
            if cap.name in seen:
                raise ValueError(f"Duplicate capability name declared on agent: '{cap.name}'.")
            seen.add(cap.name)
        return capabilities

    def has_capability(self, capability_name: str) -> bool:
        """Returns True if the agent declares the specified capability name."""
        target = capability_name.strip().lower()
        return any(cap.name == target for cap in self.capabilities)

    def get_capability(self, capability_name: str) -> AgentCapability | None:
        """Looks up a declared capability by canonical name."""
        target = capability_name.strip().lower()
        for cap in self.capabilities:
            if cap.name == target:
                return cap
        return None

    def max_access_level(self) -> CapabilityAccess:
        """Returns the highest access tier declared across all capabilities."""
        order: dict[CapabilityAccess, int] = {"read": 0, "write": 1, "sensitive": 2}
        highest: CapabilityAccess = "read"
        for cap in self.capabilities:
            if order[cap.access] > order[highest]:
                highest = cap.access
        return highest
