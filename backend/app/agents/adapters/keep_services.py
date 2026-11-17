"""KEEP Phase 4.1 — Tenant-Scoped Adapters for Existing KEEP Platform Services.

Wraps existing KEEP knowledge search and document interfaces behind strict
`AgentContext` tenant-isolation and untrusted-content sanitization checks so
agents consume KEEP capabilities without duplicating business logic or bypassing
authorization boundaries.

Owner: Member 4 (KEEP Integration, Reference Agent & QA)
Specification: devdocs/p4/p4.1.txt (Sections 2, 3, 7, 9)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from backend.app.agents.contracts import AgentContext, EvidenceReference
from backend.app.services.security.agent_policy import (
    AgentPolicyInterface,
    KeepAgentPolicyEngine,
)

# Callable signature matching KEEP's tenant-scoped search/document services
SearchBackendFn = Callable[[str, str, int], Awaitable[list[dict[str, Any]]]]
DocumentFetchFn = Callable[[str, str], Awaitable[dict[str, Any] | None]]


class KeepKnowledgeAdapter:
    """Read-only, tenant-scoped adapter around KEEP's organizational knowledge search."""

    def __init__(
        self,
        *,
        search_fn: SearchBackendFn | None = None,
        policy: AgentPolicyInterface | None = None,
    ) -> None:
        self._search_fn = search_fn
        self._policy: AgentPolicyInterface = policy or KeepAgentPolicyEngine()

    async def search_knowledge(
        self,
        query: str,
        context: AgentContext,
        *,
        limit: int = 5,
    ) -> list[EvidenceReference]:
        """Executes a tenant-scoped knowledge lookup and returns sanitized EvidenceReferences."""
        self._policy.verify_trusted_context(context)
        cleaned_query = query.strip()
        if not cleaned_query or self._search_fn is None:
            return []

        raw_hits = await self._search_fn(context.tenant_id, cleaned_query, limit)
        evidence: list[EvidenceReference] = []
        for hit in raw_hits:
            hit_tenant = str(hit.get("tenant_id") or hit.get("organization_id") or context.tenant_id)
            # Enforce tenant isolation even if an upstream backend returns an unexpected tenant hit
            self._policy.enforce_tenant_boundary(context, hit_tenant)

            raw_excerpt = str(hit.get("excerpt") or hit.get("content") or "")
            safe_excerpt = self._policy.sanitize_untrusted_content(raw_excerpt) if raw_excerpt else None

            raw_score = hit.get("score")
            score_val = float(raw_score) if isinstance(raw_score, (int, float)) else None
            if score_val is not None:
                score_val = max(0.0, min(1.0, score_val))

            evidence.append(
                EvidenceReference(
                    source_id=str(hit.get("source_id") or hit.get("id") or "unknown"),
                    source_type=hit.get("source_type", "document"),
                    title=hit.get("title"),
                    excerpt=safe_excerpt,
                    uri=hit.get("uri"),
                    score=score_val,
                    chunk_index=hit.get("chunk_index"),
                    tenant_id=context.tenant_id,
                )
            )
        return evidence


class KeepDocumentAdapter:
    """Read-only, tenant-scoped adapter for fetching KEEP document metadata/summaries."""

    def __init__(
        self,
        *,
        fetch_fn: DocumentFetchFn | None = None,
        policy: AgentPolicyInterface | None = None,
    ) -> None:
        self._fetch_fn = fetch_fn
        self._policy: AgentPolicyInterface = policy or KeepAgentPolicyEngine()

    async def get_document(
        self,
        document_id: str,
        context: AgentContext,
    ) -> dict[str, Any] | None:
        """Fetches a document strictly within `context.tenant_id`, blocking cross-tenant reads."""
        self._policy.verify_trusted_context(context)
        if self._fetch_fn is None:
            return None

        doc = await self._fetch_fn(context.tenant_id, document_id)
        if doc is None:
            return None

        doc_tenant = str(doc.get("tenant_id") or doc.get("organization_id") or "")
        self._policy.enforce_tenant_boundary(context, doc_tenant)

        sanitized_doc = dict(doc)
        if isinstance(sanitized_doc.get("content"), str):
            sanitized_doc["content"] = self._policy.sanitize_untrusted_content(
                sanitized_doc["content"]
            )
        return sanitized_doc
