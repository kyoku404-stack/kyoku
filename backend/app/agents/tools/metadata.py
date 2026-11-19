"""KEEP Phase 4.6 — Tool Metadata & Capability Specifications.

Defines model-facing tool descriptors, schemas, execution constraints,
and access policies for registered KEEP tools.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ToolMetadata(BaseModel):
    """Metadata describing a registered platform tool."""

    tool_id: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="Unique canonical tool identifier, e.g. 'knowledge.search'",
    )
    version: str = Field(
        default="1.0.0",
        min_length=1,
        max_length=32,
        description="Semantic version string of the tool implementation",
    )
    description: str = Field(
        ...,
        min_length=5,
        max_length=1024,
        description="Human and LLM readable summary of the tool capability",
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="Tags describing operational capabilities, e.g. ['search', 'documents']",
    )
    access_mode: Literal["read", "write"] = Field(
        default="read",
        description="Access tier: 'read' for safe query operations, 'write' for state-altering mutations",
    )
    enabled: bool = Field(
        default=True,
        description="Whether this tool is currently available for discovery and invocation",
    )
    requires_approval: bool = Field(
        default=False,
        description="Whether invocation requires explicit human approval before executing side effects",
    )
    parameters_schema: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema describing accepted input arguments",
    )
    returns_schema: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema describing validated output results",
    )
    timeout_seconds: float = Field(
        default=15.0,
        ge=0.5,
        le=300.0,
        description="Maximum execution duration in seconds before timing out",
    )
    max_retries: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Bounded retry count for transient errors (only valid for read access_mode)",
    )
    max_output_bytes: int = Field(
        default=1024 * 1024,  # 1 MB
        ge=1024,
        le=10 * 1024 * 1024,
        description="Maximum serialized payload size in bytes permitted for output",
    )
    required_roles: list[str] = Field(
        default_factory=list,
        description="Required user/tenant roles (e.g. ['member', 'project_manager', 'org_admin'])",
    )

    @field_validator("max_retries")
    @classmethod
    def validate_retry_for_write(cls, v: int, info: Any) -> int:
        access_mode = info.data.get("access_mode", "read")
        if access_mode == "write" and v > 0:
            raise ValueError("Write tools cannot configure automatic retries (max_retries must be 0)")
        return v
