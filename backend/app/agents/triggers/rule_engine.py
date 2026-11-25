"""KEEP Phase 4.10 — Trigger Rule Evaluation Engine.

Resolves tenant-scoped enabled TriggerRules matching an event type, enforces
source allowlists, evaluates declarative conditions safely, and computes
resource deduplication keys for cooldown & concurrency checks.

Owner: Member 2 (Trigger Registry & Rule Engine)
Specification: devdocs/p4/p4.10.txt (Section 6)
"""

from __future__ import annotations

from backend.app.agents.events.contracts import KeepEvent
from backend.app.agents.triggers.conditions import evaluate_conditions
from backend.app.agents.triggers.models import TriggerRule, TriggerRuleMatch
from backend.app.agents.triggers.repository import BaseTriggerRepository


class TriggerRuleEngine:
    """Evaluates incoming KeepEvents against enabled tenant trigger rules."""

    def __init__(self, repository: BaseTriggerRepository) -> None:
        self.repository = repository

    @staticmethod
    def resolve_resource_key(event: KeepEvent, trigger: TriggerRule) -> str:
        """Determines canonical resource key for cooldown and concurrency tracking."""
        if event.resource_id:
            return f"{trigger.trigger_id}:{event.resource_id}"
        doc_id = event.payload.get("document_id") or event.payload.get("source_id")
        if doc_id:
            return f"{trigger.trigger_id}:{doc_id}"
        return trigger.trigger_id

    async def evaluate_event(self, event: KeepEvent) -> list[TriggerRuleMatch]:
        """Evaluates all tenant rules for `event.event_type` and returns match diagnostics."""
        candidates = await self.repository.list_triggers(
            event.tenant_id,
            event_type=event.event_type,
            enabled_only=False,
            limit=200,
        )
        results: list[TriggerRuleMatch] = []
        for trigger in candidates:
            if not trigger.enabled:
                results.append(
                    TriggerRuleMatch(
                        trigger=trigger,
                        matched=False,
                        reason="Trigger rule is disabled.",
                    )
                )
                continue

            if trigger.allowed_sources and event.source not in trigger.allowed_sources:
                results.append(
                    TriggerRuleMatch(
                        trigger=trigger,
                        matched=False,
                        reason=f"Event source '{event.source}' not in rule allowed_sources.",
                    )
                )
                continue

            cond_ok, cond_reason = evaluate_conditions(event, trigger.conditions)
            res_key = self.resolve_resource_key(event, trigger) if cond_ok else None
            results.append(
                TriggerRuleMatch(
                    trigger=trigger,
                    matched=cond_ok,
                    reason=cond_reason,
                    resource_key=res_key,
                )
            )
        return results
