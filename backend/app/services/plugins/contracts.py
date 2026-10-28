"""Typed AI and Domain Contracts for Plugin SDK, Extension Framework & Developer Ecosystem.

Phase: 3.5
Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/plugins/
Specification: devdocs/p3/p3.5.txt (Chapters 1-20)
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, ClassVar
from uuid import uuid4

logger = logging.getLogger(__name__)


# ============================================================================
# Enums & Domain Taxonomies
# ============================================================================


class PluginCategory(str, Enum):
    """Categorical classification of extensions within KEEP."""

    AI = "AI"
    INTEGRATION = "INTEGRATION"
    WORKFLOW = "WORKFLOW"
    UI = "UI"
    ANALYTICS = "ANALYTICS"


class PluginStatus(str, Enum):
    """Operational lifecycle state of an installed plugin."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"
    PAUSED = "PAUSED"


class PluginVerificationTier(str, Enum):
    """Trust and audit tier for marketplace plugins."""

    VERIFIED = "VERIFIED"
    COMMUNITY = "COMMUNITY"
    INTERNAL = "INTERNAL"


class PluginCapability(str, Enum):
    """Granular platform capabilities granted to sandboxed plugins."""

    DOCUMENTS_READ = "Documents.Read"
    DOCUMENTS_WRITE = "Documents.Write"
    AI_QUERY = "AI.Query"
    ANALYTICS_READ = "Analytics.Read"
    NOTIFICATIONS_SEND = "Notifications.Send"
    WORKFLOW_EXECUTE = "Workflow.Execute"
    GRAPH_READ = "Graph.Read"
    NETWORK_OUTBOUND = "Network.Outbound"


class PluginLogStatus(str, Enum):
    """Execution status outcomes for plugin telemetry audit logs."""

    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


class HookTriggerType(str, Enum):
    """Origin mechanism triggering a plugin execution."""

    DIRECT_API = "direct_api"
    EVENT_HOOK = "event_hook"
    SCHEDULED = "scheduled"


# ============================================================================
# Data Classes & Manifest Envelopes
# ============================================================================


@dataclass
class PluginManifest:
    """Standardized metadata specification for a KEEP plugin package."""

    id: str
    name: str
    version: str
    developer: str
    description: str
    category: PluginCategory
    entry_point: str
    api_version: str = "v1"
    min_keep_version: str = "3.0.0"
    max_keep_version: str = "3.9.9"
    permissions: list[str] = field(default_factory=list)
    event_hooks: list[str] = field(default_factory=list)
    configuration_schema: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    documentation_url: str | None = None
    icon_url: str | None = None

    def calculate_checksum(self) -> str:
        """Computes deterministic SHA-256 fingerprint of the manifest definition."""
        serialized = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serializes manifest to standard dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "developer": self.developer,
            "description": self.description,
            "category": self.category.value if isinstance(self.category, PluginCategory) else self.category,
            "entry_point": self.entry_point,
            "api_version": self.api_version,
            "min_keep_version": self.min_keep_version,
            "max_keep_version": self.max_keep_version,
            "permissions": self.permissions,
            "event_hooks": self.event_hooks,
            "configuration_schema": self.configuration_schema,
            "dependencies": self.dependencies,
            "documentation_url": self.documentation_url,
            "icon_url": self.icon_url,
        }


@dataclass
class PluginExecutionInput:
    """Context and payload supplied to an invoked plugin."""

    plugin_id: str
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    context_organization_id: str | None = None
    context_user_id: str | None = None
    timeout_seconds: float = 30.0


@dataclass
class PluginExecutionOutput:
    """Response envelope returned from a sandboxed plugin execution."""

    execution_id: str
    plugin_id: str
    action: str
    status: PluginLogStatus
    duration_ms: float
    result_data: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    completed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "plugin_id": self.plugin_id,
            "action": self.action,
            "status": self.status.value if isinstance(self.status, PluginLogStatus) else self.status,
            "duration_ms": self.duration_ms,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "completed_at": self.completed_at.isoformat(),
        }


@dataclass
class MarketplaceCatalogItem:
    """Pre-indexed plugin listing in the marketplace directory."""

    id: str
    plugin_id: str
    name: str
    description: str
    category: PluginCategory
    developer: str
    version: str
    verification_tier: PluginVerificationTier = PluginVerificationTier.COMMUNITY
    rating: float = 5.0
    installs_count: int = 0
    is_public: bool = True
    permissions: list[str] = field(default_factory=list)
    event_hooks: list[str] = field(default_factory=list)
    min_keep_version: str = "3.0.0"
    max_keep_version: str = "3.9.9"
    icon_url: str | None = None
    documentation_url: str | None = None


