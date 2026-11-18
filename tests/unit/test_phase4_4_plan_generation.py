"""Phase 4.4 Member 1 Unit Tests — Goal Understanding, Contracts & Plan Generation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.app.agents.planning.contracts import (
    ExecutionPlan,
    GoalSpec,
    PlanCreateRequest,
    PlannedTask,
    PlanStatus,
)
from backend.app.agents.planning.goal_parser import GoalParser
from backend.app.agents.planning.plan_generator import PlanGenerator


class _SpoofingLLMClient:
    """Mock LLM that attempts to pre-fill resolved_agent_id; PlanGenerator MUST strip it."""

    async def propose_tasks(
        self,
        goal: GoalSpec,
        *,
        available_capabilities: list[str],
        feedback: str | None = None,
        attempt: int = 1,
    ) -> list[PlannedTask]:
        return [
            PlannedTask(
                task_id="task_1",
                description="Attempt to hijack agent binding",
                required_capabilities=["knowledge.search"],
                output_key="out_1",
                resolved_agent_id="evil_unregistered_agent",
                resolved_agent_version="9.9.9",
            )
        ]


class TestPhase44PlanGeneration:
    @pytest.mark.asyncio
    async def test_goal_parser_extracts_constraints_timeframe_and_criteria(self) -> None:
        parser = GoalParser()
        req = PlanCreateRequest(
            goal="Compare customer feedback from the last two quarters and recommend actions",
            constraints=["Include evidence references"],
            input={"project_id": "feedback-q3-q4"},
        )
        spec = await parser.parse(req)
        assert spec.is_ambiguous is False
        assert spec.requires_evidence is True
        assert spec.scope == "feedback-q3-q4"
        assert any("last two quarters" in c.lower() for c in spec.constraints)
        assert len(spec.success_criteria) >= 2

    @pytest.mark.asyncio
    async def test_goal_parser_flags_ambiguous_requests_for_clarification(self) -> None:
        parser = GoalParser()
        generator = PlanGenerator()

        spec = await parser.parse(PlanCreateRequest(goal="analyze"))
        assert spec.is_ambiguous is True
        assert len(spec.clarification_questions) >= 1

        plan = await generator.generate(
            spec,
            available_capabilities=["knowledge.search", "knowledge.analyze"],
        )
        assert plan.status == PlanStatus.CLARIFICATION_REQUIRED
        assert plan.tasks == []
        assert len(plan.clarification_questions) >= 1

    @pytest.mark.asyncio
    async def test_plan_generator_produces_multi_step_parallel_comparison_plan(self) -> None:
        parser = GoalParser()
        generator = PlanGenerator()
        spec = await parser.parse(
            PlanCreateRequest(
                goal="Compare internal customer feedback from the last two quarters, identify recurring complaints, and recommend improvements"
            )
        )
        plan = await generator.generate(
            spec,
            available_capabilities=[
                "knowledge.search",
                "knowledge.analyze",
                "knowledge.decisions",
                "knowledge.risks",
            ],
        )

        assert plan.status == PlanStatus.DRAFT
        assert len(plan.tasks) == 4
        assert plan.tasks[0].depends_on == []
        # Tasks 2 and 3 both depend only on task_1 (eligible for parallel execution)
        assert plan.tasks[1].depends_on == ["task_1"]
        assert plan.tasks[2].depends_on == ["task_1"]
        # Task 4 converges on tasks 2 and 3
        assert set(plan.tasks[3].depends_on) == {"task_2", "task_3"}
        # All resolved_agent_id must be None until Member 3's selector binds them
        assert all(t.resolved_agent_id is None for t in plan.tasks)

    @pytest.mark.asyncio
    async def test_plan_generator_strips_llm_guessed_agent_bindings(self) -> None:
        generator = PlanGenerator(llm_client=_SpoofingLLMClient())
        spec = GoalSpec(goal="Summarize quarterly project status")
        plan = await generator.generate(spec, available_capabilities=["knowledge.search"])
        assert plan.tasks[0].resolved_agent_id is None
        assert plan.tasks[0].resolved_agent_version is None

    def test_execution_plan_contract_rejects_duplicate_ids_self_deps_and_missing_deps(self) -> None:
        spec = GoalSpec(goal="Check contract guards")

        # Duplicate task_id
        with pytest.raises(ValidationError, match="Duplicate task_id"):
            ExecutionPlan(
                goal=spec,
                tasks=[
                    PlannedTask(
                        task_id="task_1",
                        description="Step A",
                        required_capabilities=["knowledge.search"],
                        output_key="out_a",
                    ),
                    PlannedTask(
                        task_id="task_1",
                        description="Step B",
                        required_capabilities=["knowledge.analyze"],
                        output_key="out_b",
                    ),
                ],
            )

        # Self dependency
        with pytest.raises(ValidationError, match="Self-dependency"):
            ExecutionPlan(
                goal=spec,
                tasks=[
                    PlannedTask(
                        task_id="task_1",
                        description="Self-loop",
                        required_capabilities=["knowledge.search"],
                        depends_on=["task_1"],
                        output_key="out_a",
                    )
                ],
            )

        # Missing dependency
        with pytest.raises(ValidationError, match="missing task_id"):
            ExecutionPlan(
                goal=spec,
                tasks=[
                    PlannedTask(
                        task_id="task_1",
                        description="Missing upstream",
                        required_capabilities=["knowledge.search"],
                        depends_on=["task_999"],
                        output_key="out_a",
                    )
                ],
            )
