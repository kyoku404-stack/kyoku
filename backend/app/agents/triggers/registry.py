"""KEEP Phase 4.10 — Trigger Registry & Lifecycle Management.

Manages tenant-scoped TriggerRule definitions, schema/condition validation,
allowed event-to-workflow mappings, enable/disable transitions, and versioning.

Owner: Member 2 (Trigger Registry & Rule Engine)
Specification: devdocs/p4/p4.10.txt (Section 6)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.app.agents.errors import (
    EventValidationError,
    TriggerAlreadyExistsError,
    TriggerNotFoundError,
    TriggerWorkflowNotAllowedError,
)
from backend.app.agents.events.contracts import EventSecurityContext
from backend.app.agents.events.validation import EventSchemaRegistry
from backend.app.agents.triggers.conditions import validate_condition_spec
from backend.app.agents.triggers.models import (
    TriggerCreateRequest,
    TriggerExecutionMode,
    TriggerRule,
    TriggerUpdateRequest,
    generate_trigger_id,
)
from backend.app.agents.triggers.repository import BaseTriggerRepository

DEFAULT_ALLOWED_AUTONOMOUS_WORKFLOWS: frozenset[str] = frozenset(
    {
        "autonomous_research",
        "autonomous_investigation",
        "churn_investigation",
        "autonomous_collaboration",
        "knowledge_analysis",
    }
)

DEFAULT_ALLOWED_STANDARD_WORKFLOWS: frozenset[str] = frozenset(
    {
        "document_enrichment",
        "knowledge_analysis",
        "parallel_project_review",
    }
)


class TriggerRegistry:
    """Tenant-isolated registry of versioned declarative trigger rules."""

    def __init__(
        self,
        repository: BaseTriggerRepository,
        *,
        workflow_registry: Any | None = None,
        schema_registry: EventSchemaRegistry | None = None,
    ) -> None:
        self.repository = repository
        self.workflow_registry = workflow_registry
        self.schema_registry = schema_registry or EventSchemaRegistry()

    def validate_workflow_target(
        self,
        workflow_id: str,
        execution_mode: TriggerExecutionMode,
    ) -> None:
        """Verifies target workflow is registered and permitted for triggered execution."""
        if execution_mode == "autonomous_workflow":
            if workflow_id in DEFAULT_ALLOWED_AUTONOMOUS_WORKFLOWS:
                return
            raise TriggerWorkflowNotAllowedError(workflow_id)

        if workflow_id in DEFAULT_ALLOWED_STANDARD_WORKFLOWS:
            return
        if (
            self.workflow_registry is not None
            and hasattr(self.workflow_registry, "is_registered")
            and self.workflow_registry.is_registered(workflow_id)
        ):
            defn = self.workflow_registry.get(workflow_id)
            if getattr(defn, "enabled", True):
                return
        raise TriggerWorkflowNotAllowedError(workflow_id)

    def validate_event_type(self, event_type: str) -> None:
        if self.schema_registry.strict and self.schema_registry.get(event_type) is None:
            raise EventValidationError(
                f"Cannot bind trigger to unregistered event type '{event_type}'."
            )

    async def create_trigger(
        self,
        request: TriggerCreateRequest,
        security_context: EventSecurityContext,
    ) -> TriggerRule:
        self.validate_event_type(request.event_type)
        self.validate_workflow_target(request.workflow_id, request.execution_mode)
        validate_condition_spec(request.conditions)

        trigger_id = (request.trigger_id or "").strip() or generate_trigger_id()
        existing = await self.repository.get_trigger(trigger_id, security_context.tenant_id)
        if existing is not None:
            raise TriggerAlreadyExistsError(trigger_id)

        now = datetime.now(UTC)
        rule = TriggerRule(
            trigger_id=trigger_id,
            tenant_id=security_context.tenant_id,
            owner_id=security_context.user_id,
            name=request.name.strip(),
            event_type=request.event_type.strip(),
            workflow_id=request.workflow_id.strip(),
            execution_mode=request.execution_mode,
            version=1,
            enabled=request.enabled,
            allowed_sources=list(request.allowed_sources),
            conditions=dict(request.conditions),
            cooldown_seconds=request.cooldown_seconds,
            max_concurrent_runs=request.max_concurrent_runs,
            created_at=now,
            updated_at=now,
        )
        return await self.repository.create_trigger(rule)

    async def get_trigger(
        self,
        trigger_id: str,
        security_context: EventSecurityContext,
    ) -> TriggerRule:
        rule = await self.repository.get_trigger(trigger_id, security_context.tenant_id)
        if rule is None:
            raise TriggerNotFoundError(trigger_id)
        return rule

    async def update_trigger(
        self,
        trigger_id: str,
        request: TriggerUpdateRequest,
        security_context: EventSecurityContext,
    ) -> TriggerRule:
        rule = await self.get_trigger(trigger_id, security_context)
        next_mode = request.execution_mode or rule.execution_mode
        next_wf = request.workflow_id or rule.workflow_id
        self.validate_workflow_target(next_wf, next_mode)

        if request.conditions is not None:
            validate_condition_spec(request.conditions)
            rule.conditions = dict(request.conditions)
        if request.name is not None:
            rule.name = request.name.strip()
        if request.allowed_sources is not None:
            rule.allowed_sources = list(request.allowed_sources)
        if request.cooldown_seconds is not None:
            rule.cooldown_seconds = request.cooldown_seconds
        if request.max_concurrent_runs is not None:
            rule.max_concurrent_runs = request.max_concurrent_runs
        rule.workflow_id = next_wf
        rule.execution_mode = next_mode
        rule.version += 1
        return await self.repository.update_trigger(rule)

    async def set_enabled(
        self,
        trigger_id: str,
        *,
        enabled: bool,
        security_context: EventSecurityContext,
    ) -> TriggerRule:
        rule = await self.get_trigger(trigger_id, security_context)
        rule.enabled = enabled
        return await self.repository.update_trigger(rule)

    async def list_triggers(
        self,
        security_context: EventSecurityContext,
        *,
        event_type: str | None = None,
        enabled_only: bool = False,
        limit: int = 100,
    ) -> list[TriggerRule]:
        return await self.repository.list_triggers(
            security_context.tenant_id,
            event_type=event_type,
            enabled_only=enabled_only,
            limit=limit,
        )
