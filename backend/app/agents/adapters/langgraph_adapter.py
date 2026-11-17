"""KEEP Phase 4.1 — LangGraph Framework Adapter Seam.

Provides a clean adapter boundary implementing KEEP's `BaseAgent` Protocol so
LangGraph compiled graphs (Phase 4.2/4.3+) can be registered in `AgentRegistry`
and governed by KEEP's security policies without coupling KEEP core contracts,
routes, or authorization directly to LangGraph internals.

Owner: Member 4 (KEEP Integration, Reference Agent & QA)
Specification: devdocs/p4/p4.1.txt (Sections 2, 6, 9)
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
from backend.app.agents.metadata import AgentMetadata


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


class LangGraphAgentAdapter:
    """Adapts any LangGraph-compatible async runnable to KEEP's BaseAgent Protocol."""

    def __init__(
        self,
        *,
        metadata: AgentMetadata,
        graph: LangGraphRunnable,
        state_mapper: StateMapperFn = _default_state_mapper,
        result_mapper: ResultMapperFn = _default_result_mapper,
    ) -> None:
        if not isinstance(graph, LangGraphRunnable):
            raise TypeError(
                "LangGraphAgentAdapter requires a graph implementing async `ainvoke(input, config)`."
            )
        self._metadata = metadata
        self._graph = graph
        self._state_mapper = state_mapper
        self._result_mapper = result_mapper

    @property
    def metadata(self) -> AgentMetadata:
        return self._metadata

    async def invoke(
        self,
        request: AgentRequest,
        context: AgentContext,
    ) -> AgentResult:
        """Executes the wrapped LangGraph runnable and returns a validated KEEP AgentResult."""
        initial_state = self._state_mapper(request, context)
        run_config = {
            "configurable": {
                "thread_id": request.task_id,
                "tenant_id": context.tenant_id,
                "correlation_id": request.correlation_id or context.correlation_id,
            }
        }
        try:
            final_state = await self._graph.ainvoke(initial_state, config=run_config)
            return self._result_mapper(final_state)
        except (RuntimeError, ValueError, TypeError, KeyError, LookupError, OSError) as exc:
            return AgentResult.failure(
                code=AgentErrorCode.AGENT_EXECUTION_FAILED,
                message=f"LangGraph adapter execution failed: {exc}",
            )
