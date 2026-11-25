"""KEEP Phase 4.3 — Versioned Approved Workflow Registry.

Stores server-approved multi-agent workflow definitions and graph factories separately
from Phase 4.1's AgentRegistry. Validates declared agent capabilities/IDs against
AgentRegistry and supports version pinning so disabling a workflow or deploying a new
version never mutates already-running executions.

Owner: Member 1 (Orchestration Architecture & Workflow Registry)
Specification: devdocs/p4/p4.3.txt (Sections 3, 11)
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.errors import (
    AgentNotFoundError,
    WorkflowAlreadyRegisteredError,
    WorkflowDependencyMissingError,
    WorkflowDisabledError,
    WorkflowNotFoundError,
)
from backend.app.agents.orchestration.workflow_contracts import (
    WorkflowDefinition,
    WorkflowGraphFactory,
)
from backend.app.agents.registry import AgentRegistry


def _semver_key(version: str) -> tuple[int, int, int, str]:
    core, _, pre = version.partition("-")
    parts = core.split(".")
    return (int(parts[0]), int(parts[1]), int(parts[2]), pre)


class WorkflowRegistry:
    """Centralized registry of KEEP-approved versioned multi-agent workflows."""

    def __init__(self, *, agent_registry: AgentRegistry | None = None) -> None:
        self._agent_registry = agent_registry
        self._definitions: dict[tuple[str, str], WorkflowDefinition] = {}
        self._factories: dict[tuple[str, str], WorkflowGraphFactory] = {}

    def bind_agent_registry(self, agent_registry: AgentRegistry) -> None:
        """Attaches an AgentRegistry used to validate workflow agent/capability dependencies."""
        self._agent_registry = agent_registry

    def validate_dependencies(self, definition: WorkflowDefinition) -> None:
        """Verifies all required agents and capabilities exist in the bound AgentRegistry."""
        if self._agent_registry is None:
            return

        missing: list[str] = []
        for agent_id in definition.required_agents:
            try:
                self._agent_registry.get_metadata(agent_id)
            except AgentNotFoundError:
                missing.append(f"agent:{agent_id}")

        for cap in definition.required_capabilities:
            matches = self._agent_registry.list_agents(include_disabled=False, capability=cap)
            if not matches:
                missing.append(f"capability:{cap}")

        if missing:
            raise WorkflowDependencyMissingError(definition.workflow_id, missing)

    def register(
        self,
        definition: WorkflowDefinition,
        factory: WorkflowGraphFactory,
        *,
        validate_deps: bool = True,
    ) -> WorkflowDefinition:
        """Registers an approved (workflow_id, version) definition and graph factory."""
        key = (definition.workflow_id, definition.version)
        if key in self._definitions:
            raise WorkflowAlreadyRegisteredError(definition.workflow_id, definition.version)
        if not callable(factory):
            raise TypeError(f"Workflow '{definition.workflow_id}' factory must be callable.")

        if validate_deps:
            self.validate_dependencies(definition)

        self._definitions[key] = definition
        self._factories[key] = factory
        return definition

    def resolve_latest_version(
        self,
        workflow_id: str,
        *,
        include_disabled: bool = False,
    ) -> str:
        """Resolves the highest semantic version registered for `workflow_id`."""
        norm_id = workflow_id.strip().lower()
        candidates = [
            defn
            for (wf_id, _ver), defn in self._definitions.items()
            if wf_id == norm_id and (include_disabled or defn.enabled)
        ]
        if not candidates:
            # Distinguish disabled from missing
            any_versions = [
                defn for (wf_id, _ver), defn in self._definitions.items() if wf_id == norm_id
            ]
            if any_versions:
                latest_disabled = max(any_versions, key=lambda d: _semver_key(d.version))
                raise WorkflowDisabledError(norm_id, latest_disabled.version)
            raise WorkflowNotFoundError(norm_id)

        latest = max(candidates, key=lambda d: _semver_key(d.version))
        return latest.version

    def get(
        self,
        workflow_id: str,
        version: str | None = None,
        *,
        allow_disabled: bool = False,
    ) -> tuple[WorkflowDefinition, WorkflowGraphFactory]:
        """Retrieves a workflow definition and factory, pinning version or resolving latest enabled."""
        norm_id = workflow_id.strip().lower()
        resolved_version = (
            version.strip()
            if version
            else self.resolve_latest_version(norm_id, include_disabled=allow_disabled)
        )
        key = (norm_id, resolved_version)
        definition = self._definitions.get(key)
        if definition is None:
            raise WorkflowNotFoundError(norm_id, resolved_version)
        if not definition.enabled and not allow_disabled:
            raise WorkflowDisabledError(norm_id, resolved_version)
        return definition, self._factories[key]

    def get_definition(
        self,
        workflow_id: str,
        version: str | None = None,
        *,
        allow_disabled: bool = True,
    ) -> WorkflowDefinition:
        """Returns metadata for a workflow definition without instantiating its graph."""
        definition, _ = self.get(workflow_id, version=version, allow_disabled=allow_disabled)
        return definition

    def set_enabled(
        self,
        workflow_id: str,
        enabled: bool,
        *,
        version: str | None = None,
    ) -> WorkflowDefinition:
        """Enables or disables a workflow version without altering in-flight pinned executions."""
        norm_id = workflow_id.strip().lower()
        resolved_version = (
            version.strip()
            if version
            else self.resolve_latest_version(norm_id, include_disabled=True)
        )
        key = (norm_id, resolved_version)
        current = self._definitions.get(key)
        if current is None:
            raise WorkflowNotFoundError(norm_id, resolved_version)
        updated = current.model_copy(update={"enabled": enabled})
        self._definitions[key] = updated
        return updated

    def list_workflows(
        self,
        *,
        include_disabled: bool = False,
        task_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Lists approved workflow definitions sorted by workflow_id and version."""
        items: list[WorkflowDefinition] = []
        for defn in self._definitions.values():
            if not include_disabled and not defn.enabled:
                continue
            if task_type and defn.task_type != task_type:
                continue
            items.append(defn)
        items.sort(key=lambda d: (d.workflow_id, _semver_key(d.version)))
        return [d.model_dump() for d in items]

    def is_registered(self, workflow_id: str) -> bool:
        """Returns True iff any version of `workflow_id` is registered."""
        norm_id = workflow_id.strip().lower()
        return any(wf_id == norm_id for (wf_id, _ver) in self._definitions)

    def get_enabled(
        self,
        workflow_id: str,
        version: str | None = None,
    ) -> WorkflowDefinition:
        """Returns the enabled WorkflowDefinition or raises WorkflowNotFoundError/WorkflowDisabledError."""
        definition, _ = self.get(workflow_id, version=version, allow_disabled=False)
        return definition

    def count(self) -> int:
        return len(self._definitions)
