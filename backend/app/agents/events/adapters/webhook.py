"""KEEP Phase 4.10 — Authenticated External Webhook Adapter.

Verifies HMAC-SHA256 signatures, timestamp replay windows, payload size limits,
and source enablement before admitting external webhooks into EventIngestionService.

Owner: Member 1 / Member 3 (Webhook Ingestion Security)
Specification: devdocs/p4/p4.10.txt (Section 10)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

from backend.app.agents.errors import (
    EventValidationError,
    WebhookAuthenticationError,
    WebhookReplayDetectedError,
)
from backend.app.agents.events.contracts import (
    EventAuditRecord,
    EventPublishRequest,
    EventSecurityContext,
    WebhookReceipt,
    WebhookSourceConfig,
)
from backend.app.agents.events.ingestion import EventIngestionService


class WebhookSourceRegistry:
    """Tenant-scoped registry of authenticated external webhook sources."""

    def __init__(self) -> None:
        self._sources: dict[str, WebhookSourceConfig] = {}

    def register(self, config: WebhookSourceConfig) -> None:
        self._sources[config.source_id] = config

    def get(self, source_id: str) -> WebhookSourceConfig | None:
        return self._sources.get(source_id)


class WebhookIngestionAdapter:
    """Verifies HMAC-SHA256 webhook signatures, timestamps, and replay windows."""

    def __init__(
        self,
        ingestion_service: EventIngestionService,
        source_registry: WebhookSourceRegistry | None = None,
    ) -> None:
        self.ingestion_service = ingestion_service
        self.source_registry = source_registry or WebhookSourceRegistry()

    @staticmethod
    def compute_signature(secret: str, timestamp: str, raw_body: bytes) -> str:
        """Computes canonical `v1=<hex>` HMAC-SHA256 signature over `timestamp.body`."""
        signed_payload = f"{timestamp}.".encode() + raw_body
        digest = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        return f"v1={digest}"

    async def handle_webhook(
        self,
        *,
        source_id: str,
        raw_body: bytes,
        signature_header: str | None,
        timestamp_header: str | None,
        correlation_id: str | None = None,
        now_epoch: float | None = None,
    ) -> WebhookReceipt:
        config = self.source_registry.get(source_id)
        if config is None or not config.enabled:
            raise WebhookAuthenticationError(
                f"Webhook source '{source_id}' is not registered or disabled."
            )

        if len(raw_body) > config.max_payload_bytes:
            raise EventValidationError(
                f"Webhook body exceeds max_payload_bytes ({config.max_payload_bytes})."
            )

        if not timestamp_header or not signature_header:
            await self.ingestion_service.event_store.append_audit(
                EventAuditRecord(
                    tenant_id=config.tenant_id,
                    action="webhook.rejected",
                    actor_id=f"webhook:{source_id}",
                    reason="Missing signature or timestamp header.",
                )
            )
            raise WebhookAuthenticationError("Missing X-KEEP-Signature or X-KEEP-Timestamp header.")

        try:
            ts_val = float(timestamp_header.strip())
        except ValueError as exc:
            raise WebhookAuthenticationError("Malformed X-KEEP-Timestamp header.") from exc

        current_ts = now_epoch if now_epoch is not None else time.time()
        if abs(current_ts - ts_val) > config.replay_window_seconds:
            await self.ingestion_service.event_store.append_audit(
                EventAuditRecord(
                    tenant_id=config.tenant_id,
                    action="webhook.rejected",
                    actor_id=f"webhook:{source_id}",
                    reason="Webhook timestamp outside replay protection window.",
                )
            )
            raise WebhookReplayDetectedError(
                f"Webhook timestamp skewed beyond ±{config.replay_window_seconds}s replay window."
            )

        expected_sig = self.compute_signature(
            config.secret, timestamp_header.strip(), raw_body
        )
        normalized_sig = signature_header.strip()
        if not hmac.compare_digest(expected_sig, normalized_sig):
            await self.ingestion_service.event_store.append_audit(
                EventAuditRecord(
                    tenant_id=config.tenant_id,
                    action="webhook.rejected",
                    actor_id=f"webhook:{source_id}",
                    reason="HMAC-SHA256 signature verification failed.",
                )
            )
            raise WebhookAuthenticationError("Signature verification failed.")

        try:
            body_json: Any = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EventValidationError("Webhook body must be valid UTF-8 JSON.") from exc

        if not isinstance(body_json, dict):
            raise EventValidationError("Webhook JSON payload must be an object.")

        payload_data = body_json.get("payload") if isinstance(body_json.get("payload"), dict) else body_json
        sec_ctx = EventSecurityContext(
            tenant_id=config.tenant_id,
            user_id=f"webhook:{source_id}",
            roles=["service"],
            permissions=["agent.invoke", "agent.read"],
            trusted_source=f"webhook.{source_id}",
            correlation_id=correlation_id,
        )
        req = EventPublishRequest(
            event_id=body_json.get("event_id"),
            event_type=str(body_json.get("event_type") or config.event_type),
            schema_version=int(body_json.get("schema_version") or 1),
            source=f"webhook.{source_id}",
            resource_id=body_json.get("resource_id"),
            correlation_id=correlation_id,
            payload=dict(payload_data),
        )
        event, delivery, deduplicated = await self.ingestion_service.ingest(req, sec_ctx)
        return WebhookReceipt(
            accepted=True,
            source_id=source_id,
            event_id=event.event_id,
            delivery_id=delivery.delivery_id,
            deduplicated=deduplicated,
        )
