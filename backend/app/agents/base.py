"""KEEP Phase 4.1 — Common BaseAgent Protocol Interface.

Uses Python structural typing (`typing.Protocol`) so any agent implementation
— pure Python, KEEP service wrapper, or LangGraph adapter — conforms cleanly
without inheriting from a framework-specific base class.

Owner: Member 1 (Architecture & Agent Registry)
Specification: devdocs/p4/p4.1.txt (Section 4.1)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.app.agents.contracts import AgentContext, AgentRequest, AgentResult
from backend.app.agents.metadata import AgentMetadata


@runtime_checkable
class BaseAgent(Protocol):
    """Canonical KEEP agent interface enforced by AgentRegistry and Phase 4.2 runtime."""

    @property
    def metadata(self) -> AgentMetadata:
        """Returns immutable/validated AgentMetadata describing this agent."""
        ...

    async def invoke(
        self,
        request: AgentRequest,
        context: AgentContext,
    ) -> AgentResult:
        """Executes a single validated agent request under a trusted AgentContext."""
        ...
