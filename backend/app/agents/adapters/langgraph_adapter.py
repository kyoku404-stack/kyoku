"""KEEP Phase 4.1 / 4.2 — LangGraph Framework Adapter with Scoped Checkpointing.

Implements KEEP's `BaseAgent` Protocol around LangGraph-compatible async runnables
with optional `KeepCheckpointStore` step-state persistence and mandatory
re-authorization before resuming any saved checkpoint (ADR-073).

Owner: Member 4 (KEEP Integration, Reference Agent & QA)
Specification: devdocs/p4/p4.1.txt (Section 6) & devdocs/p4/p4.2.txt (Section 8)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

from backend.app.agents.contracts import (
    AgentContext,
    AgentRequest,
    AgentResult,
    EvidenceReference,
)
from backend.app.agents.errors import AgentErrorCode
from backend.app.agents.metadata import AgentCapability, AgentMetadata
from backend.app.agents.persistence.checkpoints import KeepCheckpointStore
from backend.app.services.security.agent_policy import (
    AgentPolicyInterface,
    KeepAgentPolicyEngine,
)


@runtime_checkable
class LangGraphRunnable(Protocol):
    """Minimal structural protocol matching LangGraph CompiledGraph / Runnable (`ainvoke`)."""

    async def ainvoke(
        self,
        input: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ...


StateMapperFn = Callable[[AgentRequest, AgentContext], dict[str, Any]]
ResultMapperFn = Callable[[dict[str, Any]], AgentResult]


def _default_state_mapper(request: AgentRequest, context: AgentContext) -> dict[str, Any]:
    """Maps KEEP's validated AgentRequest and trusted AgentContext into initial graph state."""
    return {
        "request_id": request.request_id,
        "task_id": request.task_id,
        "goal": request.goal,
        "input": dict(request.input),
        "tenant_id": context.tenant_id,
        "user_id": context.user_id,
        "correlation_id": request.correlation_id or context.correlation_id,
    }


def _default_result_mapper(graph_state: dict[str, Any]) -> AgentResult:
    """Maps graph output state back into KEEP's canonical validated AgentResult."""
    raw_evidence = graph_state.get("evidence") or []
    evidence = [
        ev if isinstance(ev, EvidenceReference) else EvidenceReference.model_validate(ev)
        for ev in raw_evidence
    ]
    warnings = [str(w) for w in (graph_state.get("warnings") or [])]
    output = graph_state.get("output")
    if not isinstance(output, dict):
        output = {"result": output if output is not None else graph_state}

    return AgentResult(
        status="succeeded",
        output=output,
        evidence=evidence,
        warnings=warnings,
    )


