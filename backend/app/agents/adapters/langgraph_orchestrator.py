"""KEEP Phase 4.3 — LangGraph-Compatible Workflow State Graph Adapter.

Isolates graph compilation, node transitions, conditional routing, parallel
fan-out/fan-in (`asyncio.gather`), explicit state reducers, cooperative cancellation
checks, and per-node checkpoint callbacks strictly behind `backend/app/agents/adapters/`.

Owner: Member 2 (Graph State, Routing & Workflow Execution)
Specification: devdocs/p4/p4.3.txt (Sections 2, 5, 6, 7, 8)
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import WorkflowCancelledError
from backend.app.agents.orchestration.state import (
    merge_workflow_state,
    sanitize_checkpoint_state,
)

START = "__start__"
END = "__end__"

NodeCallable = Callable[[dict[str, Any], AgentContext], Awaitable[dict[str, Any]]]
RouterCallable = Callable[[dict[str, Any]], str | list[str]]
CheckpointCallback = Callable[[str, int, dict[str, Any]], Awaitable[None]]


class CompiledKeepWorkflowGraph:
    """Executable multi-agent state graph supporting sequential, conditional, and parallel flows."""

    def __init__(
        self,
        *,
        nodes: dict[str, NodeCallable],
        edges: dict[str, list[str]],
        conditional_edges: dict[str, tuple[RouterCallable, dict[str, str | list[str]]]],
    ) -> None:
        self._nodes = dict(nodes)
        self._edges = {k: list(v) for k, v in edges.items()}
        self._conditional_edges = dict(conditional_edges)

    def _resolve_next(self, current_node: str, state: dict[str, Any]) -> list[str]:
        if current_node in self._conditional_edges:
            router_fn, path_map = self._conditional_edges[current_node]
            decision = router_fn(state)
            if isinstance(decision, list):
                resolved: list[str] = []
                for key in decision:
                    mapped = path_map.get(key, key)
                    if isinstance(mapped, list):
                        resolved.extend(mapped)
                    else:
                        resolved.append(mapped)
                return resolved
            mapped = path_map.get(decision, decision)
            return list(mapped) if isinstance(mapped, list) else [mapped]
        return list(self._edges.get(current_node, [END]))

    async def arun(
        self,
        initial_state: dict[str, Any],
        *,
        context: AgentContext,
        resume_from_node: str | None = None,
        completed_nodes: set[str] | None = None,
        checkpoint_callback: CheckpointCallback | None = None,
        cancel_checker: Callable[[], bool] | None = None,
        max_supersteps: int | None = None,
    ) -> dict[str, Any]:
        """Executes the compiled graph with parallel fan-out/fan-in and per-step checkpointing."""
        state = dict(initial_state)
        skip_nodes = set(completed_nodes or set())
        step_counter = 0

        if resume_from_node:
            frontier = [resume_from_node]
        else:
            frontier = self._resolve_next(START, state)

        # Bounded iteration guard prevents accidental cycles in graph definitions
        resolved_max_supersteps = (
            max_supersteps if max_supersteps is not None else max(len(self._nodes) * 3, 16)
        )
        superstep = 0

        while frontier:
            superstep += 1
            if superstep > resolved_max_supersteps:
                raise RuntimeError("Workflow graph exceeded maximum superstep limit (possible cycle).")

            if cancel_checker is not None and cancel_checker():
                raise WorkflowCancelledError(str(state.get("workflow_execution_id", "unknown")))

            # Deduplicate frontier nodes while preserving deterministic order
            ordered_batch: list[str] = []
            for node_name in frontier:
                if node_name != END and node_name not in ordered_batch:
                    ordered_batch.append(node_name)

            if not ordered_batch:
                break

            # Execute batch sequentially if len==1, or truly concurrently via asyncio.gather if fan-out
            nodes_to_run = [n for n in ordered_batch if n not in skip_nodes]

            if len(nodes_to_run) == 1:
                node_name = nodes_to_run[0]
                patch = await self._nodes[node_name](dict(state), context)
                patch = merge_workflow_state(patch, {"completed_nodes": [node_name]})
                state = merge_workflow_state(state, patch)
                step_counter += 1
                if checkpoint_callback is not None:
                    await checkpoint_callback(
                        node_name,
                        step_counter,
                        sanitize_checkpoint_state(state),
                    )
            elif len(nodes_to_run) > 1:
                # Snapshot read-only copy for each independent parallel branch
                snapshots = [dict(state) for _ in nodes_to_run]
                patches = await asyncio.gather(
                    *(
                        self._nodes[node_name](snap, context)
                        for node_name, snap in zip(nodes_to_run, snapshots, strict=True)
                    )
                )
                for node_name, patch in zip(nodes_to_run, patches, strict=True):
                    enriched = merge_workflow_state(patch, {"completed_nodes": [node_name]})
                    state = merge_workflow_state(state, enriched)
                step_counter += 1
                if checkpoint_callback is not None:
                    await checkpoint_callback(
                        f"parallel:{'+'.join(nodes_to_run)}",
                        step_counter,
                        sanitize_checkpoint_state(state),
                    )

            # Resolve next superstep frontier from all nodes in the completed batch
            next_frontier: list[str] = []
            for node_name in ordered_batch:
                for nxt in self._resolve_next(node_name, state):
                    if nxt != END and nxt not in next_frontier:
                        next_frontier.append(nxt)
            frontier = next_frontier

        return state

    async def ainvoke(
        self,
        initial_state: dict[str, Any],
        context: AgentContext | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """LangGraph-compatible invocation alias delegating to arun."""
        ctx = context or kwargs.pop("context", None)
        return await self.arun(initial_state, context=ctx, **kwargs)


class KeepStateGraph:
    """Declarative LangGraph-compatible StateGraph builder owned by KEEP's adapter layer."""

    def __init__(self) -> None:
        self._nodes: dict[str, NodeCallable] = {}
        self._edges: dict[str, list[str]] = {}
        self._conditional_edges: dict[str, tuple[RouterCallable, dict[str, str | list[str]]]] = {}

    def add_node(self, name: str, fn: NodeCallable) -> KeepStateGraph:
        if name in (START, END):
            raise ValueError(f"Reserved node name cannot be registered: {name}")
        self._nodes[name] = fn
        return self

    def add_edge(self, source: str, target: str) -> KeepStateGraph:
        self._edges.setdefault(source, []).append(target)
        return self

    def add_conditional_edges(
        self,
        source: str,
        router_fn: RouterCallable,
        path_map: dict[str, str | list[str]],
    ) -> KeepStateGraph:
        self._conditional_edges[source] = (router_fn, dict(path_map))
        return self

    def compile(self) -> CompiledKeepWorkflowGraph:
        if START not in self._edges and START not in self._conditional_edges:
            raise ValueError("Graph must define at least one outgoing edge from START.")
        for targets in self._edges.values():
            for t in targets:
                if t != END and t not in self._nodes:
                    raise ValueError(f"Edge references unregistered node: '{t}'")
        for _router, path_map in self._conditional_edges.values():
            for mapped in path_map.values():
                targets = mapped if isinstance(mapped, list) else [mapped]
                for t in targets:
                    if t != END and t not in self._nodes:
                        raise ValueError(f"Conditional edge references unregistered node: '{t}'")

        return CompiledKeepWorkflowGraph(
            nodes=self._nodes,
            edges=self._edges,
            conditional_edges=self._conditional_edges,
        )
