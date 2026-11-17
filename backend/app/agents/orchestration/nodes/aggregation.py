"""KEEP Phase 4.3 — Conditional No-Evidence & Final Aggregation Graph Nodes."""

from __future__ import annotations

from typing import Any

from backend.app.agents.contracts import AgentContext
from backend.app.agents.orchestration.workflow_contracts import (
    WorkflowDefinition,
    WorkflowStatus,
)


def make_no_evidence_node():
    """Produces a clearly qualified limited-evidence response instead of hallucinating."""

    async def no_evidence_node(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        research = dict(state.get("research_result") or {})
        topic = research.get("topic") or "requested scope"
        return {
            "workflow_status": WorkflowStatus.SUCCEEDED.value,
            "final_result": {
                "answer_type": "limited_evidence",
                "summary": (
                    f"No authorized enterprise evidence was found for '{topic}'. "
                    "Analysis was skipped to prevent unsupported conclusions."
                ),
                "goal": state.get("goal"),
                "evidence_found": False,
                "tenant_id": context.tenant_id,
            },
            "warnings": [
                "Insufficient authorized evidence: workflow routed to limited-evidence fallback."
            ],
        }

    return no_evidence_node


def make_aggregation_node(definition: WorkflowDefinition):
    """Combines sequential or parallel validated outputs and resolves explicit final workflow status."""

    async def aggregate_node(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        # If no_evidence path already produced a final qualified result, preserve it cleanly
        if state.get("final_result") and state["final_result"].get("answer_type") == "limited_evidence":
            return {"workflow_status": WorkflowStatus.SUCCEEDED.value}

        analysis = dict(state.get("analysis_result") or {})
        branches = dict(state.get("branch_results") or {})
        failed_optional = list(state.get("failed_optional_steps") or [])
        evidence = list(state.get("evidence") or [])

        if failed_optional and definition.allow_partial_success:
            final_status = WorkflowStatus.PARTIALLY_SUCCEEDED
        elif failed_optional and not definition.allow_partial_success:
            final_status = WorkflowStatus.FAILED
        else:
            final_status = WorkflowStatus.SUCCEEDED

        if branches:
            summaries = [
                f"{key}: {val.get('summary', '')}" for key, val in sorted(branches.items())
            ]
            combined_summary = " | ".join(summaries) if summaries else "Parallel workflow completed."
            final_payload: dict[str, Any] = {
                "answer_type": "parallel_synthesis",
                "summary": combined_summary,
                "goal": state.get("goal"),
                "branches": branches,
                "completed_branches": sorted(branches.keys()),
                "failed_optional_steps": failed_optional,
                "evidence_count": len(evidence),
                "evidence_found": len(evidence) > 0,
                "tenant_id": context.tenant_id,
            }
        else:
            final_payload = {
                "answer_type": "sequential_synthesis",
                "summary": analysis.get("summary") or "Sequential workflow completed.",
                "goal": state.get("goal"),
                "key_findings": analysis.get("key_findings", []),
                "confidence": analysis.get("confidence", 0.0),
                "evidence_count": len(evidence),
                "evidence_found": len(evidence) > 0,
                "tenant_id": context.tenant_id,
            }

        return {
            "workflow_status": final_status.value,
            "final_result": final_payload,
        }

    return aggregate_node
