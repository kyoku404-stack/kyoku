"""Phase 4.3 Member 2 Unit Tests — Sequential, Conditional & Parallel Graph Orchestration."""

from __future__ import annotations

from typing import Any

import pytest

from backend.app.agents.contracts import AgentContext, AgentRequest, AgentResult
from backend.app.agents.errors import AgentContractValidationError
from backend.app.agents.metadata import AgentCapability, AgentMetadata
from backend.app.agents.orchestration.graphs import (
    KNOWLEDGE_ANALYSIS_DEFINITION,
    PARALLEL_PROJECT_REVIEW_DEFINITION,
    build_default_workflow_registry,
    build_knowledge_workflow_graph,
    build_parallel_analysis_graph,
)
from backend.app.agents.orchestration.specialist_agents import (
    DecisionExtractionAgent,
    KnowledgeAnalysisAgent,
    KnowledgeRetrievalAgent,
    RiskAnalysisAgent,
)
from backend.app.agents.orchestration.state import (
    merge_workflow_state,
    sanitize_checkpoint_state,
)
from backend.app.agents.orchestration.workflow_contracts import (
    WorkflowStatus,
    WorkflowStepLink,
)
from backend.app.agents.persistence.execution_repository import InMemoryExecutionRepository
from backend.app.agents.registry import AgentRegistry
from backend.app.agents.runtime.executor import AgentRuntime
from backend.app.agents.runtime.policies import KeepExecutionPolicy


def _make_context(tenant_id: str = "org-alpha") -> AgentContext:
    return AgentContext(
        user_id="user-m2",
        tenant_id=tenant_id,
        roles=["Member"],
        permissions=["agent.view", "agent.invoke", "document.read", "ai.search"],
        correlation_id="corr-phase43-m2",
        trusted=True,
    )


def _build_real_phase42_runtime() -> tuple[AgentRegistry, InMemoryExecutionRepository, AgentRuntime]:
    agent_registry = AgentRegistry()
    agent_registry.register(KnowledgeRetrievalAgent())
    agent_registry.register(KnowledgeAnalysisAgent())
    agent_registry.register(DecisionExtractionAgent())
    agent_registry.register(RiskAnalysisAgent())

    exec_repo = InMemoryExecutionRepository()
    runtime = AgentRuntime(
        registry=agent_registry,
        repository=exec_repo,
        policy=KeepExecutionPolicy(),
    )
    return agent_registry, exec_repo, runtime


