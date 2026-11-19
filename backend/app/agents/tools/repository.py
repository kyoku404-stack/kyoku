"""KEEP Phase 4.6 — Tool Repository & Persistence Layer.

Provides database persistence and retrieval for ToolInvocationModel
and ToolAuditLogModel with strict tenant boundary enforcement.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any

from backend.app.agents.tools.audit import ToolAuditEvent, _sanitize_payload
from backend.app.agents.tools.contracts import (
    ToolCallRequest,
    ToolCallResult,
    ToolContext,
)
from backend.app.models.agent_tool import (
    ToolAuditLogModel,
    ToolInvocationModel,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ToolRepository:
    """Repository managing persistence for tool invocation records and audit logs."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session = session
        # In-memory storage for test/standalone environments without DB session
        self._memory_invocations: dict[str, dict[str, Any]] = {}
        self._memory_audit_logs: list[dict[str, Any]] = []

    async def save_invocation(
        self,
        request: ToolCallRequest,
        context: ToolContext,
        result: ToolCallResult,
    ) -> ToolInvocationModel:
        """Persists or updates an invocation record."""
        now = datetime.datetime.now(datetime.UTC)
        sanitized_input = _sanitize_payload(request.arguments)
        sanitized_output = _sanitize_payload(result.output) if result.output else {}

        if self._session is not None:
            stmt = select(ToolInvocationModel).where(
                ToolInvocationModel.call_id == request.call_id,
                ToolInvocationModel.tenant_id == context.tenant_id,
            )
            existing = (await self._session.execute(stmt)).scalar_one_or_none()

            if existing is not None:
                existing.status = result.status
                existing.completed_at = now
                existing.duration_ms = result.duration_ms
                existing.error_code = result.error_code
                existing.output_summary = sanitized_output
                await self._session.commit()
                await self._session.refresh(existing)
                return existing

            record = ToolInvocationModel(
                id=uuid.uuid4(),
                call_id=request.call_id,
                tool_id=request.tool_id,
                tool_version="1.0.0",
                tenant_id=context.tenant_id,
                requested_by=context.user_id,
                agent_execution_id=context.agent_execution_id,
                workflow_execution_id=context.workflow_execution_id,
                correlation_id=context.correlation_id,
                idempotency_key=request.idempotency_key,
                status=result.status,
                started_at=now,
                completed_at=now,
                duration_ms=result.duration_ms,
                error_code=result.error_code,
                input_summary=sanitized_input,
                output_summary=sanitized_output,
            )
            self._session.add(record)
            await self._session.commit()
            await self._session.refresh(record)
            return record

        # In-memory fallback
        mem_rec = {
            "id": uuid.uuid4(),
            "call_id": request.call_id,
            "tool_id": request.tool_id,
            "tool_version": "1.0.0",
            "tenant_id": context.tenant_id,
            "requested_by": context.user_id,
            "agent_execution_id": context.agent_execution_id,
            "workflow_execution_id": context.workflow_execution_id,
            "correlation_id": context.correlation_id,
            "idempotency_key": request.idempotency_key,
            "status": result.status,
            "started_at": now,
            "completed_at": now,
            "duration_ms": result.duration_ms,
            "error_code": result.error_code,
            "input_summary": sanitized_input,
            "output_summary": sanitized_output,
        }
        self._memory_invocations[request.call_id] = mem_rec
        return ToolInvocationModel(**mem_rec)

    async def get_invocation(
        self,
        tenant_id: str,
        call_id: str,
    ) -> ToolInvocationModel | None:
        """Retrieves an invocation record strictly scoped to caller's tenant."""
        if self._session is not None:
            stmt = select(ToolInvocationModel).where(
                ToolInvocationModel.call_id == call_id,
                ToolInvocationModel.tenant_id == tenant_id,
            )
            return (await self._session.execute(stmt)).scalar_one_or_none()

        mem_rec = self._memory_invocations.get(call_id)
        if mem_rec and mem_rec["tenant_id"] == tenant_id:
            return ToolInvocationModel(**mem_rec)
        return None

    async def list_invocations(
        self,
        tenant_id: str,
        tool_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ToolInvocationModel]:
        """Lists invocation records filtered by tenant, tool, and status."""
        if self._session is not None:
            query = select(ToolInvocationModel).where(ToolInvocationModel.tenant_id == tenant_id)
            if tool_id:
                query = query.where(ToolInvocationModel.tool_id == tool_id)
            if status:
                query = query.where(ToolInvocationModel.status == status)
            query = query.order_by(ToolInvocationModel.created_at.desc()).limit(limit)
            rows = (await self._session.execute(query)).scalars().all()
            return list(rows)

        results: list[ToolInvocationModel] = []
        for rec in reversed(list(self._memory_invocations.values())):
            if rec["tenant_id"] == tenant_id:
                if tool_id and rec["tool_id"] != tool_id:
                    continue
                if status and rec["status"] != status:
                    continue
                results.append(ToolInvocationModel(**rec))
                if len(results) >= limit:
                    break
        return results

    async def save_audit_log(self, event: ToolAuditEvent) -> ToolAuditLogModel:
        """Persists a tool audit event."""
        now = datetime.datetime.now(datetime.UTC)
        sanitized_details = _sanitize_payload(event.details)

        if self._session is not None:
            record = ToolAuditLogModel(
                id=uuid.uuid4(),
                event_id=event.event_id,
                call_id=event.call_id,
                tenant_id=event.tenant_id,
                user_id=event.user_id,
                tool_id=event.tool_id,
                decision=event.decision,
                reason_code=event.reason_code,
                timestamp=now,
                details=sanitized_details,
            )
            self._session.add(record)
            await self._session.commit()
            await self._session.refresh(record)
            return record

        mem_rec = {
            "id": uuid.uuid4(),
            "event_id": event.event_id,
            "call_id": event.call_id,
            "tenant_id": event.tenant_id,
            "user_id": event.user_id,
            "tool_id": event.tool_id,
            "decision": event.decision,
            "reason_code": event.reason_code,
            "timestamp": now,
            "details": sanitized_details,
        }
        self._memory_audit_logs.append(mem_rec)
        return ToolAuditLogModel(**mem_rec)

    async def list_audit_logs(
        self,
        tenant_id: str,
        tool_id: str | None = None,
        limit: int = 50,
    ) -> list[ToolAuditLogModel]:
        """Lists audit events for tenant."""
        if self._session is not None:
            query = select(ToolAuditLogModel).where(ToolAuditLogModel.tenant_id == tenant_id)
            if tool_id:
                query = query.where(ToolAuditLogModel.tool_id == tool_id)
            query = query.order_by(ToolAuditLogModel.timestamp.desc()).limit(limit)
            rows = (await self._session.execute(query)).scalars().all()
            return list(rows)

        results: list[ToolAuditLogModel] = []
        for rec in reversed(self._memory_audit_logs):
            if rec["tenant_id"] == tenant_id:
                if tool_id and rec["tool_id"] != tool_id:
                    continue
                results.append(ToolAuditLogModel(**rec))
                if len(results) >= limit:
                    break
        return results
