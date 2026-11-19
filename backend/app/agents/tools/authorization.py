"""KEEP Phase 4.6 — Tool Authorization Models & Policy Decisions.

Defines PolicyDecision and authorization response structures.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PolicyDecision(BaseModel):
    """Authorization evaluation outcome for a tool call request."""

    allowed: bool = Field(..., description="Whether the tool invocation is permitted to proceed")
    approval_required: bool = Field(default=False, description="Whether human approval is required before execution")
    reason_code: str | None = Field(default=None, description="Machine-readable policy or error code")
    reason_message: str | None = Field(default=None, description="Sanitized human-readable explanation")
    context_summary: dict[str, Any] = Field(default_factory=dict, description="Diagnostic evaluation details")

    @classmethod
    def allow(cls, context_summary: dict[str, Any] | None = None) -> PolicyDecision:
        return cls(
            allowed=True,
            approval_required=False,
            reason_code="ALLOWED",
            context_summary=context_summary or {},
        )

    @classmethod
    def deny(
        cls,
        reason_code: str,
        reason_message: str,
        context_summary: dict[str, Any] | None = None,
    ) -> PolicyDecision:
        return cls(
            allowed=False,
            approval_required=False,
            reason_code=reason_code,
            reason_message=reason_message,
            context_summary=context_summary or {},
        )

    @classmethod
    def approval_needed(
        cls,
        reason_message: str = "Human approval is required for this action.",
        context_summary: dict[str, Any] | None = None,
    ) -> PolicyDecision:
        return cls(
            allowed=False,
            approval_required=True,
            reason_code="TOOL_APPROVAL_REQUIRED",
            reason_message=reason_message,
            context_summary=context_summary or {},
        )
