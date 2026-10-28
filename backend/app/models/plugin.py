"""KEEP Enterprise Platform — Plugin SDK, Extension Framework & Developer Ecosystem ORM Models.

Specification: devdocs/p3/p3.5.txt Section 3.22 & docs/database/database-schema.md
Author: Member 2 (Backend & Database Lead)
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from backend.app.db.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Plugin(Base, TimestampMixin):
    """Master registry of all marketplace catalog and enterprise plugins."""

    __tablename__ = "plugins"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    developer: Mapped[str] = mapped_column(String(150), nullable=False)
    current_version: Mapped[str] = mapped_column(String(30), default="1.0.0", nullable=False)
    verification_tier: Mapped[str] = mapped_column(String(30), default="COMMUNITY", nullable=False, index=True)
    rating: Mapped[float] = mapped_column(Numeric(3, 2), default=5.00, nullable=False)
    installs_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    documentation_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_repository: Mapped[str | None] = mapped_column(String(500), nullable=True)

    manifests = relationship("PluginManifestModel", back_populates="plugin", cascade="all, delete-orphan")
    installations = relationship("PluginInstallation", back_populates="plugin", cascade="all, delete-orphan")


class PluginManifestModel(Base, UUIDPrimaryKeyMixin):
    """Versioned semantic configuration, capability permissions, and hook definitions."""

    __tablename__ = "plugin_manifests"
    __table_args__ = (
        UniqueConstraint("plugin_id", "version", name="uq_plugin_manifest_version"),
    )

    plugin_id: Mapped[str] = mapped_column(
        ForeignKey("plugins.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(30), nullable=False)
    manifest_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    min_keep_version: Mapped[str] = mapped_column(String(30), default="3.0.0", nullable=False)
    max_keep_version: Mapped[str] = mapped_column(String(30), default="3.9.9", nullable=False)
    entry_point: Mapped[str] = mapped_column(String(255), nullable=False)
    permissions: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    event_hooks: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    configuration_schema: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    plugin = relationship("Plugin", back_populates="manifests")


class PluginInstallation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tenant-specific installation and lifecycle state."""

    __tablename__ = "plugin_installations"
    __table_args__ = (
        UniqueConstraint("organization_id", "plugin_id", name="uq_org_plugin_installation"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plugin_id: Mapped[str] = mapped_column(
        ForeignKey("plugins.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    installed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    plugin = relationship("Plugin", back_populates="installations")
    permissions = relationship("PluginPermission", back_populates="installation", cascade="all, delete-orphan")
    event_hooks = relationship("PluginEventHook", back_populates="installation", cascade="all, delete-orphan")
    execution_logs = relationship("PluginExecutionLog", back_populates="installation")


class PluginPermission(Base, UUIDPrimaryKeyMixin):
    """Granular granted capabilities per tenant installation."""

    __tablename__ = "plugin_permissions"
    __table_args__ = (
        UniqueConstraint("installation_id", "permission", name="uq_installation_permission"),
    )

    installation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plugin_installations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permission: Mapped[str] = mapped_column(String(80), nullable=False)
    is_granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    installation = relationship("PluginInstallation", back_populates="permissions")


class PluginEventHook(Base, UUIDPrimaryKeyMixin):
    """Runtime event subscriptions bound to active installations."""

    __tablename__ = "plugin_event_hooks"
    __table_args__ = (
        UniqueConstraint("installation_id", "event_topic", name="uq_installation_event"),
    )

    installation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plugin_installations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_topic: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    handler_method: Mapped[str] = mapped_column(String(120), default="on_event", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    installation = relationship("PluginInstallation", back_populates="event_hooks")


class PluginExecutionLog(Base, UUIDPrimaryKeyMixin):
    """Audit trail and sandbox execution telemetry."""

    __tablename__ = "plugin_execution_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    installation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("plugin_installations.id", ondelete="SET NULL"), nullable=True
    )
    plugin_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    triggered_by: Mapped[str] = mapped_column(String(50), default="direct_api", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_preview: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    installation = relationship("PluginInstallation", back_populates="execution_logs")
