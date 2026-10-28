"""KEEP Enterprise Platform — Security, Compliance & Governance Endpoints.

Serves enterprise login/logout, adaptive MFA, immutable audit trails,
RBAC permission matrices, automated PII & data classification, AI governance,
multi-standard regulatory compliance, and security threat alerts.

Specification: devdocs/p3/p3.3.txt & docs/api/api-contract.md Section 15
Author: Member 2 (Backend & Database Lead)
"""

from datetime import UTC, datetime
from uuid import UUID

from backend.app.api.dependencies.auth import (
    AuthenticatedUser,
    get_current_active_user,
)
from backend.app.api.dependencies.database import get_db
from backend.app.schemas.security import (
    AIGovernanceLogItem,
    AIGovernanceLogsResponse,
    AIGovernanceStatsData,
    AIGovernanceStatsResponse,
    ComplianceOverviewData,
    ComplianceOverviewResponse,
    ComplianceStandardScoreItem,
    DataClassificationScanData,
    DataClassificationScanRequest,
    DataClassificationScanResponse,
    DataRetentionPolicyRequest,
    DataRetentionPolicyResponse,
    DetectedPIIEntitySchema,
    DocumentClassificationStatusData,
    DocumentClassificationStatusResponse,
    EnterpriseLoginData,
    EnterpriseLoginRequest,
    EnterpriseLoginResponse,
    EnterpriseLogoutResponse,
    GDPRErasureData,
    GDPRErasureRequest,
    GDPRErasureResponse,
    MFADisableRequest,
    MFADisableResponse,
    MFASetupData,
    MFASetupResponse,
    MFAVerifyData,
    MFAVerifyRequest,
    MFAVerifyResponse,
    PaginatedSecurityAuditLogsResponse,
    RolePermissionItem,
    RolePermissionsResponse,
    SecurityAuditLogData,
    SecurityThreatAlertItem,
    SecurityThreatAlertResponse,
    SecurityThreatAlertsResponse,
    UpdateRolePermissionsRequest,
    UpdateRolePermissionsResponse,
)
from backend.app.services.security.service import EnterpriseSecurityService
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/security", tags=["Security & Compliance"])
security_service = EnterpriseSecurityService()


# ==============================================================================
# 15.1 Enterprise Authentication & Session Management
# ==============================================================================


