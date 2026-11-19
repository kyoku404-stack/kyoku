"""KEEP Phase 4.6 — Member 1 Tool Registry & Contracts Unit Tests.

Validates ToolMetadata, ToolContext, ToolCallRequest, ToolCallResult,
BaseTool protocol, and ToolRegistry lifecycle & discovery operations.
"""

from typing import Any

import pytest

from backend.app.agents.errors import (
    ToolAlreadyRegisteredError,
    ToolDisabledError,
    ToolNotFoundError,
)
from backend.app.agents.tools.contracts import (
    BaseTool,
    ToolCallRequest,
    ToolCallResult,
    ToolContext,
)
from backend.app.agents.tools.metadata import ToolMetadata
from backend.app.agents.tools.registry import ToolRegistry


class DummyMockTool:
    """Mock implementation of BaseTool for registry tests."""

    def __init__(self, tool_id: str = "mock.test", access_mode: str = "read", enabled: bool = True) -> None:
        self._metadata = ToolMetadata(
            tool_id=tool_id,
            version="1.0.0",
            description="A test mock tool for unit verification",
            capabilities=["test", "mock"],
            access_mode=access_mode,  # type: ignore[arg-type]
            enabled=enabled,
            requires_approval=(access_mode == "write"),
            parameters_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            returns_schema={
                "type": "object",
                "properties": {"result": {"type": "string"}},
            },
        )

    @property
    def metadata(self) -> ToolMetadata:
        return self._metadata

    def validate_arguments(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if "query" not in arguments:
            raise ValueError("Missing required 'query' argument")
        return arguments

    def validate_output(self, output: dict[str, Any]) -> dict[str, Any]:
        return output

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        return {"result": f"Executed with query: {arguments.get('query')}"}


class TestToolMetadataAndContracts:
    """Validates contracts, metadata validation, and context models."""

    def test_tool_metadata_validations(self) -> None:
        meta = ToolMetadata(
            tool_id="knowledge.search",
            version="1.2.0",
            description="Searches authorized enterprise documents",
            capabilities=["search", "rag"],
            access_mode="read",
            max_retries=2,
        )
        assert meta.tool_id == "knowledge.search"
        assert meta.access_mode == "read"
        assert meta.max_retries == 2
        assert meta.enabled is True
        assert meta.requires_approval is False

        # Write tool cannot have retries > 0
        with pytest.raises(ValueError, match="Write tools cannot configure automatic retries"):
            ToolMetadata(
                tool_id="system.mutate",
                description="Modifies system data",
                access_mode="write",
                max_retries=1,
            )

    def test_tool_context_and_admin_helper(self) -> None:
        ctx_user = ToolContext(tenant_id="tenant-123", user_id="user-456", roles=["member"])
        assert ctx_user.tenant_id == "tenant-123"
        assert ctx_user.user_id == "user-456"
        assert ctx_user.is_admin is False
        assert ctx_user.correlation_id.startswith("corr_")

        ctx_admin = ToolContext(tenant_id="tenant-123", user_id="admin-999", roles=["org_admin"])
        assert ctx_admin.is_admin is True

    def test_tool_call_request_and_result_envelopes(self) -> None:
        req = ToolCallRequest(tool_id="knowledge.search", arguments={"query": "test query"})
        assert req.tool_id == "knowledge.search"
        assert req.call_id.startswith("call_")
        assert req.idempotency_key is None

        # Success factory
        res_ok = ToolCallResult.success(
            call_id="call-1",
            tool_id="knowledge.search",
            output={"matches": ["doc1"]},
            duration_ms=45,
        )
        assert res_ok.status == "succeeded"
        assert res_ok.output == {"matches": ["doc1"]}
        assert res_ok.duration_ms == 45

        # Denied factory
        res_denied = ToolCallResult.denied(
            call_id="call-2",
            tool_id="knowledge.search",
            reason="User lacks required role",
        )
        assert res_denied.status == "denied"
        assert res_denied.error_code == "TOOL_PERMISSION_DENIED"

        # Approval required factory
        res_appr = ToolCallResult.approval_required(call_id="call-3", tool_id="report.create_draft")
        assert res_appr.status == "approval_required"
        assert res_appr.error_code == "TOOL_APPROVAL_REQUIRED"

        # Timed out factory
        res_timeout = ToolCallResult.timed_out(
            call_id="call-4",
            tool_id="knowledge.search",
            timeout_seconds=15.0,
        )
        assert res_timeout.status == "timed_out"
        assert "15.0s" in (res_timeout.error_message or "")

        # Failure factory with secret redaction
        res_fail = ToolCallResult.failure(
            call_id="call-5",
            tool_id="knowledge.search",
            error_message="Connection failed with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-ID",
        )
        assert res_fail.status == "failed"
        assert "[REDACTED]" in (res_fail.error_message or "")
        assert "eyJhbGciOiJIUzI1Ni" not in (res_fail.error_message or "")


class TestToolRegistry:
    """Validates ToolRegistry cataloging, duplicate detection, discovery, and toggling."""

    def test_register_and_get_tool(self) -> None:
        registry = ToolRegistry()
        tool = DummyMockTool("test.search")
        assert isinstance(tool, BaseTool)

        registry.register(tool)
        assert registry.is_registered("test.search") is True
        assert registry.is_enabled("test.search") is True

        retrieved = registry.get("test.search")
        assert retrieved.metadata.tool_id == "test.search"

    def test_duplicate_registration_rejected(self) -> None:
        registry = ToolRegistry()
        tool1 = DummyMockTool("test.search")
        tool2 = DummyMockTool("test.search")

        registry.register(tool1)
        with pytest.raises(ToolAlreadyRegisteredError, match="Tool with ID 'test.search' is already registered"):
            registry.register(tool2)

    def test_invalid_tool_registration_rejected(self) -> None:
        registry = ToolRegistry()
        with pytest.raises(TypeError, match="must define a valid 'metadata: ToolMetadata' property"):
            registry.register("not_a_tool")  # type: ignore[arg-type]

    def test_get_nonexistent_tool_raises_not_found(self) -> None:
        registry = ToolRegistry()
        with pytest.raises(ToolNotFoundError, match="Tool 'unknown.tool' is not registered"):
            registry.get("unknown.tool")

    def test_enable_disable_lifecycle(self) -> None:
        registry = ToolRegistry()
        tool = DummyMockTool("test.tool")
        registry.register(tool)

        # Disable
        registry.disable("test.tool")
        assert registry.is_enabled("test.tool") is False

        # Getting disabled tool raises ToolDisabledError by default
        with pytest.raises(ToolDisabledError, match="Tool 'test.tool' is currently disabled"):
            registry.get("test.tool")

        # Explicit check_enabled=False succeeds
        tool_disabled = registry.get("test.tool", check_enabled=False)
        assert tool_disabled.metadata.enabled is False

        # Re-enable
        registry.enable("test.tool")
        assert registry.is_enabled("test.tool") is True
        assert registry.get("test.tool").metadata.enabled is True

    def test_list_tools_filtering(self) -> None:
        registry = ToolRegistry()
        tool1 = DummyMockTool("tool.one", enabled=True)
        tool2 = DummyMockTool("tool.two", enabled=False)

        registry.register(tool1)
        registry.register(tool2)

        enabled_only = registry.list_tools(include_disabled=False)
        assert len(enabled_only) == 1
        assert enabled_only[0].tool_id == "tool.one"

        all_tools = registry.list_tools(include_disabled=True)
        assert len(all_tools) == 2

    def test_list_for_role_and_export_schemas(self) -> None:
        registry = ToolRegistry()
        tool_pub = DummyMockTool("tool.public")
        tool_admin = DummyMockTool("tool.admin")
        tool_admin.metadata.required_roles = ["org_admin"]

        registry.register(tool_pub)
        registry.register(tool_admin)

        # Member role sees only public
        member_tools = registry.list_for_role(["member"])
        assert [t.tool_id for t in member_tools] == ["tool.public"]

        # Admin role sees both
        admin_tools = registry.list_for_role(["org_admin"])
        assert {t.tool_id for t in admin_tools} == {"tool.public", "tool.admin"}

        # Export schemas for LLM/agent
        schemas = registry.export_schemas_for_agent(roles=["member"])
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "tool.public"
        assert "parameters" in schemas[0]["function"]
