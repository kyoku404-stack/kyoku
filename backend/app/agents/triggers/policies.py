"""KEEP Phase 4.10 — Trigger Security & Policy Engine.

Enforces zero-trust tenant isolation, RBAC clearance for trigger management
and event ingestion, cooldown throttling, and max concurrent run caps.

Owner: Member 3 (Reliability, Scheduling & Security Policies)
Specification: devdocs/p4/p4.10.txt (Sections 6, 8)
"""

from __future__ import annotations

from datetime import UTC, datetime

from backend.app.agents.errors import (
    EventTenantMismatchError,
    TriggerAccessDeniedError,
    TriggerDisabledError,
    TriggerPolicyDeniedError,
    TriggerRateLimitedError,
)
from backend.app.agents.events.contracts import (
    EventAuditRecord,
    EventSecurityContext,
    KeepEvent,
)
from backend.app.agents.events.event_store import BaseEventStore
from backend.app.agents.triggers.models import TriggerRule
from backend.app.agents.triggers.repository import BaseTriggerRepository


class TriggerPolicyEngine:
    """Enforces zero-trust RBAC, tenant isolation, cooldowns, and concurrency bounds."""

    def __init__(
        self,
        trigger_repository: BaseTriggerRepository,
        event_store: BaseEventStore | None = None,
    ) -> None:
        self.trigger_repository = trigger_repository
        self.event_store = event_store

    @staticmethod
    def authorize_manage(security_context: EventSecurityContext) -> None:
        """Verifies caller has permission to create, update, enable/disable triggers or replay DLQ."""
        roles = {r.lower() for r in security_context.roles}
        perms = {p.lower() for p in security_context.permissions}
        if "revoked" in roles or "viewer" in roles or "guest" in roles:
            raise TriggerAccessDeniedError("Caller role lacks permission to manage triggers.")
        has_perm = (
            "agent.manage" in perms
            or "agent.invoke" in perms
            or "*" in perms
            or bool(roles.intersection({"superadmin", "orgadmin", "admin", "manager", "lead", "member", "service"}))
        )
        if not has_perm:
            raise TriggerAccessDeniedError("Caller lacks 'agent.manage' or 'agent.invoke' permission.")

    @staticmethod
    def authorize_read(target_tenant_id: str, security_context: EventSecurityContext) -> None:
        if target_tenant_id != security_context.tenant_id:
            raise EventTenantMismatchError(security_context.tenant_id, target_tenant_id)
        roles = {r.lower() for r in security_context.roles}
        if "revoked" in roles:
            raise TriggerAccessDeniedError("Caller permissions have been revoked.")

    async def authorize_trigger(
        self,
        *,
        event: KeepEvent,
        trigger: TriggerRule,
        security_context: EventSecurityContext,
        resource_key: str | None = None,
        now: datetime | None = None,
    ) -> None:
        """Evaluates full dispatch authorization, cooldowns, and concurrency limits."""
        if event.tenant_id != security_context.tenant_id or trigger.tenant_id != security_context.tenant_id:
            raise EventTenantMismatchError(security_context.tenant_id, trigger.tenant_id)

        if not trigger.enabled:
            raise TriggerDisabledError(trigger.trigger_id)

        if trigger.allowed_sources and event.source not in trigger.allowed_sources:
            await self._record_suppression(
                tenant_id=trigger.tenant_id,
                event_id=event.event_id,
                trigger_id=trigger.trigger_id,
                reason=f"Source '{event.source}' is not in allowed_sources.",
            )
            raise TriggerPolicyDeniedError(
                f"Source '{event.source}' is not allowed for trigger '{trigger.trigger_id}'."
            )

        current = now or datetime.now(UTC)

        # Cooldown check per resource_key (or trigger_id)
        if trigger.cooldown_seconds > 0:
            key = resource_key or trigger.trigger_id
            latest = await self.trigger_repository.get_latest_dispatch_for_resource(
                trigger.trigger_id, trigger.tenant_id, key
            )
            if latest is not None:
                created_at = latest.created_at
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=UTC)
                elapsed = (current - created_at).total_seconds()
                if elapsed < trigger.cooldown_seconds:
                    reason = (
                        f"Cooldown active ({elapsed:.1f}s < {trigger.cooldown_seconds}s) for key '{key}'."
                    )
                    await self._record_suppression(
                        tenant_id=trigger.tenant_id,
                        event_id=event.event_id,
                        trigger_id=trigger.trigger_id,
                        reason=reason,
                    )
                    raise TriggerRateLimitedError(trigger.trigger_id, reason)

        # Active concurrent dispatch cap check
        active_count = await self.trigger_repository.count_active_dispatches(
            trigger.trigger_id, trigger.tenant_id
        )
        if active_count >= trigger.max_concurrent_runs:
            reason = (
                f"Max concurrent runs reached ({active_count}/{trigger.max_concurrent_runs})."
            )
            await self._record_suppression(
                tenant_id=trigger.tenant_id,
                event_id=event.event_id,
                trigger_id=trigger.trigger_id,
                reason=reason,
            )
            raise TriggerRateLimitedError(trigger.trigger_id, reason)

    async def _record_suppression(
        self,
        *,
        tenant_id: str,
        event_id: str,
        trigger_id: str,
        reason: str,
    ) -> None:
        if self.event_store is not None:
            await self.event_store.append_audit(
                EventAuditRecord(
                    tenant_id=tenant_id,
                    event_id=event_id,
                    trigger_id=trigger_id,
                    action="trigger.suppressed",
                    actor_id="system:policy",
                    reason=reason,
                )
            )
