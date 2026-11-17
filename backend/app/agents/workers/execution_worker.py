"""KEEP Phase 4.2 — Durable Background Execution Worker Pool.

Separates API execution submission (`202 Accepted`) from agent execution so
long-running tasks execute off the HTTP request thread, backed by persistent
`agent_executions` records and startup stale-execution crash recovery.

Owner: Member 4 (FastAPI Integration, Monitoring & End-to-End QA)
Specification: devdocs/p4/p4.2.txt (Sections 2, 5, 7, 13)
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from backend.app.agents.contracts import AgentContext, AgentRequest
from backend.app.core.logging import get_logger

logger = get_logger("agents.worker")

ExecuteItemFn = Callable[[str, AgentRequest, AgentContext], Awaitable[object]]


@dataclass
class _QueuedExecution:
    execution_id: str
    request: AgentRequest
    context: AgentContext


class DurableExecutionWorker:
    """Asyncio worker pool processing persisted PENDING agent executions."""

    def __init__(
        self,
        *,
        concurrency: int = 4,
        max_queue_size: int = 500,
    ) -> None:
        self._concurrency = max(1, concurrency)
        self._queue: asyncio.Queue[_QueuedExecution] = asyncio.Queue(maxsize=max_queue_size)
        self._workers: list[asyncio.Task] = []
        self._handler: ExecuteItemFn | None = None
        self._running = False

    def bind_handler(self, handler: ExecuteItemFn) -> None:
        """Binds `AgentRuntime.execute_existing` as the worker execution callback."""
        self._handler = handler

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def pending_queue_size(self) -> int:
        return self._queue.qsize()

    async def start(self) -> None:
        """Starts background worker tasks (idempotent)."""
        if self._running:
            return
        self._running = True
        self._workers = [
            asyncio.create_task(self._worker_loop(idx), name=f"keep-agent-worker-{idx}")
            for idx in range(self._concurrency)
        ]

    async def stop(self) -> None:
        """Gracefully cancels and awaits background worker tasks."""
        self._running = False
        for task in self._workers:
            if not task.done():
                task.cancel()
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def enqueue(
        self,
        execution_id: str,
        request: AgentRequest,
        context: AgentContext,
    ) -> None:
        """Enqueues a persisted execution for background processing; auto-starts workers if needed."""
        if not self._running:
            await self.start()
        if self._queue.full():
            raise RuntimeError("Agent execution worker queue is saturated.")
        await self._queue.put(
            _QueuedExecution(execution_id=execution_id, request=request, context=context)
        )

    async def wait_until_drained(self, *, timeout: float = 5.0) -> None:
        """Waits until all currently queued executions finish processing (useful in tests/shutdown)."""
        await asyncio.wait_for(self._queue.join(), timeout=timeout)

    async def _worker_loop(self, worker_index: int) -> None:
        while self._running:
            try:
                item = await self._queue.get()
            except asyncio.CancelledError:
                break

            try:
                if self._handler is not None:
                    await self._handler(item.execution_id, item.request, item.context)
            except (RuntimeError, ValueError, TypeError, KeyError, LookupError, OSError) as exc:
                logger.error(
                    "worker=%d execution_id=%s unhandled_error=%s",
                    worker_index,
                    item.execution_id,
                    type(exc).__name__,
                )
            finally:
                self._queue.task_done()
