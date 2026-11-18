"""KEEP Phase 4.3 — Predefined Multi-Agent Workflow Graphs & Registry Factory."""

from __future__ import annotations

from backend.app.agents.orchestration.graphs.knowledge_workflow import (
    KNOWLEDGE_ANALYSIS_DEFINITION,
    build_knowledge_workflow_graph,
)
from backend.app.agents.orchestration.graphs.parallel_analysis import (
    PARALLEL_PROJECT_REVIEW_DEFINITION,
    build_parallel_analysis_graph,
)
from backend.app.agents.orchestration.workflow_registry import WorkflowRegistry
from backend.app.agents.registry import AgentRegistry


def build_default_workflow_registry(
    agent_registry: AgentRegistry | None = None,
    *,
    validate_deps: bool = True,
) -> WorkflowRegistry:
    """Initializes KEEP's Phase 4.3 WorkflowRegistry with built-in approved workflows."""
    wf_registry = WorkflowRegistry(agent_registry=agent_registry)
    should_validate = validate_deps and (agent_registry is not None)
    wf_registry.register(
        KNOWLEDGE_ANALYSIS_DEFINITION,
        build_knowledge_workflow_graph,
        validate_deps=should_validate,
    )
    wf_registry.register(
        PARALLEL_PROJECT_REVIEW_DEFINITION,
        build_parallel_analysis_graph,
        validate_deps=should_validate,
    )
    return wf_registry


__all__ = [
    "KNOWLEDGE_ANALYSIS_DEFINITION",
    "PARALLEL_PROJECT_REVIEW_DEFINITION",
    "build_default_workflow_registry",
    "build_knowledge_workflow_graph",
    "build_parallel_analysis_graph",
]
