"""KEEP Phase 4.6 — Reference Tool B: report.create_draft.

Controlled state-modifying write tool providing draft creation for findings,
evidence references, and analysis summaries without public exposure or delivery.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from backend.app.agents.tools.base import BasePlatformTool
from backend.app.agents.tools.contracts import ToolContext
from backend.app.agents.tools.metadata import ToolMetadata
from pydantic import BaseModel, Field


class ReportDraftArgs(BaseModel):
    """Input argument schema for report.create_draft."""

    title: str = Field(..., min_length=2, max_length=256, description="Draft report title")
    findings: list[Any] = Field(..., min_length=1, description="List of synthesized findings or claim summaries")
    evidence_ids: list[str] = Field(default_factory=list, description="Referenced evidence passage IDs")
    summary: str | None = Field(default=None, max_length=2048, description="Executive draft summary")


class ReportDraftReturns(BaseModel):
    """Output schema for report.create_draft."""

    draft_id: str
    title: str
    status: str = "draft"
    created_at: str
    item_count: int
    tenant_id: str
    author_id: str


class ReportDraftTool(BasePlatformTool):
    """Controlled draft report generation tool."""

    args_model = ReportDraftArgs
    returns_model = ReportDraftReturns

    def __init__(self) -> None:
        self._drafts: dict[str, dict[str, Any]] = {}
        self._metadata = ToolMetadata(
            tool_id="report.create_draft",
            version="1.0.0",
            description="Creates a controlled draft report from synthesized findings and evidence references.",
            capabilities=["reporting", "draft", "creation", "write"],
            access_mode="write",
            enabled=True,
            requires_approval=False,  # Controlled draft creation is allowed without approval; publishing is approval-gated
            parameters_schema=ReportDraftArgs.model_json_schema(),
            returns_schema=ReportDraftReturns.model_json_schema(),
            timeout_seconds=15.0,
            max_retries=0,  # Strict: write tools cannot retry automatically
            required_roles=["member", "project_manager", "org_admin", "admin"],
        )

    @property
    def metadata(self) -> ToolMetadata:
        return self._metadata

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> dict[str, Any]:
        """Creates an internal draft record bound strictly to caller's tenant and user."""
        draft_id = f"draft_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.datetime.now(datetime.UTC).isoformat()
        findings = arguments["findings"]

        record = {
            "draft_id": draft_id,
            "title": arguments["title"],
            "status": "draft",
            "created_at": now_iso,
            "item_count": len(findings),
            "tenant_id": context.tenant_id,
            "author_id": context.user_id,
            "findings": findings,
            "evidence_ids": arguments.get("evidence_ids", []),
            "summary": arguments.get("summary"),
        }
        self._drafts[draft_id] = record

        return {
            "draft_id": draft_id,
            "title": arguments["title"],
            "status": "draft",
            "created_at": now_iso,
            "item_count": len(findings),
            "tenant_id": context.tenant_id,
            "author_id": context.user_id,
        }

    def get_draft(self, draft_id: str, tenant_id: str) -> dict[str, Any] | None:
        """Helper to inspect created draft with tenant scoping."""
        draft = self._drafts.get(draft_id)
        if draft and draft.get("tenant_id") == tenant_id:
            return draft
        return None
