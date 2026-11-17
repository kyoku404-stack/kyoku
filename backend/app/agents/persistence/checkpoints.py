"""KEEP Phase 4.2 — Tenant-Scoped Graph Checkpoint Store.

Persists LangGraph step state snapshots separately from `agent_executions`
(ADR-073). Re-validates `AgentContext` and tenant boundaries on every load
so a saved checkpoint can never bypass revoked authorization.

Owner: Member 2 (Execution State, Persistence & Result Management)
Specification: devdocs/p4/p4.2.txt (Sections 6, 8)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from backend.app.agents.contracts import AgentContext
from backend.app.models.agent_execution import AgentCheckpoint
from backend.app.services.security.agent_policy import (
    AgentPolicyInterface,
    KeepAgentPolicyEngine,
)
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class AgentCheckpointRecord(BaseModel):
    """Serialized graph checkpoint state scoped to a KEEP execution and tenant."""

    checkpoint_id: str = Field(default_factory=lambda: f"chk_{uuid4().hex}")
    execution_id: str
    thread_id: str
    tenant_id: str
    step_name: str
    step_number: int = Field(default=0, ge=0)
    state: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class KeepCheckpointStore:
    """Tenant-scoped checkpoint store supporting both durable SQLAlchemy and in-memory modes."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        policy: AgentPolicyInterface | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._policy: AgentPolicyInterface = policy or KeepAgentPolicyEngine()
        self._memory: list[AgentCheckpointRecord] = []

    async def save_checkpoint(
        self,
        *,
        execution_id: str,
        thread_id: str,
        step_name: str,
        step_number: int,
        state: dict[str, Any],
        context: AgentContext,
    ) -> AgentCheckpointRecord:
        """Persists a tenant-scoped step checkpoint."""
        self._policy.verify_trusted_context(context)
        record = AgentCheckpointRecord(
            execution_id=execution_id,
            thread_id=thread_id,
            tenant_id=context.tenant_id,
            step_name=step_name,
            step_number=step_number,
            state=dict(state),
        )
        if self._session_factory is None:
            self._memory.append(record)
            return record

        row = AgentCheckpoint(
            checkpoint_id=record.checkpoint_id,
            execution_id=record.execution_id,
            thread_id=record.thread_id,
            tenant_id=record.tenant_id,
            step_name=record.step_name,
            step_number=record.step_number,
            state_json=dict(record.state),
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()
        return record

    async def list_checkpoints(
        self,
        *,
        execution_id: str,
        context: AgentContext,
    ) -> list[AgentCheckpointRecord]:
        """Lists checkpoints for an execution strictly within `context.tenant_id`."""
        self._policy.verify_trusted_context(context)
        if self._session_factory is None:
            return sorted(
                [
                    c
                    for c in self._memory
                    if c.execution_id == execution_id and c.tenant_id == context.tenant_id
                ],
                key=lambda c: c.step_number,
            )

        async with self._session_factory() as session:
            stmt = (
                select(AgentCheckpoint)
                .where(
                    and_(
                        AgentCheckpoint.execution_id == execution_id,
                        AgentCheckpoint.tenant_id == context.tenant_id,
                    )
                )
                .order_by(AgentCheckpoint.step_number.asc())
            )
            res = await session.execute(stmt)
            return [
                AgentCheckpointRecord(
                    checkpoint_id=row.checkpoint_id,
                    execution_id=row.execution_id,
                    thread_id=row.thread_id,
                    tenant_id=row.tenant_id,
                    step_name=row.step_name,
                    step_number=row.step_number,
                    state=dict(row.state_json or {}),
                    created_at=row.created_at,
                )
                for row in res.scalars().all()
            ]

    async def get_latest_checkpoint(
        self,
        *,
        thread_id: str,
        context: AgentContext,
    ) -> AgentCheckpointRecord | None:
        """Loads the latest checkpoint for a thread after enforcing tenant boundary."""
        self._policy.verify_trusted_context(context)
        if self._session_factory is None:
            matches = [
                c
                for c in self._memory
                if c.thread_id == thread_id and c.tenant_id == context.tenant_id
            ]
            if not matches:
                return None
            return max(matches, key=lambda c: c.step_number)

        async with self._session_factory() as session:
            stmt = (
                select(AgentCheckpoint)
                .where(
                    and_(
                        AgentCheckpoint.thread_id == thread_id,
                        AgentCheckpoint.tenant_id == context.tenant_id,
                    )
                )
                .order_by(AgentCheckpoint.step_number.desc())
                .limit(1)
            )
            res = await session.execute(stmt)
            row = res.scalar_one_or_none()
            if row is None:
                return None
            return AgentCheckpointRecord(
                checkpoint_id=row.checkpoint_id,
                execution_id=row.execution_id,
                thread_id=row.thread_id,
                tenant_id=row.tenant_id,
                step_name=row.step_name,
                step_number=row.step_number,
                state=dict(row.state_json or {}),
                created_at=row.created_at,
            )
