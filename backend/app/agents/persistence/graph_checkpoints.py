"""KEEP Phase 4.3 — Tenant-Scoped Graph Checkpoint Store Adapter.

Reuses Phase 4.2's `KeepCheckpointStore` (`agent_checkpoints` table) with strict
`wf:{tenant_id}:{workflow_execution_id}` thread scoping, secret-safe state redaction,
and zero duplicate checkpoint tables.

Owner: Member 4 (FastAPI Integration, Persistence & End-to-End QA)
Specification: devdocs/p4/p4.3.txt (Sections 8, 13)
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.contracts import AgentContext
from backend.app.agents.orchestration.state import sanitize_checkpoint_state
from backend.app.agents.persistence.checkpoints import (
    AgentCheckpointRecord,
    KeepCheckpointStore,
)


class KeepGraphCheckpointStore:
    """Facade scoping multi-agent workflow checkpoints onto KEEP's KeepCheckpointStore."""

    def __init__(self, checkpoint_store: KeepCheckpointStore | None = None) -> None:
        self._store = checkpoint_store or KeepCheckpointStore()

    @staticmethod
    def _thread_id(tenant_id: str, workflow_execution_id: str) -> str:
        return f"wf:{tenant_id}:{workflow_execution_id}"

    async def save_workflow_checkpoint(
        self,
        *,
        workflow_execution_id: str,
        step_name: str,
        step_number: int,
        state: dict[str, Any],
        context: AgentContext,
    ) -> AgentCheckpointRecord:
        """Persists a sanitized, tenant-scoped graph state checkpoint."""
        sanitized = sanitize_checkpoint_state(state)
        return await self._store.save_checkpoint(
            execution_id=workflow_execution_id,
            thread_id=self._thread_id(context.tenant_id, workflow_execution_id),
            step_name=step_name,
            step_number=step_number,
            state=sanitized,
            context=context,
        )

    async def get_latest_workflow_checkpoint(
        self,
        *,
        workflow_execution_id: str,
        context: AgentContext,
    ) -> AgentCheckpointRecord | None:
        """Loads the latest checkpoint strictly within the caller's verified tenant boundary."""
        return await self._store.get_latest_checkpoint(
            thread_id=self._thread_id(context.tenant_id, workflow_execution_id),
            context=context,
        )
