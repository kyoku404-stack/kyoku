"""KEEP Phase 4.7 — Memory Lifecycle Manager.

Manages retention policies, expiration sweeps, approval/rejection workflows,
and soft-deletion with audit event logging.

Specification: devdocs/p4/p4.7.txt (Sections 4, 8, 11)
Owner: Member 3 (Privacy, Governance & Lifecycle)
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from backend.app.agents.errors import (
    MemoryNotFoundError,
    MemoryProposalNotFoundError,
)
from backend.app.agents.memory.consolidation import MemoryConsolidationEngine
from backend.app.agents.memory.contracts import (
    MemoryAccessEvent,
    MemoryProposal,
    MemoryRecord,
    MemorySecurityContext,
)
from backend.app.agents.memory.policies import MemoryPolicyEngine
from backend.app.agents.memory.repository import BaseMemoryRepository

DEFAULT_RETENTION_DAYS: dict[str, int] = {
    "preference": 90,
    "fact": 60,
    "instruction": 30,
    "intermediate_result": 1,
    "observation": 7,
}


def compute_expiration_timestamp(
    memory_type: str,
    scope: str,
    from_time: datetime.datetime | None = None,
) -> datetime.datetime:
    """Calculates expiration datetime based on memory type and scope."""
    base_time = from_time or datetime.datetime.now(datetime.UTC)
    if scope == "agent":
        return base_time + datetime.timedelta(hours=24)
    if scope == "workflow":
        return base_time + datetime.timedelta(days=7)

    days = DEFAULT_RETENTION_DAYS.get(memory_type.lower(), 30)
    return base_time + datetime.timedelta(days=days)


class MemoryLifecycleManager:
    """Orchestrates retention, expiration, approval, rejection, and deletion."""

    def __init__(
        self,
        repository: BaseMemoryRepository,
        policy_engine: MemoryPolicyEngine | None = None,
        consolidation_engine: MemoryConsolidationEngine | None = None,
    ) -> None:
        self.repository = repository
        self.policy_engine = policy_engine or MemoryPolicyEngine()
        self.consolidation_engine = consolidation_engine or MemoryConsolidationEngine(repository)

    async def log_access_event(
        self,
        *,
        tenant_id: str,
        user_id: str,
        action: str,
        allowed: bool,
        memory_id: str | None = None,
        scope: str | None = None,
        denial_reason: str | None = None,
        correlation_id: str | None = None,
        summary: dict[str, Any] | None = None,
    ) -> None:
        """Helper to append an audit event."""
        event = MemoryAccessEvent(
            event_id=f"mem_evt_{uuid.uuid4().hex[:16]}",
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,  # type: ignore[arg-type]
            memory_id=memory_id,
            scope=scope,  # type: ignore[arg-type]
            allowed=allowed,
            denial_reason=denial_reason,
            query_summary=summary or {},
            correlation_id=correlation_id,
            created_at=datetime.datetime.now(datetime.UTC),
        )
        await self.repository.record_access_event(event)

    async def approve_proposal(
        self,
        proposal_id: str,
        security_context: MemorySecurityContext,
    ) -> MemoryRecord:
        """Approves a pending proposal and consolidates it into active memory."""
        proposal = await self.repository.get_proposal(proposal_id, tenant_id=security_context.tenant_id)
        if proposal is None:
            await self.log_access_event(
                tenant_id=security_context.tenant_id,
                user_id=security_context.user_id,
                action="approve",
                allowed=False,
                denial_reason="MEMORY_PROPOSAL_NOT_FOUND",
            )
            raise MemoryProposalNotFoundError(proposal_id)

        # Policy validation
        self.policy_engine.authorize_approval(proposal, security_context)

        # Consolidate and activate
        active_record = await self.consolidation_engine.consolidate_and_activate(proposal)

        # Set retention expiration if unset
        if active_record.expires_at is None:
            active_record.expires_at = compute_expiration_timestamp(
                active_record.memory_type,
                active_record.scope,
            )
            await self.repository.update_memory(active_record)

        await self.log_access_event(
            tenant_id=security_context.tenant_id,
            user_id=security_context.user_id,
            action="approve",
            allowed=True,
            memory_id=active_record.memory_id,
            scope=active_record.scope,
            correlation_id=security_context.correlation_id,
        )

        return active_record

    async def reject_proposal(
        self,
        proposal_id: str,
        reason: str,
        security_context: MemorySecurityContext,
    ) -> MemoryProposal:
        """Rejects a proposal and updates status."""
        proposal = await self.repository.get_proposal(proposal_id, tenant_id=security_context.tenant_id)
        if proposal is None:
            raise MemoryProposalNotFoundError(proposal_id)

        self.policy_engine.authorize_approval(proposal, security_context)

        proposal.status = "rejected"
        proposal.rejection_reason = reason
        proposal.reviewed_at = datetime.datetime.now(datetime.UTC)
        updated = await self.repository.update_proposal(proposal)

        await self.log_access_event(
            tenant_id=security_context.tenant_id,
            user_id=security_context.user_id,
            action="reject",
            allowed=True,
            scope=proposal.scope,
            denial_reason=reason,
            correlation_id=security_context.correlation_id,
        )

        return updated

    async def delete_memory(
        self,
        memory_id: str,
        security_context: MemorySecurityContext,
    ) -> bool:
        """Soft-deletes an active memory record after authorization."""
        record = await self.repository.get_memory(memory_id, tenant_id=security_context.tenant_id)
        if record is None:
            await self.log_access_event(
                tenant_id=security_context.tenant_id,
                user_id=security_context.user_id,
                action="delete",
                allowed=False,
                denial_reason="MEMORY_NOT_FOUND",
            )
            raise MemoryNotFoundError(memory_id)

        self.policy_engine.authorize_deletion(record, security_context)

        deleted = await self.repository.soft_delete_memory(memory_id, tenant_id=security_context.tenant_id)

        await self.log_access_event(
            tenant_id=security_context.tenant_id,
            user_id=security_context.user_id,
            action="delete",
            allowed=deleted,
            memory_id=memory_id,
            scope=record.scope,
            correlation_id=security_context.correlation_id,
        )

        return deleted

    async def expire_memories(self, now: datetime.datetime | None = None) -> int:
        """Executes expiration sweep across stale memory records."""
        return await self.repository.expire_stale_memories(now)
