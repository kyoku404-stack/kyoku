"""KEEP Phase 4.7 — Unit Tests for Member 1 Core Memory Contracts & Repository.

Validates memory models, lifecycle flags, hashing, security context, and in-memory
storage persistence under tenant and scope boundaries.
"""

from __future__ import annotations

import datetime

import pytest
from pydantic import ValidationError

from backend.app.agents.errors import (
    MemoryAccessDeniedError,
    MemoryNotFoundError,
    MemoryProposalNotFoundError,
    MemoryTenantIsolationViolationError,
)
from backend.app.agents.memory.contracts import (
    MemoryAccessEvent,
    MemoryProposal,
    MemoryRecord,
    MemorySecurityContext,
    MemoryVersionRecord,
    compute_content_hash,
)
from backend.app.agents.memory.repository import InMemoryMemoryRepository


class TestMemoryContractsAndModels:
    """Validates contract structures, field limits, hashing, and helper properties."""

    def test_memory_record_creation_and_hashing(self) -> None:
        content = "   User prefers concise markdown tables.   "
        record = MemoryRecord(
            memory_id="mem_01",
            scope="user",
            owner_id="user_alice",
            tenant_id="tenant_omega",
            content=content,
        )

        assert record.memory_id == "mem_01"
        assert record.scope == "user"
        assert record.status == "active"
        assert record.is_active is True
        assert record.content_hash == compute_content_hash(content)
        assert record.version == 1
        assert record.estimated_tokens > 0

    def test_memory_record_content_length_validation(self) -> None:
        with pytest.raises(ValidationError):
            MemoryRecord(
                memory_id="mem_empty",
                scope="user",
                owner_id="user_alice",
                tenant_id="tenant_omega",
                content="",  # Min length is 1
            )

        with pytest.raises(ValidationError):
            MemoryRecord(
                memory_id="mem_too_long",
                scope="user",
                owner_id="user_alice",
                tenant_id="tenant_omega",
                content="x" * 4001,  # Max length is 4000
            )

    def test_memory_record_expiration_and_deletion_logic(self) -> None:
        now = datetime.datetime.now(datetime.UTC)
        past = now - datetime.timedelta(hours=1)
        future = now + datetime.timedelta(hours=1)

        # Active with future expiration
        active_rec = MemoryRecord(
            memory_id="mem_act",
            scope="organization",
            owner_id="tenant_omega",
            tenant_id="tenant_omega",
            content="Active org rule",
            expires_at=future,
        )
        assert active_rec.is_active is True

        # Expired record
        expired_rec = MemoryRecord(
            memory_id="mem_exp",
            scope="organization",
            owner_id="tenant_omega",
            tenant_id="tenant_omega",
            content="Expired org rule",
            expires_at=past,
        )
        assert expired_rec.is_active is False

        # Soft-deleted record
        deleted_rec = MemoryRecord(
            memory_id="mem_del",
            scope="user",
            owner_id="user_alice",
            tenant_id="tenant_omega",
            content="Deleted context",
            status="deleted",
            deleted_at=now,
        )
        assert deleted_rec.is_active is False

    def test_security_context_validation(self) -> None:
        ctx = MemorySecurityContext(
            tenant_id="tenant_alpha",
            user_id="user_bob",
            roles=["analyst"],
            workflow_execution_id="wf_123",
        )
        assert ctx.tenant_id == "tenant_alpha"
        assert ctx.user_id == "user_bob"
        assert ctx.is_admin is False

        with pytest.raises(ValidationError):
            MemorySecurityContext(tenant_id="   ", user_id="user_bob")

    def test_typed_exceptions(self) -> None:
        err1 = MemoryNotFoundError("mem_999")
        assert err1.code == "MEMORY_NOT_FOUND"
        assert "mem_999" in err1.safe_message

        err2 = MemoryAccessDeniedError("Forbidden scope")
        assert err2.code == "MEMORY_ACCESS_DENIED"

        err3 = MemoryTenantIsolationViolationError(tenant_id="t1", target_tenant_id="t2")
        assert err3.code == "MEMORY_TENANT_ISOLATION_VIOLATION"

        err4 = MemoryProposalNotFoundError("prop_123")
        assert err4.code == "MEMORY_PROPOSAL_NOT_FOUND"


