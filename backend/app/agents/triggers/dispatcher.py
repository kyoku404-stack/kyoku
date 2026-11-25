"""KEEP Phase 4.10 — Authorized Workflow Trigger Dispatcher.

Bridges matched TriggerRules to Phase 4.3 `KeepOrchestrationService` and
Phase 4.9 `AutonomousWorkflowService` using atomic DB `dispatch_key` claims
to ensure effectively-once workflow launches across retries and crashes.

Owner: Member 4 (Workflow Dispatch, API & Integration)
Specification: devdocs/p4/p4.10.txt (Sections 6, 7, 8)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import (
    AgentLayerError,
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
from backend.app.agents.triggers.models import TriggerDispatchRecord, TriggerRule
from backend.app.agents.triggers.policies import TriggerPolicyEngine
from backend.app.agents.triggers.repository import BaseTriggerRepository
from backend.app.agents.triggers.rule_engine import TriggerRuleEngine


class TriggerDispatcher:
    """Atomically claims dispatches and launches registered KEEP or Autonomous workflows."""

    def __init__(
        self,
        trigger_repository: BaseTriggerRepository,
        *,
        event_store: BaseEventStore | None = None,
        workflow_registry: Any | None = None,
        policy_engine: TriggerPolicyEngine | None = None,
        orchestration_service: Any | None = None,
        autonomy_service: Any | None = None,
    ) -> None:
        self.trigger_repository = trigger_repository
        self.event_store = event_store
        self.workflow_registry = workflow_registry
        self.policy_engine = policy_engine or TriggerPolicyEngine(
            trigger_repository, event_store
        )
        self.rule_engine = TriggerRuleEngine(trigger_repository)
        self.orchestration_service = orchestration_service
        self.autonomy_service = autonomy_service

    async def dispatch(
        self,
        event: KeepEvent,
        trigger: TriggerRule,
        security_context: EventSecurityContext,
        *,
        resource_key: str | None = None,
    ) -> TriggerDispatchRecord:
        """Executes single-rule policy validation, atomic claim, and workflow submission."""
        if not trigger.enabled:
            raise TriggerDisabledError(trigger.trigger_id)

        await self.policy_engine.authorize_trigger(
            event=event,
            trigger=trigger,
            security_context=security_context,
            resource_key=resource_key,
        )

        # Atomic DB unique constraint claim on `{event_id}:{trigger_id}:{trigger.version}`
        claim, is_new = await self.trigger_repository.claim_dispatch(
            event_id=event.event_id,
            trigger=trigger,
            resource_key=resource_key or trigger.trigger_id,
        )
        if not is_new and claim.workflow_execution_id is not None:
            # Crash/retry reconciliation: reuse already launched execution without duplicating
            return claim

        safe_event_data = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "schema_version": event.schema_version,
            "source": event.source,
            "resource_id": event.resource_id,
            "occurred_at": event.occurred_at.isoformat(),
            # Strictly treated as data payload metadata, never instructions
            "event_data": dict(event.payload),
        }

        goal_summary = (
            f"Event-triggered workflow '{trigger.workflow_id}' for '{event.event_type}' "
            f"(resource={event.resource_id or 'none'})."
        )

        workflow_execution_id: str | None = None
        if trigger.execution_mode == "autonomous_workflow" and self.autonomy_service is not None:
            from backend.app.agents.autonomy.contracts import (
                AutonomousWorkflowRequest,
                AutonomySecurityContext,
            )

            auto_ctx = AutonomySecurityContext(
                tenant_id=security_context.tenant_id,
                user_id=trigger.owner_id,
                roles=list(security_context.roles) or ["member"],
                permissions=list(security_context.permissions)
                or ["agent.invoke", "agent.read"],
                correlation_id=event.correlation_id,
            )
            wf_rec = await self.autonomy_service.start_workflow(
                AutonomousWorkflowRequest(
                    objective=goal_summary,
                    workflow_id=trigger.workflow_id,
                    context_metadata=safe_event_data,
                    idempotency_key=claim.dispatch_key,
                    mode="sync",
                ),
                auto_ctx,
            )
            workflow_execution_id = wf_rec.execution_id
        elif self.orchestration_service is not None:
            from backend.app.agents.orchestration.workflow_contracts import (
                WorkflowRequest,
            )

            if self.workflow_registry is not None and hasattr(
                self.workflow_registry, "get_enabled"
            ):
                self.workflow_registry.get_enabled(trigger.workflow_id)

            agent_ctx = AgentContext(
                user_id=trigger.owner_id,
                tenant_id=security_context.tenant_id,
                roles=list(security_context.roles) or ["member"],
                permissions=list(security_context.permissions)
                or ["agent.invoke", "agent.read"],
                correlation_id=event.correlation_id,
                trusted=True,
            )
            exec_rec = await self.orchestration_service.submit_workflow(
                trigger.workflow_id,
                WorkflowRequest(
                    goal=goal_summary,
                    input=safe_event_data,
                    mode="sync",
                    idempotency_key=claim.dispatch_key,
                    correlation_id=event.correlation_id,
                ),
                agent_ctx,
                idempotency_key=claim.dispatch_key,
            )
            workflow_execution_id = exec_rec.workflow_execution_id
        else:
            workflow_execution_id = f"wf_trig_{claim.dispatch_id}"

        claim.workflow_execution_id = workflow_execution_id
        claim.status = "dispatched"
        claim.reason = f"Dispatched workflow '{trigger.workflow_id}' ({trigger.execution_mode})."
        updated = await self.trigger_repository.update_dispatch(claim)

        trigger.last_triggered_at = datetime.now(UTC)
        await self.trigger_repository.update_trigger(trigger)

        if self.event_store is not None:
            await self.event_store.append_audit(
                EventAuditRecord(
                    tenant_id=trigger.tenant_id,
                    event_id=event.event_id,
                    trigger_id=trigger.trigger_id,
                    action="trigger.dispatched",
                    actor_id="system:dispatcher",
                    reason=claim.reason,
                    details={
                        "dispatch_id": updated.dispatch_id,
                        "workflow_execution_id": workflow_execution_id,
                        "workflow_id": trigger.workflow_id,
                    },
                )
            )
        return updated

    async def process_event_matches(
        self,
        event: KeepEvent,
        security_context: EventSecurityContext | None = None,
    ) -> list[TriggerDispatchRecord]:
        """Evaluates all tenant rules for an event and dispatches authorized matches."""
        ctx = security_context or EventSecurityContext(
            tenant_id=event.tenant_id,
            user_id="system:event_worker",
            roles=["service", "admin"],
            permissions=["agent.invoke", "agent.read"],
            trusted_source=event.source,
            correlation_id=event.correlation_id,
        )
        matches = await self.rule_engine.evaluate_event(event)
        dispatches: list[TriggerDispatchRecord] = []

        for m in matches:
            if not m.matched:
                continue
            try:
                rec = await self.dispatch(
                    event,
                    m.trigger,
                    ctx,
                    resource_key=m.resource_key,
                )
                dispatches.append(rec)
            except (TriggerRateLimitedError, TriggerPolicyDeniedError, TriggerDisabledError) as exc:
                # Non-fatal policy suppressions do not crash delivery
                if self.event_store is not None:
                    await self.event_store.append_audit(
                        EventAuditRecord(
                            tenant_id=event.tenant_id,
                            event_id=event.event_id,
                            trigger_id=m.trigger.trigger_id,
                            action="trigger.skipped",
                            actor_id="system:dispatcher",
                            reason=str(exc),
                        )
                    )
            except AgentLayerError:
                raise

        return dispatches
