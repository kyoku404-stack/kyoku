"""KEEP Phase 4.2 — Shared Runtime, Repository, Policy & Observability Protocols.

Defines the three core interfaces agreed across Members 1–4 and frozen for
Phase 4.3 Multi-Agent Orchestration:
1. `ExecutionRepository` — durable execution state & atomic transitions.
2. `ExecutionPolicyInterface` — timeouts, cancellation, concurrency, limits & retries.
3. `AgentRuntimeInterface` — stable execution submission/status/cancel/retry contract.

Owner: Member 1 (Runtime Architecture & Execution Lifecycle)
Specification: devdocs/p4/p4.2.txt (Sections 3, 5, 6, 14)
"""

from __future__ import annotations

from collections.abc import Awaitable
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from backend.app.agents.contracts import AgentContext, AgentRequest, AgentResult
from backend.app.agents.metadata import AgentMetadata
from backend.app.agents.runtime.lifecycle import (
    ExecutionMode,
    ExecutionRecord,
    ExecutionStatus,
)


@runtime_checkable
class ExecutionRepository(Protocol):
    """Persistence contract for durable KEEP agent execution records."""

    async def create(self, record: ExecutionRecord) -> ExecutionRecord:
        ...

    async def get(self, execution_id: str, *, tenant_id: str | None = None) -> ExecutionRecord | None:
        ...

    async def find_by_idempotency_key(
        self,
        *,
        tenant_id: str,
        requested_by: str,
        idempotency_key: str,
    ) -> ExecutionRecord | None:
        ...

    async def list_executions(
        self,
        *,
        tenant_id: str,
        agent_id: str | None = None,
        status: ExecutionStatus | None = None,
        limit: int = 50,
    ) -> list[ExecutionRecord]:
        ...

    async def mark_running(
        self,
        execution_id: str,
        *,
        started_at: datetime | None = None,
    ) -> ExecutionRecord:
        ...

    async def mark_succeeded(
        self,
        execution_id: str,
        *,
        result_payload: dict[str, Any],
        completed_at: datetime | None = None,
    ) -> ExecutionRecord:
        ...

    async def mark_failed(
        self,
        execution_id: str,
        *,
        error_code: str,
        error_message: str,
        result_payload: dict[str, Any] | None = None,
        completed_at: datetime | None = None,
    ) -> ExecutionRecord:
        ...

    async def mark_timed_out(
        self,
        execution_id: str,
        *,
        error_code: str,
        error_message: str,
        completed_at: datetime | None = None,
    ) -> ExecutionRecord:
        ...

    async def request_cancel(
        self,
        execution_id: str,
        *,
        tenant_id: str,
    ) -> ExecutionRecord:
        ...

    async def mark_cancelled(
        self,
        execution_id: str,
        *,
        reason: str = "Execution cancelled by request.",
        completed_at: datetime | None = None,
    ) -> ExecutionRecord:
        ...

    async def find_stale_running(self, *, stale_before: datetime) -> list[ExecutionRecord]:
        ...


@runtime_checkable
class ExecutionPolicyInterface(Protocol):
    """Safety & resource control interface enforced by AgentRuntime."""

    def resolve_timeout(self, requested_timeout: float | None) -> float:
        ...

    def validate_request_limits(self, request: AgentRequest) -> None:
        ...

    def authorize(
        self,
        metadata: AgentMetadata,
        request: AgentRequest,
        context: AgentContext,
    ) -> None:
        ...

    def can_retry(self, record: ExecutionRecord) -> tuple[bool, str]:
        ...

    async def run_with_controls(
        self,
        coro: Awaitable[AgentResult],
        *,
        execution_id: str,
        agent_id: str,
        tenant_id: str,
        timeout_seconds: float,
    ) -> AgentResult:
        ...

    def signal_cancel(self, execution_id: str) -> bool:
        ...


@runtime_checkable
class RuntimeObserver(Protocol):
    """Observability hook recording structured lifecycle events & metrics."""

    def record_event(
        self,
        event_type: str,
        *,
        record: ExecutionRecord,
        details: dict[str, Any] | None = None,
    ) -> None:
        ...

    def record_validation_failure(self, *, execution_id: str, agent_id: str) -> None:
        ...


@runtime_checkable
class BackgroundDispatcher(Protocol):
    """Queue/worker dispatch seam for durable asynchronous executions."""

    async def enqueue(
        self,
        execution_id: str,
        request: AgentRequest,
        context: AgentContext,
    ) -> None:
        ...


@runtime_checkable
class AgentRuntimeInterface(Protocol):
    """Stable KEEP runtime contract consumed by FastAPI and Phase 4.3 Orchestration."""

    async def submit(
        self,
        agent_id: str,
        request: AgentRequest,
        context: AgentContext,
        *,
        mode: ExecutionMode = "sync",
        idempotency_key: str | None = None,
        timeout_seconds: float | None = None,
    ) -> ExecutionRecord:
        ...

    async def execute_existing(
        self,
        execution_id: str,
        request: AgentRequest,
        context: AgentContext,
    ) -> ExecutionRecord:
        ...

    async def get_execution(
        self,
        execution_id: str,
        context: AgentContext,
    ) -> ExecutionRecord:
        ...

    async def get_result(
        self,
        execution_id: str,
        context: AgentContext,
    ) -> AgentResult:
        ...

    async def cancel_execution(
        self,
        execution_id: str,
        context: AgentContext,
    ) -> ExecutionRecord:
        ...

    async def retry_execution(
        self,
        execution_id: str,
        context: AgentContext,
        *,
        mode: ExecutionMode | None = None,
    ) -> ExecutionRecord:
        ...
