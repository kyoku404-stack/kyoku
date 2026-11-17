"""KEEP Phase 4.2 — Execution Resource Controls, Input Limits & Concurrency Limiter.

Enforces bounded timeouts, input payload byte ceilings, and active concurrency
quotas globally, per agent, and per tenant with deterministic slot release.

Owner: Member 3 (Execution Safety & Resource Control)
Specification: devdocs/p4/p4.2.txt (Sections 3, 9)
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass

from backend.app.agents.contracts import AgentRequest
from backend.app.agents.errors import (
    AgentContractValidationError,
    AgentErrorCode,
    ConcurrencyLimitExceededError,
)


@dataclass(frozen=True)
class ExecutionLimitsConfig:
    """Configurable resource and safety ceilings for KEEP's AgentRuntime."""

    default_timeout_seconds: float = 30.0
    max_timeout_seconds: float = 300.0
    min_timeout_seconds: float = 0.05
    max_input_bytes: int = 65_536
    max_total_active: int = 50
    max_per_agent: int = 10
    max_per_tenant: int = 15
    max_retries: int = 3
    base_backoff_seconds: float = 0.25
    max_backoff_seconds: float = 10.0


def validate_input_size(request: AgentRequest, *, max_bytes: int) -> int:
    """Validates serialized request goal + input payload stays within `max_bytes`."""
    serialized = json.dumps(
        {"goal": request.goal, "input": request.input},
        default=str,
        separators=(",", ":"),
    ).encode("utf-8")
    size = len(serialized)
    if size > max_bytes:
        raise AgentContractValidationError(
            f"Execution input size ({size} bytes) exceeds maximum allowed limit ({max_bytes} bytes).",
            code=AgentErrorCode.EXECUTION_INPUT_TOO_LARGE,
            details={"size_bytes": size, "max_bytes": max_bytes},
        )
    return size


class ConcurrencyLimiter:
    """Tracks active execution slots across global, per-agent, and per-tenant scopes."""

    def __init__(self, config: ExecutionLimitsConfig | None = None) -> None:
        self.config = config or ExecutionLimitsConfig()
        self._lock = asyncio.Lock()
        self._total_active = 0
        self._by_agent: dict[str, int] = defaultdict(int)
        self._by_tenant: dict[str, int] = defaultdict(int)

    @property
    def active_total(self) -> int:
        return self._total_active

    def active_for_agent(self, agent_id: str) -> int:
        return self._by_agent.get(agent_id, 0)

    def active_for_tenant(self, tenant_id: str) -> int:
        return self._by_tenant.get(tenant_id, 0)

    async def acquire(self, *, agent_id: str, tenant_id: str) -> None:
        """Reserves global, agent, and tenant capacity or raises ConcurrencyLimitExceededError."""
        async with self._lock:
            if self._total_active >= self.config.max_total_active:
                raise ConcurrencyLimitExceededError("global", self.config.max_total_active)
            if self._by_agent[agent_id] >= self.config.max_per_agent:
                raise ConcurrencyLimitExceededError(f"agent:{agent_id}", self.config.max_per_agent)
            if self._by_tenant[tenant_id] >= self.config.max_per_tenant:
                raise ConcurrencyLimitExceededError(
                    f"tenant:{tenant_id}", self.config.max_per_tenant
                )

            self._total_active += 1
            self._by_agent[agent_id] += 1
            self._by_tenant[tenant_id] += 1

    async def release(self, *, agent_id: str, tenant_id: str) -> None:
        """Releases previously reserved concurrency slots cleanly."""
        async with self._lock:
            self._total_active = max(0, self._total_active - 1)
            if self._by_agent[agent_id] <= 1:
                self._by_agent.pop(agent_id, None)
            else:
                self._by_agent[agent_id] -= 1

            if self._by_tenant[tenant_id] <= 1:
                self._by_tenant.pop(tenant_id, None)
            else:
                self._by_tenant[tenant_id] -= 1

    @asynccontextmanager
    async def slot(self, *, agent_id: str, tenant_id: str):
        """Async context manager guaranteeing capacity release on success, failure, timeout, or cancel."""
        await self.acquire(agent_id=agent_id, tenant_id=tenant_id)
        try:
            yield
        finally:
            await self.release(agent_id=agent_id, tenant_id=tenant_id)
