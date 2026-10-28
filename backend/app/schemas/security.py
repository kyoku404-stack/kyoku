"""Pydantic v2 schemas for Enterprise Security, Compliance, Governance & Data Protection.

Specification: devdocs/p3/p3.3.txt Section 15 & docs/api/api-contract.md
Author: Member 2 (Backend & Database Lead)
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ------------------------------------------------------------------------------
# 15.1 Enterprise Authentication & Session Management
# ------------------------------------------------------------------------------


class EnterpriseLoginRequest(BaseModel):
    """Payload for enterprise login or SSO authentication."""

    email: str = Field(..., description="Enterprise user email address")
    password: str = Field(..., min_length=6, description="User password for local credentials")
    provider: str = Field(default="local", description="Identity provider (local, okta, azure, google)")
    sso_token: str | None = Field(default=None, description="Optional third-party identity token")


class EnterpriseLoginData(BaseModel):
    """Authentication token claims and user profile context."""

    access_token: str = Field(..., description="Signed JWT bearer access token")
    token_type: str = Field(default="bearer", description="Token scheme type")
    expires_in: int = Field(default=3600, description="Token validity lifetime in seconds")
    user_id: uuid.UUID = Field(..., description="Authenticated user ID")
    organization_id: uuid.UUID = Field(..., description="Tenant organization ID")
    role: str = Field(..., description="Assigned organizational role")
    mfa_required: bool = Field(default=False, description="Whether MFA verification is mandated")
    mfa_verified: bool = Field(default=True, description="Whether MFA verification succeeded")


class EnterpriseLoginResponse(BaseModel):
    """Envelope response for enterprise authentication."""

    success: bool = True
    message: str = "Authentication successful."
    data: EnterpriseLoginData


class EnterpriseLogoutResponse(BaseModel):
    """Response confirming session invalidation."""

    success: bool = True
    message: str = "Session invalidated successfully."


# ------------------------------------------------------------------------------
# 15.2 Multi-Factor Authentication (MFA / TOTP)
# ------------------------------------------------------------------------------


class MFASetupData(BaseModel):
    """TOTP shared secret and backup recovery codes."""

    secret_key: str = Field(..., description="Base32 TOTP secret key")
    otpauth_uri: str = Field(..., description="RFC 6238 authenticator app registration URI")
    backup_codes: list[str] = Field(default_factory=list, description="Single-use recovery codes")


class MFASetupResponse(BaseModel):
    """Response returning MFA provisioning payload."""

    success: bool = True
    data: MFASetupData


class MFAVerifyRequest(BaseModel):
    """Payload to verify TOTP code."""

    code: str = Field(..., min_length=6, max_length=10, description="6-digit TOTP code or backup code")


class MFAVerifyData(BaseModel):
    """MFA verification outcome."""

    is_enabled: bool = True
    mfa_verified: bool = True


class MFAVerifyResponse(BaseModel):
    """Response confirming MFA verification."""

    success: bool = True
    message: str = "Multi-factor authentication verified."
    data: MFAVerifyData


class MFADisableRequest(BaseModel):
    """Payload to deactivate MFA."""

    code: str = Field(..., min_length=6, max_length=10, description="Current 6-digit TOTP code")


class MFADisableResponse(BaseModel):
    """Response confirming MFA deactivation."""

    success: bool = True
    message: str = "MFA disabled successfully."


# ------------------------------------------------------------------------------
# 15.3 Enterprise Audit Trails
# ------------------------------------------------------------------------------


class SecurityAuditLogData(BaseModel):
    """Individual security and access audit record."""

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID | None = None
    action: str
    resource: str
    resource_id: str | None = None
    ip_address: str = "127.0.0.1"
    user_agent: str | None = None
    status: str = "SUCCESS"
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class PaginatedSecurityAuditLogsResponse(BaseModel):
    """Paginated security audit trail response."""

    success: bool = True
    total: int
    page: int = 1
    page_size: int = 50
    data: list[SecurityAuditLogData] = Field(default_factory=list)


# ------------------------------------------------------------------------------
# 15.4 Roles & Permissions Management
# ------------------------------------------------------------------------------


class RolePermissionItem(BaseModel):
    """Defined organizational role and permitted action scopes."""

    role: str
    description: str
    permissions: list[str] = Field(default_factory=list)


class RolePermissionsResponse(BaseModel):
    """List of all recognized platform roles and assigned permissions."""

    success: bool = True
    data: list[RolePermissionItem]


class UpdateRolePermissionsRequest(BaseModel):
    """Payload for modifying permissions assigned to an organizational role."""

    role: str
    permissions: list[str] = Field(default_factory=list)


class UpdateRolePermissionsResponse(BaseModel):
    """Response confirming role permission modification."""

    success: bool = True
    message: str = "Permissions updated successfully."


# ------------------------------------------------------------------------------
# 15.5 Sensitive Data Classification & PII Scanner
# ------------------------------------------------------------------------------


class DataClassificationScanRequest(BaseModel):
    """Payload for scanning text or document payload for sensitive information."""

    document_id: str | None = None
    content: str = Field(..., min_length=1, description="Text content to inspect for sensitive PII")


class DetectedPIIEntitySchema(BaseModel):
    """Individual detected sensitive entity."""

    type: str
    count: int
    masked_sample: str


class DataClassificationScanData(BaseModel):
    """Classification assessment and redacted preview."""

    document_id: str | None = None
    classification_level: str
    detected_pii_entities: list[DetectedPIIEntitySchema] = Field(default_factory=list)
    pii_count: int = 0
    confidence_score: float = 1.0
    redacted_preview: str = ""


class DataClassificationScanResponse(BaseModel):
    """Response returning data classification and PII scan findings."""

    success: bool = True
    data: DataClassificationScanData


class DocumentClassificationStatusData(BaseModel):
    """Stored sensitivity classification status for a document."""

    document_id: uuid.UUID
    classification_level: str
    pii_count: int = 0
    confidence_score: float = 1.0
    scanned_at: datetime


class DocumentClassificationStatusResponse(BaseModel):
    """Response returning document classification status."""

    success: bool = True
    data: DocumentClassificationStatusData


# ------------------------------------------------------------------------------
# 15.6 AI Governance & Safety Guardrails
# ------------------------------------------------------------------------------


class AIGovernanceLogItem(BaseModel):
    """Summary of an audited AI inference interaction."""

    id: uuid.UUID
    user_id: uuid.UUID | None = None
    prompt_snippet: str
    model_name: str
    guardrail_status: str
    token_usage: int = 0
    latency_ms: float = 0.0
    created_at: datetime


class AIGovernanceLogsResponse(BaseModel):
    """Paginated AI governance inspection records."""

    success: bool = True
    total: int
    data: list[AIGovernanceLogItem] = Field(default_factory=list)


class AIGovernanceStatsData(BaseModel):
    """Aggregated AI safety and guardrail telemetry."""

    total_queries_audited: int = 0
    guardrail_blocks: int = 0
    avg_latency_ms: float = 0.0
    prompt_injection_attempts: int = 0
    safety_score_percentage: float = 100.0


class AIGovernanceStatsResponse(BaseModel):
    """Response returning AI governance telemetry metrics."""

    success: bool = True
    data: AIGovernanceStatsData


# ------------------------------------------------------------------------------
# 15.7 Enterprise Compliance Framework
# ------------------------------------------------------------------------------


class ComplianceStandardScoreItem(BaseModel):
    """Readiness evaluation for a regulatory governance standard."""

    standard: str
    score: int
    status: str
    controls_passed: int
    controls_total: int


class ComplianceOverviewData(BaseModel):
    """Overall organizational regulatory compliance rating."""

    overall_compliance_score: int
    standards: list[ComplianceStandardScoreItem] = Field(default_factory=list)


class ComplianceOverviewResponse(BaseModel):
    """Response returning multi-standard compliance status."""

    success: bool = True
    data: ComplianceOverviewData


class DataRetentionPolicyRequest(BaseModel):
    """Configuration of automated retention policy for a resource type."""

    resource_type: str = Field(..., description="Resource category (e.g. audit_logs, chat_sessions)")
    retention_days: int = Field(default=365, ge=1, le=3650, description="Retention horizon in days")
    action_on_expiry: str = Field(default="ARCHIVE", description="Action upon expiry (ARCHIVE, PURGE)")


class DataRetentionPolicyResponse(BaseModel):
    """Response confirming retention policy update."""

    success: bool = True
    message: str = "Data retention policy updated."


class GDPRErasureRequest(BaseModel):
    """Request to anonymize and erase personal data under GDPR Art. 17."""

    target_user_id: uuid.UUID
    reason: str | None = None


class GDPRErasureData(BaseModel):
    """Erasure execution certificate."""

    erasure_id: uuid.UUID
    completed_at: datetime


class GDPRErasureResponse(BaseModel):
    """Response confirming execution of GDPR erasure."""

    success: bool = True
    message: str = "User data anonymized and erased in accordance with GDPR Article 17."
    data: GDPRErasureData


# ------------------------------------------------------------------------------
# 15.8 Security Monitoring & Anomaly Alerts
# ------------------------------------------------------------------------------


class SecurityThreatAlertItem(BaseModel):
    """Threat incident or security anomaly alert."""

    id: uuid.UUID
    alert_type: str
    severity: str
    description: str
    source_ip: str
    resolved: bool = False
    triggered_at: datetime


class SecurityThreatAlertsResponse(BaseModel):
    """Response returning detected security threat alerts."""

    success: bool = True
    data: list[SecurityThreatAlertItem] = Field(default_factory=list)


class SecurityThreatAlertResponse(BaseModel):
    """Response returning a single resolved security threat alert."""

    success: bool = True
    data: SecurityThreatAlertItem
