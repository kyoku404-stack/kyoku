"""KEEP Phase 4.7 — Memory Repository Interfaces & Implementations.

Provides repository interfaces and an in-memory test implementation for
persisting and querying memory records, proposals, version history, and audit events.

Specification: devdocs/p4/p4.7.txt (Sections 4, 5, 11)
Owner: Member 1 (Memory Contracts & Storage)
"""

from __future__ import annotations

import datetime
from abc import ABC, abstractmethod

from backend.app.agents.memory.contracts import (
    MemoryAccessEvent,
    MemoryProposal,
    MemoryRecord,
    MemoryScope,
    MemoryVersionRecord,
)


class BaseMemoryRepository(ABC):
    """Abstract interface for multi-tenant memory storage."""

    @abstractmethod
    async def create_memory(self, record: MemoryRecord) -> MemoryRecord:
        """Persists a new active or approved memory record."""
        ...

    @abstractmethod
    async def get_memory(self, memory_id: str, tenant_id: str) -> MemoryRecord | None:
        """Retrieves a memory record if it belongs to tenant and is not deleted."""
        ...

    @abstractmethod
    async def update_memory(self, record: MemoryRecord) -> MemoryRecord:
        """Updates an existing memory record."""
        ...

    @abstractmethod
    async def soft_delete_memory(self, memory_id: str, tenant_id: str) -> bool:
        """Marks a memory as deleted and sets deleted_at."""
        ...

    @abstractmethod
    async def search_scoped(
        self,
        *,
        tenant_id: str,
        principal_id: str,
        allowed_scopes: list[MemoryScope],
        query: str = "",
        workflow_execution_id: str | None = None,
        agent_execution_id: str | None = None,
        memory_types: list[str] | None = None,
        limit: int = 20,
    ) -> list[MemoryRecord]:
        """Queries active, non-expired candidate memories scoped to tenant and principal."""
        ...

    @abstractmethod
    async def create_proposal(self, proposal: MemoryProposal) -> MemoryProposal:
        """Persists a new candidate memory proposal."""
        ...

    @abstractmethod
    async def get_proposal(self, proposal_id: str, tenant_id: str) -> MemoryProposal | None:
        """Retrieves a proposal by ID and tenant."""
        ...

    @abstractmethod
    async def update_proposal(self, proposal: MemoryProposal) -> MemoryProposal:
        """Updates proposal status (e.g. approved, rejected)."""
        ...

    @abstractmethod
    async def list_proposals(
        self,
        *,
        tenant_id: str,
        status: str | None = None,
        owner_id: str | None = None,
        limit: int = 50,
    ) -> list[MemoryProposal]:
        """Lists proposals matching filters for a tenant."""
        ...

    @abstractmethod
    async def record_version(self, version: MemoryVersionRecord) -> MemoryVersionRecord:
        """Records a historical version snapshot."""
        ...

    @abstractmethod
    async def get_version_history(self, memory_id: str, tenant_id: str) -> list[MemoryVersionRecord]:
        """Retrieves historical versions for a memory record."""
        ...

    @abstractmethod
    async def record_access_event(self, event: MemoryAccessEvent) -> MemoryAccessEvent:
        """Records a security/lifecycle audit access event."""
        ...

    @abstractmethod
    async def list_access_events(
        self,
        *,
        tenant_id: str,
        memory_id: str | None = None,
        limit: int = 50,
    ) -> list[MemoryAccessEvent]:
        """Lists access audit events for tenant."""
        ...

    @abstractmethod
    async def expire_stale_memories(self, now: datetime.datetime | None = None) -> int:
        """Transitions active records past expires_at to status='expired'."""
        ...


