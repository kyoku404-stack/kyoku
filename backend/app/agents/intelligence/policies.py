"""Phase 4.11 — Zero-Trust Governance, RBAC, Source Re-Check & Redaction Policies."""

from __future__ import annotations

import re

from backend.app.agents.errors import (
    IntelligenceAccessDeniedError,
    IntelligenceTenantViolationError,
)
from backend.app.agents.intelligence.contracts import (
    IntelligenceCandidate,
    IntelligenceInsight,
    IntelligenceSecurityContext,
)

_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|bearer)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
]


class IntelligencePolicyEngine:
    """Enforces tenant isolation, RBAC, source-level re-verification, and redaction."""

    def __init__(
        self,
        min_publish_priority: float = 25.0,
        min_confidence_score: float = 0.35,
        retention_days: int = 90,
    ) -> None:
        self.min_publish_priority = min_publish_priority
        self.min_confidence_score = min_confidence_score
        self.retention_days = retention_days

    def authorize_read(self, ctx: IntelligenceSecurityContext) -> None:
        if not ctx.tenant_id or not ctx.user_id:
            raise IntelligenceAccessDeniedError("Authenticated tenant and user context required.")

    def authorize_scan(self, ctx: IntelligenceSecurityContext) -> None:
        self.authorize_read(ctx)
        roles_lower = {r.lower() for r in ctx.roles}
        if (
            "agent.invoke" not in ctx.permissions
            and "agent.manage" not in ctx.permissions
            and not roles_lower.intersection({"admin", "lead", "owner", "super_admin"})
        ):
            raise IntelligenceAccessDeniedError("Caller lacks permission to initiate proactive scans.")

    def authorize_org_action(self, ctx: IntelligenceSecurityContext) -> None:
        self.authorize_read(ctx)
        roles_lower = {r.lower() for r in ctx.roles}
        if (
            "agent.manage" not in ctx.permissions
            and not roles_lower.intersection({"admin", "lead", "owner", "super_admin"})
        ):
            raise IntelligenceAccessDeniedError(
                "Organization-wide insight dismissal or resolution requires admin/lead role."
            )

    def assert_tenant_match(self, expected_tenant_id: str, ctx: IntelligenceSecurityContext) -> None:
        if expected_tenant_id != ctx.tenant_id:
            raise IntelligenceTenantViolationError()

    def filter_visible_insights(
        self,
        insights: list[IntelligenceInsight],
        ctx: IntelligenceSecurityContext,
        user_dismissed_keys: set[str],
    ) -> list[IntelligenceInsight]:
        """Filters insights by tenant, user dismissals, role audience, and live source access."""
        caller_roles = {r.lower() for r in ctx.roles}
        is_privileged = bool(caller_roles.intersection({"admin", "super_admin"}))
        allowed_refs = (
            set(ctx.accessible_resource_refs)
            if ctx.accessible_resource_refs is not None
            else None
        )

        visible: list[IntelligenceInsight] = []
        for ins in insights:
            if ins.tenant_id != ctx.tenant_id:
                continue
            if ins.dedup_key in user_dismissed_keys:
                continue
            if ins.audience_roles and not is_privileged:
                audience = {r.lower() for r in ins.audience_roles}
                if not caller_roles.intersection(audience):
                    continue
            if (
                allowed_refs is not None
                and ins.evidence_refs
                and not set(ins.evidence_refs).issubset(allowed_refs)
            ):
                continue
            visible.append(ins)
        return visible

    def check_publication_policy(
        self,
        candidate: IntelligenceCandidate,
        priority_score: float,
        evidence_valid: bool,
        ctx: IntelligenceSecurityContext,
    ) -> tuple[bool, str | None]:
        """Gates candidate promotion to published insight."""
        if not evidence_valid and not candidate.allow_evidence_free:
            return False, "Withheld: missing or unauthorized evidence references."
        if candidate.confidence_score < self.min_confidence_score and not candidate.allow_evidence_free:
            return (
                False,
                f"Withheld: confidence {candidate.confidence_score:.2f} below {self.min_confidence_score:.2f}.",
            )
        if priority_score < self.min_publish_priority:
            return (
                False,
                f"Withheld: priority score {priority_score:.1f} below threshold {self.min_publish_priority:.1f}.",
            )
        return True, None

    def sanitize_summary(self, text: str) -> str:
        """Scrubs potential secrets/tokens from insight summaries before storage or feed display."""
        cleaned = text
        for pattern in _SECRET_PATTERNS:
            cleaned = pattern.sub("[REDACTED]", cleaned)
        return cleaned
