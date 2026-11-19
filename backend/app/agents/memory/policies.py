"""KEEP Phase 4.7 — Memory Policy Engine.

Enforces zero-trust tenant isolation, prompt injection screening, credential redaction,
and proposal governance rules.

Specification: devdocs/p4/p4.7.txt (Sections 4, 6)
Owner: Member 3 (Privacy, Governance & Lifecycle)
"""

from __future__ import annotations

import re

from backend.app.agents.errors import (
    AgentErrorCode,
    MemoryAccessDeniedError,
    MemoryContentInvalidError,
    MemoryPromptInjectionBlockedError,
    MemoryTenantIsolationViolationError,
)
from backend.app.agents.memory.access_control import (
    MemoryAccessController,
    PolicyDecision,
    is_tenant_admin,
)
from backend.app.agents.memory.contracts import (
    MemoryProposal,
    MemoryQuery,
    MemoryRecord,
    MemorySecurityContext,
)

_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions"),
    re.compile(r"(?i)system\s+prompt\s*:"),
    re.compile(r"(?i)you\s+are\s+now\s+(a\s+)?(DAN|developer\s+mode|jailbroken)"),
    re.compile(r"(?i)bypass\s+(security|policy|restrictions|rules)"),
    re.compile(r"(?i)disregard\s+(all\s+)?rules"),
    re.compile(r"(?i)forget\s+all\s+(previous\s+)?instructions"),
    re.compile(r"(?i)output\s+the\s+entire\s+prompt"),
)

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"(?i)(password|secret|api[_-]?key|token)\s*[:=]\s*['\"]?[^\s'\";,]+['\"]?"),
)


def contains_prompt_injection(content: str) -> bool:
    """Checks whether content contains prompt injection or instruction override patterns."""
    return any(p.search(content) for p in _INJECTION_PATTERNS)


def sanitize_sensitive_content(content: str) -> str:
    """Masks credentials, API keys, and bearer tokens from memory content."""
    sanitized = content
    for pattern in _SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
    return sanitized


class MemoryPolicyEngine:
    """Evaluates security, content validation, and approval policies for memories."""

    def __init__(self, access_controller: MemoryAccessController | None = None) -> None:
        self.access_controller = access_controller or MemoryAccessController()

    def authorize_read_query(
        self,
        query: MemoryQuery,
        security_context: MemorySecurityContext,
    ) -> PolicyDecision:
        """Validates that query scopes and context parameters are authorized."""
        # Standard users requesting organization scope is allowed (read-only)
        # Checking workflow scope
        if (
            "workflow" in query.allowed_scopes
            and not query.workflow_execution_id
            and not security_context.workflow_execution_id
            and not is_tenant_admin(security_context)
        ):
            return PolicyDecision.deny(
                AgentErrorCode.MEMORY_ACCESS_DENIED,
                action="read_query",
                details={"reason": "Workflow scope requested without active workflow execution."},
            )

        # Checking agent scope
        if (
            "agent" in query.allowed_scopes
            and not query.agent_execution_id
            and not security_context.agent_execution_id
            and not is_tenant_admin(security_context)
        ):
            return PolicyDecision.deny(
                AgentErrorCode.MEMORY_ACCESS_DENIED,
                action="read_query",
                details={"reason": "Agent scope requested without active agent execution."},
            )

        return PolicyDecision.allow("read_query")

    def authorize_proposal(
        self,
        proposal: MemoryProposal,
        security_context: MemorySecurityContext,
    ) -> PolicyDecision:
        """Evaluates write policy, tenant boundary, and content security for a proposal."""
        # 1. Tenant boundary check
        if proposal.tenant_id != security_context.tenant_id:
            raise MemoryTenantIsolationViolationError(
                tenant_id=security_context.tenant_id,
                target_tenant_id=proposal.tenant_id,
            )

        # 2. Content validation
        if not proposal.content or not proposal.content.strip():
            raise MemoryContentInvalidError("Content cannot be empty.")
        if len(proposal.content) > 4000:
            raise MemoryContentInvalidError("Content exceeds 4000 characters limit.")

        # 3. Prompt injection screening
        if contains_prompt_injection(proposal.content):
            raise MemoryPromptInjectionBlockedError()

        # 4. Scope and ownership mutation check
        decision = self.access_controller.check_mutation_access(
            scope=proposal.scope,
            owner_id=proposal.owner_id,
            target_tenant_id=proposal.tenant_id,
            action="propose",
            security_context=security_context,
        )
        if not decision.allowed:
            raise MemoryAccessDeniedError(
                f"Unauthorized proposal for scope '{proposal.scope}'.",
                details=decision.details,
            )

        # Sanitize sensitive credentials
        proposal.content = sanitize_sensitive_content(proposal.content)

        return PolicyDecision.allow("propose")

    def determine_auto_approval(
        self,
        proposal: MemoryProposal,
        security_context: MemorySecurityContext,
    ) -> bool:
        """Determines whether a proposal can be immediately activated without manual review.

        Core rule: Model-generated proposals ('agent', 'workflow') can NEVER self-approve.
        User-submitted preferences with confidence >= 0.8 are eligible for auto-approval.
        """
        if proposal.proposer_type != "user":
            return False

        if proposal.scope == "user" and proposal.owner_id == security_context.user_id:
            return proposal.confidence >= 0.8

        if proposal.scope == "organization" and is_tenant_admin(security_context):
            return proposal.confidence >= 0.8

        return False

    def authorize_approval(
        self,
        proposal: MemoryProposal,
        security_context: MemorySecurityContext,
    ) -> PolicyDecision:
        """Validates clearance to approve a pending proposal."""
        decision = self.access_controller.check_mutation_access(
            scope=proposal.scope,
            owner_id=proposal.owner_id,
            target_tenant_id=proposal.tenant_id,
            action="approve",
            security_context=security_context,
        )
        if not decision.allowed:
            raise MemoryAccessDeniedError(
                f"Caller lacks clearance to approve proposal for scope '{proposal.scope}'.",
                details=decision.details,
            )
        return decision

    def authorize_deletion(
        self,
        record: MemoryRecord,
        security_context: MemorySecurityContext,
    ) -> PolicyDecision:
        """Validates clearance to delete an existing memory record."""
        decision = self.access_controller.check_mutation_access(
            scope=record.scope,
            owner_id=record.owner_id,
            target_tenant_id=record.tenant_id,
            action="delete",
            security_context=security_context,
        )
        if not decision.allowed:
            raise MemoryAccessDeniedError(
                f"Caller lacks clearance to delete memory in scope '{record.scope}'.",
                details=decision.details,
            )
        return decision

    def filter_results(
        self,
        memories: list[MemoryRecord],
        security_context: MemorySecurityContext,
    ) -> list[MemoryRecord]:
        """Defense-in-depth: verifies read access for each candidate before returning to caller."""
        allowed: list[MemoryRecord] = []
        for memory in memories:
            decision = self.access_controller.check_read_access(memory, security_context)
            if decision.allowed:
                allowed.append(memory)
        return allowed
