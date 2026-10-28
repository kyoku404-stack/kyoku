"""Pydantic v2 Request/Response Validation Schemas for Plugin SDK & Extension Framework.

Phase: 3.5
Owner: Member 2 (Backend & Database Lead)
Domain: /backend/app/schemas/plugin.py
Specification: devdocs/p3/p3.5.txt & docs/api/api-contract.md (Section 17)
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Plugin Lifecycle Request Schemas
# ============================================================================


class PluginInstallRequest(BaseModel):
    """Payload to install a marketplace or package plugin for a tenant."""

    plugin_id: str = Field(min_length=1, max_length=100, description="Unique plugin identifier slug")
    version: str | None = Field(default=None, max_length=30, description="Target version to install")
    configuration: dict[str, Any] = Field(default_factory=dict, description="Initial configuration values")
    approved_permissions: list[str] = Field(default_factory=list, description="Explicitly approved capabilities")
    marketplace_package_url: str | None = Field(default=None, description="Remote archive package location")

    model_config = ConfigDict(extra="ignore")


class PluginUpdateRequest(BaseModel):
    """Payload to upgrade or downgrade a plugin version."""

    plugin_id: str = Field(min_length=1, max_length=100, description="Plugin identifier slug")
    target_version: str = Field(min_length=1, max_length=30, description="SemVer version to upgrade to")

    model_config = ConfigDict(extra="ignore")


class PluginUninstallRequest(BaseModel):
    """Payload to uninstall a plugin from tenant workspace."""

    plugin_id: str = Field(min_length=1, max_length=100, description="Plugin identifier slug")
    purge_data: bool = Field(default=False, description="Whether to purge persistent logs and config")

    model_config = ConfigDict(extra="ignore")


class PluginStatusToggleRequest(BaseModel):
    """Payload to activate or deactivate a plugin."""

    plugin_id: str = Field(min_length=1, max_length=100, description="Plugin identifier slug")

    model_config = ConfigDict(extra="ignore")


# ============================================================================
# Execution & Configuration Schemas
# ============================================================================


class PluginExecuteRequest(BaseModel):
    """Payload to directly invoke an action within a plugin."""

    action: str = Field(min_length=1, max_length=120, description="Action or method to invoke")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Parameters passed to the plugin")
    timeout_seconds: float = Field(default=30.0, ge=1.0, le=300.0, description="Execution timeout SLA")

    model_config = ConfigDict(extra="ignore")


class PluginConfigUpdateRequest(BaseModel):
    """Payload to update plugin tenant settings."""

    configuration: dict[str, Any] = Field(default_factory=dict, description="Updated configuration dictionary")

    model_config = ConfigDict(extra="ignore")


class PluginPublishRequest(BaseModel):
    """Payload to register a new plugin in the marketplace catalog."""

    id: str = Field(min_length=1, max_length=100, description="Plugin ID slug")
    name: str = Field(min_length=1, max_length=255, description="Human-readable plugin name")
    description: str = Field(min_length=1, max_length=2000, description="Detailed plugin description")
    category: str = Field(default="AI", description="Plugin category: AI, INTEGRATION, WORKFLOW, UI, ANALYTICS")
    developer: str = Field(min_length=1, max_length=150, description="Author or organization name")
    version: str = Field(default="1.0.0", max_length=30, description="SemVer release version")
    entry_point: str = Field(min_length=1, max_length=255, description="Python module entrypoint or package path")
    min_keep_version: str = Field(default="3.0.0", max_length=30)
    max_keep_version: str = Field(default="3.9.9", max_length=30)
    permissions: list[str] = Field(default_factory=list, description="Requested platform capabilities")
    event_hooks: list[str] = Field(default_factory=list, description="Subscribed platform events")
    configuration_schema: dict[str, Any] = Field(default_factory=dict, description="JSON Schema for configuration")
    icon_url: str | None = Field(default=None, max_length=500)
    documentation_url: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="ignore")


# ============================================================================
# Response Schemas
# ============================================================================


class PluginItemResponse(BaseModel):
    """Summary of an installed plugin."""

    id: str
    plugin_id: str
    name: str
    version: str
    category: str
    status: str
    is_enabled: bool
    developer: str | None = None
    description: str | None = None
    permissions: list[str] = Field(default_factory=list)
    event_hooks: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
    installed_at: str | None = None
    updated_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PluginExecutionResponse(BaseModel):
    """Execution telemetry and result response."""

    execution_id: str
    plugin_id: str
    action: str
    status: str
    duration_ms: float
    result: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PluginExecutionLogResponse(BaseModel):
    """Execution log audit record."""

    id: str
    plugin_id: str
    action: str
    status: str
    duration_ms: float
    triggered_by: str
    error_message: str | None = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class PluginMarketplaceItemResponse(BaseModel):
    """Marketplace catalog listing representation."""

    id: str
    plugin_id: str
    name: str
    description: str
    category: str
    developer: str
    version: str
    verification_tier: str
    rating: float
    installs_count: int
    is_installed: bool = False
    min_keep_version: str = "3.0.0"
    max_keep_version: str = "3.9.9"
    permissions: list[str] = Field(default_factory=list)
    event_hooks: list[str] = Field(default_factory=list)
    icon_url: str | None = None
    documentation_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PluginAnalyticsResponse(BaseModel):
    """Plugin operational KPIs and performance metrics."""

    total_installed_plugins: int
    active_plugins: int
    total_executions: int
    avg_latency_ms: float
    error_rate: float
    plugins_by_category: dict[str, int] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)
