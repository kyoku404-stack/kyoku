"""KEEP Phase 4.3 — Analysis & Parallel Specialist Branch Graph Nodes."""

from __future__ import annotations

from typing import Any

from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import (
    AgentContractValidationError,
    AgentErrorCode,
    AgentLayerError,
)
from backend.app.agents.orchestration.nodes.runtime_bridge import RuntimeNodeInvoker
from backend.app.agents.orchestration.state import (
    ValidatedAnalysisOutput,
    ValidatedBranchOutput,
)
from backend.app.agents.orchestration.workflow_contracts import WorkflowStepRole
from backend.app.agents.runtime.lifecycle import ExecutionStatus
from pydantic import ValidationError


def make_analysis_node(
    invoker: RuntimeNodeInvoker,
    *,
    agent_id: str = "knowledge_analysis",
    node_name: str = "analyze",
    role: WorkflowStepRole = "required",
):
    """Creates a sequential analysis node consuming validated retrieval output."""

    async def analyze_node(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        research = dict(state.get("research_result") or {})
        base_input = dict(state.get("input") or {})
        node_input = {
            **base_input,
            "topic": research.get("topic", base_input.get("project_id", "general")),
            "evidence": list(state.get("evidence") or []),
            "retrieval_summary": research.get("summary", ""),
        }

        record, result = await invoker.invoke_node_agent(
            workflow_execution_id=str(state["workflow_execution_id"]),
            node_name=node_name,
            agent_id=agent_id,
            goal=str(state["goal"]),
            input_data=node_input,
            context=context,
            correlation_id=str(state["correlation_id"]),
            role=role,
        )

        if record.status != ExecutionStatus.SUCCEEDED or result.status != "succeeded":
            if role == "optional":
                return {
                    "execution_ids": [record.execution_id],
                    "failed_optional_steps": [node_name],
                    "warnings": [
                        (
                            f"Optional step '{node_name}' ({agent_id}) failed: "
                            f"{result.error_message or record.status.value}"
                        )
                    ],
                }
            raise AgentLayerError(
                result.error_message or f"Required analysis step '{node_name}' failed.",
                code=AgentErrorCode.WORKFLOW_STEP_FAILED,
                http_status=500,
                details={"node": node_name, "execution_id": record.execution_id},
            )

        try:
            validated = ValidatedAnalysisOutput.model_validate(result.output)
        except ValidationError as exc:
            raise AgentContractValidationError(
                f"Analysis node '{node_name}' returned invalid structured output: {exc}"
            ) from exc

        return {
            "analysis_result": validated.model_dump(mode="json"),
            "evidence": [ev.model_dump(mode="json") for ev in result.evidence],
            "execution_ids": [record.execution_id],
            "warnings": list(result.warnings),
        }

    return analyze_node


def make_parallel_branch_node(
    invoker: RuntimeNodeInvoker,
    *,
    branch_key: str,
    agent_id: str,
    node_name: str,
    role: WorkflowStepRole = "required",
):
    """Creates an independent parallel specialist node writing safely into `branch_results[branch_key]`."""

    async def branch_node(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        research = dict(state.get("research_result") or {})
        base_input = dict(state.get("input") or {})
        node_input = {
            **base_input,
            "topic": research.get("topic", base_input.get("project_id", "general")),
            "evidence": list(state.get("evidence") or []),
            "retrieval_summary": research.get("summary", ""),
        }

        record, result = await invoker.invoke_node_agent(
            workflow_execution_id=str(state["workflow_execution_id"]),
            node_name=node_name,
            agent_id=agent_id,
            goal=str(state["goal"]),
            input_data=node_input,
            context=context,
            correlation_id=str(state["correlation_id"]),
            role=role,
        )

        if record.status != ExecutionStatus.SUCCEEDED or result.status != "succeeded":
            if role == "optional":
                return {
                    "execution_ids": [record.execution_id],
                    "failed_optional_steps": [node_name],
                    "warnings": [
                        (
                            f"Optional parallel branch '{node_name}' ({agent_id}) failed: "
                            f"{result.error_message or record.status.value}"
                        )
                    ],
                }
            raise AgentLayerError(
                result.error_message or f"Required parallel branch '{node_name}' failed.",
                code=AgentErrorCode.WORKFLOW_STEP_FAILED,
                http_status=500,
                details={"node": node_name, "execution_id": record.execution_id},
            )

        try:
            validated = ValidatedBranchOutput.model_validate(
                {"branch_name": branch_key, **result.output}
            )
        except ValidationError as exc:
            raise AgentContractValidationError(
                f"Parallel branch '{node_name}' returned invalid structured output: {exc}"
            ) from exc

        return {
            "branch_results": {branch_key: validated.model_dump(mode="json")},
            "evidence": [ev.model_dump(mode="json") for ev in result.evidence],
            "execution_ids": [record.execution_id],
            "warnings": list(result.warnings),
        }

    return branch_node
