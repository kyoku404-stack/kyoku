"""KEEP Phase 4.6 — Tool Registry.

Provides central catalog management, registration validation, discovery,
and enablement controls for approved platform tools.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.app.agents.errors import (
    ToolAlreadyRegisteredError,
    ToolDisabledError,
    ToolNotFoundError,
)
from backend.app.agents.tools.contracts import BaseTool
from backend.app.agents.tools.metadata import ToolMetadata

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry and discovery engine for KEEP platform tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Registers a tool implementation, ensuring contract adherence and ID uniqueness."""
        if not hasattr(tool, "metadata") or not isinstance(tool.metadata, ToolMetadata):
            raise TypeError("Tool must define a valid 'metadata: ToolMetadata' property")

        tool_id = tool.metadata.tool_id
        if tool_id in self._tools:
            raise ToolAlreadyRegisteredError(tool_id)

        self._tools[tool_id] = tool
        logger.info(
            "Registered tool '%s' (v%s, access_mode=%s, requires_approval=%s)",
            tool_id,
            tool.metadata.version,
            tool.metadata.access_mode,
            tool.metadata.requires_approval,
        )

    def get(self, tool_id: str, *, check_enabled: bool = True) -> BaseTool:
        """Retrieves a registered tool by its tool_id.
        
        Args:
            tool_id: Unique tool identifier.
            check_enabled: If True, raises ToolDisabledError if the tool is disabled.
        """
        tool = self._tools.get(tool_id)
        if tool is None:
            raise ToolNotFoundError(tool_id)

        if check_enabled and not tool.metadata.enabled:
            raise ToolDisabledError(tool_id)

        return tool

    def is_registered(self, tool_id: str) -> bool:
        """Returns True if a tool with the given ID is registered."""
        return tool_id in self._tools

    def is_enabled(self, tool_id: str) -> bool:
        """Returns True if a tool is registered and enabled."""
        tool = self._tools.get(tool_id)
        return tool is not None and tool.metadata.enabled

    def enable(self, tool_id: str) -> ToolMetadata:
        """Enables a registered tool."""
        tool = self.get(tool_id, check_enabled=False)
        tool.metadata.enabled = True
        logger.info("Enabled tool '%s'", tool_id)
        return tool.metadata

    def disable(self, tool_id: str) -> ToolMetadata:
        """Disables a registered tool."""
        tool = self.get(tool_id, check_enabled=False)
        tool.metadata.enabled = False
        logger.info("Disabled tool '%s'", tool_id)
        return tool.metadata

    def list_tools(self, *, include_disabled: bool = False) -> list[ToolMetadata]:
        """Lists all registered tools."""
        return [
            tool.metadata
            for tool in self._tools.values()
            if include_disabled or tool.metadata.enabled
        ]

    def list_for_role(self, roles: list[str]) -> list[ToolMetadata]:
        """Lists tools enabled and accessible to a principal with the given roles."""
        user_roles = {r.lower() for r in roles}
        is_admin = bool(user_roles & {"org_admin", "superadmin", "system_admin", "admin"})

        matching: list[ToolMetadata] = []
        for tool in self._tools.values():
            if not tool.metadata.enabled:
                continue

            # If tool requires specific roles, verify the caller has at least one
            if tool.metadata.required_roles:
                req_roles = {r.lower() for r in tool.metadata.required_roles}
                if not (is_admin or bool(user_roles & req_roles)):
                    continue

            matching.append(tool.metadata)

        return matching

    def export_schemas_for_agent(
        self,
        allowed_tool_ids: list[str] | None = None,
        roles: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Exports model-visible tool definitions (OpenAI/LangGraph function calling format)."""
        accessible_tools = self.list_for_role(roles or []) if roles else self.list_tools()

        schemas: list[dict[str, Any]] = []
        for meta in accessible_tools:
            if allowed_tool_ids is not None and meta.tool_id not in allowed_tool_ids:
                continue

            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": meta.tool_id,
                        "description": meta.description,
                        "parameters": meta.parameters_schema or {"type": "object", "properties": {}},
                    },
                }
            )

        return schemas

    def clear(self) -> None:
        """Clears all registered tools (for testing)."""
        self._tools.clear()
