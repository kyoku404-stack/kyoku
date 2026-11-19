"""KEEP Memory System Contracts Re-export.

Maintains backward-compatibility with direct `app.memory.contracts` imports
specified in devdocs/p4/p4.7.txt.
"""

from backend.app.agents.memory.contracts import (
    MemoryAccessEvent,
    MemoryProposal,
    MemoryQuery,
    MemoryRecord,
    MemoryRetrievalResult,
    MemoryScope,
    MemorySecurityContext,
    MemoryStatus,
    MemoryType,
    MemoryVersionRecord,
    MemoryWriteRequest,
    ProposalStatus,
    compute_content_hash,
)

__all__ = [
    "MemoryAccessEvent",
    "MemoryProposal",
    "MemoryQuery",
    "MemoryRecord",
    "MemoryRetrievalResult",
    "MemoryScope",
    "MemorySecurityContext",
    "MemoryStatus",
    "MemoryType",
    "MemoryVersionRecord",
    "MemoryWriteRequest",
    "ProposalStatus",
    "compute_content_hash",
]
