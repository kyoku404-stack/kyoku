"""KEEP Phase 4.6 — Reference Tool A: knowledge.search.

Read-only platform tool providing authorized document retrieval,
passage search, and provenance metadata under strict tenant isolation.
"""

from __future__ import annotations

from typing import Any

from backend.app.agents.research.source_registry import AuthorizedSourceCatalog
from backend.app.agents.tools.base import BasePlatformTool
from backend.app.agents.tools.contracts import ToolContext
from backend.app.agents.tools.metadata import ToolMetadata
from pydantic import BaseModel, Field


class KnowledgeSearchArgs(BaseModel):
    """Input argument schema for knowledge.search."""

    query: str = Field(..., min_length=1, max_length=512, description="Search query string")
    filters: dict[str, Any] | None = Field(default=None, description="Optional metadata filters")
    limit: int = Field(default=5, ge=1, le=50, description="Maximum number of matches to return")


class SearchMatchItem(BaseModel):
    """Individual search match with document provenance."""

    document_id: str
    title: str
    excerpt: str
    relevance_score: float = 1.0
    source_type: str = "document"
    access_tier: str = "read"


class KnowledgeSearchResults(BaseModel):
    """Structured output schema for knowledge.search."""

    query: str
    matches: list[SearchMatchItem] = Field(default_factory=list)
    total_matches: int = 0
    tenant_id: str


class KnowledgeSearchTool(BasePlatformTool):
    """Authorized knowledge search tool wrapping KEEP document retrieval."""

    args_model = KnowledgeSearchArgs
    returns_model = KnowledgeSearchResults

    def __init__(self, catalog: AuthorizedSourceCatalog | None = None) -> None:
        self._catalog = catalog or AuthorizedSourceCatalog()
        self._metadata = ToolMetadata(
            tool_id="knowledge.search",
            version="1.0.0",
            description="Searches authorized internal knowledge documents, postmortems, and customer feedback.",
            capabilities=["search", "retrieval", "documents"],
            access_mode="read",
            enabled=True,
            requires_approval=False,
            parameters_schema=KnowledgeSearchArgs.model_json_schema(),
            returns_schema=KnowledgeSearchResults.model_json_schema(),
            timeout_seconds=10.0,
            max_retries=2,
            required_roles=["viewer", "member", "project_manager", "org_admin", "admin"],
        )

    @property
    def metadata(self) -> ToolMetadata:
        return self._metadata

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> dict[str, Any]:
        """Executes search strictly within the caller's authorized tenant boundary."""
        query = arguments["query"]
        limit = arguments.get("limit", 5)

        # Retrieve documents from authorized catalog strictly scoped to caller tenant
        raw_result = self._catalog.search(
            tenant_id=context.tenant_id,
            query=query,
            limit=limit,
        )
        if hasattr(raw_result, "__await__"):
            resolved = await raw_result
        else:
            resolved = raw_result

        # Handle tuple of (hits, filtered_count) or direct list
        if isinstance(resolved, tuple):
            hits = resolved[0]
        elif isinstance(resolved, list):
            hits = resolved
        else:
            hits = []

        matches: list[dict[str, Any]] = []
        for item in hits:
            if isinstance(item, dict):
                matches.append(
                    {
                        "document_id": item.get("source_id", "unknown"),
                        "title": item.get("title", "Untitled Document"),
                        "excerpt": (item.get("excerpt") or item.get("passage", ""))[:300],
                        "relevance_score": float(item.get("score", 0.95)),
                        "source_type": str(item.get("source_type", "document")),
                        "access_tier": str(item.get("access_tier", "read")),
                    }
                )
            else:
                matches.append(
                    {
                        "document_id": getattr(item, "source_id", "unknown"),
                        "title": getattr(item, "title", "Untitled Document"),
                        "excerpt": getattr(item, "passage", "")[:300],
                        "relevance_score": 0.95,
                        "source_type": getattr(item, "source_type", "document"),
                        "access_tier": str(getattr(item, "access_tier", "read")),
                    }
                )

        return {
            "query": query,
            "matches": matches,
            "total_matches": len(matches),
            "tenant_id": context.tenant_id,
        }
