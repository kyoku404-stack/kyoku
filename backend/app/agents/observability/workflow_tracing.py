"""KEEP Phase 4.3 — Workflow-Level Observability, Tracing & Metrics Collector.

Captures secret-safe workflow lifecycle events and per-agent step telemetry sharing
the parent workflow's `correlation_id`, enabling operators to trace multi-agent
durations, partial-success rates, agent invocation counts, cancellations, and recoveries.

Owner: Member 4 (FastAPI Integration, Persistence & End-to-End QA)
Specification: devdocs/p4/p4.3.txt (Sections 12, 13)
"""

from __future__ import annotations

from collections import Counter, deque
from datetime import UTC, datetime
from typing import Any

from backend.app.agents.orchestration.workflow_contracts import (
    WorkflowExecutionRecord,
    WorkflowStepLink,
)
from backend.app.core.logging import get_logger
from pydantic import BaseModel, Field

logger = get_logger("agents.orchestration")


class WorkflowLifecycleEvent(BaseModel):
    """Structured, secret-safe workflow orchestration event."""

    event_type: str
    workflow_execution_id: str
    workflow_id: str
    workflow_version: str
    status: str
    correlation_id: str
    duration_ms: int | None = None
    error_code: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    details: dict[str, Any] = Field(default_factory=dict)


class WorkflowMetricsCollector:
    """In-process workflow & step observability collector for `/api/v1/workflow-executions/metrics`."""

    def __init__(self, *, max_recent_events: int = 200) -> None:
        self._events: deque[WorkflowLifecycleEvent] = deque(maxlen=max_recent_events)
        self._status_counts: Counter[str] = Counter()
        self._durations_ms: deque[int] = deque(maxlen=500)
        self._step_durations_ms: deque[int] = deque(maxlen=1000)
        self._agents_per_workflow: deque[int] = deque(maxlen=500)
        self._active_ids: set[str] = set()
        self._step_counts_by_agent: Counter[str] = Counter()
        self._cancel_count = 0
        self._recovery_count = 0
        self._partial_success_count = 0

    def record_event(
        self,
        event_type: str,
        *,
        record: WorkflowExecutionRecord,
        details: dict[str, Any] | None = None,
    ) -> None:
        event = WorkflowLifecycleEvent(
            event_type=event_type,
            workflow_execution_id=record.workflow_execution_id,
            workflow_id=record.workflow_id,
            workflow_version=record.workflow_version,
            status=record.status.value,
            correlation_id=record.correlation_id,
            duration_ms=record.duration_ms,
            error_code=record.error_code,
            details=details or {},
        )
        self._events.append(event)

        if event_type in ("workflow.started", "workflow.resumed"):
            self._active_ids.add(record.workflow_execution_id)
            if event_type == "workflow.resumed":
                self._recovery_count += 1
        elif event_type in (
            "workflow.succeeded",
            "workflow.partially_succeeded",
            "workflow.failed",
            "workflow.timed_out",
            "workflow.cancelled",
        ):
            self._active_ids.discard(record.workflow_execution_id)
            self._status_counts[record.status.value] += 1
            if record.duration_ms is not None:
                self._durations_ms.append(record.duration_ms)
            agents_invoked = int((details or {}).get("agents_invoked", len(record.execution_ids)))
            self._agents_per_workflow.append(agents_invoked)
            if event_type == "workflow.partially_succeeded":
                self._partial_success_count += 1
            elif event_type == "workflow.cancelled":
                self._cancel_count += 1

        logger.info(
            "event=%s workflow_execution_id=%s workflow_id=%s version=%s status=%s correlation_id=%s duration_ms=%s error_code=%s",
            event.event_type,
            event.workflow_execution_id,
            event.workflow_id,
            event.workflow_version,
            event.status,
            event.correlation_id,
            event.duration_ms,
            event.error_code,
        )

    def record_step(self, step: WorkflowStepLink, *, correlation_id: str) -> None:
        self._step_counts_by_agent[step.agent_id] += 1
        if step.duration_ms is not None:
            self._step_durations_ms.append(step.duration_ms)
        logger.info(
            "event=workflow.step workflow_execution_id=%s node=%s agent_id=%s agent_execution_id=%s role=%s status=%s correlation_id=%s duration_ms=%s",
            step.workflow_execution_id,
            step.node_name,
            step.agent_id,
            step.agent_execution_id,
            step.role,
            step.status,
            correlation_id,
            step.duration_ms,
        )

    @property
    def recent_events(self) -> list[WorkflowLifecycleEvent]:
        return list(self._events)

    def snapshot(self) -> dict[str, Any]:
        total_completed = sum(self._status_counts.values())
        succeeded = self._status_counts.get("SUCCEEDED", 0)
        partial = self._status_counts.get("PARTIALLY_SUCCEEDED", 0)
        avg_duration = (
            round(sum(self._durations_ms) / len(self._durations_ms), 2)
            if self._durations_ms
            else 0.0
        )
        avg_step_duration = (
            round(sum(self._step_durations_ms) / len(self._step_durations_ms), 2)
            if self._step_durations_ms
            else 0.0
        )
        avg_agents = (
            round(sum(self._agents_per_workflow) / len(self._agents_per_workflow), 2)
            if self._agents_per_workflow
            else 0.0
        )
        success_rate = (
            round(((succeeded + partial) / total_completed) * 100.0, 2)
            if total_completed > 0
            else 100.0
        )
        partial_rate = (
            round((partial / total_completed) * 100.0, 2) if total_completed > 0 else 0.0
        )

        return {
            "total_completed": total_completed,
            "active_workflows": len(self._active_ids),
            "workflows_by_status": dict(self._status_counts),
            "success_rate_percent": success_rate,
            "partial_success_rate_percent": partial_rate,
            "avg_workflow_duration_ms": avg_duration,
            "avg_step_duration_ms": avg_step_duration,
            "avg_agents_per_workflow": avg_agents,
            "invocations_by_agent": dict(self._step_counts_by_agent),
            "cancellation_count": self._cancel_count,
            "recovery_count": self._recovery_count,
            "recent_events": [e.model_dump(mode="json") for e in list(self._events)[-20:]],
        }
