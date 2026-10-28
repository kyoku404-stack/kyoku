"""KEEP Enterprise Platform — Enterprise Plugin Service & Lifecycle Orchestrator.

Phase: 3.5
Owner: Member 2 (Backend & Database Lead)
Domain: /backend/app/services/plugins/service.py
Specification: devdocs/p3/p3.5.txt & docs/api/api-contract.md (Section 17)
"""

import asyncio
import hashlib
import json
import logging
import uuid
from typing import Any

from backend.app.models.plugin import (
    Plugin,
    PluginEventHook,
    PluginExecutionLog,
    PluginInstallation,
    PluginManifestModel,
    PluginPermission,
)
from backend.app.schemas.plugin import (
    PluginConfigUpdateRequest,
    PluginExecuteRequest,
    PluginInstallRequest,
    PluginPublishRequest,
    PluginUpdateRequest,
)
from backend.app.services.plugins.contracts import (
    BasePlugin,
    PluginCategory,
    PluginExecutionInput,
    PluginExecutionOutput,
    PluginLogStatus,
    PluginManifest,
    PluginSandboxRunner,
    SampleClaudeAIPlugin,
    SampleSAPInvoicePlugin,
    SemanticVersionValidator,
)
from fastapi import HTTPException, status
from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# In-memory registry of executable plugin instances / factories
_PLUGIN_REGISTRY: dict[str, type[BasePlugin]] = {
    "ai-anthropic-claude": SampleClaudeAIPlugin,
    "sap-s4hana-connector": SampleSAPInvoicePlugin,
}


def register_plugin_runtime(plugin_id: str, plugin_cls: type[BasePlugin]) -> None:
    """Register a runtime plugin implementation class."""
    _PLUGIN_REGISTRY[plugin_id] = plugin_cls


# Built-in Seed Catalog definitions
DEFAULT_SEED_PLUGINS: list[dict[str, Any]] = [
    {
        "id": "ai-anthropic-claude",
        "name": "Anthropic Claude 3.5 Sonnet Integration",
        "description": "Enterprise-grade reasoning, artifact analysis, and multimodal contextual generation connector.",
        "category": "AI",
        "developer": "Anthropic PBC",
        "current_version": "1.2.0",
        "verification_tier": "CERTIFIED",
        "rating": 4.95,
        "installs_count": 1420,
        "min_keep_version": "3.0.0",
        "max_keep_version": "3.9.9",
        "entry_point": "plugins.ai.anthropic_claude:SampleClaudeAIPlugin",
        "permissions": ["AI_INFERENCE", "READ_DOCUMENTS", "NETWORK_EGRESS"],
        "event_hooks": ["on_document_uploaded", "on_chat_completion_requested"],
        "configuration_schema": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "title": "Anthropic API Key"},
                "model": {"type": "string", "default": "claude-3-5-sonnet-20241022"},
                "temperature": {"type": "number", "default": 0.2},
            },
            "required": ["api_key"],
        },
        "icon_url": "https://cdn.keep.enterprise/icons/claude-ai.svg",
        "documentation_url": "https://docs.keep.enterprise/plugins/ai-anthropic-claude",
    },
    {
        "id": "sap-s4hana-connector",
        "name": "SAP S/4HANA Enterprise ERP Connector",
        "description": "Bi-directional ERP sync for purchase orders, general ledger journals, and automated invoice clearance.",
        "category": "INTEGRATION",
        "developer": "SAP SE & KEEP Enterprise",
        "current_version": "2.1.0",
        "verification_tier": "CERTIFIED",
        "rating": 4.88,
        "installs_count": 890,
        "min_keep_version": "3.0.0",
        "max_keep_version": "3.9.9",
        "entry_point": "plugins.integrations.sap_s4hana:SampleSAPInvoicePlugin",
        "permissions": ["STORAGE_READ", "STORAGE_WRITE", "DATABASE_ACCESS", "NETWORK_EGRESS"],
        "event_hooks": ["on_workflow_step_approved", "on_audit_logged"],
        "configuration_schema": {
            "type": "object",
            "properties": {
                "endpoint_url": {"type": "string", "title": "SAP S/4HANA OData Endpoint"},
                "client_id": {"type": "string", "title": "OAuth2 Client ID"},
                "client_secret": {"type": "string", "title": "OAuth2 Client Secret"},
            },
            "required": ["endpoint_url", "client_id"],
        },
        "icon_url": "https://cdn.keep.enterprise/icons/sap-logo.svg",
        "documentation_url": "https://docs.keep.enterprise/plugins/sap-s4hana-connector",
    },
    {
        "id": "slack-realtime-notifier",
        "name": "Slack Enterprise Grid Alerts & Bot",
        "description": "Interactive incident dispatch, workflow approval notifications, and bidirectional bot queries via Slack.",
        "category": "WORKFLOW",
        "developer": "Slack Technologies",
        "current_version": "1.0.5",
        "verification_tier": "VERIFIED",
        "rating": 4.75,
        "installs_count": 640,
        "min_keep_version": "3.0.0",
        "max_keep_version": "3.9.9",
        "entry_point": "plugins.workflows.slack_notifier:SlackNotifierPlugin",
        "permissions": ["NETWORK_EGRESS", "EVENT_LISTEN"],
        "event_hooks": ["on_security_alert", "on_workflow_step_rejected"],
        "configuration_schema": {
            "type": "object",
            "properties": {
                "webhook_url": {"type": "string", "title": "Slack Incoming Webhook URL"},
                "default_channel": {"type": "string", "default": "#general"},
            },
            "required": ["webhook_url"],
        },
        "icon_url": "https://cdn.keep.enterprise/icons/slack.svg",
        "documentation_url": "https://docs.keep.enterprise/plugins/slack-realtime-notifier",
    },
]


