"""KEEP Phase 4.8 — Multi-Agent Collaboration Contracts & Enums.

Defines session models, task representations, message envelopes, findings,
peer review results, conflict records, and security contexts.

Specification: devdocs/p4/p4.8.txt
Owner: Member 1 (Contracts & Session Management)
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Lifecycle statuses for a multi-agent collaboration session."""

    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEWING = "reviewing"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Execution statuses for subtasks within a collaboration session."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CollaborationMessageType(str, Enum):
    """Types of structured communication exchanged between collaboration agents."""

    TASK_ASSIGNMENT = "task_assignment"
    HANDOFF = "handoff"
    CLARIFICATION = "clarification"
    REVIEW_REQUEST = "review_request"
    REVIEW_RESPONSE = "review_response"


class ReviewOutcome(str, Enum):
    """Possible outcomes of a peer review evaluation."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    CONFLICT_DETECTED = "conflict_detected"


class ConflictStatus(str, Enum):
    """Statuses of a contradiction/conflict between agent findings."""

    DETECTED = "detected"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


# ==============================================================================
# ID Generators
# ==============================================================================


def generate_collaboration_session_id() -> str:
    """Generate a unique domain identifier for a collaboration session."""
    return f"collab_sess_{uuid4().hex[:16]}"


def generate_collaboration_task_id() -> str:
    """Generate a unique domain identifier for a collaboration task."""
    return f"collab_task_{uuid4().hex[:16]}"


def generate_collaboration_message_id() -> str:
    """Generate a unique domain identifier for an inter-agent message."""
    return f"collab_msg_{uuid4().hex[:16]}"


def generate_collaboration_finding_id() -> str:
    """Generate a unique domain identifier for a collaboration finding."""
    return f"collab_fnd_{uuid4().hex[:16]}"


def generate_collaboration_review_id() -> str:
    """Generate a unique domain identifier for a peer review."""
    return f"collab_rev_{uuid4().hex[:16]}"


def generate_collaboration_conflict_id() -> str:
    """Generate a unique domain identifier for a collaboration conflict."""
    return f"collab_cnf_{uuid4().hex[:16]}"


# ==============================================================================
# Security Context
# ==============================================================================


class CollaborationSecurityContext(BaseModel):
    """JWT-verified security context propagating tenant and user authorization."""

    tenant_id: str
    user_id: str
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


# ==============================================================================
# Request & Task Specs
# ==============================================================================


class CollaborationTaskSpec(BaseModel):
    """Specification of a task to be executed within a collaboration session."""

    task_id: str | None = None
    agent_id: str
    title: str
    dependencies: list[str] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    max_attempts: int = Field(default=3, ge=1, le=10)


class CollaborationRequest(BaseModel):
    """Request payload to initiate a new multi-agent collaboration session."""

    objective: str
    workflow_id: str | None = None
    agent_ids: list[str] = Field(default_factory=list)
    tasks: list[CollaborationTaskSpec] = Field(default_factory=list)
    require_review: bool = True
    max_revisions: int = Field(default=2, ge=0, le=5)
    max_agents: int = Field(default=5, ge=1, le=20)


# ==============================================================================
# Domain Entities
# ==============================================================================


class CollaborationTask(BaseModel):
    """A delegated task assigned to a specific agent in a collaboration session."""

    task_id: str
    session_id: str
    tenant_id: str
    agent_id: str
    title: str
    status: TaskStatus = TaskStatus.PENDING
    attempt: int = 0
    max_attempts: int = 3
    dependencies: list[str] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    completed_at: datetime.datetime | None = None


class CollaborationMessage(BaseModel):
    """A validated, structured message routed between collaborating agents."""

    message_id: str
    session_id: str
    tenant_id: str
    sender_id: str
    recipient_id: str
    task_id: str | None = None
    message_type: CollaborationMessageType
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )


class CollaborationFinding(BaseModel):
    """An evidence-backed claim generated by an agent during collaboration."""

    finding_id: str
    session_id: str
    tenant_id: str
    task_id: str
    claim: str
    evidence_refs: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    limitations: str | None = None
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )


class ReviewResult(BaseModel):
    """Evaluation result emitted by a reviewing agent evaluating findings."""

    review_id: str
    session_id: str
    tenant_id: str
    reviewer_id: str
    finding_ids: list[str] = Field(default_factory=list)
    outcome: ReviewOutcome
    reasons: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )


class CollaborationConflict(BaseModel):
    """Contradictory findings across agents tracked for resolution or escalation."""

    conflict_id: str
    session_id: str
    tenant_id: str
    finding_ids: list[str] = Field(default_factory=list)
    status: ConflictStatus = ConflictStatus.DETECTED
    description: str
    resolution: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime.datetime | None = None
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )


class ConflictResolutionRequest(BaseModel):
    """Payload to resolve a detected or escalated conflict."""

    conflict_id: str
    resolution: str
    accepted_finding_ids: list[str] = Field(default_factory=list)
    rejected_finding_ids: list[str] = Field(default_factory=list)


class CancelSessionRequest(BaseModel):
    """Payload to request collaboration session cancellation."""

    reason: str = "User requested cancellation"


class CollaborationReport(BaseModel):
    """Consolidated synthesis report produced at collaboration conclusion."""

    session_id: str
    objective: str
    status: SessionStatus
    summary: str | None = None
    findings: list[CollaborationFinding] = Field(default_factory=list)
    reviews: list[ReviewResult] = Field(default_factory=list)
    conflicts: list[CollaborationConflict] = Field(default_factory=list)
    unresolved_conflicts: list[CollaborationConflict] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime.datetime | None = None


class CollaborationSession(BaseModel):
    """Master collaboration session tracking multi-agent coordination."""

    session_id: str
    tenant_id: str
    requested_by: str
    objective: str
    status: SessionStatus = SessionStatus.PLANNING
    workflow_id: str | None = None
    max_agents: int = 5
    require_review: bool = True
    max_revisions: int = 2
    summary: str | None = None
    report: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    completed_at: datetime.datetime | None = None
