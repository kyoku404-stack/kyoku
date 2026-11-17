"""KEEP Phase 4.1 — Multi-Agent Architecture Package.

Exposes KEEP's canonical agent protocol, metadata, contracts, message envelopes,
error hierarchy, and registry.
"""

from backend.app.agents.base import BaseAgent
from backend.app.agents.contracts import (
    AGENT_CONTRACT_SCHEMA_VERSION,
    EXAMPLE_AGENT_REQUEST,
    EXAMPLE_AGENT_RESULT,
    SUPPORTED_SCHEMA_VERSIONS,
    AgentContext,
    AgentRequest,
    AgentResult,
    EvidenceReference,
    generate_correlation_id,
    generate_request_id,
    generate_task_id,
)
from backend.app.agents.errors import (
    AgentAlreadyRegisteredError,
    AgentAuthorizationError,
    AgentContractValidationError,
    AgentDisabledError,
    AgentErrorCode,
    AgentErrorDetail,
    AgentLayerError,
    AgentNotFoundError,
    AgentPromptInjectionError,
    AgentTenantIsolationError,
    sanitize_error_message,
)
from backend.app.agents.messages import (
    AgentHandoffPayload,
    AgentMessageEnvelope,
    AgentParticipant,
    MessagePriority,
    MessageType,
    generate_message_id,
)
from backend.app.agents.metadata import AgentCapability, AgentMetadata, CapabilityAccess
from backend.app.agents.registry import AgentRegistry

__all__ = [
    "AGENT_CONTRACT_SCHEMA_VERSION",
    "EXAMPLE_AGENT_REQUEST",
    "EXAMPLE_AGENT_RESULT",
    "SUPPORTED_SCHEMA_VERSIONS",
    "AgentAlreadyRegisteredError",
    "AgentAuthorizationError",
    "AgentCapability",
    "AgentContext",
    "AgentContractValidationError",
    "AgentDisabledError",
    "AgentErrorCode",
    "AgentErrorDetail",
    "AgentHandoffPayload",
    "AgentLayerError",
    "AgentMessageEnvelope",
    "AgentMetadata",
    "AgentNotFoundError",
    "AgentParticipant",
    "AgentPromptInjectionError",
    "AgentRegistry",
    "AgentRequest",
    "AgentResult",
    "AgentTenantIsolationError",
    "BaseAgent",
    "CapabilityAccess",
    "EvidenceReference",
    "MessagePriority",
    "MessageType",
    "generate_correlation_id",
    "generate_message_id",
    "generate_request_id",
    "generate_task_id",
    "sanitize_error_message",
]
