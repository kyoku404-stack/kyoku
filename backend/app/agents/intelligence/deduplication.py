"""Phase 4.11 — Deterministic Deduplication & Suppression Window Management."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from backend.app.agents.intelligence.contracts import (
    IntelligenceCandidate,
    SuppressionRecord,
    SuppressionScope,
)


def compute_dedup_key(tenant_id: str, candidate: IntelligenceCandidate) -> str:
    """Builds a deterministic deduplication key for a candidate within a tenant."""
    if candidate.dedup_hint:
        raw = f"{tenant_id}:{candidate.category}:{candidate.dedup_hint}"
    else:
        refs = ",".join(sorted(set(candidate.affected_resource_refs or candidate.evidence_refs)))
        normalized_title = " ".join(candidate.title.lower().split())
        raw = f"{tenant_id}:{candidate.category}:{refs}:{normalized_title}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"dedup_{candidate.category}_{digest}"


def build_suppression_record(
    tenant_id: str,
    dedup_key: str,
    reason: str,
    window_seconds: int = 3600,
    scope: SuppressionScope = "tenant",
    user_id: str | None = None,
    now: datetime | None = None,
) -> SuppressionRecord:
    """Constructs a time-bounded suppression record."""
    current = now or datetime.now(UTC)
    return SuppressionRecord(
        tenant_id=tenant_id,
        dedup_key=dedup_key,
        scope=scope,
        user_id=user_id,
        reason=reason,
        suppressed_until=current + timedelta(seconds=max(0, window_seconds)),
        created_at=current,
    )


def is_suppressed(
    active_suppressions: list[SuppressionRecord],
    dedup_key: str,
    user_id: str | None = None,
    now: datetime | None = None,
) -> tuple[bool, str | None]:
    """Checks whether `dedup_key` is suppressed for the tenant/audience or user."""
    current = now or datetime.now(UTC)
    for record in active_suppressions:
        if record.dedup_key != dedup_key:
            continue
        until = record.suppressed_until
        if until.tzinfo is None:
            until = until.replace(tzinfo=UTC)
        if until <= current:
            continue
        if record.scope in ("tenant", "audience"):
            return True, record.reason
        if record.scope == "user" and user_id and record.user_id == user_id:
            return True, record.reason
    return False, None
