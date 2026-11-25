"""KEEP Phase 4.9 — Autonomous Progress Evaluator.

Evaluates intermediate task outcomes, collected evidence sufficiency, task
failures, and whether the workflow objective is satisfied, needs bounded
replanning, requires human review, or should terminate with caveats.

Owner: Member 2 (Adaptive Planning & Progress Evaluation)
Specification: devdocs/p4/p4.9.txt (Sections 3, 4, 5)
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.autonomy.contracts import (
    AutonomousStepRecord,
    AutonomyBudgetSnapshot,
    EvaluationResult,
)


class ProgressEvaluator:
    """Deterministic evidence & progress evaluator gating continuation and replanning."""

    def evaluate(
        self,
        *,
        objective: str,
        steps: list[AutonomousStepRecord],
        latest_outcome: dict[str, Any] | None = None,
        budget: AutonomyBudgetSnapshot | None = None,
    ) -> EvaluationResult:
        """Assesses objective satisfaction, evidence sufficiency, and recovery options."""
        outcome = latest_outcome or {}
        reasons: list[str] = []
        missing_evidence: list[str] = list(outcome.get("missing_evidence", []))

        succeeded_steps = [s for s in steps if s.status == "succeeded"]
        failed_steps = [s for s in steps if s.status == "failed"]
        pending_steps = [
            s for s in steps if s.status in ("pending", "running", "awaiting_approval")
        ]

        # Collect grounded evidence references across succeeded steps
        evidence_refs: list[str] = []
        for s in succeeded_steps:
            refs = s.outputs.get("evidence_refs", [])
            if isinstance(refs, list):
                evidence_refs.extend(str(r) for r in refs if r)

        explicit_gap = bool(outcome.get("evidence_gap")) or len(missing_evidence) > 0
        task_failed = outcome.get("status") == "failed" or any(
            s.error_code is not None and s.status == "failed" for s in failed_steps
        )
        human_review_flagged = bool(outcome.get("requires_human_review"))

        # Confidence grows monotonically with grounded evidence steps and drops on gaps/failures
        base_conf = min(0.95, 0.35 * len(succeeded_steps) + 0.1 * len(evidence_refs))
        if explicit_gap or task_failed:
            base_conf = max(0.2, base_conf - 0.3)

        if task_failed:
            reasons.append("One or more scheduled tasks failed and require recovery or replanning.")
        if explicit_gap:
            reasons.append(
                "Missing or insufficient evidence detected: "
                + (", ".join(missing_evidence) if missing_evidence else "evidence gap flagged.")
            )
            if not missing_evidence:
                missing_evidence.append("supporting_corroboration")

        has_synthesis_complete = (
            len(pending_steps) == 0
            and len(succeeded_steps) > 0
            and not explicit_gap
            and not task_failed
        )
        evidence_sufficient = len(evidence_refs) > 0 and not explicit_gap

        if has_synthesis_complete and evidence_sufficient:
            reasons.append(
                f"Objective '{objective[:80]}' satisfied with {len(evidence_refs)} grounded evidence references."
            )
            return EvaluationResult(
                objective_satisfied=True,
                evidence_sufficient=True,
                should_replan=False,
                requires_human_review=human_review_flagged,
                reasons=reasons,
                confidence=round(max(0.75, base_conf), 2),
                missing_evidence=[],
            )

        # Not yet finished or encountered gap/failure
        can_replan = budget is None or budget.replans_consumed < budget.max_replans
        should_replan = (explicit_gap or task_failed) and can_replan

        if len(pending_steps) == 0 and not has_synthesis_complete:
            # All current steps executed, but evidence gaps or failures remained
            if not can_replan:
                reasons.append(
                    "Replan budget exhausted; remaining evidence limitations will be documented."
                )
            return EvaluationResult(
                objective_satisfied=len(succeeded_steps) > 0
                and not task_failed
                and not explicit_gap
                and not should_replan,
                evidence_sufficient=evidence_sufficient,
                should_replan=should_replan,
                requires_human_review=human_review_flagged,
                reasons=reasons or ["Execution loop concluded."],
                confidence=round(base_conf, 2),
                missing_evidence=missing_evidence,
            )

        return EvaluationResult(
            objective_satisfied=False,
            evidence_sufficient=evidence_sufficient,
            should_replan=should_replan,
            requires_human_review=human_review_flagged,
            reasons=reasons or ["Intermediate step complete; continuing planned workflow."],
            confidence=round(base_conf, 2),
            missing_evidence=missing_evidence,
        )
