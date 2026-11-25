"""Phase 4.10 Member 1 Unit Tests — Event Contracts, Schema Validation & Ingestion."""

from __future__ import annotations

import json
import time

import pytest

from backend.app.agents.errors import (
    EventDuplicateError,
    EventTenantMismatchError,
    EventValidationError,
    WebhookAuthenticationError,
    WebhookReplayDetectedError,
)
from backend.app.agents.events.adapters.internal import InternalKeepEventAdapter
from backend.app.agents.events.adapters.webhook import (
    WebhookIngestionAdapter,
    WebhookSourceRegistry,
)
from backend.app.agents.events.contracts import (
    EventPublishRequest,
    EventSecurityContext,
    WebhookSourceConfig,
)
from backend.app.agents.events.event_store import InMemoryEventStore
from backend.app.agents.events.ingestion import EventIngestionService
from backend.app.agents.events.publisher import OutboxEventRelay


def _ctx(tenant: str = "tenant-evt", user: str = "svc-knowledge") -> EventSecurityContext:
    return EventSecurityContext(
        tenant_id=tenant,
        user_id=user,
        roles=["service"],
        permissions=["agent.invoke", "agent.read"],
        trusted_source="keep.knowledge",
    )


@pytest.mark.asyncio
async def test_valid_event_accepted_and_preserves_metadata():
    store = InMemoryEventStore()
    ingestion = EventIngestionService(store)
    adapter = InternalKeepEventAdapter(ingestion)

    event, delivery, deduplicated = await adapter.emit_document_indexed(
        tenant_id="tenant-evt",
        user_id="svc-knowledge",
        document_id="doc-789",
        collection_id="col-10",
        correlation_id="corr-456",
        event_id="evt-12345",
    )

    assert deduplicated is False
    assert event.event_id == "evt-12345"
    assert event.schema_version == 1
    assert event.correlation_id == "corr-456"
    assert event.tenant_id == "tenant-evt"
    assert event.published_at is not None
    assert delivery.status == "pending"


@pytest.mark.asyncio
async def test_malformed_and_secret_bearing_events_rejected():
    store = InMemoryEventStore()
    ingestion = EventIngestionService(store)

    # Unregistered event type rejected
    with pytest.raises(EventValidationError):
        await ingestion.ingest(
            EventPublishRequest(event_type="unknown.arbitrary.event", payload={"document_id": "1"}),
            _ctx(),
        )

    # Missing required field `document_id` rejected
    with pytest.raises(EventValidationError):
        await ingestion.ingest(
            EventPublishRequest(event_type="knowledge.document.indexed", payload={}),
            _ctx(),
        )

    # Raw content / credentials rejected
    with pytest.raises(EventValidationError):
        await ingestion.ingest(
            EventPublishRequest(
                event_type="knowledge.document.indexed",
                payload={"document_id": "doc-1", "api_key": "sk-secret1234567890abcdef"},
            ),
            _ctx(),
        )


@pytest.mark.asyncio
async def test_tenant_spoofing_and_idempotent_deduplication():
    store = InMemoryEventStore()
    ingestion = EventIngestionService(store)

    with pytest.raises(EventTenantMismatchError):
        await ingestion.ingest(
            EventPublishRequest(
                event_type="knowledge.document.indexed",
                tenant_id="tenant-victim",
                payload={"document_id": "doc-1"},
            ),
            _ctx(tenant="tenant-attacker"),
        )

    req = EventPublishRequest(
        event_id="evt-idem-01",
        event_type="knowledge.document.indexed",
        payload={"document_id": "doc-1"},
    )
    _, d1, dedup1 = await ingestion.ingest(req, _ctx())
    _, d2, dedup2 = await ingestion.ingest(req, _ctx())
    assert dedup1 is False
    assert dedup2 is True
    assert d1.delivery_id == d2.delivery_id

    # Same event_id with altered payload triggers conflict
    with pytest.raises(EventDuplicateError):
        await ingestion.ingest(
            EventPublishRequest(
                event_id="evt-idem-01",
                event_type="knowledge.document.indexed",
                payload={"document_id": "doc-different"},
            ),
            _ctx(),
        )


@pytest.mark.asyncio
async def test_transactional_outbox_relay():
    store = InMemoryEventStore()
    ingestion = EventIngestionService(store)
    relay = OutboxEventRelay(store)

    ev, _, _ = await ingestion.ingest(
        EventPublishRequest(
            event_id="evt-outbox-1",
            event_type="knowledge.document.indexed",
            payload={"document_id": "doc-99"},
            use_outbox=True,
        ),
        _ctx(),
    )
    assert ev.outbox_published is False
    assert await store.list_deliveries_for_event("evt-outbox-1", "tenant-evt") == []

    relayed = await relay.relay_pending(tenant_id="tenant-evt")
    assert len(relayed) == 1
    updated = await store.get_event("evt-outbox-1", "tenant-evt")
    assert updated is not None
    assert updated.outbox_published is True


@pytest.mark.asyncio
async def test_webhook_hmac_signature_and_replay_window():
    store = InMemoryEventStore()
    ingestion = EventIngestionService(store)
    src_registry = WebhookSourceRegistry()
    src_registry.register(
        WebhookSourceConfig(
            source_id="github_enterprise",
            tenant_id="tenant-hook",
            secret="super_secret_hmac_signing_key",
            replay_window_seconds=300,
        )
    )
    adapter = WebhookIngestionAdapter(ingestion, src_registry)

    now_ts = int(time.time())
    body = json.dumps({"event_id": "wh-1", "payload": {"repo": "keep"}}).encode("utf-8")
    sig = adapter.compute_signature("super_secret_hmac_signing_key", str(now_ts), body)

    receipt = await adapter.handle_webhook(
        source_id="github_enterprise",
        raw_body=body,
        signature_header=sig,
        timestamp_header=str(now_ts),
        now_epoch=float(now_ts),
    )
    assert receipt.accepted is True
    assert receipt.event_id == "wh-1"

    # Bad signature rejected
    with pytest.raises(WebhookAuthenticationError):
        await adapter.handle_webhook(
            source_id="github_enterprise",
            raw_body=body,
            signature_header="v1=deadbeef",
            timestamp_header=str(now_ts),
            now_epoch=float(now_ts),
        )

    # Stale timestamp outside replay window rejected
    stale_ts = now_ts - 600
    stale_sig = adapter.compute_signature("super_secret_hmac_signing_key", str(stale_ts), body)
    with pytest.raises(WebhookReplayDetectedError):
        await adapter.handle_webhook(
            source_id="github_enterprise",
            raw_body=body,
            signature_header=stale_sig,
            timestamp_header=str(stale_ts),
            now_epoch=float(now_ts),
        )
