"""KEEP Phase 4.8 — Multi-Agent Collaboration Module."""

from backend.app.agents.collaboration.contracts import (
    CancelSessionRequest,
    CollaborationConflict,
    CollaborationFinding,
    CollaborationMessage,
    CollaborationMessageType,
    CollaborationReport,
    CollaborationRequest,
    CollaborationSecurityContext,
    CollaborationSession,
    CollaborationTask,
    CollaborationTaskSpec,
    ConflictResolutionRequest,
    ConflictStatus,
    ReviewOutcome,
    ReviewResult,
    SessionStatus,
    TaskStatus,
    generate_collaboration_conflict_id,
    generate_collaboration_finding_id,
    generate_collaboration_message_id,
    generate_collaboration_review_id,
    generate_collaboration_session_id,
    generate_collaboration_task_id,
)
from backend.app.agents.collaboration.findings import FindingsCatalog
from backend.app.agents.collaboration.messaging import (
    CollaborationMessageService,
    scrub_secrets_from_text,
    scrub_secrets_recursively,
)
from backend.app.agents.collaboration.repository import (
    BaseCollaborationRepository,
    InMemoryCollaborationRepository,
)
from backend.app.agents.collaboration.service import CollaborationService
from backend.app.agents.collaboration.session_manager import SessionManager
from backend.app.agents.collaboration.task_dispatcher import TaskDispatcher

__all__ = [
    "BaseCollaborationRepository",
    "CancelSessionRequest",
    "CollaborationConflict",
    "CollaborationFinding",
    "CollaborationMessage",
    "CollaborationMessageService",
    "CollaborationMessageType",
    "CollaborationReport",
    "CollaborationRequest",
    "CollaborationSecurityContext",
    "CollaborationService",
    "CollaborationSession",
    "CollaborationTask",
    "CollaborationTaskSpec",
    "ConflictResolutionRequest",
    "ConflictStatus",
    "FindingsCatalog",
    "InMemoryCollaborationRepository",
    "ReviewOutcome",
    "ReviewResult",
    "SessionManager",
    "SessionStatus",
    "TaskDispatcher",
    "TaskStatus",
    "generate_collaboration_conflict_id",
    "generate_collaboration_finding_id",
    "generate_collaboration_message_id",
    "generate_collaboration_review_id",
    "generate_collaboration_session_id",
    "generate_collaboration_task_id",
    "scrub_secrets_from_text",
    "scrub_secrets_recursively",
]
