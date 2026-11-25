"""KEEP Phase 4.10 — Internal Domain Event Adapter.

Allows existing KEEP subsystems (Documents, Ingestion Pipelines, Connectors)
to emit normalized internal events cleanly into EventIngestionService.

Owner: Member 1 (Event Contracts & Ingestion)
Specification: devdocs/p4/p4.10.txt (Section 4)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.app.agents.events.contracts import (
    EventDeliveryRecord,
    EventPublishRequest,
    EventSecurityContext,
    KeepEvent,
)
from backend.app.agents.events.ingestion import EventIngestionService


class InternalKeepEventAdapter:
    """Convenience helper publishing typed KEEP subsystem domain events."""

    def __init__(self, ingestion_service: EventIngestionService) -> None:
        self.ingestion_service = ingestion_service

    async def emit_document_indexed(
        self,
        *,
        tenant_id: str,
        user_id: str,
        document_id: str,
        collection_id: str | None = None,
        correlation_id: str | None = None,
        event_id: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> tuple[KeepEvent, EventDeliveryRecord, bool]:
        payload: dict[str, Any] = {"document_id": document_id}
        if collection_id is not None:
            payload["collection_id"] = collection_id
        if extra_metadata:
            payload.update(extra_metadata)

        ctx = EventSecurityContext(
            tenant_id=tenant_id,
            user_id=user_id,
            roles=["system"],
            permissions=["agent.invoke", "agent.read"],
            trusted_source="keep.knowledge",
            correlation_id=correlation_id,
        )
        req = EventPublishRequest(
            event_id=event_id,
            event_type="knowledge.document.indexed",
            source="keep.knowledge",
            occurred_at=datetime.now(UTC),
            resource_id=document_id,
            correlation_id=correlation_id,
            payload=payload,
        )
        return await self.ingestion_service.ingest(req, ctx)
