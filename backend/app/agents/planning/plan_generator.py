"""KEEP Phase 4.4 — Structured Plan Generator & Deterministic Mock LLM Client.

Proposes structured `PlannedTask` DAGs from a `GoalSpec` using an injectable
`StructuredPlanLLMClient` (with deterministic `MockStructuredPlanLLM` default so
unit and integration tests run reproducibly with zero external LLM dependencies).

Owner: Member 1 (Goal Understanding & Plan Generation)
Specification: devdocs/p4/p4.4.txt (Sections 3, 5, 6)
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.planning.contracts import (
    ExecutionPlan,
    GoalSpec,
    PlannedTask,
    PlanStatus,
    StructuredPlanLLMClient,
)
from backend.app.agents.planning.prompts import build_plan_generation_prompt


class MockStructuredPlanLLM:
    """Deterministic structured plan proposer supporting multi-step, parallel, and edge scenarios."""

    async def propose_tasks(
        self,
        goal: GoalSpec,
        *,
        available_capabilities: list[str],
        feedback: str | None = None,
        attempt: int = 1,
    ) -> list[PlannedTask]:
        lower = goal.goal.lower()
        fb_lower = (feedback or "").lower()
        avail = set(available_capabilities)

        # Scenario A: Explicit unsupported capability request (tests Member 3 rejection)
        if any(kw in lower for kw in ("quantum_simulation", "external_wire_transfer", "deploy_nuclear")):
            return [
                PlannedTask(
                    task_id="task_1",
                    description=f"Retrieve tenant context for '{goal.goal}'",
                    required_capabilities=["knowledge.search"],
                    depends_on=[],
                    input_refs=[],
                    output_key="retrieved_context",
                    requires_evidence=True,
                ),
                PlannedTask(
                    task_id="task_2",
                    description="Execute unsupported external specialized operation",
                    required_capabilities=["unsupported.magic_capability"],
                    depends_on=["task_1"],
                    input_refs=["retrieved_context"],
                    output_key="magic_result",
                    required=True,
                ),
            ]

        # Scenario B: Restricted / side-effecting request (triggers approval_required gate)
        if any(
            kw in lower
            for kw in ("delete", "purge", "broadcast", "send external email", "modify production", "publish externally")
        ):
            return [
                PlannedTask(
                    task_id="task_1",
                    description=f"Retrieve authorized records relevant to '{goal.goal}'",
                    required_capabilities=["knowledge.search"],
                    depends_on=[],
                    input_refs=[],
                    output_key="retrieved_records",
                    requires_evidence=True,
                ),
                PlannedTask(
                    task_id="task_2",
                    description=f"Execute restricted action for '{goal.goal}' (requires human approval)",
                    required_capabilities=["knowledge.analyze"],
                    depends_on=["task_1"],
                    input_refs=["retrieved_records"],
                    output_key="action_outcome",
                    required=True,
                    is_side_effecting=True,
                ),
            ]

        # Scenario C: Multi-step parallel comparison / feedback / project decisions & risks
        if (
            ("compare" in lower and ("quarter" in lower or "feedback" in lower))
            or ("decision" in lower and "risk" in lower)
            or ("parallel" in lower)
            or ("add risk" in fb_lower)
        ):
            # Prefer real registered Phase 4.3 capabilities when available
            branch_a_cap = (
                "knowledge.decisions" if "knowledge.decisions" in avail else "knowledge.analyze"
            )
            branch_b_cap = (
                "knowledge.risks" if "knowledge.risks" in avail else "knowledge.analyze"
            )
            synth_cap = "knowledge.analyze" if "knowledge.analyze" in avail else "knowledge.search"

            if "compare" in lower and ("quarter" in lower or "feedback" in lower):
                return [
                    PlannedTask(
                        task_id="task_1",
                        description="Retrieve authorized internal customer feedback across both quarters.",
                        required_capabilities=["knowledge.search"],
                        depends_on=[],
                        input_refs=[],
                        output_key="retrieved_feedback",
                        requires_evidence=True,
                    ),
                    PlannedTask(
                        task_id="task_2",
                        description="Analyze earlier quarter feedback themes, decisions, and supporting evidence.",
                        required_capabilities=[branch_a_cap],
                        depends_on=["task_1"],
                        input_refs=["retrieved_feedback"],
                        output_key="earlier_quarter_analysis",
                        requires_evidence=True,
                    ),
                    PlannedTask(
                        task_id="task_3",
                        description="Analyze later quarter feedback complaints, risks, and supporting evidence.",
                        required_capabilities=[branch_b_cap],
                        depends_on=["task_1"],
                        input_refs=["retrieved_feedback"],
                        output_key="later_quarter_analysis",
                        requires_evidence=True,
                    ),
                    PlannedTask(
                        task_id="task_4",
                        description="Compare both quarters and generate three evidence-backed recommendations.",
                        required_capabilities=[synth_cap],
                        depends_on=["task_2", "task_3"],
                        input_refs=["earlier_quarter_analysis", "later_quarter_analysis"],
                        output_key="comparison_recommendations",
                        requires_evidence=True,
                    ),
                ]

            return [
                PlannedTask(
                    task_id="task_1",
                    description=f"Retrieve authorized project documents for '{goal.scope}'.",
                    required_capabilities=["knowledge.search"],
                    depends_on=[],
                    input_refs=[],
                    output_key="retrieved_documents",
                    requires_evidence=True,
                ),
                PlannedTask(
                    task_id="task_2",
                    description="Extract approved project decisions and accountable owners.",
                    required_capabilities=[branch_a_cap],
                    depends_on=["task_1"],
                    input_refs=["retrieved_documents"],
                    output_key="extracted_decisions",
                    requires_evidence=True,
                ),
                PlannedTask(
                    task_id="task_3",
                    description="Identify operational blockers, delivery risks, and mitigations.",
                    required_capabilities=[branch_b_cap],
                    depends_on=["task_1"],
                    input_refs=["retrieved_documents"],
                    output_key="identified_risks",
                    required=False,
                    requires_evidence=True,
                ),
                PlannedTask(
                    task_id="task_4",
                    description="Synthesize decisions and risks into an executive evidence-backed brief.",
                    required_capabilities=[synth_cap],
                    depends_on=["task_2", "task_3"],
                    input_refs=["extracted_decisions", "identified_risks"],
                    output_key="executive_brief",
                    requires_evidence=True,
                ),
            ]

        # Scenario D: Default sequential retrieval -> analysis plan
        synth_cap = "knowledge.analyze" if "knowledge.analyze" in avail else "knowledge.search"
        return [
            PlannedTask(
                task_id="task_1",
                description=f"Retrieve authorized KEEP knowledge relevant to: {goal.goal}",
                required_capabilities=["knowledge.search"],
                depends_on=[],
                input_refs=[],
                output_key="retrieved_evidence",
                requires_evidence=True,
            ),
            PlannedTask(
                task_id="task_2",
                description=f"Synthesize retrieved evidence to produce: {goal.expected_output}",
                required_capabilities=[synth_cap],
                depends_on=["task_1"],
                input_refs=["retrieved_evidence"],
                output_key="final_synthesis",
                requires_evidence=True,
            ),
        ]


class PlanGenerator:
    """Generates candidate structured ExecutionPlan objects from a parsed GoalSpec."""

    def __init__(self, llm_client: StructuredPlanLLMClient | None = None) -> None:
        self._llm: StructuredPlanLLMClient = llm_client or MockStructuredPlanLLM()

    async def generate(
        self,
        goal: GoalSpec,
        *,
        available_capabilities: list[str],
        input_data: dict[str, Any] | None = None,
        max_steps: int = 20,
        max_replans: int = 2,
        plan_id: str | None = None,
        version: int = 1,
        replan_count: int = 0,
        feedback: str | None = None,
        revision_reason: str = "Initial plan generation",
    ) -> ExecutionPlan:
        """Creates a candidate draft ExecutionPlan (or clarification_required if ambiguous)."""
        if goal.is_ambiguous:
            kwargs: dict[str, Any] = {
                "version": version,
                "goal": goal,
                "tasks": [],
                "max_steps": max_steps,
                "max_replans": max_replans,
                "replan_count": replan_count,
                "status": PlanStatus.CLARIFICATION_REQUIRED,
                "input": dict(input_data or {}),
                "clarification_questions": list(goal.clarification_questions),
                "revision_reason": revision_reason,
            }
            if plan_id:
                kwargs["plan_id"] = plan_id
            return ExecutionPlan(**kwargs)

        # Prompt construction stays auditable & ready for real LLM adapters
        _prompt = build_plan_generation_prompt(
            goal_text=goal.goal,
            expected_output=goal.expected_output,
            constraints=goal.constraints,
            available_capabilities=available_capabilities,
            feedback=feedback,
        )
        proposed_tasks = await self._llm.propose_tasks(
            goal,
            available_capabilities=available_capabilities,
            feedback=feedback,
            attempt=replan_count + 1,
        )

        # Strip any LLM-guessed agent bindings so Member 3's selector ALWAYS resolves from registry
        sanitized_tasks = [
            task.model_copy(
                update={
                    "resolved_agent_id": None,
                    "resolved_agent_version": None,
                }
            )
            for task in proposed_tasks
        ]

        plan_kwargs: dict[str, Any] = {
            "version": version,
            "goal": goal,
            "tasks": sanitized_tasks,
            "max_steps": max_steps,
            "max_replans": max_replans,
            "replan_count": replan_count,
            "status": PlanStatus.DRAFT,
            "input": dict(input_data or {}),
            "revision_reason": revision_reason,
        }
        if plan_id:
            plan_kwargs["plan_id"] = plan_id
        return ExecutionPlan(**plan_kwargs)
