"""KEEP Phase 4.9 — Autonomous Workflow LangGraph State Schema.

Defines `AutonomyState` TypedDict matching Section 6 of `devdocs/p4/p4.9.txt`
plus secret-safe state sanitization helpers before checkpoint persistence.

Owner: Member 1 (Autonomous Controller & Lifecycle)
Specification: devdocs/p4/p4.9.txt (Section 6)
"""

from __future__ import annotations

import re
from typing import Any, TypedDict

_CREDENTIAL_KEY_MARKERS = ("token", "secret", "password", "api_key", "authorization", "cookie")
_CREDENTIAL_VALUE_PATTERN = re.compile(
    r"(?i)(bearer\s+[A-Za-z0-9\-._~+/]+=*|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|sk-[A-Za-z0-9]{16,})"
)


class AutonomyState(TypedDict, total=False):
    """Serializable LangGraph controller state across adaptive plan-execute-evaluate loops."""

    execution_id: str
    tenant_id: str
    workflow_id: str
    objective: str
    security_context_ref: str
    plan: dict[str, Any]
    current_step: int
    completed_steps: list[dict[str, Any]]
    last_outcome: dict[str, Any]
    evaluation: dict[str, Any]
    replan_count: int
    remaining_steps: int
    status: str
    termination_reason: str
    final_result: dict[str, Any]
    approval_granted: bool
    pending_write_step_id: str | None
    limitations: list[str]
    policy_snapshot: dict[str, Any]


def _scrub_value(val: Any) -> Any:
    if isinstance(val, str):
        return _CREDENTIAL_VALUE_PATTERN.sub("[REDACTED]", val)
    if isinstance(val, list):
        return [_scrub_value(item) for item in val]
    if isinstance(val, dict):
        cleaned: dict[str, Any] = {}
        for k, v in val.items():
            if any(marker in str(k).lower() for marker in _CREDENTIAL_KEY_MARKERS):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = _scrub_value(v)
        return cleaned
    return val


def sanitize_autonomy_state(state: dict[str, Any]) -> dict[str, Any]:
    """Strips secrets, bearer tokens, JWTs, and sensitive raw identity fields before checkpointing."""
    sanitized: dict[str, Any] = _scrub_value(dict(state))
    # Never store raw authorization headers or full credential objects in graph checkpoints
    sanitized.pop("raw_jwt", None)
    sanitized.pop("authorization_header", None)
    return sanitized
