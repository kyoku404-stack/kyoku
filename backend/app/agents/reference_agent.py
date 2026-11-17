"""KEEP Phase 4.1 — Reference Agent Implementation.

Intentionally lightweight agent proving that KEEP's `BaseAgent` Protocol,
`AgentMetadata`, `AgentRegistry`, trusted `AgentContext`, security policies,
and KEEP service adapters work end-to-end before Phase 4.2 introduces the
full execution runtime.

Owner: Member 4 (KEEP Integration, Reference Agent & QA)
Specification: devdocs/p4/p4.1.txt (Sections 4.5, 9)
"""

from __future__ import annotations

from backend.app.agents.adapters.keep_services import KeepKnowledgeAdapter
from backend.app.agents.contracts import AgentContext, AgentRequest, AgentResult
from backend.app.agents.metadata import AgentCapability, AgentMetadata


class ReferenceAgent:
    """Canonical Phase 4.1 reference agent conforming to KEEP's BaseAgent Protocol."""

    def __init__(self, *, knowledge_adapter: KeepKnowledgeAdapter | None = None) -> None:
        self._knowledge_adapter = knowledge_adapter
        self._metadata = AgentMetadata(
            agent_id="reference",
            name="Reference Agent",
            version="1.0.0",
            description="Validates the KEEP agent contract integration.",
            capabilities=[
                AgentCapability(
                    name="agent.echo",
                    description="Validates request/result contracts and echoes goal metadata.",
                    access="read",
                ),
                AgentCapability(
                    name="knowledge.inspect",
                    description="Performs read-only tenant-scoped lookup via KeepKnowledgeAdapter.",
                    access="read",
                ),
            ],
            tags=["phase-4.1", "reference", "contract-validation"],
        )

    @property
    def metadata(self) -> AgentMetadata:
        return self._metadata

    async def invoke(
        self,
        request: AgentRequest,
        context: AgentContext,
    ) -> AgentResult:
        """Processes a validated request under a trusted AgentContext."""
        evidence = []
        query = request.input.get("query")
        if isinstance(query, str) and query.strip() and self._knowledge_adapter is not None:
            evidence = await self._knowledge_adapter.search_knowledge(query, context, limit=3)

        return AgentResult(
            status="succeeded",
            output={
                "message": "Agent contract integration is working.",
                "agent_id": self._metadata.agent_id,
                "goal": request.goal,
                "request_id": request.request_id,
                "task_id": request.task_id,
                "correlation_id": request.correlation_id or context.correlation_id,
                "tenant_id": context.tenant_id,
                "evidence_count": len(evidence),
            },
            evidence=evidence,
        )