class _BrokenRetrievalAgent:
    """Returns invalid retrieval payload missing required `query` field to verify contract gate."""

    def __init__(self) -> None:
        self._meta = AgentMetadata(
            agent_id="knowledge_retrieval",
            name="Broken Retrieval",
            version="1.0.0",
            description="Returns malformed output",
            capabilities=[AgentCapability(name="knowledge.search", description="Search", access="read")],
        )

    @property
    def metadata(self) -> AgentMetadata:
        return self._meta

    async def invoke(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        return AgentResult(status="succeeded", output={"bad_field": 123}, evidence=[])


class TestPhase43Graphs:
    @pytest.mark.asyncio
    async def test_sequential_knowledge_workflow_invokes_phase42_runtime(self) -> None:
        agent_registry, exec_repo, runtime = _build_real_phase42_runtime()
        wf_registry = build_default_workflow_registry(agent_registry)
        assert wf_registry.count() == 2

        recorded_steps: list[WorkflowStepLink] = []
        checkpoints: list[tuple[str, int]] = []

        async def _on_step(step: WorkflowStepLink) -> None:
            recorded_steps.append(step)

        async def _on_chk(step_name: str, step_number: int, state: dict[str, Any]) -> None:
            checkpoints.append((step_name, step_number))

        graph = build_knowledge_workflow_graph(
            runtime=runtime,
            definition=KNOWLEDGE_ANALYSIS_DEFINITION,
            on_step=_on_step,
        )
        ctx = _make_context()
        final_state = await graph.arun(
            {
                "workflow_execution_id": "wfexec_seq_01",
                "correlation_id": ctx.correlation_id,
                "goal": "Summarize architecture decisions for project-123",
                "input": {"project_id": "project-123"},
                "execution_ids": [],
                "warnings": [],
                "evidence": [],
            },
            context=ctx,
            checkpoint_callback=_on_chk,
        )

        assert final_state["workflow_status"] == WorkflowStatus.SUCCEEDED.value
        assert final_state["final_result"]["answer_type"] == "sequential_synthesis"
        assert final_state["final_result"]["evidence_found"] is True
        assert len(final_state["execution_ids"]) == 2
        assert [s.agent_id for s in recorded_steps] == ["knowledge_retrieval", "knowledge_analysis"]
        assert len(checkpoints) == 3  # retrieve, analyze, aggregate

        # Confirm BOTH executions were durably recorded inside Phase 4.2 ExecutionRepository
        stored_execs = await exec_repo.list_executions(tenant_id=ctx.tenant_id)
        assert len(stored_execs) == 2
        assert all(e.correlation_id == ctx.correlation_id for e in stored_execs)

    @pytest.mark.asyncio
    async def test_conditional_routing_no_evidence_skips_analysis(self) -> None:
        _, exec_repo, runtime = _build_real_phase42_runtime()
        recorded_steps: list[WorkflowStepLink] = []

        async def _on_step(step: WorkflowStepLink) -> None:
            recorded_steps.append(step)

        graph = build_knowledge_workflow_graph(runtime=runtime, on_step=_on_step)
        ctx = _make_context()
        final_state = await graph.arun(
            {
                "workflow_execution_id": "wfexec_noev_01",
                "correlation_id": ctx.correlation_id,
                "goal": "Find documents for nonexistent topic",
                "input": {"project_id": "empty", "force_no_evidence": True},
                "execution_ids": [],
                "warnings": [],
                "evidence": [],
            },
            context=ctx,
        )

        assert final_state["workflow_status"] == WorkflowStatus.SUCCEEDED.value
        assert final_state["final_result"]["answer_type"] == "limited_evidence"
        assert final_state["final_result"]["evidence_found"] is False
        assert len(recorded_steps) == 1
        assert recorded_steps[0].agent_id == "knowledge_retrieval"
        assert any("limited-evidence" in w.lower() for w in final_state["warnings"])
        assert len(await exec_repo.list_executions(tenant_id=ctx.tenant_id)) == 1

    @pytest.mark.asyncio
    async def test_parallel_fan_out_and_safe_reducer_aggregation(self) -> None:
        _, exec_repo, runtime = _build_real_phase42_runtime()
        recorded_steps: list[WorkflowStepLink] = []

        async def _on_step(step: WorkflowStepLink) -> None:
            recorded_steps.append(step)

        graph = build_parallel_analysis_graph(
            runtime=runtime,
            definition=PARALLEL_PROJECT_REVIEW_DEFINITION,
            on_step=_on_step,
        )
        ctx = _make_context()
        final_state = await graph.arun(
            {
                "workflow_execution_id": "wfexec_par_01",
                "correlation_id": ctx.correlation_id,
                "goal": "Find project decisions and summarize outstanding risks",
                "input": {"project_id": "project-456"},
                "execution_ids": [],
                "warnings": [],
                "evidence": [],
                "branch_results": {},
            },
            context=ctx,
        )

        assert final_state["workflow_status"] == WorkflowStatus.SUCCEEDED.value
        assert final_state["final_result"]["answer_type"] == "parallel_synthesis"
        assert set(final_state["final_result"]["completed_branches"]) == {"decisions", "risks"}
        assert "decisions" in final_state["branch_results"]
        assert "risks" in final_state["branch_results"]
        assert len(final_state["execution_ids"]) == 3
        assert len(await exec_repo.list_executions(tenant_id=ctx.tenant_id)) == 3

    @pytest.mark.asyncio
    async def test_parallel_optional_branch_failure_yields_partial_success(self) -> None:
        _, _, runtime = _build_real_phase42_runtime()
        graph = build_parallel_analysis_graph(
            runtime=runtime,
            definition=PARALLEL_PROJECT_REVIEW_DEFINITION,
        )
        ctx = _make_context()
        final_state = await graph.arun(
            {
                "workflow_execution_id": "wfexec_partial_01",
                "correlation_id": ctx.correlation_id,
                "goal": "Extract decisions even if risk branch fails",
                "input": {"project_id": "project-789", "force_fail_risks": True},
                "execution_ids": [],
                "warnings": [],
                "evidence": [],
                "branch_results": {},
            },
            context=ctx,
        )

        assert final_state["workflow_status"] == WorkflowStatus.PARTIALLY_SUCCEEDED.value
        assert final_state["final_result"]["completed_branches"] == ["decisions"]
        assert final_state["failed_optional_steps"] == ["analyze_risks"]
        assert any("analyze_risks" in w for w in final_state["warnings"])

    @pytest.mark.asyncio
    async def test_invalid_intermediate_output_rejected_before_downstream_handoff(self) -> None:
        bad_registry = AgentRegistry()
        bad_registry.register(_BrokenRetrievalAgent())
        bad_registry.register(KnowledgeAnalysisAgent())
        runtime = AgentRuntime(
            registry=bad_registry,
            repository=InMemoryExecutionRepository(),
            policy=KeepExecutionPolicy(),
        )
        graph = build_knowledge_workflow_graph(runtime=runtime)
        ctx = _make_context()

        with pytest.raises(AgentContractValidationError):
            await graph.arun(
                {
                    "workflow_execution_id": "wfexec_bad_out",
                    "correlation_id": ctx.correlation_id,
                    "goal": "Test malformed output",
                    "input": {},
                },
                context=ctx,
            )

    def test_state_reducers_and_checkpoint_secret_sanitization(self) -> None:
        s1 = merge_workflow_state(
            {"execution_ids": ["e1"], "branch_results": {"a": {"v": 1}}},
            {"execution_ids": ["e1", "e2"], "branch_results": {"b": {"v": 2}}},
        )
        assert s1["execution_ids"] == ["e1", "e2"]
        assert s1["branch_results"] == {"a": {"v": 1}, "b": {"v": 2}}

        sanitized = sanitize_checkpoint_state(
            {
                "goal": "Analyze Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.aaaaaaaaaaa.bbbbbbbbbbb",
                "api_key": "sk-supersecret1234567890",
                "nested": {"password": "hunter2", "safe": "ok"},
            }
        )
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["nested"]["password"] == "[REDACTED]"
        assert sanitized["nested"]["safe"] == "ok"
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized["goal"]