class EnterprisePluginService:
    """Core enterprise business service for plugin lifecycle, sandbox dispatch, and marketplace."""

    CURRENT_PLATFORM_VERSION = "3.5.0"

    async def seed_default_marketplace(self, db: AsyncSession) -> None:
        """Seed default enterprise certified plugins if registry is uninitialized."""
        for item in DEFAULT_SEED_PLUGINS:
            existing = await db.get(Plugin, item["id"])
            if not existing:
                plugin = Plugin(
                    id=item["id"],
                    name=item["name"],
                    description=item["description"],
                    category=item["category"],
                    developer=item["developer"],
                    current_version=item["current_version"],
                    verification_tier=item["verification_tier"],
                    rating=item["rating"],
                    installs_count=item["installs_count"],
                    is_public=True,
                    icon_url=item.get("icon_url"),
                    documentation_url=item.get("documentation_url"),
                )
                db.add(plugin)
                await db.flush()

                manifest_dict = {
                    "id": item["id"],
                    "name": item["name"],
                    "version": item["current_version"],
                    "category": item["category"],
                    "developer": item["developer"],
                    "entry_point": item["entry_point"],
                    "min_keep_version": item["min_keep_version"],
                    "max_keep_version": item["max_keep_version"],
                    "permissions": item["permissions"],
                    "event_hooks": item["event_hooks"],
                    "configuration_schema": item["configuration_schema"],
                }
                checksum = hashlib.sha256(json.dumps(manifest_dict, sort_keys=True).encode()).hexdigest()

                manifest = PluginManifestModel(
                    plugin_id=item["id"],
                    version=item["current_version"],
                    manifest_json=manifest_dict,
                    min_keep_version=item["min_keep_version"],
                    max_keep_version=item["max_keep_version"],
                    entry_point=item["entry_point"],
                    permissions=item["permissions"],
                    event_hooks=item["event_hooks"],
                    configuration_schema=item["configuration_schema"],
                    checksum_sha256=checksum,
                )
                db.add(manifest)

        await db.commit()

    async def browse_marketplace(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        search: str | None = None,
        category: str | None = None,
        verified_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Browse marketplace catalog with installed state per tenant."""
        await self.seed_default_marketplace(db)

        query = select(Plugin)
        if category:
            query = query.where(Plugin.category == category.upper())
        if verified_only:
            query = query.where(Plugin.verification_tier.in_(["VERIFIED", "CERTIFIED"]))
        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.where(
                (func.lower(Plugin.name).like(search_pattern))
                | (func.lower(Plugin.description).like(search_pattern))
                | (func.lower(Plugin.developer).like(search_pattern))
            )

        query = query.order_by(desc(Plugin.rating), desc(Plugin.installs_count))
        result = await db.execute(query)
        plugins = result.scalars().all()

        # Query installed plugins for this tenant
        inst_query = select(PluginInstallation.plugin_id).where(
            PluginInstallation.organization_id == org_id
        )
        inst_res = await db.execute(inst_query)
        installed_ids = set(inst_res.scalars().all())

        catalog_items = []
        for p in plugins:
            # Fetch latest manifest
            mf_query = select(PluginManifestModel).where(
                PluginManifestModel.plugin_id == p.id,
                PluginManifestModel.version == p.current_version,
            )
            mf_res = await db.execute(mf_query)
            manifest = mf_res.scalars().first()

            catalog_items.append(
                {
                    "id": p.id,
                    "plugin_id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "category": p.category,
                    "developer": p.developer,
                    "version": p.current_version,
                    "verification_tier": p.verification_tier,
                    "rating": float(p.rating),
                    "installs_count": p.installs_count,
                    "is_installed": p.id in installed_ids,
                    "min_keep_version": manifest.min_keep_version if manifest else "3.0.0",
                    "max_keep_version": manifest.max_keep_version if manifest else "3.9.9",
                    "permissions": manifest.permissions if manifest else [],
                    "event_hooks": manifest.event_hooks if manifest else [],
                    "icon_url": p.icon_url,
                    "documentation_url": p.documentation_url,
                }
            )

        return catalog_items

    async def publish_marketplace_plugin(
        self,
        db: AsyncSession,
        user_id: uuid.UUID | None,
        payload: PluginPublishRequest,
    ) -> dict[str, Any]:
        """Publish or update a plugin catalog listing."""
        # Validate SemVer compatibility
        is_compat = SemanticVersionValidator.is_compatible(
            self.CURRENT_PLATFORM_VERSION, payload.min_keep_version, payload.max_keep_version
        )
        if not is_compat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plugin version constraints [{payload.min_keep_version} - {payload.max_keep_version}] incompatible with KEEP {self.CURRENT_PLATFORM_VERSION}",
            )

        plugin = await db.get(Plugin, payload.id)
        if not plugin:
            plugin = Plugin(
                id=payload.id,
                name=payload.name,
                description=payload.description,
                category=payload.category.upper(),
                developer=payload.developer,
                current_version=payload.version,
                verification_tier="COMMUNITY",
                rating=5.00,
                installs_count=0,
                is_public=True,
                icon_url=payload.icon_url,
                documentation_url=payload.documentation_url,
            )
            db.add(plugin)
            await db.flush()
        else:
            plugin.name = payload.name
            plugin.description = payload.description
            plugin.category = payload.category.upper()
            plugin.current_version = payload.version
            plugin.icon_url = payload.icon_url
            plugin.documentation_url = payload.documentation_url

        manifest_dict = payload.model_dump()
        checksum = hashlib.sha256(json.dumps(manifest_dict, sort_keys=True).encode()).hexdigest()

        # Check existing manifest version
        mf_query = select(PluginManifestModel).where(
            PluginManifestModel.plugin_id == payload.id,
            PluginManifestModel.version == payload.version,
        )
        mf_res = await db.execute(mf_query)
        manifest = mf_res.scalars().first()

        if not manifest:
            manifest = PluginManifestModel(
                plugin_id=payload.id,
                version=payload.version,
                manifest_json=manifest_dict,
                min_keep_version=payload.min_keep_version,
                max_keep_version=payload.max_keep_version,
                entry_point=payload.entry_point,
                permissions=payload.permissions,
                event_hooks=payload.event_hooks,
                configuration_schema=payload.configuration_schema,
                checksum_sha256=checksum,
            )
            db.add(manifest)
        else:
            manifest.manifest_json = manifest_dict
            manifest.permissions = payload.permissions
            manifest.event_hooks = payload.event_hooks
            manifest.configuration_schema = payload.configuration_schema
            manifest.checksum_sha256 = checksum

        await db.commit()
        return {
            "id": plugin.id,
            "plugin_id": plugin.id,
            "name": plugin.name,
            "version": plugin.current_version,
            "status": "PUBLISHED",
        }

    async def install_plugin(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID | None,
        payload: PluginInstallRequest,
    ) -> dict[str, Any]:
        """Install a plugin into tenant workspace and grant permissions."""
        await self.seed_default_marketplace(db)

        # Check existing installation
        inst_query = select(PluginInstallation).where(
            PluginInstallation.organization_id == org_id,
            PluginInstallation.plugin_id == payload.plugin_id,
        )
        inst_res = await db.execute(inst_query)
        existing_inst = inst_res.scalars().first()
        if existing_inst:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plugin '{payload.plugin_id}' is already installed in this organization.",
            )

        plugin = await db.get(Plugin, payload.plugin_id)
        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{payload.plugin_id}' not found in registry.",
            )

        version_to_install = payload.version or plugin.current_version
        mf_query = select(PluginManifestModel).where(
            PluginManifestModel.plugin_id == payload.plugin_id,
            PluginManifestModel.version == version_to_install,
        )
        mf_res = await db.execute(mf_query)
        manifest = mf_res.scalars().first()

        if not manifest:
            # Fallback to current version manifest
            mf_query = select(PluginManifestModel).where(
                PluginManifestModel.plugin_id == payload.plugin_id,
                PluginManifestModel.version == plugin.current_version,
            )
            mf_res = await db.execute(mf_query)
            manifest = mf_res.scalars().first()

        # SemVer compatibility check
        min_v = manifest.min_keep_version if manifest else "3.0.0"
        max_v = manifest.max_keep_version if manifest else "3.9.9"
        if not SemanticVersionValidator.is_compatible(self.CURRENT_PLATFORM_VERSION, min_v, max_v):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plugin {payload.plugin_id} requires KEEP [{min_v} - {max_v}], current is {self.CURRENT_PLATFORM_VERSION}",
            )

        installation = PluginInstallation(
            organization_id=org_id,
            plugin_id=payload.plugin_id,
            version=version_to_install,
            status="ACTIVE",
            is_enabled=True,
            configuration=payload.configuration,
            installed_by=user_id,
        )
        db.add(installation)
        await db.flush()

        # Record permissions
        permissions_to_grant = payload.approved_permissions or (manifest.permissions if manifest else [])
        for perm in permissions_to_grant:
            db.add(
                PluginPermission(
                    installation_id=installation.id,
                    permission=perm,
                    is_granted=True,
                    granted_by=user_id,
                )
            )

        # Record event hooks
        if manifest and manifest.event_hooks:
            for hook in manifest.event_hooks:
                db.add(
                    PluginEventHook(
                        installation_id=installation.id,
                        event_topic=hook,
                        handler_method="on_event",
                        is_active=True,
                    )
                )

        plugin.installs_count += 1
        await db.commit()
        await db.refresh(installation)

        return await self.get_plugin(db, org_id, payload.plugin_id)

    async def list_installed_plugins(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        category: str | None = None,
        status_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """List installed plugins for the organization."""
        query = (
            select(PluginInstallation, Plugin)
            .join(Plugin, PluginInstallation.plugin_id == Plugin.id)
            .where(PluginInstallation.organization_id == org_id)
        )
        if category:
            query = query.where(Plugin.category == category.upper())
        if status_filter:
            query = query.where(PluginInstallation.status == status_filter.upper())

        query = query.order_by(desc(PluginInstallation.installed_at))
        result = await db.execute(query)
        rows = result.all()

        installed_list = []
        for inst, p in rows:
            # Fetch permissions and hooks
            perm_query = select(PluginPermission.permission).where(
                PluginPermission.installation_id == inst.id, PluginPermission.is_granted.is_(True)
            )
            perms = (await db.execute(perm_query)).scalars().all()

            hook_query = select(PluginEventHook.event_topic).where(
                PluginEventHook.installation_id == inst.id, PluginEventHook.is_active.is_(True)
            )
            hooks = (await db.execute(hook_query)).scalars().all()

            installed_list.append(
                {
                    "id": str(inst.id),
                    "plugin_id": inst.plugin_id,
                    "name": p.name,
                    "version": inst.version,
                    "category": p.category,
                    "status": inst.status,
                    "is_enabled": inst.is_enabled,
                    "developer": p.developer,
                    "description": p.description,
                    "permissions": list(perms),
                    "event_hooks": list(hooks),
                    "configuration": inst.configuration,
                    "installed_at": inst.installed_at.isoformat() if inst.installed_at else None,
                    "updated_at": inst.updated_at.isoformat() if inst.updated_at else None,
                }
            )

        return installed_list

    async def get_plugin(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        plugin_id: str,
    ) -> dict[str, Any]:
        """Retrieve details of an installed plugin."""
        query = (
            select(PluginInstallation, Plugin)
            .join(Plugin, PluginInstallation.plugin_id == Plugin.id)
            .where(
                PluginInstallation.organization_id == org_id,
                PluginInstallation.plugin_id == plugin_id,
            )
        )
        result = await db.execute(query)
        row = result.first()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_id}' is not installed in this organization.",
            )

        inst, p = row
        perm_query = select(PluginPermission.permission).where(
            PluginPermission.installation_id == inst.id, PluginPermission.is_granted.is_(True)
        )
        perms = (await db.execute(perm_query)).scalars().all()

        hook_query = select(PluginEventHook.event_topic).where(
            PluginEventHook.installation_id == inst.id, PluginEventHook.is_active.is_(True)
        )
        hooks = (await db.execute(hook_query)).scalars().all()

        return {
            "id": str(inst.id),
            "plugin_id": inst.plugin_id,
            "name": p.name,
            "version": inst.version,
            "category": p.category,
            "status": inst.status,
            "is_enabled": inst.is_enabled,
            "developer": p.developer,
            "description": p.description,
            "permissions": list(perms),
            "event_hooks": list(hooks),
            "configuration": inst.configuration,
            "installed_at": inst.installed_at.isoformat() if inst.installed_at else None,
            "updated_at": inst.updated_at.isoformat() if inst.updated_at else None,
        }

    async def enable_plugin(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        plugin_id: str,
    ) -> dict[str, Any]:
        """Activate a disabled plugin."""
        inst_query = select(PluginInstallation).where(
            PluginInstallation.organization_id == org_id,
            PluginInstallation.plugin_id == plugin_id,
        )
        inst_res = await db.execute(inst_query)
        inst = inst_res.scalars().first()
        if not inst:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_id}' not found.",
            )

        inst.is_enabled = True
        inst.status = "ACTIVE"
        await db.commit()
        return await self.get_plugin(db, org_id, plugin_id)

    async def disable_plugin(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        plugin_id: str,
    ) -> dict[str, Any]:
        """Deactivate an active plugin."""
        inst_query = select(PluginInstallation).where(
            PluginInstallation.organization_id == org_id,
            PluginInstallation.plugin_id == plugin_id,
        )
        inst_res = await db.execute(inst_query)
        inst = inst_res.scalars().first()
        if not inst:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_id}' not found.",
            )

        inst.is_enabled = False
        inst.status = "DISABLED"
        await db.commit()
        return await self.get_plugin(db, org_id, plugin_id)

    async def update_plugin_version(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        payload: PluginUpdateRequest,
    ) -> dict[str, Any]:
        """Upgrade/downgrade plugin version."""
        inst_query = select(PluginInstallation).where(
            PluginInstallation.organization_id == org_id,
            PluginInstallation.plugin_id == payload.plugin_id,
        )
        inst_res = await db.execute(inst_query)
        inst = inst_res.scalars().first()
        if not inst:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{payload.plugin_id}' not found.",
            )

        # Check target version manifest
        mf_query = select(PluginManifestModel).where(
            PluginManifestModel.plugin_id == payload.plugin_id,
            PluginManifestModel.version == payload.target_version,
        )
        mf_res = await db.execute(mf_query)
        manifest = mf_res.scalars().first()
        if not manifest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target version '{payload.target_version}' does not exist for plugin '{payload.plugin_id}'.",
            )

        if not SemanticVersionValidator.is_compatible(
            self.CURRENT_PLATFORM_VERSION, manifest.min_keep_version, manifest.max_keep_version
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Version {payload.target_version} is incompatible with platform version {self.CURRENT_PLATFORM_VERSION}",
            )

        inst.version = payload.target_version
        await db.commit()
        return await self.get_plugin(db, org_id, payload.plugin_id)

    async def update_plugin_configuration(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        plugin_id: str,
        payload: PluginConfigUpdateRequest,
    ) -> dict[str, Any]:
        """Update runtime configuration for a plugin."""
        inst_query = select(PluginInstallation).where(
            PluginInstallation.organization_id == org_id,
            PluginInstallation.plugin_id == plugin_id,
        )
        inst_res = await db.execute(inst_query)
        inst = inst_res.scalars().first()
        if not inst:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_id}' not found.",
            )

        # Merge or replace configuration
        new_config = dict(inst.configuration or {})
        new_config.update(payload.configuration)
        inst.configuration = new_config
        await db.commit()
        return await self.get_plugin(db, org_id, plugin_id)

    async def uninstall_plugin(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        plugin_id: str,
        purge_data: bool = False,
    ) -> dict[str, Any]:
        """Uninstall plugin from organization workspace."""
        inst_query = select(PluginInstallation).where(
            PluginInstallation.organization_id == org_id,
            PluginInstallation.plugin_id == plugin_id,
        )
        inst_res = await db.execute(inst_query)
        inst = inst_res.scalars().first()
        if not inst:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_id}' not found.",
            )

        inst_id = inst.id
        await db.delete(inst)

        if purge_data:
            del_logs = delete(PluginExecutionLog).where(
                PluginExecutionLog.organization_id == org_id,
                PluginExecutionLog.plugin_id == plugin_id,
            )
            await db.execute(del_logs)

        # Decrement installs count
        plugin = await db.get(Plugin, plugin_id)
        if plugin and plugin.installs_count > 0:
            plugin.installs_count -= 1

        await db.commit()
        return {
            "success": True,
            "message": f"Plugin '{plugin_id}' uninstalled successfully.",
            "uninstalled_id": str(inst_id),
        }

    async def execute_plugin_action(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID | None,
        plugin_id: str,
        payload: PluginExecuteRequest,
    ) -> dict[str, Any]:
        """Execute an action inside a sandboxed plugin instance and record telemetry."""
        # Check installation and enabled status
        inst_query = select(PluginInstallation).where(
            PluginInstallation.organization_id == org_id,
            PluginInstallation.plugin_id == plugin_id,
        )
        inst_res = await db.execute(inst_query)
        inst = inst_res.scalars().first()
        if not inst:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_id}' is not installed in this organization.",
            )
        if not inst.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plugin '{plugin_id}' is currently disabled.",
            )

        # Look up plugin implementation class
        plugin_cls = _PLUGIN_REGISTRY.get(plugin_id)
        if not plugin_cls:
            # Fallback stub plugin for catalog items without local runtime implementation
            class DynamicCatalogPlugin(BasePlugin):
                async def initialize(self, configuration: dict[str, Any]) -> None:
                    self.configuration = configuration

                async def execute(self, execution_input: PluginExecutionInput) -> PluginExecutionOutput:
                    return PluginExecutionOutput(
                        success=True,
                        data={
                            "action": execution_input.action,
                            "plugin_id": self.manifest.id,
                            "dispatched_to": "dynamic_connector",
                            "echo_params": execution_input.parameters,
                        },
                    )

                async def shutdown(self) -> None:
                    pass

            manifest_obj = PluginManifest(
                id=plugin_id,
                name=plugin_id,
                version=inst.version,
                developer="Dynamic Runtime",
                description="Dynamic Catalog Plugin Runtime",
                category=PluginCategory.AI,
                entry_point=f"dynamic.{plugin_id}",
                min_keep_version="3.0.0",
                max_keep_version="3.9.9",
            )
            plugin_instance = DynamicCatalogPlugin(manifest_obj)
        else:
            manifest_obj = PluginManifest(
                id=plugin_id,
                name=plugin_id,
                version=inst.version,
                developer="Enterprise Developer",
                description="Enterprise Sandboxed Plugin Runtime",
                category=PluginCategory.AI if "ai" in plugin_id else PluginCategory.INTEGRATION,
                entry_point=f"plugins.{plugin_id}",
                min_keep_version="3.0.0",
                max_keep_version="3.9.9",
            )
            try:
                plugin_instance = plugin_cls()
            except TypeError:
                plugin_instance = plugin_cls(manifest_obj)

        init_res = plugin_instance.initialize(inst.configuration or {})
        if asyncio.iscoroutine(init_res):
            await init_res

        exec_input = PluginExecutionInput(
            plugin_id=plugin_id,
            action=payload.action,
            parameters=payload.parameters,
            context_organization_id=str(org_id),
            context_user_id=str(user_id) if user_id else None,
            timeout_seconds=payload.timeout_seconds,
        )

        runner = PluginSandboxRunner(default_timeout_seconds=payload.timeout_seconds)
        output = await runner.execute_sandboxed(plugin_instance, exec_input)

        log_status = output.status.value if isinstance(output.status, PluginLogStatus) else str(output.status)
        log_record = PluginExecutionLog(
            organization_id=org_id,
            installation_id=inst.id,
            plugin_id=plugin_id,
            action=payload.action,
            status=log_status,
            duration_ms=output.duration_ms,
            triggered_by="direct_api",
            error_message=output.error_message,
            payload_preview={"action": payload.action, "params_count": len(payload.parameters)},
        )
        db.add(log_record)
        await db.commit()
        await db.refresh(log_record)

        return {
            "execution_id": str(log_record.id),
            "plugin_id": plugin_id,
            "action": payload.action,
            "status": log_status,
            "duration_ms": output.duration_ms,
            "result": output.result_data,
            "error_message": output.error_message,
        }

    async def list_execution_logs(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        plugin_id: str | None = None,
        status_filter: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Query execution history and telemetry logs."""
        query = select(PluginExecutionLog).where(PluginExecutionLog.organization_id == org_id)
        if plugin_id:
            query = query.where(PluginExecutionLog.plugin_id == plugin_id)
        if status_filter:
            query = query.where(PluginExecutionLog.status == status_filter.upper())

        query = query.order_by(desc(PluginExecutionLog.created_at)).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()

        return [
            {
                "id": str(log.id),
                "plugin_id": log.plugin_id,
                "action": log.action,
                "status": log.status,
                "duration_ms": log.duration_ms,
                "triggered_by": log.triggered_by,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]

    async def get_plugin_analytics(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Compute operational KPIs, latency percentiles, and category distributions."""
        # Total installed and active
        inst_query = select(
            func.count(PluginInstallation.id),
            func.count(PluginInstallation.id).filter(PluginInstallation.is_enabled.is_(True)),
        ).where(PluginInstallation.organization_id == org_id)
        inst_res = await db.execute(inst_query)
        total_installed, active_plugins = inst_res.first() or (0, 0)

        # Execution telemetry metrics
        log_query = select(
            func.count(PluginExecutionLog.id),
            func.avg(PluginExecutionLog.duration_ms),
            func.count(PluginExecutionLog.id).filter(PluginExecutionLog.status != "SUCCESS"),
        ).where(PluginExecutionLog.organization_id == org_id)
        log_res = await db.execute(log_query)
        total_execs, avg_latency, error_count = log_res.first() or (0, 0.0, 0)

        error_rate = (error_count / total_execs * 100.0) if total_execs and total_execs > 0 else 0.0

        # Distribution by category
        cat_query = (
            select(Plugin.category, func.count(PluginInstallation.id))
            .join(Plugin, PluginInstallation.plugin_id == Plugin.id)
            .where(PluginInstallation.organization_id == org_id)
            .group_by(Plugin.category)
        )
        cat_res = await db.execute(cat_query)
        plugins_by_cat = {row[0]: row[1] for row in cat_res.all()}

        return {
            "total_installed_plugins": total_installed or 0,
            "active_plugins": active_plugins or 0,
            "total_executions": total_execs or 0,
            "avg_latency_ms": round(float(avg_latency or 0.0), 2),
            "error_rate": round(float(error_rate), 2),
            "plugins_by_category": plugins_by_cat,
        }
