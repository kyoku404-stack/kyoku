"""Phase 4.1 Member 1 — Agent Protocol, Metadata & Registry Unit Tests.

Verifies:
- BaseAgent structural typing (Protocol) conformance & rejection of invalid agents.
- AgentMetadata & AgentCapability validation (SemVer, agent_id, unique capabilities, access tiers).
- AgentRegistry registration, lookup, duplicate-ID rejection, disabled-agent handling,
  enable/disable toggling, unregister, capability discovery, and filtered listing.

Specification: devdocs/p4/p4.1.txt (Sections 3, 4.1, 4.2, 4.4, 9)
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.app.agents.base import BaseAgent
from backend.app.agents.contracts import AgentContext, AgentRequest, AgentResult
from backend.app.agents.metadata import AgentCapability, AgentMetadata
from backend.app.agents.registry import AgentRegistry


class _SampleResearchAgent:
    def __init__(self, *, agent_id: str = "research", enabled: bool = True) -> None:
        self._metadata = AgentMetadata(
            agent_id=agent_id,
            name="Knowledge Research Agent",
            version="1.0.0",
            description="Finds and synthesizes relevant KEEP knowledge.",
            capabilities=[
                AgentCapability(
                    name="knowledge.search",
                    description="Search authorized organizational knowledge",
                    access="read",
                )
            ],
            enabled=enabled,
        )

    @property
    def metadata(self) -> AgentMetadata:
        return self._metadata

    async def invoke(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        return AgentResult(status="succeeded", output={"goal": request.goal})


class _SensitiveWriteAgent:
    metadata = AgentMetadata(
        agent_id="policy-writer",
        name="Governance Write Agent",
        version="1.2.0",
        capabilities=[
            AgentCapability(name="governance.read", access="read"),
            AgentCapability(name="governance.mutate", access="sensitive", requires_approval=True),
        ],
    )

    async def invoke(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        return AgentResult(status="succeeded", output={})


class _NonAsyncAgent:
    metadata = AgentMetadata(agent_id="bad-sync", name="Sync Agent", version="1.0.0")

    def invoke(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        return AgentResult(status="succeeded")


class _MissingInvokeAgent:
    metadata = AgentMetadata(agent_id="incomplete", name="Incomplete", version="1.0.0")


class TestAgentMetadataAndCapabilities:
    def test_valid_metadata_and_helpers(self) -> None:
        meta = AgentMetadata(
            agent_id="Research-Bot",
            name="Research Bot",
            version="1.0.0",
            capabilities=[
                AgentCapability(name="Knowledge.Search", access="read"),
                AgentCapability(name="Report.Create", access="write"),
            ],
        )
        assert meta.agent_id == "research-bot"
        assert meta.has_capability("knowledge.search") is True
        assert meta.has_capability("missing.cap") is False
        assert meta.get_capability("report.create") is not None
        assert meta.max_access_level() == "write"

    def test_invalid_agent_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AgentMetadata(agent_id="bad id with spaces!", name="Bad", version="1.0.0")

    def test_invalid_semver_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AgentMetadata(agent_id="valid-id", name="Bad Ver", version="v1")

    def test_duplicate_capability_names_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Duplicate capability"):
            AgentMetadata(
                agent_id="dup-cap",
                name="Dup Cap",
                version="1.0.0",
                capabilities=[
                    AgentCapability(name="knowledge.search", access="read"),
                    AgentCapability(name="KNOWLEDGE.SEARCH", access="read"),
                ],
            )


class TestAgentRegistry:
    def test_protocol_conformance_and_registration(self) -> None:
        registry = AgentRegistry()
        agent = _SampleResearchAgent()
        assert isinstance(agent, BaseAgent)

        meta = registry.register(agent)
        assert meta.agent_id == "research"
        assert registry.is_registered("research") is True
        assert registry.count() == 1
        assert registry.get("research") is agent

    def test_duplicate_id_rejected(self) -> None:
        registry = AgentRegistry()
        registry.register(_SampleResearchAgent(agent_id="research"))

        with pytest.raises(ValueError, match="Agent already registered: research"):
            registry.register(_SampleResearchAgent(agent_id="RESEARCH"))

    def test_unknown_agent_lookup_raises_lookup_error(self) -> None:
        registry = AgentRegistry()
        with pytest.raises(LookupError, match="Unknown agent: missing"):
            registry.get("missing")

    def test_disabled_agent_blocked_on_get_and_toggled(self) -> None:
        registry = AgentRegistry()
        agent = _SampleResearchAgent(agent_id="research", enabled=True)
        registry.register(agent)

        disabled_meta = registry.disable("research")
        assert disabled_meta.enabled is False
        assert registry.is_enabled("research") is False
        assert registry.count(include_disabled=False) == 0

        with pytest.raises(ValueError, match="Agent is disabled: research"):
            registry.get("research")

        enabled_meta = registry.enable("research")
        assert enabled_meta.enabled is True
        assert registry.get("research") is agent

    def test_list_agents_and_capability_discovery(self) -> None:
        registry = AgentRegistry()
        registry.register(_SampleResearchAgent(agent_id="research", enabled=True))
        registry.register(_SampleResearchAgent(agent_id="research-beta", enabled=False))
        registry.register(_SensitiveWriteAgent())

        all_agents = registry.list_agents(include_disabled=True)
        assert [a["agent_id"] for a in all_agents] == ["policy-writer", "research", "research-beta"]

        enabled_only = registry.list_agents(include_disabled=False)
        assert [a["agent_id"] for a in enabled_only] == ["policy-writer", "research"]

        read_only = registry.list_agents(include_disabled=False, max_access="read")
        assert [a["agent_id"] for a in read_only] == ["research"]

        by_cap = registry.find_by_capability("knowledge.search", include_disabled=False)
        assert [m.agent_id for m in by_cap] == ["research"]

        by_cap_all = registry.find_by_capability("knowledge.search", include_disabled=True)
        assert [m.agent_id for m in by_cap_all] == ["research", "research-beta"]

    def test_rejects_non_conforming_and_sync_agents(self) -> None:
        registry = AgentRegistry()
        with pytest.raises(TypeError, match="must be an async coroutine"):
            registry.register(_NonAsyncAgent())  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="BaseAgent protocol"):
            registry.register(_MissingInvokeAgent())  # type: ignore[arg-type]

    def test_unregister_removes_agent(self) -> None:
        registry = AgentRegistry()
        registry.register(_SampleResearchAgent(agent_id="temp"))
        registry.unregister("temp")
        assert registry.is_registered("temp") is False
        with pytest.raises(LookupError):
            registry.unregister("temp")
