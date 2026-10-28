"""KEEP Enterprise Platform — Security, Compliance & Governance ORM Models.

Specification: devdocs/p3/p3.3.txt Section 3.20 & docs/database/database-schema.md
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
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class SecurityMFACredential(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Encrypted TOTP shared secrets and backup recovery codes per enterprise user."""

    __tablename__ = "security_mfa_credentials"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_mfa_user"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    secret_key: Mapped[str] = mapped_column(String(255), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    backup_codes: Mapped[list[Any]] = mapped_column(JSONB, server_default="[]", nullable=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User")


class SecurityAuditLog(Base, UUIDPrimaryKeyMixin):
    """Immutable enterprise audit log recording all authorization and operational events."""

    __tablename__ = "security_audit_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), default="127.0.0.1", nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="SUCCESS", nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    organization = relationship("Organization")
    user = relationship("User")


class SecurityDataClassification(Base, UUIDPrimaryKeyMixin):
    """Document data sensitivity classification tier and detected PII entity inventory."""

    __tablename__ = "security_data_classifications"
    __table_args__ = (
        UniqueConstraint("document_id", name="uq_data_classification_doc"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    classification_level: Mapped[str] = mapped_column(
        String(30), default="INTERNAL", nullable=False, index=True
    )
    detected_pii_entities: Mapped[list[Any]] = mapped_column(JSONB, server_default="[]", nullable=False)
    pii_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    scan_status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False)
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    organization = relationship("Organization")
    document = relationship("Document")


class SecurityAIGovernanceLog(Base, UUIDPrimaryKeyMixin):
    """Audit log for AI inference, prompt injection verification, and token telemetry."""

    __tablename__ = "security_ai_governance_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    retrieved_sources: Mapped[list[Any]] = mapped_column(JSONB, server_default="[]", nullable=False)
    guardrail_status: Mapped[str] = mapped_column(String(30), default="PASSED", nullable=False, index=True)
    guardrail_flags: Mapped[list[Any]] = mapped_column(JSONB, server_default="[]", nullable=False)
    token_usage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    user_feedback: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    organization = relationship("Organization")
    user = relationship("User")


class SecurityCompliancePolicy(Base, UUIDPrimaryKeyMixin):
    """Regulatory framework control status and compliance posture tracking."""

    __tablename__ = "security_compliance_policies"
    __table_args__ = (
        UniqueConstraint("organization_id", "standard", "control_key", name="uq_compliance_control"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    standard: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    control_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="COMPLIANT", nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    last_evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    organization = relationship("Organization")


class SecurityDataRetentionRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Configurable automated data retention and purge rules per resource type."""

    __tablename__ = "security_data_retention_rules"
    __table_args__ = (
        UniqueConstraint("organization_id", "resource_type", name="uq_retention_resource"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    resource_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    retention_days: Mapped[int] = mapped_column(Integer, default=365, nullable=False)
    action_on_expiry: Mapped[str] = mapped_column(String(30), default="ARCHIVE", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization = relationship("Organization")


class SecurityErasureRequest(Base, UUIDPrimaryKeyMixin):
    """GDPR Article 17 Right to Erasure execution tracking and certificate archive."""

    __tablename__ = "security_erasure_requests"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    requester_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    target_user_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    target_email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    anonymized_assets_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    certificate_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    organization = relationship("Organization")
    requester = relationship("User", foreign_keys=[requester_id])


class SecurityThreatAlert(Base, UUIDPrimaryKeyMixin):
    """Automated security incident and threat anomaly detection alert."""

    __tablename__ = "security_threat_alerts"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    alert_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_ip: Mapped[str] = mapped_column(String(45), default="127.0.0.1", nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    organization = relationship("Organization")
