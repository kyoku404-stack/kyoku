"""KEEP Phase 4.9 — Adaptive Planning Adapter.

Integrates Phase 4.4 planning components (`GoalParser`, `PlanGenerator`,
`KeepPlanningService`) to propose initial bounded plans and adaptive
replanning steps when evidence is missing or tasks fail.

Owner: Member 2 (Adaptive Planning & Progress Evaluation)
Specification: devdocs/p4/p4.9.txt (Sections 3, 5, 6)
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from backend.app.agents.autonomy.contracts import (
    AutonomyPolicy,
    AutonomySecurityContext,
    EvaluationResult,
    PlannedStepSpec,
)
from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import AgentLayerError
from backend.app.agents.planning.contracts import PlanCreateRequest
from backend.app.agents.planning.goal_parser import GoalParser
from backend.app.agents.planning.plan_generator import PlanGenerator


class AutonomyPlannerAdapter:
    """Proposes bounded candidate plans and adaptive revisions (never self-authorizing)."""

    def __init__(
        self,
        *,
        planning_service: Any | None = None,
        goal_parser: GoalParser | None = None,
        plan_generator: PlanGenerator | None = None,
        agent_registry: Any | None = None,
    ) -> None:
        self.planning_service = planning_service
        self.goal_parser = goal_parser or GoalParser()
        self.plan_generator = plan_generator or PlanGenerator()
        self.agent_registry = agent_registry

    def _resolve_agent_for_capability(
        self,
        capability: str,
        policy: AutonomyPolicy,
    ) -> str:
        """Resolves capability against live Phase 4.1 AgentRegistry if available."""
        if self.agent_registry is not None and hasattr(self.agent_registry, "find_by_capability"):
            matches = self.agent_registry.find_by_capability(capability, enabled_only=True)
            for meta in matches:
                if not policy.allowed_agents or meta.agent_id in policy.allowed_agents:
                    return meta.agent_id
        # Deterministic canonical KEEP agent mapping
        fallback_map = {
            "knowledge.research": "research_agent",
            "knowledge.search": "knowledge_retrieval",
            "knowledge.analyze": "knowledge_analysis",
            "knowledge.decisions": "decision_extractor",
            "knowledge.risks": "risk_analyst",
            "report.draft": "report_synthesis",
        }
        return fallback_map.get(capability, "reference")

    async def propose_initial_plan(
        self,
        *,
        objective: str,
        workflow_id: str,
        policy: AutonomyPolicy,
        security_context: AutonomySecurityContext,
        context_metadata: dict[str, Any] | None = None,
    ) -> list[PlannedStepSpec]:
        """Generates an initial bounded list of PlannedStepSpec candidates."""
        meta = dict(context_metadata or {})
        lower_obj = objective.lower()

        # Check explicit write/side-effect triggers for approval gating
        has_write_intent = bool(meta.get("requires_write")) or any(
            kw in lower_obj
            for kw in (
                "publish",
                "update crm",
                "send email",
                "send external email",
                "external email",
                "broadcast",
                "modify production",
                "notify customers",
                "delete",
                "write report to",
            )
        )

        # Build steps via Phase 4.4 planning engine if injected
        steps: list[PlannedStepSpec] = []
        if self.planning_service is not None:
            agent_ctx = AgentContext(
                user_id=security_context.user_id,
                tenant_id=security_context.tenant_id,
                roles=list(security_context.roles),
                permissions=list(security_context.permissions),
                correlation_id=security_context.correlation_id or f"corr_{uuid4().hex[:12]}",
                trusted=True,
            )
            try:
                plan = await self.planning_service.create_plan(
                    PlanCreateRequest(
                        goal=objective,
                        input=meta,
                        max_steps=policy.max_steps,
                        max_replans=policy.max_replans,
                    ),
                    agent_ctx,
                )
                for idx, task in enumerate(plan.tasks, start=1):
                    cap = task.required_capabilities[0] if task.required_capabilities else "knowledge.search"
                    agent_id = task.resolved_agent_id or self._resolve_agent_for_capability(cap, policy)
                    steps.append(
                        PlannedStepSpec(
                            step_order=idx,
                            title=task.description[:250],
                            description=task.description,
                            agent_id=agent_id,
                            tool_id="knowledge_search" if "search" in cap or "research" in cap else None,
                            required_capability=cap,
                            is_side_effecting=bool(task.is_side_effecting),
                            depends_on=list(task.depends_on),
                            inputs={"objective": objective, **meta},
                        )
                    )
            except (AgentLayerError, ValueError, RuntimeError):
                # Fall through to deterministic adaptive planner if PlanCreateRequest triggers clarification/policy edge
                steps = []

        if not steps:
            if workflow_id == "churn_investigation" or "churn" in lower_obj:
                steps = [
                    PlannedStepSpec(
                        step_order=1,
                        title="Retrieve customer churn telemetry and support evidence",
                        description=f"Search enterprise knowledge base for evidence regarding: {objective}",
                        agent_id=self._resolve_agent_for_capability("knowledge.research", policy),
                        tool_id="knowledge_search",
                        required_capability="knowledge.research",
                        is_side_effecting=False,
                        inputs={"query": objective, "scope": "churn_metrics", **meta},
                    ),
                    PlannedStepSpec(
                        step_order=2,
                        title="Analyze root causes and billing/usage correlations",
                        description="Correlate usage drop, ticket escalation spikes, and cohort trends.",
                        agent_id=self._resolve_agent_for_capability("knowledge.analyze", policy),
                        tool_id=None,
                        required_capability="knowledge.analyze",
                        is_side_effecting=False,
                        inputs={"focus": "root_cause_analysis", **meta},
                    ),
                    PlannedStepSpec(
                        step_order=3,
                        title="Synthesize churn investigation report with limitations",
                        description="Produce verifiable summary, evidence citations, and retention recommendations.",
                        agent_id=self._resolve_agent_for_capability("knowledge.analyze", policy),
                        tool_id="report_draft",
                        required_capability="knowledge.analyze",
                        is_side_effecting=False,
                        inputs={"format": "executive_report", **meta},
                    ),
                ]
            else:
                steps = [
                    PlannedStepSpec(
                        step_order=1,
                        title="Gather authorized KEEP evidence for objective",
                        description=f"Retrieve grounded sources for: {objective}",
                        agent_id=self._resolve_agent_for_capability("knowledge.research", policy),
                        tool_id="knowledge_search",
                        required_capability="knowledge.research",
                        is_side_effecting=False,
                        inputs={"query": objective, **meta},
                    ),
                    PlannedStepSpec(
                        step_order=2,
                        title="Synthesize evidence and verify objective coverage",
                        description=f"Analyze findings for: {objective}",
                        agent_id=self._resolve_agent_for_capability("knowledge.analyze", policy),
                        tool_id="report_draft",
                        required_capability="knowledge.analyze",
                        is_side_effecting=False,
                        inputs={"objective": objective, **meta},
                    ),
                ]

        if has_write_intent and not any(s.is_side_effecting for s in steps):
            steps.append(
                PlannedStepSpec(
                    step_order=len(steps) + 1,
                    title="Execute requested external write / publication action",
                    description=f"Write or publish action requested in objective: {objective}",
                    agent_id=self._resolve_agent_for_capability("knowledge.analyze", policy),
                    tool_id="report_draft",
                    required_capability="knowledge.analyze",
                    is_side_effecting=True,
                    inputs={"action_type": "write_publication", **meta},
                )
            )

        # Enforce plan length never exceeds policy step allowance at generation time
        return steps[: policy.max_steps]

    async def propose_replan(
        self,
        *,
        objective: str,
        evaluation: EvaluationResult,
        completed_outputs: list[dict[str, Any]],
        failed_steps: list[dict[str, Any]],
        policy: AutonomyPolicy,
        next_step_order: int = 1,
    ) -> list[PlannedStepSpec]:
        """Generates bounded follow-up steps targeting missing evidence or failed tasks."""
        missing = list(evaluation.missing_evidence)
        reasons = "; ".join(evaluation.reasons) or "Evidence gap or prior task failure"
        target_desc = (
            f"Collect missing evidence ({', '.join(missing)})"
            if missing
            else f"Recover from step failure and gather supplemental evidence ({reasons})"
        )

        follow_up = [
            PlannedStepSpec(
                step_order=next_step_order,
                title="Adaptive follow-up retrieval for missing evidence",
                description=target_desc,
                agent_id=self._resolve_agent_for_capability("knowledge.research", policy),
                tool_id="knowledge_search",
                required_capability="knowledge.research",
                is_side_effecting=False,
                inputs={
                    "objective": objective,
                    "missing_evidence": missing,
                    "failed_steps": failed_steps,
                    "replan_recovery": True,
                },
            ),
            PlannedStepSpec(
                step_order=next_step_order + 1,
                title="Re-evaluate and finalize findings with updated evidence",
                description=f"Consolidate prior outputs ({len(completed_outputs)}) with newly retrieved evidence.",
                agent_id=self._resolve_agent_for_capability("knowledge.analyze", policy),
                tool_id="report_draft",
                required_capability="knowledge.analyze",
                is_side_effecting=False,
                inputs={"objective": objective, "consolidated_pass": True},
            ),
        ]
        return follow_up
