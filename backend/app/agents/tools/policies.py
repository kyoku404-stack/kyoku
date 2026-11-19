"""KEEP Phase 4.6 — Tool Policy Engine & Security Enforcer.

Enforces zero-trust authorization, tenant isolation, role-based tool clearance,
approval requirement gating, prompt injection screening, and invocation rate limits.
"""

from __future__ import annotations

import collections
import logging
import re
import time
from typing import Any

from backend.app.agents.errors import (
    ToolPromptInjectionBlockedError,
)
from backend.app.agents.tools.authorization import PolicyDecision
from backend.app.agents.tools.contracts import BaseTool, ToolContext

logger = logging.getLogger(__name__)

_PROMPT_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions"),
    re.compile(r"(?i)(?:system\s+prompt|###\s*system|```\s*system)"),
    re.compile(r"(?i)bypass\s+(?:rbac|security|tenant|policy)"),
    re.compile(r"(?i)<\s*script\b"),
    re.compile(r"(?i)drop\s+table\s+[a-z0-9_]+"),
    re.compile(r"(?i)(?:role\s*:\s*system|admin\s*override)"),
)

_TENANT_ARG_KEYS: frozenset[str] = frozenset(
    {"tenant_id", "organization_id", "org_id"}
)


class ToolPolicyEngine:
    """Zero-trust policy evaluator for tool invocations."""

    def __init__(
        self,
        default_rate_limit: int = 120,  # 120 calls per 60 seconds
        rate_limit_window_seconds: int = 60,
    ) -> None:
        self.default_rate_limit = default_rate_limit
        self.rate_limit_window_seconds = rate_limit_window_seconds
        # In-memory sliding window rate tracker: tenant_id -> deque of timestamps
        self._tenant_call_timestamps: dict[str, collections.deque[float]] = collections.defaultdict(
            collections.deque
        )
        # Tenant specific approval policies (e.g. require approval for all writes)
        self._tenant_write_approval_policies: dict[str, bool] = {}

    def set_tenant_write_approval(self, tenant_id: str, required: bool) -> None:
        """Configures whether a tenant mandates approval for all write tools."""
        self._tenant_write_approval_policies[tenant_id] = required

    def _check_rate_limit(self, tenant_id: str) -> bool:
        """Evaluates sliding window rate limits. Returns True if allowed, False if exceeded."""
        now = time.monotonic()
        cutoff = now - self.rate_limit_window_seconds
        timestamps = self._tenant_call_timestamps[tenant_id]

        while timestamps and timestamps[0] < cutoff:
            timestamps.popleft()

        if len(timestamps) >= self.default_rate_limit:
            return False

        timestamps.append(now)
        return True

    def _screen_prompt_injection(self, tool_id: str, arguments: dict[str, Any]) -> None:
        """Recursively checks string arguments for prompt injection patterns."""
        to_inspect: list[str] = []

        def _extract_strings(val: Any) -> None:
            if isinstance(val, str):
                to_inspect.append(val)
            elif isinstance(val, dict):
                for v in val.values():
                    _extract_strings(v)
            elif isinstance(val, (list, tuple, set)):
                for item in val:
                    _extract_strings(item)

        _extract_strings(arguments)

        for text in to_inspect:
            for pattern in _PROMPT_INJECTION_PATTERNS:
                match = pattern.search(text)
                if match:
                    logger.warning(
                        "Prompt injection blocked in tool '%s': matched '%s'",
                        tool_id,
                        match.group(0),
                    )
                    raise ToolPromptInjectionBlockedError(
                        tool_id=tool_id,
                        pattern_matched=match.group(0),
                    )

    async def authorize(
        self,
        tool: BaseTool,
        context: ToolContext,
        arguments: dict[str, Any],
    ) -> PolicyDecision:
        """Runs the complete policy authorization gate for a tool call."""
        metadata = tool.metadata
        tool_id = metadata.tool_id

        # 1. Identity & Context Verification
        if not context.tenant_id or not context.user_id:
            return PolicyDecision.deny(
                reason_code="AGENT_UNTRUSTED_CONTEXT",
                reason_message="Missing verified tenant_id or user_id in execution context.",
            )

        # 2. Hard Tenant Boundary Enforcement
        # Model-supplied arguments cannot specify a differing tenant_id
        for key in _TENANT_ARG_KEYS:
            if key in arguments:
                arg_tenant = str(arguments[key]).strip()
                if arg_tenant and arg_tenant != context.tenant_id and not context.is_admin:
                    return PolicyDecision.deny(
                        reason_code="AGENT_TENANT_ISOLATION_VIOLATION",
                        reason_message=f"Cross-tenant tool parameter violation: argument {key}='{arg_tenant}' "
                        f"does not match caller tenant '{context.tenant_id}'.",
                        context_summary={"attempted_tenant": arg_tenant, "caller_tenant": context.tenant_id},
                    )

        # 3. Prompt Injection Screening
        try:
            self._screen_prompt_injection(tool_id, arguments)
        except ToolPromptInjectionBlockedError as err:
            return PolicyDecision.deny(
                reason_code="TOOL_PROMPT_INJECTION_BLOCKED",
                reason_message=err.safe_message,
                context_summary=err.details,
            )

        # 4. Role Clearance & Access Mode Verification
        user_roles = {r.lower() for r in context.roles}
        is_admin = context.is_admin

        # Check required roles if specified on tool metadata
        if metadata.required_roles and not is_admin:
            required = {r.lower() for r in metadata.required_roles}
            if not bool(user_roles & required):
                return PolicyDecision.deny(
                    reason_code="TOOL_PERMISSION_DENIED",
                    reason_message=f"Caller lacks required role for tool '{tool_id}'. Required: {metadata.required_roles}",
                    context_summary={"user_roles": context.roles, "required_roles": metadata.required_roles},
                )

        # Check write access mode against pure read-only roles
        if metadata.access_mode == "write" and not is_admin and user_roles == {"viewer"}:
            return PolicyDecision.deny(
                reason_code="TOOL_PERMISSION_DENIED",
                reason_message=f"Read-only viewer cannot invoke state-modifying write tool '{tool_id}'.",
            )

        # 5. Approval Requirement Gating
        # A) Explicit tool metadata requirement
        if metadata.requires_approval and not is_admin:
            return PolicyDecision.approval_needed(
                reason_message=f"Tool '{tool_id}' is configured to require human approval before execution.",
                context_summary={"tool_id": tool_id, "requires_approval": True},
            )

        # B) Tenant-wide write approval requirement
        if metadata.access_mode == "write" and not is_admin:
            tenant_mandate = self._tenant_write_approval_policies.get(context.tenant_id, False)
            if tenant_mandate:
                return PolicyDecision.approval_needed(
                    reason_message=f"Tenant '{context.tenant_id}' requires human approval for all write actions.",
                    context_summary={"tenant_policy": "require_write_approval"},
                )

        # 6. Rate Limit Evaluation
        if not is_admin and not self._check_rate_limit(context.tenant_id):
            return PolicyDecision.deny(
                reason_code="TOOL_RATE_LIMITED",
                reason_message=f"Tenant '{context.tenant_id}' tool invocation rate limit exceeded.",
                context_summary={
                    "limit": self.default_rate_limit,
                    "window_seconds": self.rate_limit_window_seconds,
                },
            )

        # Authorized
        return PolicyDecision.allow(
            context_summary={
                "tool_id": tool_id,
                "tenant_id": context.tenant_id,
                "access_mode": metadata.access_mode,
            }
        )
