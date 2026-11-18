"""KEEP Phase 4.4 — Task Decomposer & Execution Layer Normalizer.

Normalizes candidate tasks into deduplicated atomic steps, validates dependency
graph acyclicity and I/O contracts via `DependencyGraphValidator`, and annotates
every task with its deterministic `parallel_group` and `plan.execution_layers`.

Owner: Member 2 (Task Decomposition & Dependency Graph)
Specification: devdocs/p4/p4.4.txt (Sections 3, 5)
"""

from __future__ import annotations

from backend.app.agents.planning.contracts import ExecutionPlan, PlannedTask
from backend.app.agents.planning.dependency_graph import (
    DependencyGraphResult,
    DependencyGraphValidator,
)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        norm = item.strip()
        if norm and norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out


class TaskDecomposer:
    """Normalizes plans into atomic, parallel-grouped tasks validated as a strict DAG."""

    def __init__(self, graph_validator: DependencyGraphValidator | None = None) -> None:
        self.graph_validator = graph_validator or DependencyGraphValidator()

    def decompose(self, plan: ExecutionPlan) -> tuple[ExecutionPlan, DependencyGraphResult]:
        """Normalizes task definitions, validates graph structure, and assigns parallel layers."""
        cleaned_tasks: list[PlannedTask] = [
            task.model_copy(
                update={
                    "required_capabilities": _dedupe(task.required_capabilities),
                    "depends_on": _dedupe(task.depends_on),
                    "input_refs": _dedupe(task.input_refs),
                }
            )
            for task in plan.tasks
        ]
        candidate = plan.model_copy(update={"tasks": cleaned_tasks})
        graph_result = self.graph_validator.validate(candidate)

        layer_lookup: dict[str, int] = {}
        for layer_idx, layer_nodes in enumerate(graph_result.parallel_layers):
            for tid in layer_nodes:
                layer_lookup[tid] = layer_idx

        ordered_tasks = [
            next(t for t in cleaned_tasks if t.task_id == tid).model_copy(
                update={"parallel_group": layer_lookup[tid]}
            )
            for tid in graph_result.topological_order
        ]

        normalized_plan = candidate.model_copy(
            update={
                "tasks": ordered_tasks,
                "execution_layers": [list(layer) for layer in graph_result.parallel_layers],
            }
        )
        return normalized_plan, graph_result
