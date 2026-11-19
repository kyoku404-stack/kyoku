"""KEEP Phase 4.7 — Unit Tests for Member 2 Memory Retrieval, Ranking & Consolidation.

Validates relevance scoring, recency decay, token budgeting, exact and near deduplication,
conflict detection, and version superseding.
"""

from __future__ import annotations

import datetime

import pytest

from backend.app.agents.errors import MemoryConflictDetectedError
from backend.app.agents.memory.consolidation import MemoryConsolidationEngine
from backend.app.agents.memory.contracts import (
    MemoryProposal,
    MemoryQuery,
    MemoryRecord,
    MemorySecurityContext,
)
from backend.app.agents.memory.relevance import MemoryRanker
from backend.app.agents.memory.repository import InMemoryMemoryRepository
from backend.app.agents.memory.retrieval import MemoryRetrievalService


class TestMemoryRelevanceAndRanking:
    """Validates lexical similarity, recency decay, and context token budgeting."""

    def test_lexical_similarity_and_ranking_order(self) -> None:
        ranker = MemoryRanker()
        now = datetime.datetime.now(datetime.UTC)

        m1 = MemoryRecord(
            memory_id="mem_target",
            scope="user",
            owner_id="user_alice",
            tenant_id="tenant_1",
            content="User prefers markdown bulleted reports for quarterly financials",
            created_at=now,
            updated_at=now,
        )
        m2 = MemoryRecord(
            memory_id="mem_irrelevant",
            scope="user",
            owner_id="user_alice",
            tenant_id="tenant_1",
            content="Database connection timeout is 30 seconds for postgres cluster",
            created_at=now,
            updated_at=now,
        )

        query = "quarterly reports markdown"
        scored = ranker.rank(query, [m1, m2], limit=5, max_tokens=1000)

        assert len(scored) == 2
        # m1 must score higher than m2 for this query
        assert scored[0][0].memory_id == "mem_target"
        assert scored[0][1] > scored[1][1]

    def test_recency_decay_weighting(self) -> None:
        ranker = MemoryRanker(half_life_days=30.0)
        now = datetime.datetime.now(datetime.UTC)
        two_months_ago = now - datetime.timedelta(days=60)

        recent_mem = MemoryRecord(
            memory_id="mem_recent",
            scope="organization",
            owner_id="tenant_1",
            tenant_id="tenant_1",
            content="Standard API retry policy is exponential backoff",
            created_at=now,
            updated_at=now,
        )
        old_mem = MemoryRecord(
            memory_id="mem_old",
            scope="organization",
            owner_id="tenant_1",
            tenant_id="tenant_1",
            content="Standard API retry policy is exponential backoff",
            created_at=two_months_ago,
            updated_at=two_months_ago,
        )

        factor_recent = ranker.compute_recency_factor(recent_mem, now)
        factor_old = ranker.compute_recency_factor(old_mem, now)
        assert factor_recent > factor_old

    def test_context_token_budgeting(self) -> None:
        ranker = MemoryRanker()
        now = datetime.datetime.now(datetime.UTC)

        # Create 3 memories, each ~100 characters (~25 tokens)
        memories = [
            MemoryRecord(
                memory_id=f"mem_{i}",
                scope="user",
                owner_id="user_1",
                tenant_id="tenant_1",
                content=f"Important instruction number {i} regarding reporting details and summary items.",
                created_at=now,
                updated_at=now,
            )
            for i in range(5)
        ]

        # Allow max 25 tokens (19 tokens each, so only 1 fits)
        results = ranker.rank("reporting", memories, limit=10, max_tokens=25)
        assert len(results) == 1
        assert results[0][0].estimated_tokens <= 25


class TestMemoryRetrievalService:
    """Validates the integrated retrieval service."""

    @pytest.mark.asyncio
    async def test_scoped_retrieval_and_budgeting(self) -> None:
        repo = InMemoryMemoryRepository()
        service = MemoryRetrievalService(repository=repo)

        # Populate repository with tenant records
        await repo.create_memory(
            MemoryRecord(
                memory_id="mem_pref_1",
                scope="user",
                owner_id="user_alice",
                tenant_id="tenant_alpha",
                content="Always format financial figures in USD with two decimals",
            )
        )
        await repo.create_memory(
            MemoryRecord(
                memory_id="mem_org_1",
                scope="organization",
                owner_id="tenant_alpha",
                tenant_id="tenant_alpha",
                content="Corporate policy mandates two-space indents and standard headers",
            )
        )

        query = MemoryQuery(
            query="financial figures format",
            allowed_scopes=["user", "organization"],
            limit=5,
            max_tokens=500,
        )
        sec_ctx = MemorySecurityContext(
            tenant_id="tenant_alpha",
            user_id="user_alice",
        )

        retrieval = await service.search(query, sec_ctx)
        assert retrieval.returned_count >= 1
        assert retrieval.memories[0].memory_id == "mem_pref_1"
        assert retrieval.total_estimated_tokens > 0


