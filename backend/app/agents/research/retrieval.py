"""KEEP Phase 4.5 — Tenant-Scoped Research Retrieval Service.

Wraps KEEP's Phase 4.1 `KeepKnowledgeAdapter`, `KeepAgentPolicyEngine`, and
`AuthorizedSourceCatalog` to retrieve, enforce tenant & access-tier boundaries,
deduplicate, and sanitize evidence passages without duplicating KEEP's storage
or vector infrastructure.

Owner: Member 2 (Retrieval & Evidence Management)
Specification: devdocs/p4/p4.5.txt (Sections 4.2, 5, 7, 8, 9)
"""

from __future__ import annotations

import time
from typing import Any

from backend.app.agents.adapters.keep_services import KeepKnowledgeAdapter
from backend.app.agents.contracts import AgentContext
from backend.app.agents.errors import (
    AgentTenantIsolationError,
    ResearchRetrievalUnavailableError,
)
from backend.app.agents.research.contracts import (
    ResearchRequest,
    RetrievalOutcome,
)
from backend.app.agents.research.evidence import normalize_evidence_items
from backend.app.agents.research.research_service import (
    caller_can_view_sensitive_evidence,
)
from backend.app.agents.research.source_registry import AuthorizedSourceCatalog
from backend.app.services.security.agent_policy import (
    AgentPolicyInterface,
    KeepAgentPolicyEngine,
)


class KeepResearchRetrievalService:
    """Authorized research retrieval wrapper reusing KEEP's `KeepKnowledgeAdapter`."""

    def __init__(
        self,
        *,
        knowledge_adapter: KeepKnowledgeAdapter | None = None,
        source_catalog: AuthorizedSourceCatalog | None = None,
        policy: AgentPolicyInterface | None = None,
    ) -> None:
        self._policy: AgentPolicyInterface = policy or KeepAgentPolicyEngine()
        self._catalog = source_catalog or AuthorizedSourceCatalog()
        self._knowledge_adapter = knowledge_adapter

    async def retrieve_evidence(
        self,
        request: ResearchRequest,
        context: AgentContext,
    ) -> RetrievalOutcome:
        """Retrieves authorized, deduplicated, sanitized evidence passages for a research query."""
        self._policy.verify_trusted_context(context)
        started = time.perf_counter()

        allow_sensitive = caller_can_view_sensitive_evidence(context)
        raw_hits: list[dict[str, Any]] = []
        filtered_restricted = 0
        warnings: list[str] = []

        try:
            # 1. Query KEEP's Phase 4.1 KeepKnowledgeAdapter if configured
            if self._knowledge_adapter is not None:
                adapter_refs = await self._knowledge_adapter.search_knowledge(
                    request.question,
                    context,
                    limit=request.max_sources,
                )
                for ref in adapter_refs:
                    if ref.tenant_id is not None:
                        self._policy.enforce_tenant_boundary(context, ref.tenant_id)
                    raw_hits.append(
                        {
                            "source_id": ref.source_id,
                            "source_title": ref.title or ref.source_id,
                            "passage": ref.excerpt or "",
                            "retrieval_reference": ref.uri or f"{ref.source_id}#chunk:{ref.chunk_index or 0}",
                            "relevance_score": ref.score,
                            "tenant_id": ref.tenant_id or context.tenant_id,
                            "access_tier": "read",
                            "metadata": {"provider": "keep_knowledge_adapter"},
                        }
                    )

            # 2. Query authorized internal KEEP catalog (preserving dates, access tiers, and stances)
            catalog_hits, filtered_restricted = await self._catalog.search(
                context.tenant_id,
                request.question,
                limit=request.max_sources,
                scope=request.scope,
                allow_sensitive=allow_sensitive,
            )
            for hit in catalog_hits:
                hit_tenant = str(hit.get("tenant_id") or context.tenant_id)
                self._policy.enforce_tenant_boundary(context, hit_tenant)
                raw_hits.append(hit)

        except AgentTenantIsolationError:
            raise
        except ResearchRetrievalUnavailableError:
            raise
        except Exception as exc:
            raise ResearchRetrievalUnavailableError(
                f"KEEP knowledge retrieval backend failed: {exc}"
            ) from exc

        sources_retrieved = len(raw_hits)
        evidence_items, sanitized_count = normalize_evidence_items(
            raw_hits,
            max_items=request.max_sources,
            policy=self._policy,
        )

        if sanitized_count > 0:
            warnings.append(
                f"Sanitized untrusted control directives from {sanitized_count} retrieved passage(s)."
            )
        if filtered_restricted > 0:
            warnings.append(
                f"Excluded {filtered_restricted} restricted source(s) outside caller's authorization tier."
            )

        elapsed_ms = max(1, int((time.perf_counter() - started) * 1000))
        return RetrievalOutcome(
            evidence=evidence_items,
            sources_retrieved=sources_retrieved,
            sources_retained=len(evidence_items),
            retrieval_latency_ms=elapsed_ms,
            sanitized_passages_count=sanitized_count,
            filtered_restricted_count=filtered_restricted,
            warnings=warnings,
        )
