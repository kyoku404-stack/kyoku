"""KEEP Phase 4.10 — Event Schema Registry & Payload Validation.

Validates incoming events against registered schemas, checks payload size
and credential/raw-content hygiene, and blocks malformed events before queueing.

Owner: Member 1 (Event Contracts & Ingestion)
Specification: devdocs/p4/p4.10.txt (Section 5)
"""

from __future__ import annotations

import json
import re
from typing import Any

from backend.app.agents.errors import EventValidationError
from backend.app.agents.events.contracts import EventSchemaSpec, KeepEvent

MAX_EVENT_PAYLOAD_BYTES = 65_536
_DISALLOWED_PAYLOAD_KEYS = frozenset(
    {
        "raw_content",
        "file_bytes",
        "document_body",
        "password",
        "secret",
        "api_key",
        "access_token",
        "private_key",
    }
)
_SECRET_VALUE_PATTERN = re.compile(
    r"(?i)(bearer\s+[A-Za-z0-9\-._~+/]+=*|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|sk-[A-Za-z0-9]{16,})"
)


class EventSchemaRegistry:
    """Registry of approved KEEP event types, schema versions, and required metadata fields."""

    def __init__(self, *, strict: bool = True) -> None:
        self._schemas: dict[str, EventSchemaSpec] = {}
        self.strict = strict
        self._register_defaults()

    def _register_defaults(self) -> None:
        defaults = [
            EventSchemaSpec(
                event_type="knowledge.document.uploaded",
                supported_versions=[1],
                required_fields=["document_id"],
                description="Document uploaded into tenant KEEP repository.",
            ),
            EventSchemaSpec(
                event_type="knowledge.document.updated",
                supported_versions=[1],
                required_fields=["document_id"],
                description="Document updated or re-uploaded.",
            ),
            EventSchemaSpec(
                event_type="knowledge.document.deleted",
                supported_versions=[1],
                required_fields=["document_id"],
                description="Document deleted from KEEP repository.",
            ),
            EventSchemaSpec(
                event_type="knowledge.document.indexed",
                supported_versions=[1],
                required_fields=["document_id"],
                description="Document finished RAG/KG indexing successfully.",
            ),
            EventSchemaSpec(
                event_type="ingestion.pipeline.completed",
                supported_versions=[1],
                required_fields=["job_id"],
                description="Ingestion pipeline job completed.",
            ),
            EventSchemaSpec(
                event_type="ingestion.pipeline.failed",
                supported_versions=[1],
                required_fields=["job_id"],
                description="Ingestion pipeline job failed.",
            ),
            EventSchemaSpec(
                event_type="knowledge.source.changed",
                supported_versions=[1],
                required_fields=["source_id"],
                description="Monitored external connector or knowledge source changed.",
            ),
            EventSchemaSpec(
                event_type="schedule.triggered",
                supported_versions=[1],
                required_fields=["schedule_id", "trigger_id"],
                description="Scheduled time-based trigger fired.",
            ),
            EventSchemaSpec(
                event_type="webhook.external.received",
                supported_versions=[1],
                required_fields=[],
                description="Authenticated external webhook payload accepted.",
            ),
            EventSchemaSpec(
                event_type="threshold.metric.breached",
                supported_versions=[1],
                required_fields=["metric", "value"],
                description="Configured enterprise metric threshold crossed.",
            ),
        ]
        for spec in defaults:
            self.register(spec)

    def register(self, spec: EventSchemaSpec) -> None:
        self._schemas[spec.event_type] = spec

    def get(self, event_type: str) -> EventSchemaSpec | None:
        return self._schemas.get(event_type)

    def list_schemas(self) -> list[EventSchemaSpec]:
        return list(self._schemas.values())


class EventValidator:
    """Validates schema registration, required fields, payload size, and secret hygiene."""

    def __init__(
        self,
        schema_registry: EventSchemaRegistry | None = None,
        *,
        max_payload_bytes: int = MAX_EVENT_PAYLOAD_BYTES,
    ) -> None:
        self.schema_registry = schema_registry or EventSchemaRegistry()
        self.max_payload_bytes = max_payload_bytes

    def validate(self, event: KeepEvent) -> None:
        spec = self.schema_registry.get(event.event_type)
        if spec is None:
            if self.schema_registry.strict:
                raise EventValidationError(
                    f"Event type '{event.event_type}' is not registered.",
                    details={"event_type": event.event_type},
                )
        else:
            if event.schema_version not in spec.supported_versions:
                raise EventValidationError(
                    f"Unsupported schema_version {event.schema_version} for event '{event.event_type}'.",
                    details={"supported_versions": spec.supported_versions},
                )
            for req_field in spec.required_fields:
                if req_field not in event.payload or event.payload[req_field] in (None, ""):
                    raise EventValidationError(
                        f"Missing required payload field '{req_field}' for '{event.event_type}'.",
                        details={"missing_field": req_field},
                    )
            if spec.allowed_sources and event.source not in spec.allowed_sources:
                raise EventValidationError(
                    f"Source '{event.source}' is not allowed for event '{event.event_type}'.",
                    details={"source": event.source},
                )

        serialized = json.dumps(event.payload, default=str)
        if len(serialized.encode("utf-8")) > self.max_payload_bytes:
            raise EventValidationError(
                f"Event payload exceeds maximum allowed size ({self.max_payload_bytes} bytes)."
            )

        self._check_payload_hygiene(event.payload)

    def _check_payload_hygiene(self, obj: Any) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if str(k).lower() in _DISALLOWED_PAYLOAD_KEYS:
                    raise EventValidationError(
                        f"Disallowed key '{k}' in event payload; pass authorized resource references instead of raw content or secrets."
                    )
                self._check_payload_hygiene(v)
        elif isinstance(obj, list):
            for item in obj:
                self._check_payload_hygiene(item)
        elif isinstance(obj, str) and _SECRET_VALUE_PATTERN.search(obj):
            raise EventValidationError(
                "Event payload contains credential or token pattern which must not be published in events."
            )
