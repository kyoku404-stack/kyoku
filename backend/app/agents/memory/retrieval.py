"""KEEP Phase 4.7 — Memory Retrieval Service.

Executes authorized scoped memory searches against repository storage, applies
relevance ranking, recency weighting, and context budget enforcement.

Specification: devdocs/p4/p4.7.txt (Sections 4, 7)
Owner: Member 2 (Retrieval, Relevance & Consolidation)
"""

from __future__ import annotations

import datetime

from backend.app.agents.memory.contracts import (
    MemoryQuery,
    MemoryRetrievalResult,
    MemorySecurityContext,
)
from backend.app.agents.memory.relevance import MemoryRanker
from backend.app.agents.memory.repository import BaseMemoryRepository


class MemoryRetrievalService:
    """Coordinates retrieval, ranking, and token budgeting for agent tasks."""

    def __init__(
        self,
        repository: BaseMemoryRepository,
        ranker: MemoryRanker | None = None,
    ) -> None:
        self.repository = repository
        self.ranker = ranker or MemoryRanker()

    async def search(
        self,
        query: MemoryQuery,
        security_context: MemorySecurityContext,
        now: datetime.datetime | None = None,
    ) -> MemoryRetrievalResult:
        """Executes tenant-scoped retrieval, candidate filtering, ranking, and budgeting."""
        # 1. Retrieve candidates from repository with tenant and scope filtering
        candidates = await self.repository.search_scoped(
            tenant_id=security_context.tenant_id,
            principal_id=security_context.user_id,
            allowed_scopes=query.allowed_scopes,
            query=query.query,
            workflow_execution_id=query.workflow_execution_id or security_context.workflow_execution_id,
            agent_execution_id=query.agent_execution_id or security_context.agent_execution_id,
            memory_types=query.memory_types,
            limit=query.limit * 3,  # Overfetch candidates for ranking & budgeting
        )

        # 2. Defense-in-depth: exclude inactive/expired memories
        active_candidates = [m for m in candidates if m.is_active]

        # 3. Apply ranker with context token budget
        ranked_pairs = self.ranker.rank(
            query=query.query,
            memories=active_candidates,
            limit=query.limit,
            max_tokens=query.max_tokens,
            min_confidence=query.min_confidence,
            now=now,
        )

        selected_memories = [m for m, _ in ranked_pairs]
        total_tokens = sum(m.estimated_tokens for m in selected_memories)

        return MemoryRetrievalResult(
            memories=selected_memories,
            total_candidates=len(active_candidates),
            returned_count=len(selected_memories),
            total_estimated_tokens=total_tokens,
            query=query.query,
        )
