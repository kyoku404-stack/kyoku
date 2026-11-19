"""KEEP Phase 4.7 — LangGraph & Agent Memory Adapter.

Provides declarative graph nodes for loading relevant memories and proposing
candidate memories within LangGraph workflows and Research Agents.

Specification: devdocs/p4/p4.7.txt (Sections 4, 9)
Owner: Member 4 (LangGraph Integration, API, Persistence & QA)
"""

from __future__ import annotations

import logging
from typing import Any

from backend.app.agents.memory.contracts import (
    MemoryQuery,
    MemorySecurityContext,
    MemoryWriteRequest,
)
from backend.app.agents.memory.service import MemoryService

logger = logging.getLogger(__name__)


def _extract_security_context(state: dict[str, Any]) -> MemorySecurityContext:
    """Extracts or reconstructs trusted MemorySecurityContext from graph state."""
    raw_ctx = state.get("security_context")
    if isinstance(raw_ctx, MemorySecurityContext):
        return raw_ctx
    if isinstance(raw_ctx, dict):
        return MemorySecurityContext(**raw_ctx)

    tenant_id = state.get("tenant_id") or "tenant_default"
    user_id = state.get("user_id") or "user_system"
    return MemorySecurityContext(
        tenant_id=tenant_id,
        user_id=user_id,
        workflow_execution_id=state.get("workflow_execution_id"),
        agent_execution_id=state.get("agent_execution_id"),
        correlation_id=state.get("correlation_id"),
    )


async def load_memory_node(
    state: dict[str, Any],
    memory_service: MemoryService,
) -> dict[str, Any]:
    """LangGraph node: loads top-ranked relevant memories within context budget."""
    security_context = _extract_security_context(state)
    query_text = state.get("memory_query") or state.get("research_topic") or state.get("query") or ""

    if not query_text:
        return {"relevant_memories": []}

    allowed_scopes = state.get("allowed_memory_scopes") or ["user", "organization"]
    max_tokens = state.get("memory_token_budget", 1000)

    query = MemoryQuery(
        query=query_text,
        allowed_scopes=allowed_scopes,
        limit=state.get("memory_limit", 5),
        max_tokens=max_tokens,
        workflow_execution_id=state.get("workflow_execution_id"),
        agent_execution_id=state.get("agent_execution_id"),
    )

    try:
        retrieval = await memory_service.retrieve(query, security_context)
        return {
            "relevant_memories": [m.model_dump() for m in retrieval.memories],
            "memory_tokens_used": retrieval.total_estimated_tokens,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Memory retrieval in LangGraph node failed safely: %s", exc)
        return {"relevant_memories": [], "memory_error": str(exc)}


async def propose_memory_node(
    state: dict[str, Any],
    memory_service: MemoryService,
) -> dict[str, Any]:
    """LangGraph node: submits candidate memory proposal for policy governance."""
    proposal_data = state.get("memory_proposal")
    if not proposal_data:
        return {}

    security_context = _extract_security_context(state)

    if isinstance(proposal_data, dict):
        request = MemoryWriteRequest(**proposal_data)
    elif isinstance(proposal_data, MemoryWriteRequest):
        request = proposal_data
    else:
        return {}

    try:
        saved_proposal = await memory_service.propose(request, security_context)
        return {
            "memory_proposal_id": saved_proposal.proposal_id,
            "memory_proposal_status": saved_proposal.status,
            "memory_approved_id": saved_proposal.approved_memory_id,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Memory proposal in LangGraph node failed safely: %s", exc)
        return {"memory_proposal_error": str(exc)}
