"""KEEP Phase 4.4 — Task Dependency Graph Validator & Parallel Layer Scheduler.

Validates DAG acyclicity (Kahn's algorithm), duplicate/missing references, strict
transitive upstream `input_refs` compatibility, task count limits, and computes
deterministic parallel execution layers consumable by KEEP's Phase 4.3 orchestrator.

Owner: Member 2 (Task Decomposition & Dependency Graph)
Specification: devdocs/p4/p4.4.txt (Sections 3, 4, 8)
"""

from __future__ import annotations

from backend.app.agents.errors import PlanGraphValidationError
from backend.app.agents.planning.contracts import ExecutionPlan, PlannedTask
from pydantic import BaseModel, Field


class DependencyGraphResult(BaseModel):
    """Validated topological structure and parallel execution layers for an ExecutionPlan."""

    topological_order: list[str] = Field(default_factory=list)
    parallel_layers: list[list[str]] = Field(default_factory=list)
    root_tasks: list[str] = Field(default_factory=list)
    leaf_tasks: list[str] = Field(default_factory=list)
    critical_path_length: int = Field(default=0, ge=0)
    output_producers: dict[str, str] = Field(default_factory=dict)


class DependencyGraphValidator:
    """Validates task graph integrity, acyclicity, I/O contracts, and parallel layers."""

    def __init__(self, *, max_tasks_hard_limit: int = 20) -> None:
        self._max_tasks_hard_limit = max_tasks_hard_limit

    def validate(self, plan: ExecutionPlan) -> DependencyGraphResult:
        """Validates `plan.tasks` as a strict DAG and computes parallel execution layers."""
        tasks = plan.tasks
        if not tasks:
            raise PlanGraphValidationError("Execution plan must contain at least one task.")

        effective_limit = min(plan.max_steps, self._max_tasks_hard_limit)
        if len(tasks) > effective_limit:
            raise PlanGraphValidationError(
                f"Plan contains {len(tasks)} tasks, exceeding limit of {effective_limit}.",
                details={"task_count": len(tasks), "limit": effective_limit},
            )

        task_map: dict[str, PlannedTask] = {}
        output_producers: dict[str, str] = {}
        for task in tasks:
            if task.task_id in task_map:
                raise PlanGraphValidationError(
                    f"Duplicate task_id detected: '{task.task_id}'.",
                    details={"task_id": task.task_id},
                )
            if task.output_key in output_producers:
                raise PlanGraphValidationError(
                    f"Duplicate output_key detected: '{task.output_key}'.",
                    details={"output_key": task.output_key},
                )
            task_map[task.task_id] = task
            output_producers[task.output_key] = task.task_id

        # Build adjacency & in-degree tables while verifying dependency existence
        in_degree: dict[str, int] = {t.task_id: 0 for t in tasks}
        dependents: dict[str, list[str]] = {t.task_id: [] for t in tasks}

        for task in tasks:
            seen_deps: set[str] = set()
            for dep_id in task.depends_on:
                if dep_id == task.task_id:
                    raise PlanGraphValidationError(
                        f"Task '{task.task_id}' cannot depend on itself.",
                        details={"task_id": task.task_id},
                    )
                if dep_id not in task_map:
                    raise PlanGraphValidationError(
                        f"Task '{task.task_id}' depends on missing task '{dep_id}'.",
                        details={"task_id": task.task_id, "missing_dependency": dep_id},
                    )
                if dep_id not in seen_deps:
                    seen_deps.add(dep_id)
                    dependents[dep_id].append(task.task_id)
                    in_degree[task.task_id] += 1

        # Kahn's layered topological sort: identifies cycles AND parallel execution layers!
        current_layer = sorted(tid for tid, deg in in_degree.items() if deg == 0)
        parallel_layers: list[list[str]] = []
        topological_order: list[str] = []

        while current_layer:
            parallel_layers.append(list(current_layer))
            topological_order.extend(current_layer)
            next_layer_candidates: list[str] = []
            for tid in current_layer:
                for child in dependents[tid]:
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        next_layer_candidates.append(child)
            current_layer = sorted(next_layer_candidates)

        if len(topological_order) != len(tasks):
            cyclic_nodes = sorted(tid for tid, deg in in_degree.items() if deg > 0)
            raise PlanGraphValidationError(
                f"Dependency cycle detected involving task(s): {', '.join(cyclic_nodes)}.",
                details={"cyclic_tasks": cyclic_nodes},
            )

        # Compute transitive ancestors for each task to verify `input_refs` strictly reference upstream outputs
        ancestors: dict[str, set[str]] = {}
        for tid in topological_order:
            task = task_map[tid]
            anc: set[str] = set(task.depends_on)
            for dep_id in task.depends_on:
                anc.update(ancestors[dep_id])
            ancestors[tid] = anc

        for tid in topological_order:
            task = task_map[tid]
            for ref in task.input_refs:
                producer = output_producers.get(ref)
                if producer is None:
                    raise PlanGraphValidationError(
                        f"Task '{tid}' references unknown input_ref '{ref}'.",
                        details={"task_id": tid, "input_ref": ref},
                    )
                if producer not in ancestors[tid]:
                    raise PlanGraphValidationError(
                        f"Task '{tid}' references output '{ref}' from task '{producer}', "
                        f"which is not an upstream dependency of '{tid}'.",
                        details={"task_id": tid, "input_ref": ref, "producer_task_id": producer},
                    )

        root_tasks = parallel_layers[0] if parallel_layers else []
        leaf_tasks = sorted(tid for tid, children in dependents.items() if not children)

        return DependencyGraphResult(
            topological_order=topological_order,
            parallel_layers=parallel_layers,
            root_tasks=root_tasks,
            leaf_tasks=leaf_tasks,
            critical_path_length=len(parallel_layers),
            output_producers=output_producers,
        )
