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
from backend.app.models.agent_memory import (
    MemoryAccessEventModel,
    MemoryModel,
    MemoryProposalModel,
    MemoryVersionModel,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


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


class SqlAlchemyMemoryRepository(BaseMemoryRepository):
    """Database repository implementing BaseMemoryRepository with SQLAlchemy ORM."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session = session
        self._fallback = InMemoryMemoryRepository()

    @staticmethod
    def _model_to_record(model: MemoryModel) -> MemoryRecord:
        return MemoryRecord(
            memory_id=model.memory_id,
            tenant_id=model.tenant_id,
            scope=model.scope,  # type: ignore[arg-type]
            owner_id=model.owner_id,
            memory_type=model.memory_type,
            content=model.content,
            content_hash=model.content_hash,
            source_type=model.source_type,
            source_reference=model.source_reference,
            confidence=model.confidence,
            status=model.status,  # type: ignore[arg-type]
            version=model.version,
            superseded_by=model.superseded_by,
            meta_data=model.meta_data,
            expires_at=model.expires_at,
            deleted_at=model.deleted_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _model_to_proposal(model: MemoryProposalModel) -> MemoryProposal:
        return MemoryProposal(
            proposal_id=model.proposal_id,
            tenant_id=model.tenant_id,
            scope=model.scope,  # type: ignore[arg-type]
            owner_id=model.owner_id,
            proposer_id=model.proposer_id,
            proposer_type=model.proposer_type,  # type: ignore[arg-type]
            memory_type=model.memory_type,
            content=model.content,
            confidence=model.confidence,
            source_reference=model.source_reference,
            status=model.status,  # type: ignore[arg-type]
            rejection_reason=model.rejection_reason,
            approved_memory_id=model.approved_memory_id,
            meta_data=model.meta_data,
            created_at=model.created_at,
            reviewed_at=model.reviewed_at,
        )

    async def create_memory(self, record: MemoryRecord) -> MemoryRecord:
        if self._session is None:
            return await self._fallback.create_memory(record)

        model = MemoryModel(
            memory_id=record.memory_id,
            tenant_id=record.tenant_id,
            scope=record.scope,
            owner_id=record.owner_id,
            memory_type=record.memory_type,
            content=record.content,
            content_hash=record.content_hash,
            source_type=record.source_type,
            source_reference=record.source_reference,
            confidence=record.confidence,
            status=record.status,
            version=record.version,
            superseded_by=record.superseded_by,
            meta_data=record.meta_data,
            expires_at=record.expires_at,
            deleted_at=record.deleted_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return record

    async def get_memory(self, memory_id: str, tenant_id: str) -> MemoryRecord | None:
        if self._session is None:
            return await self._fallback.get_memory(memory_id, tenant_id)

        stmt = select(MemoryModel).where(
            MemoryModel.memory_id == memory_id,
            MemoryModel.tenant_id == tenant_id,
            MemoryModel.status != "deleted",
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        return self._model_to_record(row)

    async def update_memory(self, record: MemoryRecord) -> MemoryRecord:
        if self._session is None:
            return await self._fallback.update_memory(record)

        stmt = select(MemoryModel).where(
            MemoryModel.memory_id == record.memory_id,
            MemoryModel.tenant_id == record.tenant_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is not None:
            row.content = record.content
            row.content_hash = record.content_hash
            row.confidence = record.confidence
            row.status = record.status
            row.version = record.version
            row.superseded_by = record.superseded_by
            row.meta_data = record.meta_data
            row.expires_at = record.expires_at
            row.deleted_at = record.deleted_at
            row.updated_at = datetime.datetime.now(datetime.UTC)
            await self._session.flush()
        return record

    async def soft_delete_memory(self, memory_id: str, tenant_id: str) -> bool:
        if self._session is None:
            return await self._fallback.soft_delete_memory(memory_id, tenant_id)

        stmt = select(MemoryModel).where(
            MemoryModel.memory_id == memory_id,
            MemoryModel.tenant_id == tenant_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return False
        row.status = "deleted"
        row.deleted_at = datetime.datetime.now(datetime.UTC)
        row.updated_at = datetime.datetime.now(datetime.UTC)
        await self._session.flush()
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
        if self._session is None:
            return await self._fallback.search_scoped(
                tenant_id=tenant_id,
                principal_id=principal_id,
                allowed_scopes=allowed_scopes,
                query=query,
                workflow_execution_id=workflow_execution_id,
                agent_execution_id=agent_execution_id,
                memory_types=memory_types,
                limit=limit,
            )

        now = datetime.datetime.now(datetime.UTC)
        stmt = (
            select(MemoryModel)
            .where(
                MemoryModel.tenant_id == tenant_id,
                MemoryModel.status == "active",
                MemoryModel.scope.in_(allowed_scopes),
            )
            .order_by(MemoryModel.updated_at.desc())
        )
        if memory_types:
            stmt = stmt.where(MemoryModel.memory_type.in_(memory_types))

        rows = (await self._session.execute(stmt)).scalars().all()
        candidates: list[MemoryRecord] = []

        for row in rows:
            # Check expiration
            if row.expires_at is not None and row.expires_at <= now:
                continue

            # Scope-specific ownership rules
            if row.scope == "user" and row.owner_id != principal_id:
                continue
            if row.scope == "workflow" and (
                workflow_execution_id is None or row.owner_id != workflow_execution_id
            ):
                continue
            if row.scope == "agent" and (
                agent_execution_id is None or row.owner_id != agent_execution_id
            ):
                continue

            candidates.append(self._model_to_record(row))
            if len(candidates) >= limit:
                break

        return candidates

    async def create_proposal(self, proposal: MemoryProposal) -> MemoryProposal:
        if self._session is None:
            return await self._fallback.create_proposal(proposal)

        model = MemoryProposalModel(
            proposal_id=proposal.proposal_id,
            tenant_id=proposal.tenant_id,
            scope=proposal.scope,
            owner_id=proposal.owner_id,
            proposer_id=proposal.proposer_id,
            proposer_type=proposal.proposer_type,
            memory_type=proposal.memory_type,
            content=proposal.content,
            confidence=proposal.confidence,
            source_reference=proposal.source_reference,
            status=proposal.status,
            rejection_reason=proposal.rejection_reason,
            approved_memory_id=proposal.approved_memory_id,
            meta_data=proposal.meta_data,
            created_at=proposal.created_at,
            reviewed_at=proposal.reviewed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return proposal

    async def get_proposal(self, proposal_id: str, tenant_id: str) -> MemoryProposal | None:
        if self._session is None:
            return await self._fallback.get_proposal(proposal_id, tenant_id)

        stmt = select(MemoryProposalModel).where(
            MemoryProposalModel.proposal_id == proposal_id,
            MemoryProposalModel.tenant_id == tenant_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        return self._model_to_proposal(row)

    async def update_proposal(self, proposal: MemoryProposal) -> MemoryProposal:
        if self._session is None:
            return await self._fallback.update_proposal(proposal)

        stmt = select(MemoryProposalModel).where(
            MemoryProposalModel.proposal_id == proposal.proposal_id,
            MemoryProposalModel.tenant_id == proposal.tenant_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is not None:
            row.status = proposal.status
            row.rejection_reason = proposal.rejection_reason
            row.approved_memory_id = proposal.approved_memory_id
            row.reviewed_at = proposal.reviewed_at or datetime.datetime.now(datetime.UTC)
            await self._session.flush()
        return proposal

    async def list_proposals(
        self,
        *,
        tenant_id: str,
        status: str | None = None,
        owner_id: str | None = None,
        limit: int = 50,
    ) -> list[MemoryProposal]:
        if self._session is None:
            return await self._fallback.list_proposals(
                tenant_id=tenant_id,
                status=status,
                owner_id=owner_id,
                limit=limit,
            )

        stmt = select(MemoryProposalModel).where(MemoryProposalModel.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(MemoryProposalModel.status == status)
        if owner_id:
            stmt = stmt.where(MemoryProposalModel.owner_id == owner_id)
        stmt = stmt.order_by(MemoryProposalModel.created_at.desc()).limit(limit)

        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._model_to_proposal(r) for r in rows]

    async def record_version(self, version: MemoryVersionRecord) -> MemoryVersionRecord:
        if self._session is None:
            return await self._fallback.record_version(version)

        model = MemoryVersionModel(
            memory_id=version.memory_id,
            tenant_id=version.tenant_id,
            version=version.version,
            content=version.content,
            content_hash=version.content_hash,
            reason=version.reason,
            created_at=version.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return version

    async def get_version_history(self, memory_id: str, tenant_id: str) -> list[MemoryVersionRecord]:
        if self._session is None:
            return await self._fallback.get_version_history(memory_id, tenant_id)

        stmt = (
            select(MemoryVersionModel)
            .where(
                MemoryVersionModel.memory_id == memory_id,
                MemoryVersionModel.tenant_id == tenant_id,
            )
            .order_by(MemoryVersionModel.version.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            MemoryVersionRecord(
                version_id=str(r.id),
                memory_id=r.memory_id,
                tenant_id=r.tenant_id,
                version=r.version,
                content=r.content,
                content_hash=r.content_hash,
                reason=r.reason,
                created_at=r.created_at,
            )
            for r in rows
        ]

    async def record_access_event(self, event: MemoryAccessEvent) -> MemoryAccessEvent:
        if self._session is None:
            return await self._fallback.record_access_event(event)

        model = MemoryAccessEventModel(
            event_id=event.event_id,
            tenant_id=event.tenant_id,
            user_id=event.user_id,
            action=event.action,
            memory_id=event.memory_id,
            scope=event.scope,
            allowed=event.allowed,
            denial_reason=event.denial_reason,
            query_summary=event.query_summary,
            correlation_id=event.correlation_id,
            created_at=event.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return event

    async def list_access_events(
        self,
        *,
        tenant_id: str,
        memory_id: str | None = None,
        limit: int = 50,
    ) -> list[MemoryAccessEvent]:
        if self._session is None:
            return await self._fallback.list_access_events(
                tenant_id=tenant_id,
                memory_id=memory_id,
                limit=limit,
            )

        stmt = select(MemoryAccessEventModel).where(MemoryAccessEventModel.tenant_id == tenant_id)
        if memory_id:
            stmt = stmt.where(MemoryAccessEventModel.memory_id == memory_id)
        stmt = stmt.order_by(MemoryAccessEventModel.created_at.desc()).limit(limit)

        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            MemoryAccessEvent(
                event_id=r.event_id,
                tenant_id=r.tenant_id,
                user_id=r.user_id,
                action=r.action,  # type: ignore[arg-type]
                memory_id=r.memory_id,
                scope=r.scope,  # type: ignore[arg-type]
                allowed=r.allowed,
                denial_reason=r.denial_reason,
                query_summary=r.query_summary,
                correlation_id=r.correlation_id,
                created_at=r.created_at,
            )
            for r in rows
        ]

    async def expire_stale_memories(self, now: datetime.datetime | None = None) -> int:
        if self._session is None:
            return await self._fallback.expire_stale_memories(now)

        current_time = now or datetime.datetime.now(datetime.UTC)
        stmt = select(MemoryModel).where(
            MemoryModel.status == "active",
            MemoryModel.expires_at.is_not(None),
            MemoryModel.expires_at <= current_time,
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        count = 0
        for r in rows:
            r.status = "expired"
            r.updated_at = current_time
            count += 1
        if count > 0:
            await self._session.flush()
        return count

