"""KEEP Phase 4.3 — Parallel Project Review (Decisions + Risks) Workflow Graph.

Topology:
    START -> retrieve -> route_after_retrieval
                             ├── "parallel_branches" -> [extract_decisions, analyze_risks] -> aggregate -> END
                             └── "no_evidence"       -> no_evidence                        -> aggregate -> END

Demonstrates concurrent multi-agent fan-out/fan-in with reducer-safe state merging
and explicit optional-branch partial-success policy (`analyze_risks` is optional so
decision extraction results are preserved with a warning if risk analysis fails).

Owner: Member 2 (Graph State, Routing & Workflow Execution)
Specification: devdocs/p4/p4.3.txt (Sections 7, 9)
"""

from __future__ import annotations

from typing import Any, Literal

from backend.app.agents.adapters.langgraph_orchestrator import (
    END,
    START,
    CompiledKeepWorkflowGraph,
    KeepStateGraph,
)
from backend.app.agents.orchestration.nodes import (
    RuntimeNodeInvoker,
    make_aggregation_node,
    make_no_evidence_node,
    make_parallel_branch_node,
    make_retrieval_node,
)
from backend.app.agents.orchestration.workflow_contracts import WorkflowDefinition

PARALLEL_PROJECT_REVIEW_DEFINITION = WorkflowDefinition(
    workflow_id="parallel_project_review",
    name="Parallel Project Decisions & Risk Review",
    version="1.0.0",
    description=(
        "Retrieves authorized project documents then executes decision extraction (required) "
        "and risk analysis (optional) concurrently, converging into a unified evidence-backed report."
    ),
    task_type="project_review",
    required_capabilities=["knowledge.search", "knowledge.decisions", "knowledge.risks"],
    required_agents=["knowledge_retrieval", "decision_extractor"],
    optional_agents=["risk_analyzer"],
    allow_partial_success=True,
    default_timeout_seconds=90.0,
    max_timeout_seconds=300.0,
    max_agent_invocations=8,
    tags=["phase-4.3", "parallel", "conditional", "partial-success"],
)


def route_to_parallel_or_fallback(
    state: dict[str, Any],
) -> Literal["parallel_branches", "no_evidence"]:
    evidence = state.get("evidence") or state.get("research_result", {}).get("evidence") or []
    return "parallel_branches" if len(evidence) > 0 else "no_evidence"


def build_parallel_analysis_graph(
    *,
    runtime: Any,
    definition: WorkflowDefinition = PARALLEL_PROJECT_REVIEW_DEFINITION,
    on_step: Any | None = None,
    workflow_policy: Any | None = None,
) -> CompiledKeepWorkflowGraph:
    """Compiles the parallel fan-out/fan-in project review workflow bound to Phase 4.2 AgentRuntime."""
    invoker = RuntimeNodeInvoker(
        runtime=runtime,
        definition=definition,
        on_step=on_step,
        workflow_policy=workflow_policy,
    )

    graph = KeepStateGraph()
    graph.add_node("retrieve", make_retrieval_node(invoker))
    graph.add_node(
        "extract_decisions",
        make_parallel_branch_node(
            invoker,
            branch_key="decisions",
            agent_id="decision_extractor",
            node_name="extract_decisions",
            role="required",
        ),
    )
    graph.add_node(
        "analyze_risks",
        make_parallel_branch_node(
            invoker,
            branch_key="risks",
            agent_id="risk_analyzer",
            node_name="analyze_risks",
            role="optional",
        ),
    )
    graph.add_node("no_evidence", make_no_evidence_node())
    graph.add_node("aggregate", make_aggregation_node(definition))

    graph.add_edge(START, "retrieve")
    graph.add_conditional_edges(
        "retrieve",
        route_to_parallel_or_fallback,
        {
            "parallel_branches": ["extract_decisions", "analyze_risks"],
            "no_evidence": "no_evidence",
        },
    )
    graph.add_edge("extract_decisions", "aggregate")
    graph.add_edge("analyze_risks", "aggregate")
    graph.add_edge("no_evidence", "aggregate")
    graph.add_edge("aggregate", END)
    return graph.compile()
