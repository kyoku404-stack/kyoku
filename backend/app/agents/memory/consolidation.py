"""KEEP Phase 4.7 — Memory Consolidation & Lifecycle Resolution Engine.

Implements exact and near-duplicate detection, conflict identification,
provenance preservation, and version superseding.

Specification: devdocs/p4/p4.7.txt (Sections 4, 8)
Owner: Member 2 (Retrieval, Relevance & Consolidation)
"""

from __future__ import annotations

import datetime
import uuid

from backend.app.agents.errors import MemoryConflictDetectedError
from backend.app.agents.memory.contracts import (
    MemoryProposal,
    MemoryRecord,
    MemoryVersionRecord,
    compute_content_hash,
)
from backend.app.agents.memory.relevance import calculate_jaccard_similarity, tokenize
from backend.app.agents.memory.repository import BaseMemoryRepository

# Semantic antonym / polarity pairs for conflict detection
_OPPOSITION_PAIRS: tuple[tuple[str, str], ...] = (
    ("concise", "detailed"),
    ("concise", "verbose"),
    ("brief", "comprehensive"),
    ("enable", "disable"),
    ("json", "csv"),
    ("json", "xml"),
    ("markdown", "html"),
    ("tabular", "bullet"),
    ("sync", "async"),
)


class MemoryConsolidationEngine:
    """Manages memory deduplication, conflict detection, and version superseding."""

    def __init__(
        self,
        repository: BaseMemoryRepository,
        *,
        near_duplicate_threshold: float = 0.85,
    ) -> None:
        self.repository = repository
        self.near_duplicate_threshold = near_duplicate_threshold

    async def check_duplicate(
        self,
        proposal: MemoryProposal,
        existing_memories: list[MemoryRecord],
    ) -> MemoryRecord | None:
        """Returns existing active memory if proposal is an exact or near duplicate."""
        target_hash = compute_content_hash(proposal.content)

        for memory in existing_memories:
            if not memory.is_active:
                continue
            if memory.scope != proposal.scope or memory.owner_id != proposal.owner_id:
                continue

            # 1. Exact hash match
            if memory.content_hash == target_hash:
                return memory

            # 2. Near-duplicate text similarity
            similarity = calculate_jaccard_similarity(proposal.content, memory.content)
            if similarity >= self.near_duplicate_threshold:
                return memory

        return None

    def detect_conflicts(
        self,
        candidate_content: str,
        existing_memory: MemoryRecord,
    ) -> str | None:
        """Detects if candidate content contradicts an existing active memory.

        Returns conflict description if contradictory, else None.
        """
        cand_tokens = tokenize(candidate_content)
        exist_tokens = tokenize(existing_memory.content)

        for term_a, term_b in _OPPOSITION_PAIRS:
            if (term_a in cand_tokens and term_b in exist_tokens) or (
                term_b in cand_tokens and term_a in exist_tokens
            ):
                return (
                    f"Direct polarity conflict detected between '{term_a}' and '{term_b}' "
                    f"in memory type '{existing_memory.memory_type}'."
                )

        return None

    async def consolidate_and_activate(
        self,
        proposal: MemoryProposal,
        *,
        supersede_existing: bool = True,
    ) -> MemoryRecord:
        """Validates, deduplicates, supersedes older versions, and persists active memory."""
        # 1. Fetch active memories for this tenant and owner
        existing_records = await self.repository.search_scoped(
            tenant_id=proposal.tenant_id,
            principal_id=proposal.owner_id,
            allowed_scopes=[proposal.scope],
            memory_types=[proposal.memory_type],
            limit=50,
        )

        # 2. Deduplication check
        duplicate = await self.check_duplicate(proposal, existing_records)
        if duplicate is not None:
            # Refresh confidence and updated_at on existing memory rather than duplicating
            duplicate.confidence = max(duplicate.confidence, proposal.confidence)
            duplicate.updated_at = datetime.datetime.now(datetime.UTC)
            await self.repository.update_memory(duplicate)
            return duplicate

        # 3. Conflict and Superseding Check
        conflicting_record: MemoryRecord | None = None
        for memory in existing_records:
            if memory.memory_type == proposal.memory_type and memory.is_active:
                conflict_reason = self.detect_conflicts(proposal.content, memory)
                if conflict_reason:
                    conflicting_record = memory
                    if not supersede_existing:
                        raise MemoryConflictDetectedError(memory.memory_id, conflict_reason)
                    break

        new_memory_id = f"mem_{uuid.uuid4().hex[:16]}"
        now = datetime.datetime.now(datetime.UTC)

        version = 1
        if conflicting_record is not None and supersede_existing:
            # Archive old version
            old_version = MemoryVersionRecord(
                version_id=f"ver_{uuid.uuid4().hex[:12]}",
                memory_id=conflicting_record.memory_id,
                tenant_id=conflicting_record.tenant_id,
                version=conflicting_record.version,
                content=conflicting_record.content,
                content_hash=conflicting_record.content_hash,
                reason=f"Superseded by new memory {new_memory_id}",
                created_at=now,
            )
            await self.repository.record_version(old_version)

            # Mark conflicting record as superseded / expired
            conflicting_record.status = "expired"
            conflicting_record.superseded_by = new_memory_id
            conflicting_record.updated_at = now
            await self.repository.update_memory(conflicting_record)
            version = conflicting_record.version + 1

        # 4. Create new canonical active MemoryRecord
        new_record = MemoryRecord(
            memory_id=new_memory_id,
            scope=proposal.scope,
            owner_id=proposal.owner_id,
            tenant_id=proposal.tenant_id,
            memory_type=proposal.memory_type,
            content=proposal.content,
            content_hash=compute_content_hash(proposal.content),
            source_type=proposal.proposer_type,
            source_reference=proposal.source_reference,
            confidence=proposal.confidence,
            status="active",
            version=version,
            meta_data=proposal.meta_data,
            created_at=now,
            updated_at=now,
        )

        persisted = await self.repository.create_memory(new_record)

        # 5. Update proposal status
        proposal.status = "approved"
        proposal.approved_memory_id = new_memory_id
        proposal.reviewed_at = now
        await self.repository.update_proposal(proposal)

        return persisted
