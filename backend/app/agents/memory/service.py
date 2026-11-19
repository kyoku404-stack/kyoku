"""KEEP Phase 4.7 — Memory Service.

Coordinates memory storage, retrieval, relevance, security policy validation,
and lifecycle operations.

Specification: devdocs/p4/p4.7.txt (Sections 4, 6)
Owner: Member 4 (LangGraph Integration, API, Persistence & QA)
"""

from __future__ import annotations

import uuid

from backend.app.agents.errors import (
    MemoryAccessDeniedError,
    MemoryNotFoundError,
)
from backend.app.agents.memory.consolidation import MemoryConsolidationEngine
from backend.app.agents.memory.contracts import (
    MemoryProposal,
    MemoryQuery,
    MemoryRecord,
    MemoryRetrievalResult,
    MemorySecurityContext,
    MemoryWriteRequest,
)
from backend.app.agents.memory.lifecycle import MemoryLifecycleManager
from backend.app.agents.memory.policies import MemoryPolicyEngine
from backend.app.agents.memory.repository import (
    BaseMemoryRepository,
    InMemoryMemoryRepository,
)
from backend.app.agents.memory.retrieval import MemoryRetrievalService


class MemoryService:
    """Unified service coordinating memory operations across KEEP."""

    def __init__(
        self,
        repository: BaseMemoryRepository | None = None,
        retrieval_service: MemoryRetrievalService | None = None,
        policy_engine: MemoryPolicyEngine | None = None,
        lifecycle_manager: MemoryLifecycleManager | None = None,
        consolidation_engine: MemoryConsolidationEngine | None = None,
    ) -> None:
        self.repository = repository or InMemoryMemoryRepository()
        self.retrieval_service = retrieval_service or MemoryRetrievalService(self.repository)
        self.policy_engine = policy_engine or MemoryPolicyEngine()
        self.consolidation_engine = consolidation_engine or MemoryConsolidationEngine(self.repository)
        self.lifecycle_manager = lifecycle_manager or MemoryLifecycleManager(
            repository=self.repository,
            policy_engine=self.policy_engine,
            consolidation_engine=self.consolidation_engine,
        )

    async def retrieve(
        self,
        query: MemoryQuery,
        security_context: MemorySecurityContext,
    ) -> MemoryRetrievalResult:
        """Retrieves and ranks authorized memories within context budget."""
        # 1. Authorize query scopes
        decision = self.policy_engine.authorize_read_query(query, security_context)
        if not decision.allowed:
            await self.lifecycle_manager.log_access_event(
                tenant_id=security_context.tenant_id,
                user_id=security_context.user_id,
                action="retrieve",
                allowed=False,
                denial_reason=decision.reason_code,
                correlation_id=security_context.correlation_id,
                summary={"query": query.query, "allowed_scopes": query.allowed_scopes},
            )
            raise MemoryAccessDeniedError(
                f"Memory retrieval query denied: {decision.details.get('reason', 'Unauthorized scope')}",
                details=decision.details,
            )

        # 2. Scoped search & ranking
        result = await self.retrieval_service.search(query, security_context)

        # 3. Defense-in-depth: policy filter
        filtered_memories = self.policy_engine.filter_results(result.memories, security_context)
        total_tokens = sum(m.estimated_tokens for m in filtered_memories)

        # 4. Audit logging
        await self.lifecycle_manager.log_access_event(
            tenant_id=security_context.tenant_id,
            user_id=security_context.user_id,
            action="retrieve",
            allowed=True,
            correlation_id=security_context.correlation_id,
            summary={"query": query.query, "returned_count": len(filtered_memories)},
        )

        return MemoryRetrievalResult(
            memories=filtered_memories,
            total_candidates=result.total_candidates,
            returned_count=len(filtered_memories),
            total_estimated_tokens=total_tokens,
            query=query.query,
        )

    async def propose(
        self,
        request: MemoryWriteRequest,
        security_context: MemorySecurityContext,
    ) -> MemoryProposal:
        """Submits a memory proposal, screens content, and auto-approves if eligible."""
        owner_id = request.owner_id
        if not owner_id:
            if request.scope == "user":
                owner_id = security_context.user_id
            elif request.scope == "workflow":
                owner_id = security_context.workflow_execution_id or "unspecified_workflow"
            elif request.scope == "agent":
                owner_id = security_context.agent_execution_id or "unspecified_agent"
            else:
                owner_id = security_context.tenant_id

        proposer_type = "user" if request.source_type == "user_input" else "agent"

        proposal = MemoryProposal(
            proposal_id=f"prop_{uuid.uuid4().hex[:16]}",
            tenant_id=security_context.tenant_id,
            scope=request.scope,
            owner_id=owner_id,
            proposer_id=security_context.user_id,
            proposer_type=proposer_type,
            memory_type=request.memory_type,
            content=request.content,
            confidence=request.confidence,
            source_reference=request.source_reference,
            meta_data=request.meta_data,
        )

        # 1. Authorize proposal & screen content
        self.policy_engine.authorize_proposal(proposal, security_context)

        # 2. Persist proposal
        saved_proposal = await self.repository.create_proposal(proposal)

        # 3. Audit logging
        await self.lifecycle_manager.log_access_event(
            tenant_id=security_context.tenant_id,
            user_id=security_context.user_id,
            action="propose",
            allowed=True,
            scope=saved_proposal.scope,
            correlation_id=security_context.correlation_id,
            summary={"proposal_id": saved_proposal.proposal_id},
        )

        # 4. Check auto-approval rules
        if self.policy_engine.determine_auto_approval(saved_proposal, security_context):
            active_mem = await self.lifecycle_manager.approve_proposal(
                saved_proposal.proposal_id,
                security_context,
            )
            saved_proposal.status = "approved"
            saved_proposal.approved_memory_id = active_mem.memory_id

        return saved_proposal

    async def get_memory(
        self,
        memory_id: str,
        security_context: MemorySecurityContext,
    ) -> MemoryRecord:
        """Retrieves an authorized memory record by ID."""
        record = await self.repository.get_memory(memory_id, tenant_id=security_context.tenant_id)
        if record is None or not record.is_active:
            raise MemoryNotFoundError(memory_id)

        decision = self.policy_engine.access_controller.check_read_access(record, security_context)
        if not decision.allowed:
            await self.lifecycle_manager.log_access_event(
                tenant_id=security_context.tenant_id,
                user_id=security_context.user_id,
                action="retrieve",
                allowed=False,
                memory_id=memory_id,
                denial_reason=decision.reason_code,
            )
            raise MemoryAccessDeniedError(
                "Access to requested memory record denied.",
                details=decision.details,
            )

        return record

    async def approve_proposal(
        self,
        proposal_id: str,
        security_context: MemorySecurityContext,
    ) -> MemoryRecord:
        """Approves a proposal and consolidates it into active memory."""
        return await self.lifecycle_manager.approve_proposal(proposal_id, security_context)

    async def reject_proposal(
        self,
        proposal_id: str,
        reason: str,
        security_context: MemorySecurityContext,
    ) -> MemoryProposal:
        """Rejects a pending proposal."""
        return await self.lifecycle_manager.reject_proposal(proposal_id, reason, security_context)

    async def delete_memory(
        self,
        memory_id: str,
        security_context: MemorySecurityContext,
    ) -> bool:
        """Soft-deletes a memory record."""
        return await self.lifecycle_manager.delete_memory(memory_id, security_context)