class TestInMemoryMemoryRepository:
    """Validates repository operations under tenant boundaries and scope rules."""

    @pytest.mark.asyncio
    async def test_crud_and_tenant_isolation(self) -> None:
        repo = InMemoryMemoryRepository()
        rec_a = MemoryRecord(
            memory_id="mem_a1",
            scope="user",
            owner_id="user_alice",
            tenant_id="tenant_a",
            content="Alice preference in tenant A",
        )
        await repo.create_memory(rec_a)

        # Readable within tenant A
        fetched = await repo.get_memory("mem_a1", tenant_id="tenant_a")
        assert fetched is not None
        assert fetched.content == rec_a.content

        # Hidden from tenant B
        forbidden = await repo.get_memory("mem_a1", tenant_id="tenant_b")
        assert forbidden is None

        # Update within tenant A
        rec_a.content = "Updated preference"
        updated = await repo.update_memory(rec_a)
        assert updated.content == "Updated preference"

        # Soft delete
        deleted = await repo.soft_delete_memory("mem_a1", tenant_id="tenant_b")
        assert deleted is False  # Cannot delete across tenants

        deleted_ok = await repo.soft_delete_memory("mem_a1", tenant_id="tenant_a")
        assert deleted_ok is True
        fetched_after_delete = await repo.get_memory("mem_a1", tenant_id="tenant_a")
        assert fetched_after_delete is not None
        assert fetched_after_delete.status == "deleted"
        assert fetched_after_delete.is_active is False

    @pytest.mark.asyncio
    async def test_search_scoped_filtering(self) -> None:
        repo = InMemoryMemoryRepository()

        # 1. User Alice memory (tenant_a)
        await repo.create_memory(
            MemoryRecord(
                memory_id="mem_user_alice",
                scope="user",
                owner_id="user_alice",
                tenant_id="tenant_a",
                content="Alice prefers JSON",
            )
        )

        # 2. User Bob memory (tenant_a)
        await repo.create_memory(
            MemoryRecord(
                memory_id="mem_user_bob",
                scope="user",
                owner_id="user_bob",
                tenant_id="tenant_a",
                content="Bob prefers CSV",
            )
        )

        # 3. Organization memory (tenant_a)
        await repo.create_memory(
            MemoryRecord(
                memory_id="mem_org_shared",
                scope="organization",
                owner_id="tenant_a",
                tenant_id="tenant_a",
                content="Corporate reporting standard is ISO-8601",
            )
        )

        # 4. Workflow memory (tenant_a)
        await repo.create_memory(
            MemoryRecord(
                memory_id="mem_wf_exec_1",
                scope="workflow",
                owner_id="wf_exec_100",
                tenant_id="tenant_a",
                content="Intermediate cluster output",
            )
        )

        # Alice searches user + org scopes
        alice_results = await repo.search_scoped(
            tenant_id="tenant_a",
            principal_id="user_alice",
            allowed_scopes=["user", "organization"],
        )
        alice_ids = {m.memory_id for m in alice_results}
        assert "mem_user_alice" in alice_ids
        assert "mem_org_shared" in alice_ids
        assert "mem_user_bob" not in alice_ids  # Bob's private memory excluded!
        assert "mem_wf_exec_1" not in alice_ids  # Workflow scope was not requested

        # Alice searches workflow scope with matching workflow_execution_id
        wf_results = await repo.search_scoped(
            tenant_id="tenant_a",
            principal_id="user_alice",
            allowed_scopes=["workflow"],
            workflow_execution_id="wf_exec_100",
        )
        assert len(wf_results) == 1
        assert wf_results[0].memory_id == "mem_wf_exec_1"

        # Workflow search with mismatched workflow_execution_id returns empty
        mismatched_wf = await repo.search_scoped(
            tenant_id="tenant_a",
            principal_id="user_alice",
            allowed_scopes=["workflow"],
            workflow_execution_id="wf_exec_999",
        )
        assert len(mismatched_wf) == 0

    @pytest.mark.asyncio
    async def test_proposals_and_versions(self) -> None:
        repo = InMemoryMemoryRepository()

        proposal = MemoryProposal(
            proposal_id="prop_01",
            tenant_id="tenant_corp",
            scope="user",
            owner_id="user_charlie",
            proposer_id="agent_researcher_01",
            proposer_type="agent",
            content="User prefers summarized takeaways",
        )
        await repo.create_proposal(proposal)

        fetched_prop = await repo.get_proposal("prop_01", tenant_id="tenant_corp")
        assert fetched_prop is not None
        assert fetched_prop.status == "pending"

        # Cross-tenant proposal query
        assert await repo.get_proposal("prop_01", tenant_id="tenant_other") is None

        # Record version
        ver = MemoryVersionRecord(
            version_id="ver_01",
            memory_id="mem_01",
            tenant_id="tenant_corp",
            version=1,
            content="Old content",
            content_hash=compute_content_hash("Old content"),
            reason="Initial commit",
        )
        await repo.record_version(ver)
        history = await repo.get_version_history("mem_01", tenant_id="tenant_corp")
        assert len(history) == 1
        assert history[0].version == 1

        # Record access audit event
        evt = MemoryAccessEvent(
            event_id="evt_01",
            tenant_id="tenant_corp",
            user_id="user_charlie",
            action="retrieve",
            allowed=True,
        )
        await repo.record_access_event(evt)
        events = await repo.list_access_events(tenant_id="tenant_corp")
        assert len(events) == 1
        assert events[0].event_id == "evt_01"

    @pytest.mark.asyncio
    async def test_stale_memory_expiration(self) -> None:
        repo = InMemoryMemoryRepository()
        now = datetime.datetime.now(datetime.UTC)
        past = now - datetime.timedelta(minutes=10)
        future = now + datetime.timedelta(minutes=10)

        await repo.create_memory(
            MemoryRecord(
                memory_id="mem_stale",
                scope="agent",
                owner_id="agent_exec_1",
                tenant_id="tenant_test",
                content="Temporary working context",
                expires_at=past,
            )
        )
        await repo.create_memory(
            MemoryRecord(
                memory_id="mem_fresh",
                scope="user",
                owner_id="user_dan",
                tenant_id="tenant_test",
                content="Persistent preference",
                expires_at=future,
            )
        )

        expired_count = await repo.expire_stale_memories(now)
        assert expired_count == 1

        stale = await repo.get_memory("mem_stale", tenant_id="tenant_test")
        assert stale is not None
        assert stale.status == "expired"

        fresh = await repo.get_memory("mem_fresh", tenant_id="tenant_test")
        assert fresh is not None
        assert fresh.status == "active"