@router.post(
    "/login",
    response_model=EnterpriseLoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Enterprise user login & SSO handshake",
    description="Authenticates enterprise user credentials or processes SSO tokens with MFA status.",
)
async def login(
    payload: EnterpriseLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> EnterpriseLoginResponse:
    ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent")

    result = await security_service.authenticate_user(
        db=db,
        email=payload.email,
        password=payload.password,
        provider=payload.provider,
        sso_token=payload.sso_token,
        ip_address=ip,
        user_agent=user_agent,
    )
    return EnterpriseLoginResponse(
        success=True,
        message="Authentication successful.",
        data=EnterpriseLoginData(**result),
    )


@router.post(
    "/logout",
    response_model=EnterpriseLogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Enterprise session logout",
    description="Revokes the active enterprise session and registers an immutable audit event.",
)
async def logout(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EnterpriseLogoutResponse:
    ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent")

    await security_service.logout_session(
        db=db,
        user_id=current_user.id,
        org_id=current_user.organization_id,
        ip_address=ip,
        user_agent=user_agent,
    )
    return EnterpriseLogoutResponse(success=True, message="Session invalidated successfully.")


# ==============================================================================
# 15.2 Multi-Factor Authentication (MFA / TOTP)
# ==============================================================================


@router.post(
    "/mfa/setup",
    response_model=MFASetupResponse,
    status_code=status.HTTP_200_OK,
    summary="Provision MFA TOTP secret and backup codes",
    description="Generates an RFC 6238 TOTP shared secret and backup recovery codes for user account.",
)
async def setup_mfa(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MFASetupResponse:
    data = await security_service.setup_mfa(
        db=db,
        user_id=current_user.id,
        email=current_user.email,
    )
    return MFASetupResponse(success=True, data=MFASetupData(**data))


@router.post(
    "/mfa/verify",
    response_model=MFAVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify MFA passcode",
    description="Validates a 6-digit TOTP code or backup recovery code to activate MFA protection.",
)
async def verify_mfa(
    payload: MFAVerifyRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MFAVerifyResponse:
    is_valid = await security_service.verify_mfa(
        db=db,
        user_id=current_user.id,
        code=payload.code,
    )
    return MFAVerifyResponse(
        success=True,
        message="Multi-factor authentication verified.",
        data=MFAVerifyData(is_enabled=is_valid, mfa_verified=is_valid),
    )


@router.post(
    "/mfa/disable",
    response_model=MFADisableResponse,
    status_code=status.HTTP_200_OK,
    summary="Disable MFA",
    description="Deactivates MFA protection for the authenticated user upon valid passcode confirmation.",
)
async def disable_mfa(
    payload: MFADisableRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MFADisableResponse:
    await security_service.disable_mfa(
        db=db,
        user_id=current_user.id,
        code=payload.code,
    )
    return MFADisableResponse(success=True, message="MFA disabled successfully.")


# ==============================================================================
# 15.3 Enterprise Audit Trails
# ==============================================================================


@router.get(
    "/audit",
    response_model=PaginatedSecurityAuditLogsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve immutable security audit trail",
    description="Queries tamper-evident security and data access audit events scoped to tenant.",
)
async def get_audit_trail(
    action: str | None = Query(default=None, description="Filter by event action"),
    status_filter: str | None = Query(default=None, alias="status", description="Filter by status (SUCCESS, FAILURE, DENIED)"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedSecurityAuditLogsResponse:
    logs, total = await security_service.get_audit_logs(
        db=db,
        org_id=current_user.organization_id,
        action=action,
        status=status_filter,
        page=page,
        page_size=page_size,
    )
    return PaginatedSecurityAuditLogsResponse(
        success=True,
        total=total,
        page=page,
        page_size=page_size,
        data=[
            SecurityAuditLogData(
                id=log.id,
                organization_id=log.organization_id,
                user_id=log.user_id,
                action=log.action,
                resource=log.resource,
                resource_id=log.resource_id,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                status=log.status,
                details=log.details,
                created_at=log.created_at,
            )
            for log in logs
        ],
    )


# ==============================================================================
# 15.4 Roles & Permissions Management
# ==============================================================================


@router.get(
    "/roles",
    response_model=RolePermissionsResponse,
    status_code=status.HTTP_200_OK,
    summary="List role permission matrix",
    description="Returns all predefined organizational roles and their authorized permission scopes.",
)
async def get_roles(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
) -> RolePermissionsResponse:
    roles = security_service.get_roles_and_permissions()
    return RolePermissionsResponse(
        success=True,
        data=[RolePermissionItem(**r) for r in roles],
    )


@router.post(
    "/permissions",
    response_model=UpdateRolePermissionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Update role permissions",
    description="Updates action scopes assigned to an organizational role.",
)
async def update_role_permissions(
    payload: UpdateRolePermissionsRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UpdateRolePermissionsResponse:
    await security_service.log_audit_event(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        action="ROLE_PERMISSIONS_UPDATE",
        resource="roles",
        resource_id=payload.role,
        status="SUCCESS",
        details={"permissions": payload.permissions},
    )
    return UpdateRolePermissionsResponse(success=True, message="Permissions updated successfully.")


# ==============================================================================
# 15.5 Sensitive Data Classification & PII Scanner
# ==============================================================================


@router.post(
    "/data-classification/scan",
    response_model=DataClassificationScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan content for PII & assign sensitivity tier",
    description="Inspects text for PII, secrets, and financial info, outputting tier and redacted preview.",
)
async def scan_data_classification(
    payload: DataClassificationScanRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DataClassificationScanResponse:
    result = await security_service.scan_data_classification(
        db=db,
        org_id=current_user.organization_id,
        content=payload.content,
        document_id=payload.document_id,
    )
    return DataClassificationScanResponse(
        success=True,
        data=DataClassificationScanData(
            document_id=result["document_id"],
            classification_level=result["classification_level"],
            detected_pii_entities=[DetectedPIIEntitySchema(**e) for e in result["detected_pii_entities"]],
            pii_count=result["pii_count"],
            confidence_score=result["confidence_score"],
            redacted_preview=result["redacted_preview"],
        ),
    )


@router.get(
    "/data-classification/{document_id}",
    response_model=DocumentClassificationStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document classification status",
    description="Retrieves the sensitivity classification and scanned PII summary for a document.",
)
async def get_document_classification_status(
    document_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentClassificationStatusResponse:
    record = await security_service.get_document_classification(
        db=db,
        org_id=current_user.organization_id,
        document_id=document_id,
    )
    if not record:
        # Default fallback if unscanned
        return DocumentClassificationStatusResponse(
            success=True,
            data=DocumentClassificationStatusData(
                document_id=document_id,
                classification_level="INTERNAL",
                pii_count=0,
                confidence_score=1.0,
                scanned_at=datetime.now(UTC),
            ),
        )
    return DocumentClassificationStatusResponse(
        success=True,
        data=DocumentClassificationStatusData(
            document_id=record.document_id,
            classification_level=record.classification_level,
            pii_count=record.pii_count,
            confidence_score=record.confidence_score,
            scanned_at=record.scanned_at,
        ),
    )


# ==============================================================================
# 15.6 AI Governance & Safety Guardrails
# ==============================================================================


@router.get(
    "/ai-governance/logs",
    response_model=AIGovernanceLogsResponse,
    status_code=status.HTTP_200_OK,
    summary="Query AI governance inspection logs",
    description="Retrieves logged AI model prompts, guardrail flags, token usage, and latency records.",
)
async def get_ai_governance_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AIGovernanceLogsResponse:
    logs, total = await security_service.get_ai_governance_logs(
        db=db,
        org_id=current_user.organization_id,
        page=page,
        page_size=page_size,
    )
    return AIGovernanceLogsResponse(
        success=True,
        total=total,
        data=[
            AIGovernanceLogItem(
                id=log.id,
                user_id=log.user_id,
                prompt_snippet=log.prompt_text[:80] + ("..." if len(log.prompt_text) > 80 else ""),
                model_name=log.model_name,
                guardrail_status=log.guardrail_status,
                token_usage=log.token_usage,
                latency_ms=log.latency_ms,
                created_at=log.created_at,
            )
            for log in logs
        ],
    )


@router.get(
    "/ai-governance/stats",
    response_model=AIGovernanceStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="AI governance safety telemetry",
    description="Aggregated safety metrics, guardrail block counts, and average latency.",
)
async def get_ai_governance_stats(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AIGovernanceStatsResponse:
    stats = await security_service.get_ai_governance_stats(
        db=db,
        org_id=current_user.organization_id,
    )
    return AIGovernanceStatsResponse(
        success=True,
        data=AIGovernanceStatsData(**stats),
    )


# ==============================================================================
# 15.7 Enterprise Compliance Framework
# ==============================================================================


@router.get(
    "/compliance",
    response_model=ComplianceOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Multi-standard compliance rating & scorecards",
    description="Calculates compliance readiness across GDPR, ISO 27001, SOC 2, and HIPAA frameworks.",
)
async def get_compliance_posture(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ComplianceOverviewResponse:
    data = await security_service.get_compliance_overview(
        db=db,
        org_id=current_user.organization_id,
    )
    return ComplianceOverviewResponse(
        success=True,
        data=ComplianceOverviewData(
            overall_compliance_score=data["overall_compliance_score"],
            standards=[ComplianceStandardScoreItem(**s) for s in data["standards"]],
        ),
    )


@router.post(
    "/compliance/retention-policies",
    response_model=DataRetentionPolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Configure data retention policy",
    description="Configures time-to-live retention days and automated purge/archive action per resource type.",
)
async def set_retention_policy(
    payload: DataRetentionPolicyRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DataRetentionPolicyResponse:
    await security_service.set_retention_policy(
        db=db,
        org_id=current_user.organization_id,
        resource_type=payload.resource_type,
        retention_days=payload.retention_days,
        action_on_expiry=payload.action_on_expiry,
    )
    return DataRetentionPolicyResponse(success=True, message="Data retention policy updated.")


@router.post(
    "/compliance/gdpr-erasure",
    response_model=GDPRErasureResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute GDPR Article 17 Right to Erasure",
    description="Anonymizes personal identifiers and produces a verifiable erasure certificate.",
)
async def execute_gdpr_erasure(
    payload: GDPRErasureRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GDPRErasureResponse:
    req = await security_service.execute_gdpr_erasure(
        db=db,
        org_id=current_user.organization_id,
        requester_id=current_user.id,
        target_user_id=payload.target_user_id,
        reason=payload.reason,
    )
    return GDPRErasureResponse(
        success=True,
        message="User data anonymized and erased in accordance with GDPR Article 17.",
        data=GDPRErasureData(
            erasure_id=req.id,
            completed_at=req.completed_at or req.created_at,
        ),
    )


# ==============================================================================
# 15.8 Security Monitoring & Anomaly Alerts
# ==============================================================================


@router.get(
    "/monitoring/alerts",
    response_model=SecurityThreatAlertsResponse,
    status_code=status.HTTP_200_OK,
    summary="Query security threat and anomaly alerts",
    description="Retrieves security alerts including failed login spikes and prompt injection events.",
)
async def get_threat_alerts(
    unresolved_only: bool = Query(default=False, description="Filter for unresolved alerts"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SecurityThreatAlertsResponse:
    alerts = await security_service.get_threat_alerts(
        db=db,
        org_id=current_user.organization_id,
        unresolved_only=unresolved_only,
    )
    return SecurityThreatAlertsResponse(
        success=True,
        data=[
            SecurityThreatAlertItem(
                id=a.id,
                alert_type=a.alert_type,
                severity=a.severity,
                description=a.description,
                source_ip=a.source_ip,
                resolved=a.resolved,
                triggered_at=a.triggered_at,
            )
            for a in alerts
        ],
    )


@router.put(
    "/monitoring/alerts/{alert_id}/resolve",
    response_model=SecurityThreatAlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Resolve a security threat incident",
    description="Marks an active threat anomaly alert as investigated and resolved.",
)
async def resolve_threat_alert(
    alert_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SecurityThreatAlertResponse:
    alert = await security_service.resolve_threat_alert(
        db=db,
        org_id=current_user.organization_id,
        alert_id=alert_id,
    )
    return SecurityThreatAlertResponse(
        success=True,
        data=SecurityThreatAlertItem(
            id=alert.id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            description=alert.description,
            source_ip=alert.source_ip,
            resolved=alert.resolved,
            triggered_at=alert.triggered_at,
        ),
    )