class TwoStepResearchGraph:
    """Deterministic Phase 4.2 proof-of-concept 2-step graph: retrieve -> analyze.

    Conforms to `LangGraphRunnable` (`ainvoke`) and demonstrates step-by-step
    checkpointing behind `LangGraphAgentAdapter` without requiring live LLM keys.
    """

    async def ainvoke(
        self,
        input: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        configurable = (config or {}).get("configurable", {})
        thread_id = str(configurable.get("thread_id") or input.get("task_id") or "thread")
        tenant_id = str(input.get("tenant_id") or "")
        goal = str(input.get("goal") or "")
        topic = str((input.get("input") or {}).get("project_id") or (input.get("input") or {}).get("topic") or "enterprise-knowledge")

        # Step 1: Retrieval node
        retrieved_docs = [
            {
                "source_id": f"doc_{topic}_01",
                "source_type": "document",
                "title": f"KEEP Knowledge Brief: {topic}",
                "excerpt": f"Authorized tenant context retrieved for goal: {goal[:120]}",
                "score": 0.94,
                "tenant_id": tenant_id,
            }
        ]

        # Step 2: Analysis / Synthesis node
        synthesis = {
            "summary": f"Completed 2-step graph analysis for '{goal}'.",
            "topic": topic,
            "steps_completed": ["retrieve", "analyze"],
            "thread_id": thread_id,
            "tenant_id": tenant_id,
            "sources_analyzed": len(retrieved_docs),
        }

        return {
            "output": synthesis,
            "evidence": retrieved_docs,
            "warnings": [],
            "checkpoints": [
                {"step_name": "retrieve", "step_number": 1, "state": {"retrieved_count": len(retrieved_docs), "topic": topic}},
                {"step_name": "analyze", "step_number": 2, "state": {"summary": synthesis["summary"], "completed": True}},
            ],
        }


class LangGraphAgentAdapter:
    """Adapts any LangGraph-compatible async runnable to KEEP's BaseAgent Protocol."""

    def __init__(
        self,
        *,
        metadata: AgentMetadata,
        graph: LangGraphRunnable,
        state_mapper: StateMapperFn = _default_state_mapper,
        result_mapper: ResultMapperFn = _default_result_mapper,
        checkpoint_store: KeepCheckpointStore | None = None,
        policy: AgentPolicyInterface | None = None,
    ) -> None:
        if not isinstance(graph, LangGraphRunnable):
            raise TypeError(
                "LangGraphAgentAdapter requires a graph implementing async `ainvoke(input, config)`."
            )
        self._metadata = metadata
        self._graph = graph
        self._state_mapper = state_mapper
        self._result_mapper = result_mapper
        self._checkpoint_store = checkpoint_store
        self._policy: AgentPolicyInterface = policy or KeepAgentPolicyEngine()

    @property
    def metadata(self) -> AgentMetadata:
        return self._metadata

    async def invoke(
        self,
        request: AgentRequest,
        context: AgentContext,
    ) -> AgentResult:
        """Executes the wrapped LangGraph runnable with scoped checkpointing and re-auth on resume."""
        initial_state = self._state_mapper(request, context)
        thread_id = f"{context.tenant_id}:{request.task_id}"

        # If resuming from a prior checkpoint, re-verify authorization strictly (ADR-073)
        if self._checkpoint_store is not None:
            prior = await self._checkpoint_store.get_latest_checkpoint(
                thread_id=thread_id,
                context=context,
            )
            if prior is not None:
                self._policy.authorize_invocation(self._metadata, request, context)
                initial_state["resumed_from_checkpoint"] = prior.checkpoint_id
                initial_state["prior_state"] = dict(prior.state)

        run_config = {
            "configurable": {
                "thread_id": request.task_id,
                "scoped_thread_id": thread_id,
                "tenant_id": context.tenant_id,
                "correlation_id": request.correlation_id or context.correlation_id,
            }
        }
        try:
            final_state = await self._graph.ainvoke(initial_state, config=run_config)

            # Persist step checkpoints if emitted and checkpoint store is configured
            if self._checkpoint_store is not None:
                raw_checkpoints = final_state.get("checkpoints")
                if isinstance(raw_checkpoints, list) and raw_checkpoints:
                    for idx, chk in enumerate(raw_checkpoints, start=1):
                        await self._checkpoint_store.save_checkpoint(
                            execution_id=request.request_id,
                            thread_id=thread_id,
                            step_name=str(chk.get("step_name", f"step_{idx}")),
                            step_number=int(chk.get("step_number", idx)),
                            state=dict(chk.get("state") or {}),
                            context=context,
                        )
                else:
                    await self._checkpoint_store.save_checkpoint(
                        execution_id=request.request_id,
                        thread_id=thread_id,
                        step_name="completed",
                        step_number=1,
                        state={"output_keys": sorted((final_state.get("output") or {}).keys())},
                        context=context,
                    )

            return self._result_mapper(final_state)
        except (RuntimeError, ValueError, TypeError, KeyError, LookupError, OSError) as exc:
            return AgentResult.failure(
                code=AgentErrorCode.AGENT_EXECUTION_FAILED,
                message=f"LangGraph adapter execution failed: {exc}",
            )


def build_research_graph_agent(
    *,
    checkpoint_store: KeepCheckpointStore | None = None,
    policy: AgentPolicyInterface | None = None,
) -> LangGraphAgentAdapter:
    """Factory creating KEEP's Phase 4.2 2-step LangGraph proof-of-concept agent."""
    meta = AgentMetadata(
        agent_id="research-graph",
        name="Research Graph Agent (LangGraph PoC)",
        version="1.0.0",
        description="Two-step retrieval and analysis agent backed by KEEP's LangGraph adapter and checkpoint store.",
        capabilities=[
            AgentCapability(
                name="knowledge.search",
                description="Retrieve tenant-authorized organizational knowledge.",
                access="read",
            ),
            AgentCapability(
                name="knowledge.analyze",
                description="Synthesize retrieved excerpts into structured evidence-backed summaries.",
                access="read",
            ),
        ],
        tags=["phase-4.2", "langgraph", "checkpointed"],
    )
    return LangGraphAgentAdapter(
        metadata=meta,
        graph=TwoStepResearchGraph(),
        checkpoint_store=checkpoint_store,
        policy=policy,
    )
