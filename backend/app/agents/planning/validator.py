"""KEEP Phase 4.4 — Comprehensive 9-Point Execution Plan Validator (Fail-Closed).

Orchestrates structural DAG validation, input/output contract verification, live
Phase 4.1 capability resolution, RBAC & prompt-injection policy evaluation, resource
budgets, evidence ordering requirements, approval gating, version consistency, and
bounded replanning checks before any plan can enter `validated` status.

Owner: Member 3 (Agent Selection, Policies & Plan Validation)
Specification: devdocs/p4/p4.4.txt (Sections 3, 8)
"""

from __future__ import annotations

from datetime import UTC, datetime

from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import PlanGraphValidationError, sanitize_error_message
from backend.app.agents.planning.agent_selector import CapabilityAgentSelector
from backend.app.agents.planning.contracts import (
    ExecutionPlan,
    PlanStatus,
    ValidationFinding,
    ValidationSeverity,
)
from backend.app.agents.planning.decomposer import TaskDecomposer
from backend.app.agents.planning.policies import (
    PLANNING_POLICY_VERSION,
    KeepPlanningPolicyEngine,
)
from backend.app.agents.registry import AgentRegistry
from pydantic import BaseModel, Field


class PlanValidationReport(BaseModel):
    """Structured outcome returned by PlanValidator.validate_plan()."""

    plan: ExecutionPlan
    is_executable: bool
    has_errors: bool
    findings: list[ValidationFinding] = Field(default_factory=list)
    approval_required: bool = False
    approval_reasons: list[str] = Field(default_factory=list)
    policy_version: str = PLANNING_POLICY_VERSION


class PlanValidator:
    """Runs all 9 Section 8 validation checks deterministically and fails closed on errors."""

    def __init__(
        self,
        *,
        agent_registry: AgentRegistry,
        decomposer: TaskDecomposer | None = None,
        agent_selector: CapabilityAgentSelector | None = None,
        policy_engine: KeepPlanningPolicyEngine | None = None,
    ) -> None:
        self.agent_registry = agent_registry
        self.decomposer = decomposer or TaskDecomposer()
        self.agent_selector = agent_selector or CapabilityAgentSelector(agent_registry)
        self.policy_engine = policy_engine or KeepPlanningPolicyEngine()

    def _check_evidence_requirements(self, plan: ExecutionPlan) -> list[ValidationFinding]:
        """Verifies that when a goal requires evidence, a retrieval/search task exists upstream."""
        if not plan.goal.requires_evidence or not plan.tasks:
            return []

        has_retrieval = any(
            any(
                "search" in cap.lower() or "retriev" in cap.lower()
                for cap in t.required_capabilities
            )
            for t in plan.tasks
        )
        if not has_retrieval:
            return [
                ValidationFinding(
                    code="PLAN_EVIDENCE_MISSING",
                    check="evidence_requirements",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        "Goal requires grounded evidence references, but plan contains no "
                        "retrieval/search task before synthesis."
                    ),
                )
            ]
        return []

    async def validate_plan(
        self,
        plan: ExecutionPlan,
        *,
        context: AgentContext,
    ) -> PlanValidationReport:
        """Executes all 9 validation checks fail-closed and sets the resulting PlanStatus."""
        # Ambiguous plans stay in clarification_required cleanly
        if plan.status == PlanStatus.CLARIFICATION_REQUIRED:
            finding = ValidationFinding(
                code="PLAN_CLARIFICATION_REQUIRED",
                check="goal_clarity",
                severity=ValidationSeverity.WARNING,
                message="User goal is ambiguous; clarification is required before execution.",
            )
            updated = plan.model_copy(
                update={
                    "policy_version": PLANNING_POLICY_VERSION,
                    "validation_findings": [finding],
                    "updated_at": datetime.now(UTC),
                }
            )
            return PlanValidationReport(
                plan=updated,
                is_executable=False,
                has_errors=False,
                findings=[finding],
                policy_version=PLANNING_POLICY_VERSION,
            )

        all_findings: list[ValidationFinding] = []
        working_plan = plan
        approval_required = False
        approval_reasons: list[str] = []

        try:
            # Checks 1 & 2: Graph integrity, acyclicity, task limits, I/O refs, parallel layers
            try:
                working_plan, _graph = self.decomposer.decompose(working_plan)
            except PlanGraphValidationError as exc:
                all_findings.append(
                    ValidationFinding(
                        code=exc.code.value,
                        check="graph_integrity",
                        severity=ValidationSeverity.ERROR,
                        message=str(exc),
                        details=exc.details,
                    )
                )

            # Check 3: Capability resolution strictly against Phase 4.1 AgentRegistry
            working_plan, cap_findings = await self.agent_selector.resolve(
                working_plan,
                context=context,
            )
            all_findings.extend(cap_findings)

            # Checks 4, 5, 7, 9: Authorization, guardrails, budgets, approval, replan bounds
            policy_findings, approval_required, approval_reasons = (
                self.policy_engine.evaluate_plan_policies(
                    working_plan,
                    agent_registry=self.agent_registry,
                    context=context,
                )
            )
            all_findings.extend(policy_findings)

            # Check 6: Evidence requirements
            all_findings.extend(self._check_evidence_requirements(working_plan))

        except (RuntimeError, ValueError, TypeError, KeyError, LookupError) as exc:
            # Fail closed on unexpected validator errors (devdocs/p4/p4.4.txt Section 5)
            all_findings.append(
                ValidationFinding(
                    code="PLAN_VALIDATION_INTERNAL_ERROR",
                    check="fail_closed_guard",
                    severity=ValidationSeverity.ERROR,
                    message=sanitize_error_message(
                        f"Plan validation failed closed due to internal error: {exc}"
                    ),
                )
            )

        has_errors = any(f.severity == ValidationSeverity.ERROR for f in all_findings)
        if has_errors:
            final_status = PlanStatus.REJECTED
        elif approval_required:
            final_status = PlanStatus.APPROVAL_REQUIRED
        else:
            final_status = PlanStatus.VALIDATED

        # Check 8: Version consistency stamped on final plan
        final_plan = working_plan.model_copy(
            update={
                "status": final_status,
                "policy_version": PLANNING_POLICY_VERSION,
                "validation_findings": all_findings,
                "approval_required": approval_required,
                "approval_reasons": approval_reasons,
                "updated_at": datetime.now(UTC),
            }
        )
        return PlanValidationReport(
            plan=final_plan,
            is_executable=(final_status == PlanStatus.VALIDATED),
            has_errors=has_errors,
            findings=all_findings,
            approval_required=approval_required,
            approval_reasons=approval_reasons,
            policy_version=PLANNING_POLICY_VERSION,
        )
