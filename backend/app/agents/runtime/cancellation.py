"""KEEP Phase 4.2 — Cooperative Cancellation Tokens & Active Task Registry.

Provides cooperative cancellation signals and active asyncio task tracking so
running agent invocations can be cancelled cleanly without leaking capacity or
overwriting completed terminal states.

Owner: Member 3 (Execution Safety & Resource Control)
Specification: devdocs/p4/p4.2.txt (Sections 3, 9)
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from backend.app.agents.errors import ExecutionCancelledError


class CancellationToken:
    """Cooperative cancellation handle attached to an active agent execution."""

    def __init__(self, execution_id: str) -> None:
        self.execution_id = execution_id
        self._event = asyncio.Event()
        self.requested_at: datetime | None = None
        self.acknowledged_at: datetime | None = None
        self.reason: str | None = None

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def cancel(self, reason: str = "Cancellation requested by caller.") -> None:
        """Signals cancellation (idempotent)."""
        if not self._event.is_set():
            self.requested_at = datetime.now(UTC)
            self.reason = reason
            self._event.set()

    def acknowledge(self) -> None:
        """Marks cancellation as acknowledged by the running execution."""
        if self.acknowledged_at is None:
            self.acknowledged_at = datetime.now(UTC)

    async def wait(self) -> None:
        """Suspends until cancellation is signalled."""
        await self._event.wait()

    def raise_if_cancelled(self) -> None:
        """Raises ExecutionCancelledError if cancellation has been requested."""
        if self._event.is_set():
            self.acknowledge()
            raise ExecutionCancelledError(self.execution_id)


class CancellationRegistry:
    """Tracks active execution tokens and running asyncio Tasks for cooperative cancellation."""

    def __init__(self) -> None:
        self._tokens: dict[str, CancellationToken] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def register(
        self,
        execution_id: str,
        task: asyncio.Task | None = None,
    ) -> CancellationToken:
        """Registers an active execution and returns its CancellationToken."""
        token = self._tokens.get(execution_id) or CancellationToken(execution_id)
        self._tokens[execution_id] = token
        if task is not None:
            self._tasks[execution_id] = task
        return token

    def bind_task(self, execution_id: str, task: asyncio.Task) -> None:
        """Associates a running asyncio.Task with a registered execution_id."""
        self._tasks[execution_id] = task
        token = self._tokens.get(execution_id)
        if token is not None and token.is_cancelled and not task.done():
            task.cancel()

    def request_cancel(
        self,
        execution_id: str,
        *,
        reason: str = "Cancellation requested by caller.",
    ) -> bool:
        """Signals cancellation on an active execution token and cancels its asyncio Task if bound."""
        token = self._tokens.get(execution_id)
        if token is None:
            return False
        token.cancel(reason)
        task = self._tasks.get(execution_id)
        if task is not None and not task.done():
            task.cancel()
        return True

    def is_cancelled(self, execution_id: str) -> bool:
        token = self._tokens.get(execution_id)
        return token.is_cancelled if token is not None else False

    def unregister(self, execution_id: str) -> None:
        """Releases token and task references once execution reaches terminal state."""
        self._tokens.pop(execution_id, None)
        self._tasks.pop(execution_id, None)

    @property
    def active_count(self) -> int:
        return len(self._tokens)