class TestMemoryConsolidationEngine:
    """Validates deduplication, conflict detection, and version superseding."""

    @pytest.mark.asyncio
    async def test_exact_duplicate_deduplication(self) -> None:
        repo = InMemoryMemoryRepository()
        engine = MemoryConsolidationEngine(repository=repo)

        prop1 = MemoryProposal(
            proposal_id="prop_01",
            tenant_id="tenant_1",
            scope="user",
            owner_id="user_alice",
            proposer_id="agent_1",
            memory_type="preference",
            content="User prefers concise markdown tables",
            confidence=0.8,
        )
        mem1 = await engine.consolidate_and_activate(prop1)
        assert mem1.status == "active"
        assert mem1.version == 1

        # Propose exact same content with higher confidence
        prop2 = MemoryProposal(
            proposal_id="prop_02",
            tenant_id="tenant_1",
            scope="user",
            owner_id="user_alice",
            proposer_id="agent_2",
            memory_type="preference",
            content="   User prefers concise markdown tables   ",
            confidence=0.95,
        )
        mem2 = await engine.consolidate_and_activate(prop2)
        # Should return existing record without creating duplicate
        assert mem2.memory_id == mem1.memory_id
        assert mem2.confidence == 0.95

    @pytest.mark.asyncio
    async def test_conflict_detection_and_rejection_when_supersede_disabled(self) -> None:
        repo = InMemoryMemoryRepository()
        engine = MemoryConsolidationEngine(repository=repo)

        # 1. Existing memory: concise reports
        prop1 = MemoryProposal(
            proposal_id="prop_concise",
            tenant_id="tenant_1",
            scope="user",
            owner_id="user_bob",
            proposer_id="agent_1",
            memory_type="preference",
            content="User requires concise summary tables",
        )
        await engine.consolidate_and_activate(prop1)

        # 2. Contradictory proposal: verbose reports
        prop2 = MemoryProposal(
            proposal_id="prop_verbose",
            tenant_id="tenant_1",
            scope="user",
            owner_id="user_bob",
            proposer_id="agent_2",
            memory_type="preference",
            content="User requires verbose summary tables",
        )

        with pytest.raises(MemoryConflictDetectedError):
            await engine.consolidate_and_activate(prop2, supersede_existing=False)

    @pytest.mark.asyncio
    async def test_conflict_superseding_and_version_lineage(self) -> None:
        repo = InMemoryMemoryRepository()
        engine = MemoryConsolidationEngine(repository=repo)

        # 1. Active memory version 1
        prop1 = MemoryProposal(
            proposal_id="prop_v1",
            tenant_id="tenant_1",
            scope="user",
            owner_id="user_carol",
            proposer_id="agent_1",
            memory_type="preference",
            content="User prefers concise overview",
        )
        mem_v1 = await engine.consolidate_and_activate(prop1)
        assert mem_v1.version == 1

        # 2. Updated preference supersedes version 1
        prop2 = MemoryProposal(
            proposal_id="prop_v2",
            tenant_id="tenant_1",
            scope="user",
            owner_id="user_carol",
            proposer_id="agent_2",
            memory_type="preference",
            content="User prefers detailed overview",
        )
        mem_v2 = await engine.consolidate_and_activate(prop2, supersede_existing=True)

        assert mem_v2.memory_id != mem_v1.memory_id
        assert mem_v2.version == 2
        assert mem_v2.status == "active"

        # Check that mem_v1 was expired and linked
        old_mem = await repo.get_memory(mem_v1.memory_id, tenant_id="tenant_1")
        assert old_mem is not None
        assert old_mem.status == "expired"
        assert old_mem.superseded_by == mem_v2.memory_id

        # Check version history recorded
        versions = await repo.get_version_history(mem_v1.memory_id, tenant_id="tenant_1")
        assert len(versions) == 1
        assert versions[0].version == 1
        assert versions[0].content == mem_v1.content