# ============================================================================
# Abstract Base Classes (Plugin SDK Developer Interfaces)
# ============================================================================


class BasePlugin(ABC):
    """Abstract base class that all KEEP plugins must implement."""

    def __init__(self, manifest: PluginManifest) -> None:
        self.manifest = manifest
        self.config: dict[str, Any] = {}
        self.is_initialized: bool = False

    def initialize(self, config: dict[str, Any]) -> None:
        """Initializes plugin with tenant-specific configuration."""
        self.config = config
        self.is_initialized = True

    @abstractmethod
    async def execute(self, execution_input: PluginExecutionInput) -> dict[str, Any]:
        """Main execution entrypoint for direct action invocation."""
        ...

    async def on_event(self, event_topic: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Optional hook invoked when a subscribed platform event fires."""
        return {"event": event_topic, "handled": True}

    def shutdown(self) -> None:
        """Gracefully disposes allocated resources."""
        self.is_initialized = False


class BaseAIPlugin(BasePlugin):
    """Specialized base class for AI, LLM, and Embedding provider plugins."""

    @abstractmethod
    async def execute_inference(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        """Executes LLM inference or AI transformation."""
        ...

    async def execute(self, execution_input: PluginExecutionInput) -> dict[str, Any]:
        prompt = execution_input.parameters.get("prompt", "")
        return await self.execute_inference(prompt, execution_input.parameters)


class BaseIntegrationPlugin(BasePlugin):
    """Specialized base class for SaaS, ERP, and database integration plugins."""

    @abstractmethod
    async def sync_external_entities(self, params: dict[str, Any]) -> dict[str, Any]:
        """Synchronizes external entities into the KEEP platform."""
        ...

    async def execute(self, execution_input: PluginExecutionInput) -> dict[str, Any]:
        return await self.sync_external_entities(execution_input.parameters)


class BaseWorkflowActionPlugin(BasePlugin):
    """Specialized base class for custom workflow action nodes."""

    @abstractmethod
    async def run_step(self, step_context: dict[str, Any]) -> dict[str, Any]:
        """Executes custom workflow step logic."""
        ...

    async def execute(self, execution_input: PluginExecutionInput) -> dict[str, Any]:
        return await self.run_step(execution_input.parameters)


# ============================================================================
# Reference Engine 1: Semantic Version Validator
# ============================================================================


class SemanticVersionValidator:
    """Validates semantic version numbers (SemVer 2.0) and compatibility boundaries."""

    SEMVER_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>[0-9A-Za-z.-]+))?$"
    )

    @classmethod
    def parse(cls, version_str: str) -> tuple[int, int, int]:
        """Parses version string into (major, minor, patch) integer tuple."""
        match = cls.SEMVER_PATTERN.match(version_str.strip())
        if not match:
            raise ValueError(f"Invalid SemVer string: '{version_str}'")
        return (
            int(match.group("major")),
            int(match.group("minor")),
            int(match.group("patch")),
        )

    @classmethod
    def is_compatible(cls, current_version: str, min_version: str, max_version: str) -> bool:
        """Determines if current_version falls within [min_version, max_version] inclusive."""
        try:
            curr = cls.parse(current_version)
            min_v = cls.parse(min_version)
            max_v = cls.parse(max_version)
            return min_v <= curr <= max_v
        except ValueError:
            return False


# ============================================================================
# Reference Engine 2: Plugin Manifest Validator
# ============================================================================


class PluginManifestValidator:
    """Validates plugin manifest structure, permissions, and dependencies."""

    VALID_CATEGORIES: ClassVar[set[str]] = {c.value for c in PluginCategory}
    VALID_CAPABILITIES: ClassVar[set[str]] = {p.value for p in PluginCapability}

    @classmethod
    def validate(cls, manifest_dict: dict[str, Any], current_platform_version: str = "3.5.0") -> PluginManifest:
        """Validates dictionary representation of a manifest against specifications."""
        required_fields = ["id", "name", "version", "developer", "category", "entry_point"]
        for rf in required_fields:
            if not manifest_dict.get(rf):
                raise ValueError(f"Missing mandatory manifest field: '{rf}'")

        category_val = manifest_dict["category"].upper()
        if category_val not in cls.VALID_CATEGORIES:
            raise ValueError(f"Invalid plugin category: '{category_val}'. Must be one of {cls.VALID_CATEGORIES}")

        version_str = manifest_dict["version"]
        SemanticVersionValidator.parse(version_str)

        min_ver = manifest_dict.get("min_keep_version", "3.0.0")
        max_ver = manifest_dict.get("max_keep_version", "3.9.9")

        if not SemanticVersionValidator.is_compatible(current_platform_version, min_ver, max_ver):
            raise ValueError(
                f"Plugin version '{version_str}' is incompatible with platform version '{current_platform_version}' "
                f"(required {min_ver} - {max_ver})"
            )

        permissions = manifest_dict.get("permissions", [])
        for perm in permissions:
            if perm not in cls.VALID_CAPABILITIES:
                logger.warning("Unrecognized capability '%s' in manifest '%s'", perm, manifest_dict['id'])

        return PluginManifest(
            id=manifest_dict["id"],
            name=manifest_dict["name"],
            version=version_str,
            developer=manifest_dict["developer"],
            description=manifest_dict.get("description", ""),
            category=PluginCategory(category_val),
            entry_point=manifest_dict["entry_point"],
            api_version=manifest_dict.get("api_version", "v1"),
            min_keep_version=min_ver,
            max_keep_version=max_ver,
            permissions=permissions,
            event_hooks=manifest_dict.get("event_hooks", []),
            configuration_schema=manifest_dict.get("configuration_schema", {}),
            dependencies=manifest_dict.get("dependencies", []),
            documentation_url=manifest_dict.get("documentation_url"),
            icon_url=manifest_dict.get("icon_url"),
        )


# ============================================================================
# Reference Engine 3: Capability Permission Guard
# ============================================================================


class CapabilityPermissionGuard:
    """Enforces capability authorization gating for plugins attempting platform API calls."""

    @staticmethod
    def verify_capability(
        granted_permissions: list[str],
        required_capability: PluginCapability,
        plugin_id: str,
    ) -> bool:
        """Verifies if the plugin has been explicitly granted the required capability."""
        cap_val = required_capability.value
        if cap_val not in granted_permissions:
            raise PermissionError(
                f"Security Capability Violation: Plugin '{plugin_id}' lacks required permission '{cap_val}'."
            )
        return True


# ============================================================================
# Reference Engine 4: Plugin Sandbox Runner
# ============================================================================


class PluginSandboxRunner:
    """Executes plugin tasks inside an isolated asynchronous timeout & error boundary."""

    def __init__(self, default_timeout_seconds: float = 30.0) -> None:
        self.default_timeout_seconds = default_timeout_seconds

    async def execute_sandboxed(
        self,
        plugin: BasePlugin,
        execution_input: PluginExecutionInput,
    ) -> PluginExecutionOutput:
        """Invokes a plugin execution with timeout guardrails and captures performance telemetry."""
        exec_id = str(uuid4())
        start_time = time.perf_counter()
        timeout = execution_input.timeout_seconds or self.default_timeout_seconds

        try:
            result = await asyncio.wait_for(
                plugin.execute(execution_input),
                timeout=timeout,
            )
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            return PluginExecutionOutput(
                execution_id=exec_id,
                plugin_id=execution_input.plugin_id,
                action=execution_input.action,
                status=PluginLogStatus.SUCCESS,
                duration_ms=round(duration_ms, 2),
                result_data=result,
            )

        except TimeoutError:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("Sandbox timeout: Plugin '%s' exceeded %ss SLA", execution_input.plugin_id, timeout)
            return PluginExecutionOutput(
                execution_id=exec_id,
                plugin_id=execution_input.plugin_id,
                action=execution_input.action,
                status=PluginLogStatus.TIMEOUT,
                duration_ms=round(duration_ms, 2),
                error_message=f"Plugin execution exceeded timeout SLA of {timeout}s",
            )

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.exception("Plugin '%s' execution crashed", execution_input.plugin_id)
            return PluginExecutionOutput(
                execution_id=exec_id,
                plugin_id=execution_input.plugin_id,
                action=execution_input.action,
                status=PluginLogStatus.ERROR,
                duration_ms=round(duration_ms, 2),
                error_message=str(exc),
            )


# ============================================================================
# Reference Engine 5: Plugin Hook Broker
# ============================================================================


class PluginHookBroker:
    """Dispatches core system events to registered plugin event hooks."""

    def __init__(self) -> None:
        # Maps event topic to list of (plugin_id, handler_coroutine)
        self._subscriptions: dict[str, list[tuple[str, Callable[[str, dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]]]] = {}

    def subscribe(
        self,
        event_topic: str,
        plugin_id: str,
        handler: Callable[[str, dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]],
    ) -> None:
        """Registers a plugin handler for a specific event topic."""
        if event_topic not in self._subscriptions:
            self._subscriptions[event_topic] = []
        self._subscriptions[event_topic].append((plugin_id, handler))

    def unsubscribe_plugin(self, plugin_id: str) -> None:
        """Removes all hook registrations for a designated plugin."""
        for topic in self._subscriptions:
            self._subscriptions[topic] = [
                sub for sub in self._subscriptions[topic] if sub[0] != plugin_id
            ]

    async def dispatch_event(
        self,
        event_topic: str,
        payload: dict[str, Any],
        timeout_seconds: float = 10.0,
    ) -> dict[str, Any]:
        """Concurrently dispatches an event to all subscribed plugin hooks."""
        subscribers = self._subscriptions.get(event_topic, [])
        if not subscribers:
            return {"dispatched_count": 0, "results": {}}

        results: dict[str, Any] = {}

        async def _call_sub(pid: str, handler: Callable) -> tuple[str, dict[str, Any]]:
            try:
                res = await asyncio.wait_for(handler(event_topic, payload), timeout=timeout_seconds)
                return pid, {"status": "SUCCESS", "data": res}
            except Exception as e:  # noqa: BLE001
                return pid, {"status": "ERROR", "error": str(e)}

        tasks = [_call_sub(pid, handler) for pid, handler in subscribers]
        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for item in completed:
            if isinstance(item, tuple):
                pid, res_dict = item
                results[pid] = res_dict

        return {"dispatched_count": len(subscribers), "results": results}


# ============================================================================
# Reference Implementation 1: Sample Claude AI Plugin
# ============================================================================


class SampleClaudeAIPlugin(BaseAIPlugin):
    """Reference implementation of a third-party LLM inference plugin."""

    def __init__(self) -> None:
        manifest = PluginManifest(
            id="ai-anthropic-claude",
            name="Anthropic Claude 3.5 Sonnet Provider",
            version="2.1.0",
            developer="Anthropic Community Partner",
            description="Drop-in LLM adapter for Claude 3.5 Sonnet and Haiku inference.",
            category=PluginCategory.AI,
            entry_point="anthropic_claude.plugin:SampleClaudeAIPlugin",
            permissions=[PluginCapability.AI_QUERY.value],
            event_hooks=["ai.query.generated"],
        )
        super().__init__(manifest)

    async def execute_inference(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        model_name = self.config.get("model", "claude-3-5-sonnet-20241022")
        # Simulating external SDK inference response
        return {
            "provider": "Anthropic",
            "model": model_name,
            "completion": f"[Claude 3.5 Response] Processed query: {prompt[:80]}...",
            "tokens_used": len(prompt.split()) + 45,
            "latency_ms": 112.4,
        }

    async def on_event(self, event_topic: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "logged", "topic": event_topic, "model": self.config.get("model", "claude-3-5-sonnet")}


# ============================================================================
# Reference Implementation 2: Sample SAP Invoice Plugin
# ============================================================================


class SampleSAPInvoicePlugin(BaseIntegrationPlugin):
    """Reference implementation of an enterprise ERP invoice integration plugin."""

    def __init__(self) -> None:
        manifest = PluginManifest(
            id="sap-s4hana-connector",
            name="SAP S/4HANA Enterprise Connector",
            version="1.2.0",
            developer="Acme Integrations Inc.",
            description="Bi-directional document synchronization and invoice indexing for SAP S/4HANA.",
            category=PluginCategory.INTEGRATION,
            entry_point="sap_connector.plugin:SampleSAPInvoicePlugin",
            permissions=[
                PluginCapability.DOCUMENTS_READ.value,
                PluginCapability.DOCUMENTS_WRITE.value,
                PluginCapability.NOTIFICATIONS_SEND.value,
                PluginCapability.NETWORK_OUTBOUND.value,
            ],
            event_hooks=["document.uploaded"],
        )
        super().__init__(manifest)

    async def sync_external_entities(self, params: dict[str, Any]) -> dict[str, Any]:
        endpoint = self.config.get("endpoint_url", "https://sap.internal.acme.com")
        limit = params.get("limit", 25)
        return {
            "endpoint": endpoint,
            "synced_count": limit,
            "entities": [f"INV-2026-{1000 + i}" for i in range(min(limit, 5))],
            "status": "COMPLETED",
        }

    async def on_event(self, event_topic: str, payload: dict[str, Any]) -> dict[str, Any]:
        doc_id = payload.get("document_id", "unknown-doc")
        return {"action": "indexed_in_sap", "doc_id": doc_id, "status": "SYNCED"}
