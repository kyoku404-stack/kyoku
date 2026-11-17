"""KEEP Phase 4.3 — Sequential & Conditional Knowledge Analysis Workflow Graph.

Topology:
    START -> retrieve -> route_after_retrieval
                             ├── "analyze"     -> analyze     -> aggregate -> END
                             └── "no_evidence" -> no_evidence -> aggregate -> END

Owner: Member 2 (Graph State, Routing & Workflow Execution)
Specification: devdocs/p4/p4.3.txt (Section 6)
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
    make_analysis_node,
    make_no_evidence_node,
    make_retrieval_node,
)
from backend.app.agents.orchestration.workflow_contracts import WorkflowDefinition

KNOWLEDGE_ANALYSIS_DEFINITION = WorkflowDefinition(
    workflow_id="knowledge_analysis",
    name="Knowledge Retrieval & Evidence-Backed Analysis",
    version="1.0.0",
    description=(
        "Sequential multi-agent workflow retrieving tenant-authorized documents, routing "
        "conditionally when evidence is absent, and synthesizing validated findings."
    ),
    task_type="knowledge_analysis",
    required_capabilities=["knowledge.search", "knowledge.analyze"],
    required_agents=["knowledge_retrieval", "knowledge_analysis"],
    optional_agents=[],
    allow_partial_success=False,
    default_timeout_seconds=60.0,
    max_timeout_seconds=300.0,
    max_agent_invocations=6,
    tags=["phase-4.3", "sequential", "conditional"],
)


def route_after_retrieval(state: dict[str, Any]) -> Literal["analyze", "no_evidence"]:
    """Structured conditional router checking validated retrieval evidence."""
    evidence = state.get("evidence") or state.get("research_result", {}).get("evidence") or []
    return "analyze" if len(evidence) > 0 else "no_evidence"


def build_knowledge_workflow_graph(
    *,
    runtime: Any,
    definition: WorkflowDefinition = KNOWLEDGE_ANALYSIS_DEFINITION,
    on_step: Any | None = None,
    workflow_policy: Any | None = None,
) -> CompiledKeepWorkflowGraph:
    """Compiles the sequential + conditional knowledge analysis graph bound to Phase 4.2 AgentRuntime."""
    invoker = RuntimeNodeInvoker(
        runtime=runtime,
        definition=definition,
        on_step=on_step,
        workflow_policy=workflow_policy,
    )

    graph = KeepStateGraph()
    graph.add_node("retrieve", make_retrieval_node(invoker))
    graph.add_node("analyze", make_analysis_node(invoker, role="required"))
    graph.add_node("no_evidence", make_no_evidence_node())
    graph.add_node("aggregate", make_aggregation_node(definition))

    graph.add_edge(START, "retrieve")
    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieval,
        {
            "analyze": "analyze",
            "no_evidence": "no_evidence",
        },
    )
    graph.add_edge("analyze", "aggregate")
    graph.add_edge("no_evidence", "aggregate")
    graph.add_edge("aggregate", END)
    return graph.compile()
