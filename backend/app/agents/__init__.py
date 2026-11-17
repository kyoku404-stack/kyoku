"""KEEP Phase 4.1 — Multi-Agent Architecture Package.

Exposes KEEP's canonical agent protocol, metadata, contracts, and registry.
"""

from backend.app.agents.base import BaseAgent
from backend.app.agents.contracts import (
    AGENT_CONTRACT_SCHEMA_VERSION,
    AgentContext,
    AgentRequest,
    AgentResult,
    EvidenceReference,
)
from backend.app.agents.metadata import AgentCapability, AgentMetadata, CapabilityAccess
from backend.app.agents.registry import AgentRegistry

__all__ = [
    "AGENT_CONTRACT_SCHEMA_VERSION",
    "AgentCapability",
    "AgentContext",
    "AgentMetadata",
    "AgentRegistry",
    "AgentRequest",
    "AgentResult",
    "BaseAgent",
    "CapabilityAccess",
    "EvidenceReference",
]
