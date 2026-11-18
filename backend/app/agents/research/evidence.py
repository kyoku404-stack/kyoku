"""KEEP Phase 4.5 — Evidence Normalization, Deduplication & Untrusted Sanitization.

Converts raw KEEP retrieval hits into deduplicated, provenance-tracked
`EvidenceItem` records with stable `ev_01`, `ev_02`, ... citation identifiers
while neutralizing embedded prompt-injection instructions inside passages.

Owner: Member 2 (Retrieval & Evidence Management)
Specification: devdocs/p4/p4.5.txt (Sections 4.2, 5, 7, 9)
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from backend.app.agents.metadata import CapabilityAccess
from backend.app.agents.research.contracts import EvidenceItem
from backend.app.services.security.agent_policy import (
    AgentPolicyInterface,
    KeepAgentPolicyEngine,
)

_WHITESPACE_RE = re.compile(r"\s+")
_EXTRA_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?i)ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions[^.\n]*\.?",
    ),
    re.compile(
        r"(?i)(?:override|disregard)\s+(?:system|safety|policy)\s+(?:rules|instructions)[^.\n]*\.?",
    ),
    re.compile(
        r"(?i)bypass\s+(?:rbac|security|tenant(?:\s+isolation)?)[^.\n]*\.?",
    ),
    re.compile(
        r"(?i)reveal\s+(?:system\s+prompt|secret|credentials|api\s+key)[^.\n]*\.?",
    ),
)


def sanitize_research_passage(
    passage: str,
    *,
    policy: AgentPolicyInterface | None = None,
) -> tuple[str, bool]:
    """Neutralizes untrusted control directives inside retrieved passages.

    Returns `(cleaned_passage, was_sanitized)`.
    """
    active_policy = policy or KeepAgentPolicyEngine()
    cleaned = active_policy.sanitize_untrusted_content(passage)
    for pattern in _EXTRA_INJECTION_PATTERNS:
        cleaned = pattern.sub("[UNTRUSTED_DIRECTIVE_STRIPPED]", cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    was_sanitized = cleaned != _WHITESPACE_RE.sub(" ", passage).strip()
    return cleaned, was_sanitized


def _dedupe_fingerprint(source_id: str, passage: str) -> str:
    normalized = _WHITESPACE_RE.sub(" ", passage.strip().lower())
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"{source_id.strip().lower()}::{digest}"


def normalize_evidence_items(
    raw_hits: list[dict[str, Any]],
    *,
    max_items: int = 12,
    policy: AgentPolicyInterface | None = None,
) -> tuple[list[EvidenceItem], int]:
    """Deduplicates, sanitizes, and assigns stable `ev_XX` IDs to raw retrieval hits.

    Returns `(evidence_items, sanitized_passages_count)`.
    """
    active_policy = policy or KeepAgentPolicyEngine()
    seen: set[str] = set()
    items: list[EvidenceItem] = []
    sanitized_count = 0

    for hit in raw_hits:
        if len(items) >= max_items:
            break

        raw_passage = str(hit.get("passage") or hit.get("excerpt") or hit.get("content") or "").strip()
        if not raw_passage:
            continue

        source_id = str(hit.get("source_id") or hit.get("id") or "unknown_source").strip()
        source_title = str(hit.get("source_title") or hit.get("title") or source_id).strip()
        retrieval_ref = str(
            hit.get("retrieval_reference") or hit.get("uri") or f"{source_id}#chunk:0"
        ).strip()

        safe_passage, was_sanitized = sanitize_research_passage(raw_passage, policy=active_policy)
        if was_sanitized:
            sanitized_count += 1
        if not safe_passage:
            continue

        key = _dedupe_fingerprint(source_id, safe_passage)
        if key in seen:
            continue
        seen.add(key)

        raw_score = hit.get("relevance_score", hit.get("score"))
        score_val: float | None = None
        if isinstance(raw_score, (int, float)):
            score_val = max(0.0, min(1.0, float(raw_score)))

        raw_tier = str(hit.get("access_tier") or "read").strip().lower()
        access_tier: CapabilityAccess = (
            raw_tier if raw_tier in ("read", "write", "sensitive") else "read"  # type: ignore[assignment]
        )

        doc_date_raw = hit.get("document_date")
        # pyrefly: ignore[unnecessary-type-conversion]
        doc_date = str(doc_date_raw).strip() if isinstance(doc_date_raw, str) and doc_date_raw.strip() else None

        metadata_raw = hit.get("metadata")
        metadata = dict(metadata_raw) if isinstance(metadata_raw, dict) else {}
        if was_sanitized:
            metadata["sanitized_untrusted_content"] = True

        evidence_id = f"ev_{len(items) + 1:02d}"
        items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                source_id=source_id,
                source_title=source_title,
                passage=safe_passage[:4000],
                retrieval_reference=retrieval_ref,
                relevance_score=score_val,
                document_date=doc_date,
                access_tier=access_tier,
                metadata=metadata,
            )
        )

    return items, sanitized_count
