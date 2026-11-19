"""KEEP Phase 4.6 — LangGraph Tool Calling Adapter.

Encapsulates tool definitions for LangGraph agents, ensuring that all tool
invocations emitted by graph nodes route strictly through KeepToolExecutor
with server-side trusted context and policy verification.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from backend.app.agents.tools.contracts import (
    ToolCallRequest,
    ToolCallResult,
    ToolContext,
)
from backend.app.agents.tools.executor import KeepToolExecutor
from backend.app.agents.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class LangGraphToolAdapter:
    """Bridges KEEP platform tools and executor to LangGraph graph workflows."""

    def __init__(
        self,
        executor: KeepToolExecutor,
        registry: ToolRegistry,
    ) -> None:
        self.executor = executor
        self.registry = registry

    def get_tool_definitions(
        self,
        roles: list[str] | None = None,
        allowed_tool_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Returns standard function-calling definitions for eligible tools."""
        return self.registry.export_schemas_for_agent(
            allowed_tool_ids=allowed_tool_ids,
            roles=roles,
        )

    async def invoke_tool_call(
        self,
        tool_id: str,
        arguments: dict[str, Any],
        context: ToolContext,
        *,
        call_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> ToolCallResult:
        """Executes a single model-proposed tool call through the trusted executor."""
        request = ToolCallRequest(
            tool_id=tool_id,
            arguments=arguments,
            call_id=call_id or f"call_{uuid.uuid4().hex[:12]}",
            idempotency_key=idempotency_key,
        )
        return await self.executor.invoke(request, context)

    def build_tool_node(
        self,
        context: ToolContext,
        allowed_tool_ids: list[str] | None = None,
    ) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
        """Creates a LangGraph-compatible node function that processes tool calls in graph state."""

        async def _tool_node(state: dict[str, Any]) -> dict[str, Any]:
            # Extract proposed tool calls from state
            proposed_calls = state.get("tool_calls", [])
            if not proposed_calls and "tool_id" in state:
                proposed_calls = [
                    {
                        "tool_id": state["tool_id"],
                        "arguments": state.get("arguments", {}),
                        "call_id": state.get("call_id"),
                    }
                ]

            results: list[dict[str, Any]] = []
            for call in proposed_calls:
                tid = call.get("tool_id", "")
                if allowed_tool_ids is not None and tid not in allowed_tool_ids:
                    dur_ms = 0
                    cid = call.get("call_id") or f"call_{uuid.uuid4().hex[:12]}"
                    res = ToolCallResult.denied(
                        call_id=cid,
                        tool_id=tid,
                        reason=f"Tool '{tid}' is not eligible for discovery by this agent.",
                        error_code="TOOL_PERMISSION_DENIED",
                        duration_ms=dur_ms,
                    )
                    results.append(res.model_dump())
                    continue

                call_res = await self.invoke_tool_call(
                    tool_id=tid,
                    arguments=call.get("arguments", {}),
                    context=context,
                    call_id=call.get("call_id"),
                )
                results.append(call_res.model_dump())

            # Return updated state with structured, bounded tool results
            new_state = dict(state)
            new_state["tool_results"] = results
            return new_state

        return _tool_node
