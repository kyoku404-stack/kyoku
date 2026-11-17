"""KEEP Phase 4.1 — Agent Registry & Capability Discovery.

Provides registration, contract conformance validation, lookup, duplicate-ID
rejection, enable/disable lifecycle controls, and capability-based discovery.

Owner: Member 1 (Architecture & Agent Registry)
Specification: devdocs/p4/p4.1.txt (Sections 3, 4.4)
"""

from __future__ import annotations

import inspect
from typing import Any

from backend.app.agents.base import BaseAgent
from backend.app.agents.metadata import AgentMetadata, CapabilityAccess


class AgentRegistry:
    """In-memory KEEP agent registry with contract validation and lifecycle controls.

    Initialized inside FastAPI lifespan (`app.state.agent_registry`) and injected
    via FastAPI dependencies so tests and runtime instances remain cleanly isolated.
    """

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}
        self._enabled_overrides: dict[str, bool] = {}

    def _validate_agent(self, agent: Any) -> AgentMetadata:
        """Validates BaseAgent protocol conformance and metadata integrity."""
        if not isinstance(agent, BaseAgent):
            raise TypeError(
                "Agent does not conform to KEEP BaseAgent protocol "
                "(must define 'metadata' property and async 'invoke(request, context)' method)."
            )

        invoke_fn = getattr(agent, "invoke", None)
        if not inspect.iscoroutinefunction(invoke_fn):
            raise TypeError(
                f"Agent '{type(agent).__name__}.invoke' must be an async coroutine function."
            )

        metadata = agent.metadata
        if not isinstance(metadata, AgentMetadata):
            raise TypeError(
                f"Agent '{type(agent).__name__}.metadata' must be an instance of AgentMetadata."
            )

        # Re-validate metadata via Pydantic to guarantee invariants
        return AgentMetadata.model_validate(metadata.model_dump())

    def register(self, agent: BaseAgent) -> AgentMetadata:
        """Registers a validated agent, rejecting duplicate agent IDs."""
        validated_meta = self._validate_agent(agent)
        agent_id = validated_meta.agent_id
        if agent_id in self._agents:
            raise ValueError(f"Agent already registered: {agent_id}")
        self._agents[agent_id] = agent
        self._enabled_overrides[agent_id] = validated_meta.enabled
        return validated_meta

    def unregister(self, agent_id: str) -> None:
        """Removes an agent from the registry."""
        normalized_id = agent_id.strip().lower()
        if normalized_id not in self._agents:
            raise LookupError(f"Unknown agent: {agent_id}")
        del self._agents[normalized_id]
        self._enabled_overrides.pop(normalized_id, None)

    def is_registered(self, agent_id: str) -> bool:
        """Returns True if an agent with this ID is registered."""
        return agent_id.strip().lower() in self._agents

    def is_enabled(self, agent_id: str) -> bool:
        """Returns True if the registered agent is currently enabled."""
        normalized_id = agent_id.strip().lower()
        agent = self._agents.get(normalized_id)
        if agent is None:
            raise LookupError(f"Unknown agent: {agent_id}")
        override = self._enabled_overrides.get(normalized_id)
        if override is not None:
            return override
        return bool(agent.metadata.enabled)

    def set_enabled(self, agent_id: str, enabled: bool) -> AgentMetadata:
        """Updates the enabled state of a registered agent without mutating shared class attributes."""
        normalized_id = agent_id.strip().lower()
        agent = self._agents.get(normalized_id)
        if agent is None:
            raise LookupError(f"Unknown agent: {agent_id}")
        self._enabled_overrides[normalized_id] = bool(enabled)
        return self.get_metadata(normalized_id)

    def enable(self, agent_id: str) -> AgentMetadata:
        """Enables a previously disabled agent."""
        return self.set_enabled(agent_id, True)

    def disable(self, agent_id: str) -> AgentMetadata:
        """Disables a registered agent so lookup/invocation is blocked."""
        return self.set_enabled(agent_id, False)

    def get(self, agent_id: str) -> BaseAgent:
        """Returns an enabled agent by ID; raises LookupError if missing or ValueError if disabled."""
        normalized_id = agent_id.strip().lower()
        agent = self._agents.get(normalized_id)
        if agent is None:
            raise LookupError(f"Unknown agent: {agent_id}")
        if not self.is_enabled(normalized_id):
            raise ValueError(f"Agent is disabled: {normalized_id}")
        return agent

    def get_metadata(self, agent_id: str) -> AgentMetadata:
        """Returns effective AgentMetadata (reflecting current enabled override) for an agent."""
        normalized_id = agent_id.strip().lower()
        agent = self._agents.get(normalized_id)
        if agent is None:
            raise LookupError(f"Unknown agent: {agent_id}")
        effective_enabled = self.is_enabled(normalized_id)
        return agent.metadata.model_copy(update={"enabled": effective_enabled})

    def list_agents(
        self,
        *,
        include_disabled: bool = True,
        capability: str | None = None,
        max_access: CapabilityAccess | None = None,
    ) -> list[dict[str, Any]]:
        """Lists serialized metadata dicts for registered agents with optional filtering."""
        access_rank: dict[CapabilityAccess, int] = {"read": 0, "write": 1, "sensitive": 2}
        results: list[dict[str, Any]] = []
        for agent_id in sorted(self._agents.keys()):
            meta = self.get_metadata(agent_id)
            if not include_disabled and not meta.enabled:
                continue
            if capability and not meta.has_capability(capability):
                continue
            if max_access is not None and access_rank[meta.max_access_level()] > access_rank[max_access]:
                continue
            results.append(meta.model_dump())
        return results

    def find_by_capability(
        self,
        capability_name: str,
        *,
        include_disabled: bool = False,
    ) -> list[AgentMetadata]:
        """Discovers registered agents declaring a specific capability."""
        target = capability_name.strip().lower()
        matches: list[AgentMetadata] = []
        for agent_id in sorted(self._agents.keys()):
            meta = self.get_metadata(agent_id)
            if not include_disabled and not meta.enabled:
                continue
            if meta.has_capability(target):
                matches.append(meta)
        return matches

    def count(self, *, include_disabled: bool = True) -> int:
        """Returns the number of registered agents."""
        if include_disabled:
            return len(self._agents)
        return sum(1 for agent_id in self._agents if self.is_enabled(agent_id))
