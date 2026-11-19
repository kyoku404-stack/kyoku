"""KEEP Phase 4.6 — Member 2 Tool Execution Engine & Adapters Unit Tests.

Validates BasePlatformTool, KnowledgeSearchTool, ReportDraftTool,
and KeepToolExecutor execution pipelines including timeouts, retries,
and output size bounding.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from backend.app.agents.research.source_registry import (
    AuthorizedSourceCatalog,
    ResearchSourceDocument,
)
from backend.app.agents.tools.adapters.knowledge_search import KnowledgeSearchTool
from backend.app.agents.tools.adapters.report_draft import ReportDraftTool
from backend.app.agents.tools.base import BasePlatformTool
from backend.app.agents.tools.contracts import (
    ToolCallRequest,
    ToolContext,
)
from backend.app.agents.tools.executor import KeepToolExecutor
from backend.app.agents.tools.metadata import ToolMetadata
from backend.app.agents.tools.registry import ToolRegistry


class SlowSleepTool(BasePlatformTool):
    """Tool that deliberately sleeps to verify timeout enforcement."""

    def __init__(self, sleep_seconds: float = 1.0) -> None:
        self.sleep_seconds = sleep_seconds
        self._metadata = ToolMetadata(
            tool_id="test.slow",
            description="Deliberately slow tool",
            access_mode="read",
            timeout_seconds=0.5,  # Valid minimum timeout
        )

    @property
    def metadata(self) -> ToolMetadata:
        return self._metadata

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        await asyncio.sleep(self.sleep_seconds)
        return {"done": True}


class FlakyReadTool(BasePlatformTool):
    """Tool that fails initially then succeeds, to verify bounded retries."""

    def __init__(self, succeed_on_attempt: int = 2) -> None:
        self.attempts = 0
        self.succeed_on_attempt = succeed_on_attempt
        self._metadata = ToolMetadata(
            tool_id="test.flaky_read",
            description="Flaky read tool",
            access_mode="read",
            max_retries=2,
        )

    @property
    def metadata(self) -> ToolMetadata:
        return self._metadata

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        self.attempts += 1
        if self.attempts < self.succeed_on_attempt:
            raise RuntimeError(f"Simulated network glitch on attempt {self.attempts}")
        return {"data": "ok", "attempt": self.attempts}


class HugeOutputTool(BasePlatformTool):
    """Tool that returns output exceeding size limits."""

    def __init__(self) -> None:
        self._metadata = ToolMetadata(
            tool_id="test.huge",
            description="Generates huge payload",
            access_mode="read",
            max_output_bytes=2048,  # 2 KB limit
        )

    @property
    def metadata(self) -> ToolMetadata:
        return self._metadata

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        return {"big_string": "x" * 5000}


class ApprovalGatedWriteTool(BasePlatformTool):
    """Tool requiring approval."""

    def __init__(self) -> None:
        self._metadata = ToolMetadata(
            tool_id="system.deploy",
            description="Deploy system update",
            access_mode="write",
            requires_approval=True,
        )

    @property
    def metadata(self) -> ToolMetadata:
        return self._metadata

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        return {"deployed": True}


@pytest.fixture
def tool_context() -> ToolContext:
    return ToolContext(
        tenant_id="tenant-alpha",
        user_id="user-1",
        roles=["member"],
    )


@pytest.mark.asyncio
class TestKnowledgeSearchTool:
    """Validates KnowledgeSearchTool behavior and tenant isolation."""

    async def test_search_execution_tenant_isolation(self, tool_context: ToolContext) -> None:
        catalog = AuthorizedSourceCatalog()
        # Seed test document for tenant-alpha
        catalog.add_document(
            ResearchSourceDocument(
                source_id="doc_alpha_1",
                tenant_id="tenant-alpha",
                title="Q3 Incident Postmortem",
                passage="The latency degradation was caused by an unindexed tenant query.",
                source_type="postmortem",
                retrieval_reference="pm_q3_chunk_01",
            )
        )
        # Seed test document for tenant-beta
        catalog.add_document(
            ResearchSourceDocument(
                source_id="doc_beta_1",
                tenant_id="tenant-beta",
                title="Q3 Incident Postmortem Beta",
                passage="Beta latency degradation postmortem details.",
                source_type="postmortem",
                retrieval_reference="pm_beta_chunk_01",
            )
        )

        tool = KnowledgeSearchTool(catalog=catalog)
        assert tool.metadata.tool_id == "knowledge.search"
        assert tool.metadata.access_mode == "read"

        # Validate arguments
        validated = tool.validate_arguments({"query": "latency degradation", "limit": 5})
        assert validated["query"] == "latency degradation"

        # Execute under tenant-alpha context
        res = await tool.execute(validated, tool_context)
        doc_ids = [m["document_id"] for m in res["matches"]]
        assert "doc_alpha_1" in doc_ids
        assert "doc_beta_1" not in doc_ids
        assert res["tenant_id"] == "tenant-alpha"


@pytest.mark.asyncio
class TestReportDraftTool:
    """Validates ReportDraftTool behavior and draft storage."""

    async def test_draft_creation(self, tool_context: ToolContext) -> None:
        tool = ReportDraftTool()
        assert tool.metadata.tool_id == "report.create_draft"
        assert tool.metadata.access_mode == "write"
        assert tool.metadata.max_retries == 0

        args = {
            "title": "Quarterly Reliability Findings",
            "findings": [{"claim": "Database connection pool exhausted", "severity": "high"}],
            "evidence_ids": ["ev_1", "ev_2"],
            "summary": "Summary of incident review",
        }
        validated = tool.validate_arguments(args)
        res = await tool.execute(validated, tool_context)

        assert res["status"] == "draft"
        assert res["title"] == "Quarterly Reliability Findings"
        assert res["item_count"] == 1
        assert res["tenant_id"] == "tenant-alpha"
        assert res["author_id"] == "user-1"

        # Verify draft lookup
        draft = tool.get_draft(res["draft_id"], "tenant-alpha")
        assert draft is not None
        assert draft["title"] == "Quarterly Reliability Findings"

        # Cross-tenant draft lookup returns None
        assert tool.get_draft(res["draft_id"], "tenant-beta") is None


@pytest.mark.asyncio
class TestKeepToolExecutor:
    """Validates KeepToolExecutor execution pipeline, timeouts, retries, and errors."""

    async def test_successful_invocation(self, tool_context: ToolContext) -> None:
        registry = ToolRegistry()
        tool = ReportDraftTool()
        registry.register(tool)

        executor = KeepToolExecutor(registry=registry)
        req = ToolCallRequest(
            tool_id="report.create_draft",
            arguments={"title": "Draft 1", "findings": ["Finding A"]},
        )
        res = await executor.invoke(req, tool_context)
        assert res.status == "succeeded"
        assert res.output is not None
        assert res.output["title"] == "Draft 1"
        assert res.duration_ms >= 0

    async def test_unknown_tool_rejection(self, tool_context: ToolContext) -> None:
        registry = ToolRegistry()
        executor = KeepToolExecutor(registry=registry)
        req = ToolCallRequest(tool_id="nonexistent.tool", arguments={})
        res = await executor.invoke(req, tool_context)

        assert res.status == "failed"
        assert res.error_code == "TOOL_NOT_FOUND"
        assert "not registered" in (res.error_message or "")

    async def test_disabled_tool_rejection(self, tool_context: ToolContext) -> None:
        registry = ToolRegistry()
        tool = ReportDraftTool()
        registry.register(tool)
        registry.disable("report.create_draft")

        executor = KeepToolExecutor(registry=registry)
        req = ToolCallRequest(tool_id="report.create_draft", arguments={"title": "A", "findings": ["B"]})
        res = await executor.invoke(req, tool_context)

        assert res.status == "denied"
        assert res.error_code == "TOOL_DISABLED"

    async def test_invalid_argument_rejection(self, tool_context: ToolContext) -> None:
        registry = ToolRegistry()
        tool = ReportDraftTool()
        registry.register(tool)

        executor = KeepToolExecutor(registry=registry)
        # Missing required 'findings' argument
        req = ToolCallRequest(tool_id="report.create_draft", arguments={"title": "Missing findings"})
        res = await executor.invoke(req, tool_context)

        assert res.status == "failed"
        assert res.error_code == "TOOL_ARGUMENT_INVALID"

    async def test_timeout_enforcement(self, tool_context: ToolContext) -> None:
        registry = ToolRegistry()
        slow_tool = SlowSleepTool(sleep_seconds=1.0)
        registry.register(slow_tool)

        executor = KeepToolExecutor(registry=registry)
        req = ToolCallRequest(tool_id="test.slow", arguments={})
        res = await executor.invoke(req, tool_context)

        assert res.status == "timed_out"
        assert res.error_code == "TOOL_TIMED_OUT"

    async def test_bounded_retries_on_read_tool(self, tool_context: ToolContext) -> None:
        registry = ToolRegistry()
        flaky_tool = FlakyReadTool(succeed_on_attempt=2)
        registry.register(flaky_tool)

        executor = KeepToolExecutor(registry=registry)
        req = ToolCallRequest(tool_id="test.flaky_read", arguments={})
        res = await executor.invoke(req, tool_context)

        assert res.status == "succeeded"
        assert flaky_tool.attempts == 2

    async def test_output_size_bounding(self, tool_context: ToolContext) -> None:
        registry = ToolRegistry()
        huge_tool = HugeOutputTool()
        registry.register(huge_tool)

        executor = KeepToolExecutor(registry=registry)
        req = ToolCallRequest(tool_id="test.huge", arguments={})
        res = await executor.invoke(req, tool_context)

        assert res.status == "failed"
        assert res.error_code == "TOOL_OUTPUT_TOO_LARGE"

    async def test_approval_gated_tool(self, tool_context: ToolContext) -> None:
        registry = ToolRegistry()
        gated_tool = ApprovalGatedWriteTool()
        registry.register(gated_tool)

        executor = KeepToolExecutor(registry=registry)
        req = ToolCallRequest(tool_id="system.deploy", arguments={})
        res = await executor.invoke(req, tool_context)

        assert res.status == "approval_required"
        assert res.error_code == "TOOL_APPROVAL_REQUIRED"
