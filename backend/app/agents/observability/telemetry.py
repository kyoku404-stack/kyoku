"""KEEP Phase 4.2 — Runtime Observability: Structured Lifecycle Events & Metrics.

Records secret-safe execution lifecycle events (`execution.created`, `queued`,
`started`, `succeeded`, `failed`, `timed_out`, `cancel_requested`, `cancelled`,
`retry_scheduled`) and aggregates runtime KPIs without logging raw prompts,
secrets, or confidential document payloads.

Owner: Member 4 (FastAPI Integration, Monitoring & End-to-End QA)
Specification: devdocs/p4/p4.2.txt (Sections 10, 13)
"""

from __future__ import annotations

from collections import Counter, deque
from datetime import UTC, datetime
from typing import Any

from backend.app.agents.runtime.lifecycle import ExecutionRecord
from backend.app.core.logging import get_logger
from pydantic import BaseModel, Field

logger = get_logger("agents.runtime")


class ExecutionLifecycleEvent(BaseModel):
    """Structured, secret-safe lifecycle event emitted during agent execution."""

    event_type: str
    execution_id: str
    agent_id: str
    agent_version: str
    status: str
    correlation_id: str
    attempt_number: int = 1
    duration_ms: int | None = None
    queue_wait_ms: int | None = None
    error_code: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    details: dict[str, Any] = Field(default_factory=dict)


class RuntimeMetricsCollector:
    """In-process runtime telemetry & structured lifecycle event collector."""

    def __init__(self, *, max_recent_events: int = 200) -> None:
        self._events: deque[ExecutionLifecycleEvent] = deque(maxlen=max_recent_events)
        self._status_counts: Counter[str] = Counter()
        self._durations_ms: deque[int] = deque(maxlen=500)
        self._queue_waits_ms: deque[int] = deque(maxlen=500)
        self._active_ids: set[str] = set()
        self._timeout_count = 0
        self._cancel_count = 0
        self._retry_count = 0
        self._validation_failures = 0

    def record_event(
        self,
        event_type: str,
        *,
        record: ExecutionRecord,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Records a structured lifecycle event and updates runtime metrics."""
        event = ExecutionLifecycleEvent(
            event_type=event_type,
            execution_id=record.execution_id,
            agent_id=record.agent_id,
            agent_version=record.agent_version,
            status=record.status.value,
            correlation_id=record.correlation_id,
            attempt_number=record.attempt_number,
            duration_ms=record.duration_ms,
            queue_wait_ms=record.queue_wait_ms,
            error_code=record.error_code,
            details=details or {},
        )
        self._events.append(event)

        if event_type == "execution.started":
            self._active_ids.add(record.execution_id)
            if record.queue_wait_ms is not None:
                self._queue_waits_ms.append(record.queue_wait_ms)
        elif event_type in (
            "execution.succeeded",
            "execution.failed",
            "execution.timed_out",
            "execution.cancelled",
        ):
            self._active_ids.discard(record.execution_id)
            self._status_counts[record.status.value] += 1
            if record.duration_ms is not None:
                self._durations_ms.append(record.duration_ms)
            if event_type == "execution.timed_out":
                self._timeout_count += 1
            elif event_type == "execution.cancelled":
                self._cancel_count += 1
        elif event_type == "execution.retry_scheduled":
            self._retry_count += 1

        logger.info(
            "event=%s execution_id=%s agent_id=%s version=%s status=%s correlation_id=%s duration_ms=%s error_code=%s",
            event.event_type,
            event.execution_id,
            event.agent_id,
            event.agent_version,
            event.status,
            event.correlation_id,
            event.duration_ms,
            event.error_code,
        )

    def record_validation_failure(self, *, execution_id: str, agent_id: str) -> None:
        self._validation_failures += 1
        logger.warning(
            "event=execution.output_validation_failed execution_id=%s agent_id=%s",
            execution_id,
            agent_id,
        )

    @property
    def recent_events(self) -> list[ExecutionLifecycleEvent]:
        return list(self._events)

    def snapshot(self) -> dict[str, Any]:
        """Returns a serializable telemetry snapshot for `/api/v1/executions/metrics`."""
        total_completed = sum(self._status_counts.values())
        succeeded = self._status_counts.get("SUCCEEDED", 0)
        avg_duration = (
            round(sum(self._durations_ms) / len(self._durations_ms), 2)
            if self._durations_ms
            else 0.0
        )
        sorted_durs = sorted(self._durations_ms)
        p95_duration = (
            float(sorted_durs[int(0.95 * (len(sorted_durs) - 1))]) if sorted_durs else 0.0
        )
        avg_queue_wait = (
            round(sum(self._queue_waits_ms) / len(self._queue_waits_ms), 2)
            if self._queue_waits_ms
            else 0.0
        )
        success_rate = round((succeeded / total_completed) * 100.0, 2) if total_completed > 0 else 100.0

        return {
            "total_completed": total_completed,
            "active_executions": len(self._active_ids),
            "executions_by_status": dict(self._status_counts),
            "success_rate_percent": success_rate,
            "avg_duration_ms": avg_duration,
            "p95_duration_ms": p95_duration,
            "avg_queue_wait_ms": avg_queue_wait,
            "timeout_count": self._timeout_count,
            "cancellation_count": self._cancel_count,
            "retry_count": self._retry_count,
            "output_validation_failures": self._validation_failures,
            "recent_events": [e.model_dump(mode="json") for e in list(self._events)[-20:]],
        }
