"""KEEP Phase 4.4 — Goal Understanding & Ambiguity Detection Module.

Normalizes natural-language user requests into structured `GoalSpec` contracts,
extracting expected outputs, constraints, success criteria, evidence requirements,
and clarification questions for underspecified requests.

Owner: Member 1 (Goal Understanding & Plan Generation)
Specification: devdocs/p4/p4.4.txt (Sections 1, 3, 4)
"""

from __future__ import annotations

import re

from backend.app.agents.planning.contracts import GoalSpec, PlanCreateRequest

_AMBIGUOUS_SHORT_TERMS = frozenset(
    {
        "help",
        "analyze",
        "check",
        "do it",
        "fix it",
        "report",
        "summary",
        "summarize",
        "review",
        "status",
        "compare",
        "something",
    }
)

_TIMEFRAME_PATTERN = re.compile(
    r"(?i)\b(last\s+\w+\s+(?:quarters?|months?|weeks?|days?|years?)|q[1-4]\s*\d{0,4}|20\d{2})\b"
)


class GoalParser:
    """Deterministic structured goal parser with ambiguity detection & constraint extraction."""

    async def parse(self, request: PlanCreateRequest) -> GoalSpec:
        """Converts a caller PlanCreateRequest into a validated structured GoalSpec."""
        raw_goal = request.goal.strip()
        lower_goal = raw_goal.lower()
        words = [w for w in re.split(r"\s+", raw_goal) if w]

        # Detect underspecified / ambiguous goals that need clarification before planning
        is_ambiguous = False
        clarification_questions: list[str] = []

        if len(words) <= 2 or lower_goal.rstrip(".?!") in _AMBIGUOUS_SHORT_TERMS:
            is_ambiguous = True
            clarification_questions.append(
                "Which specific project, department, or document scope should KEEP analyze?"
            )
            clarification_questions.append(
                "What concrete output format do you expect (e.g., decision summary, risk list, or comparison report)?"
            )
        elif any(phrase in lower_goal for phrase in ("that thing", "stuff from earlier", "tbd")):
            is_ambiguous = True
            clarification_questions.append(
                "Please clarify the target project or topic name instead of an ambiguous reference."
            )

        # Infer expected output if caller omitted one
        if request.expected_output and request.expected_output.strip():
            expected_output = request.expected_output.strip()
        elif "compare" in lower_goal and ("recommend" in lower_goal or "action" in lower_goal):
            expected_output = (
                "Structured multi-period comparison with recurring themes and evidence-backed recommendations."
            )
        elif "decision" in lower_goal and "risk" in lower_goal:
            expected_output = (
                "Consolidated report listing approved decisions, owners, and prioritized operational risks."
            )
        elif "risk" in lower_goal:
            expected_output = "Prioritized risk register with mitigations and source citations."
        elif "decision" in lower_goal:
            expected_output = "Structured decision log with accountable owners and citations."
        else:
            expected_output = "Evidence-backed structured synthesis addressing the requested goal."

        # Merge caller constraints + inferred scope/timeframe constraints
        constraints = [c.strip() for c in request.constraints if c.strip()]
        if not any("authorized" in c.lower() for c in constraints):
            constraints.append("Use tenant-authorized internal KEEP sources only.")

        timeframe_matches = _TIMEFRAME_PATTERN.findall(raw_goal)
        for tf in timeframe_matches:
            note = f"Scope timeframe: {tf}"
            if note not in constraints:
                constraints.append(note)

        # Determine whether evidence references are required
        requires_evidence = True
        if any("no evidence required" in c.lower() for c in constraints):
            requires_evidence = False

        # Build verifiable success criteria
        success_criteria = [c.strip() for c in request.success_criteria if c.strip()]
        if not success_criteria:
            success_criteria.append("All tasks execute strictly within caller RBAC and tenant boundaries.")
            if requires_evidence:
                success_criteria.append("Final findings include grounded EvidenceReference citations.")
            if "recommend" in lower_goal:
                success_criteria.append("Recommendations directly trace back to analyzed evidence.")

        project_scope = str(
            request.input.get("project_id") or request.input.get("topic") or "tenant_authorized_knowledge"
        )

        return GoalSpec(
            goal=raw_goal,
            expected_output=expected_output,
            constraints=constraints,
            success_criteria=success_criteria,
            scope=project_scope,
            requires_evidence=requires_evidence,
            is_ambiguous=is_ambiguous,
            clarification_questions=clarification_questions,
        )
