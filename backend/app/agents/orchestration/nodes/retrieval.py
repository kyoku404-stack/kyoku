"""KEEP Phase 4.3 — Knowledge Retrieval Graph Node."""

from __future__ import annotations

from typing import Any

from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import (
    AgentContractValidationError,
    AgentErrorCode,
    AgentLayerError,
)
from backend.app.agents.orchestration.nodes.runtime_bridge import RuntimeNodeInvoker
from backend.app.agents.orchestration.state import ValidatedRetrievalOutput
from backend.app.agents.runtime.lifecycle import ExecutionStatus
from pydantic import ValidationError


def make_retrieval_node(
    invoker: RuntimeNodeInvoker,
    *,
    agent_id: str = "knowledge_retrieval",
    node_name: str = "retrieve",
):
    """Creates a graph node that retrieves authorized tenant evidence via Phase 4.2 AgentRuntime."""

    async def retrieve_node(state: dict[str, Any], context: AgentContext) -> dict[str, Any]:
        record, result = await invoker.invoke_node_agent(
            workflow_execution_id=str(state["workflow_execution_id"]),
            node_name=node_name,
            agent_id=agent_id,
            goal=str(state["goal"]),
            input_data=dict(state.get("input") or {}),
            context=context,
            correlation_id=str(state["correlation_id"]),
            role="required",
        )

        if record.status != ExecutionStatus.SUCCEEDED or result.status != "succeeded":
            raise AgentLayerError(
                result.error_message or f"Required retrieval step '{node_name}' failed.",
                code=AgentErrorCode.WORKFLOW_STEP_FAILED,
                http_status=500,
                details={"node": node_name, "execution_id": record.execution_id},
            )

        try:
            validated = ValidatedRetrievalOutput.model_validate(
                {
                    **result.output,
                    "evidence": [ev.model_dump(mode="json") for ev in result.evidence],
                }
            )
        except ValidationError as exc:
            raise AgentContractValidationError(
                f"Retrieval node '{node_name}' returned invalid structured output: {exc}"
            ) from exc

        return {
            "research_result": validated.model_dump(mode="json"),
            "evidence": [ev.model_dump(mode="json") for ev in validated.evidence],
            "execution_ids": [record.execution_id],
            "warnings": list(result.warnings),
        }

    return retrieve_node