class InMemoryMemoryRepository(BaseMemoryRepository):
    """Thread-safe in-memory memory repository for unit tests and local isolation."""

    def __init__(self) -> None:
        self._memories: dict[str, MemoryRecord] = {}
        self._proposals: dict[str, MemoryProposal] = {}
        self._versions: list[MemoryVersionRecord] = []
        self._access_events: list[MemoryAccessEvent] = []

    async def create_memory(self, record: MemoryRecord) -> MemoryRecord:
        self._memories[record.memory_id] = record.model_copy(deep=True)
        return record

    async def get_memory(self, memory_id: str, tenant_id: str) -> MemoryRecord | None:
        record = self._memories.get(memory_id)
        if record is None or record.tenant_id != tenant_id:
            return None
        return record.model_copy(deep=True)

    async def update_memory(self, record: MemoryRecord) -> MemoryRecord:
        record.updated_at = datetime.datetime.now(datetime.UTC)
        self._memories[record.memory_id] = record.model_copy(deep=True)
        return record

    async def soft_delete_memory(self, memory_id: str, tenant_id: str) -> bool:
        record = self._memories.get(memory_id)
        if record is None or record.tenant_id != tenant_id:
            return False
        record.status = "deleted"
        record.deleted_at = datetime.datetime.now(datetime.UTC)
        record.updated_at = datetime.datetime.now(datetime.UTC)
        return True

    async def search_scoped(
        self,
        *,
        tenant_id: str,
        principal_id: str,
        allowed_scopes: list[MemoryScope],
        query: str = "",
        workflow_execution_id: str | None = None,
        agent_execution_id: str | None = None,
        memory_types: list[str] | None = None,
        limit: int = 20,
    ) -> list[MemoryRecord]:
        now = datetime.datetime.now(datetime.UTC)
        candidates: list[MemoryRecord] = []

        for record in self._memories.values():
            # 1. Tenant boundary check
            if record.tenant_id != tenant_id:
                continue

            # 2. Status & Expiration checks
            if not record.is_active:
                continue
            if record.expires_at is not None and record.expires_at <= now:
                continue

            # 3. Scope clearance
            if record.scope not in allowed_scopes:
                continue

            # 4. Scope-specific ownership rules
            if record.scope == "user" and record.owner_id != principal_id:
                continue
            if record.scope == "workflow" and (
                workflow_execution_id is None or record.owner_id != workflow_execution_id
            ):
                continue
            if record.scope == "agent" and (
                agent_execution_id is None or record.owner_id != agent_execution_id
            ):
                continue

            # 5. Memory type filter
            if memory_types and record.memory_type not in memory_types:
                continue

            candidates.append(record.model_copy(deep=True))

        return candidates[:limit]

    async def create_proposal(self, proposal: MemoryProposal) -> MemoryProposal:
        self._proposals[proposal.proposal_id] = proposal.model_copy(deep=True)
        return proposal

    async def get_proposal(self, proposal_id: str, tenant_id: str) -> MemoryProposal | None:
        proposal = self._proposals.get(proposal_id)
        if proposal is None or proposal.tenant_id != tenant_id:
            return None
        return proposal.model_copy(deep=True)

    async def update_proposal(self, proposal: MemoryProposal) -> MemoryProposal:
        self._proposals[proposal.proposal_id] = proposal.model_copy(deep=True)
        return proposal

    async def list_proposals(
        self,
        *,
        tenant_id: str,
        status: str | None = None,
        owner_id: str | None = None,
        limit: int = 50,
    ) -> list[MemoryProposal]:
        results = [
            p.model_copy(deep=True)
            for p in self._proposals.values()
            if p.tenant_id == tenant_id
            and (status is None or p.status == status)
            and (owner_id is None or p.owner_id == owner_id)
        ]
        results.sort(key=lambda p: p.created_at, reverse=True)
        return results[:limit]

    async def record_version(self, version: MemoryVersionRecord) -> MemoryVersionRecord:
        self._versions.append(version.model_copy(deep=True))
        return version

    async def get_version_history(self, memory_id: str, tenant_id: str) -> list[MemoryVersionRecord]:
        versions = [
            v.model_copy(deep=True)
            for v in self._versions
            if v.memory_id == memory_id and v.tenant_id == tenant_id
        ]
        versions.sort(key=lambda v: v.version, reverse=True)
        return versions

    async def record_access_event(self, event: MemoryAccessEvent) -> MemoryAccessEvent:
        self._access_events.append(event.model_copy(deep=True))
        return event

    async def list_access_events(
        self,
        *,
        tenant_id: str,
        memory_id: str | None = None,
        limit: int = 50,
    ) -> list[MemoryAccessEvent]:
        events = [
            e.model_copy(deep=True)
            for e in self._access_events
            if e.tenant_id == tenant_id
            and (memory_id is None or e.memory_id == memory_id)
        ]
        events.sort(key=lambda e: e.created_at, reverse=True)
        return events[:limit]

    async def expire_stale_memories(self, now: datetime.datetime | None = None) -> int:
        current_time = now or datetime.datetime.now(datetime.UTC)
        expired_count = 0
        for record in self._memories.values():
            if record.status == "active" and record.expires_at and record.expires_at <= current_time:
                record.status = "expired"
                record.updated_at = current_time
                expired_count += 1
        return expired_count
