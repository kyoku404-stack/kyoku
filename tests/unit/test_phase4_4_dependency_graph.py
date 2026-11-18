"""Phase 4.4 Member 2 Unit Tests — Task Decomposition & Dependency Graph Validation."""

from __future__ import annotations

import pytest

from backend.app.agents.errors import PlanGraphValidationError
from backend.app.agents.planning.contracts import ExecutionPlan, GoalSpec, PlannedTask
from backend.app.agents.planning.decomposer import TaskDecomposer
from backend.app.agents.planning.dependency_graph import DependencyGraphValidator


class TestPhase44DependencyGraph:
    def test_parallel_layers_computed_for_diamond_comparison_plan(self) -> None:
        plan = ExecutionPlan(
            goal=GoalSpec(goal="Compare Q3 and Q4 feedback"),
            tasks=[
                PlannedTask(
                    task_id="task_1",
                    description="Retrieve feedback",
                    required_capabilities=["knowledge.search"],
                    output_key="feedback_docs",
                ),
                PlannedTask(
                    task_id="task_2",
                    description="Analyze Q3 feedback",
                    required_capabilities=["knowledge.decisions"],
                    depends_on=["task_1"],
                    input_refs=["feedback_docs"],
                    output_key="q3_analysis",
                ),
                PlannedTask(
                    task_id="task_3",
                    description="Analyze Q4 feedback",
                    required_capabilities=["knowledge.risks"],
                    depends_on=["task_1"],
                    input_refs=["feedback_docs"],
                    output_key="q4_analysis",
                ),
                PlannedTask(
                    task_id="task_4",
                    description="Compare and recommend",
                    required_capabilities=["knowledge.analyze"],
                    depends_on=["task_2", "task_3"],
                    input_refs=["q3_analysis", "q4_analysis"],
                    output_key="final_report",
                ),
            ],
        )

        decomposer = TaskDecomposer()
        normalized, graph = decomposer.decompose(plan)

        assert graph.parallel_layers == [["task_1"], ["task_2", "task_3"], ["task_4"]]
        assert graph.root_tasks == ["task_1"]
        assert graph.leaf_tasks == ["task_4"]
        assert graph.critical_path_length == 3
        assert normalized.execution_layers == [["task_1"], ["task_2", "task_3"], ["task_4"]]
        groups = {t.task_id: t.parallel_group for t in normalized.tasks}
        assert groups == {"task_1": 0, "task_2": 1, "task_3": 1, "task_4": 2}

    def test_cycle_detection_rejects_two_and_three_node_cycles(self) -> None:
        cyclic_plan = ExecutionPlan(
            goal=GoalSpec(goal="Cyclic plan test"),
            tasks=[
                PlannedTask(
                    task_id="task_1",
                    description="Step 1",
                    required_capabilities=["knowledge.search"],
                    depends_on=["task_2"],
                    output_key="out_1",
                ),
                PlannedTask(
                    task_id="task_2",
                    description="Step 2",
                    required_capabilities=["knowledge.analyze"],
                    depends_on=["task_1"],
                    output_key="out_2",
                ),
            ],
        )

        validator = DependencyGraphValidator()
        with pytest.raises(PlanGraphValidationError, match="Dependency cycle detected") as exc:
            validator.validate(cyclic_plan)
        assert set(exc.value.details["cyclic_tasks"]) == {"task_1", "task_2"}

    def test_input_refs_must_reference_strict_upstream_ancestor_outputs(self) -> None:
        # Unknown input_ref
        unknown_ref_plan = ExecutionPlan(
            goal=GoalSpec(goal="Unknown ref"),
            tasks=[
                PlannedTask(
                    task_id="task_1",
                    description="Retrieve",
                    required_capabilities=["knowledge.search"],
                    input_refs=["nonexistent_output"],
                    output_key="out_1",
                )
            ],
        )
        validator = DependencyGraphValidator()
        with pytest.raises(PlanGraphValidationError, match="unknown input_ref"):
            validator.validate(unknown_ref_plan)

        # Sibling output referenced without depends_on edge
        sibling_ref_plan = ExecutionPlan(
            goal=GoalSpec(goal="Sibling ref without dependency"),
            tasks=[
                PlannedTask(
                    task_id="task_1",
                    description="Retrieve",
                    required_capabilities=["knowledge.search"],
                    output_key="out_1",
                ),
                PlannedTask(
                    task_id="task_2",
                    description="Branch A",
                    required_capabilities=["knowledge.decisions"],
                    depends_on=["task_1"],
                    input_refs=["out_1"],
                    output_key="out_2",
                ),
                PlannedTask(
                    task_id="task_3",
                    description="Branch B trying to read sibling Branch A",
                    required_capabilities=["knowledge.risks"],
                    depends_on=["task_1"],
                    input_refs=["out_2"],  # invalid: task_2 is sibling, not ancestor!
                    output_key="out_3",
                ),
            ],
        )
        with pytest.raises(PlanGraphValidationError, match="not an upstream dependency"):
            validator.validate(sibling_ref_plan)

    def test_transitive_ancestor_input_ref_is_allowed(self) -> None:
        plan = ExecutionPlan(
            goal=GoalSpec(goal="Transitive input reference"),
            tasks=[
                PlannedTask(
                    task_id="task_1",
                    description="Retrieve",
                    required_capabilities=["knowledge.search"],
                    output_key="raw_docs",
                ),
                PlannedTask(
                    task_id="task_2",
                    description="Analyze",
                    required_capabilities=["knowledge.analyze"],
                    depends_on=["task_1"],
                    input_refs=["raw_docs"],
                    output_key="analysis",
                ),
                PlannedTask(
                    task_id="task_3",
                    description="Synthesize using both raw_docs and analysis",
                    required_capabilities=["knowledge.decisions"],
                    depends_on=["task_2"],
                    input_refs=["raw_docs", "analysis"],
                    output_key="summary",
                ),
            ],
        )
        normalized, graph = TaskDecomposer().decompose(plan)
        assert graph.topological_order == ["task_1", "task_2", "task_3"]
        assert len(normalized.execution_layers) == 3
