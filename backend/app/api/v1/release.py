"""KEEP Enterprise Platform — Phase 3.7 Production Release & Security Audit API Endpoints.

Specification Source: devdocs/p3/p3.7.txt (Chapters 1-20) & docs/api/api-contract.md (Section 19)
Role: Member 2 (Backend & Database Lead)
"""

from __future__ import annotations

from backend.app.api.dependencies.auth import AuthenticatedUser
from backend.app.api.dependencies.authorization import require_permission
from backend.app.api.dependencies.database import get_db
from backend.app.schemas.release import (
    PreflightCheckDetail,
    ReleaseDeployData,
    ReleaseDeployRequest,
    ReleaseDeployResponse,
    ReleaseHistoryItemData,
    ReleaseHistoryResponse,
    SecurityAuditData,
    SecurityAuditResponse,
    SecurityControlData,
    SecurityFindingData,
    SystemReadinessData,
    SystemReadinessResponse,
)
from backend.app.services.ai.interfaces import AIPermission
from backend.app.services.release.contracts import (
    PreflightCheckCategory,
)
from backend.app.services.release.service import release_service
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/system", tags=["Production Release & Quality Assurance"])


# ============================================================================
# 1. System Pre-Flight Readiness Gate
# ============================================================================

@router.get(
    "/readiness",
    response_model=SystemReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate system pre-flight deployment readiness",
    description="Evaluates database migrations, connection pool, Redis cache hit ratio, storage headroom, pgvector HNSW index, AI model cache, and security audit gates.",
)
async def get_system_readiness(
    target_version: str = Query(default="1.0.0", description="Target release semantic version"),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.RELEASE_VIEW)),
    db: AsyncSession = Depends(get_db),
) -> SystemReadinessResponse:
    """Computes real-time system readiness score and validates production deployment gates."""
    report = await release_service.get_deployment_readiness(db, target_version=target_version)

    checks_detail = [
        PreflightCheckDetail(
            check_name=c.check_name,
            category=c.category.value if isinstance(c.category, PreflightCheckCategory) else str(c.category),
            status=c.status.value if hasattr(c.status, "value") else str(c.status),
            score=c.score,
            details=c.details,
            verified_at=c.verified_at,
        )
        for c in report.checks
    ]

    data = SystemReadinessData(
        is_ready=report.is_ready,
        overall_score=report.overall_score,
        evaluated_at=report.evaluated_at,
        target_version=report.target_version,
        git_commit=report.git_commit,
        checks=checks_detail,
        failing_checks=report.failing_checks,
    )

    return SystemReadinessResponse(
        success=True,
        message="System pre-flight readiness evaluation completed.",
        data=data,
    )


# ============================================================================
# 2. Production Release Trigger
# ============================================================================

@router.post(
    "/release",
    response_model=ReleaseDeployResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger production release deployment",
    description="Validates pre-flight readiness gate, packages container and SPA artifacts, tags release, and records production deployment audit trail.",
)
async def trigger_production_release(
    payload: ReleaseDeployRequest,
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.RELEASE_DEPLOY)),
    db: AsyncSession = Depends(get_db),
) -> ReleaseDeployResponse:
    """Executes a production release deployment when all pre-flight gates pass."""
    user_id_str = str(current_user.id) if current_user and current_user.id else None
    release_row = await release_service.trigger_production_release(
        db=db,
        request=payload,
        user_id=user_id_str,
    )

    deploy_data = ReleaseDeployData(
        release_id=release_row.release_id,
        version=release_row.version,
        release_tag=release_row.release_tag,
        git_commit=release_row.git_commit,
        status=release_row.status,
        preflight_score=float(release_row.preflight_score),
        deployed_by=str(release_row.deployed_by) if release_row.deployed_by else None,
        started_at=release_row.started_at,
        completed_at=release_row.completed_at,
        changelog=release_row.changelog,
        artifacts=release_row.artifacts_json or {},
    )

    return ReleaseDeployResponse(
        success=True,
        message="Production release deployment initiated successfully.",
        data=deploy_data,
    )


# ============================================================================
# 3. Release History Catalog
# ============================================================================

@router.get(
    "/releases",
    response_model=ReleaseHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get catalog of historical production releases",
    description="Retrieves chronological log of all historical production releases, SemVer tags, pre-flight scores, and artifact manifests.",
)
async def get_release_history(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum release records to return"),
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.RELEASE_VIEW)),
    db: AsyncSession = Depends(get_db),
) -> ReleaseHistoryResponse:
    """Returns historical production releases ordered newest first."""
    releases = await release_service.get_release_history(db=db, limit=limit)

    items = [
        ReleaseHistoryItemData(
            release_id=r.release_id,
            version=r.version,
            release_tag=r.release_tag,
            git_commit=r.git_commit,
            status=r.status,
            preflight_score=float(r.preflight_score),
            deployed_by=str(r.deployed_by) if r.deployed_by else None,
            created_at=r.created_at,
            completed_at=r.completed_at,
        )
        for r in releases
    ]

    return ReleaseHistoryResponse(
        success=True,
        data=items,
    )


# ============================================================================
# 4. Enterprise Security Audit Report
# ============================================================================

@router.get(
    "/security/audit",
    response_model=SecurityAuditResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute enterprise cybersecurity & compliance audit",
    description="Evaluates all 10 OWASP Top 10 and LLM Top 10 security controls including SQLi, XSS, CSRF, RBAC, Encryption, Prompt Injection, Audit Logging, DDoS, CVE hygiene, and Sandbox isolation.",
)
async def get_security_audit(
    current_user: AuthenticatedUser = Depends(require_permission(AIPermission.RELEASE_VIEW)),
    db: AsyncSession = Depends(get_db),
) -> SecurityAuditResponse:
    """Runs automated security audit and returns compliance breakdown."""
    auditor_id_str = str(current_user.id) if current_user and current_user.id else None
    audit_record = await release_service.get_security_audit_report(db=db, auditor_id=auditor_id_str)

    controls_list = [
        SecurityControlData(
            control_id=c.get("control_id", ""),
            name=c.get("name", ""),
            status=c.get("status", "PASSED"),
            severity=c.get("severity", "HIGH"),
            description=c.get("description", ""),
            mitigation=c.get("mitigation", ""),
        )
        for c in (audit_record.controls_json or [])
    ]

    findings_list = [
        SecurityFindingData(
            finding_id=f.get("finding_id", ""),
            control_id=f.get("control_id", ""),
            severity=f.get("severity", "HIGH"),
            title=f.get("title", ""),
            remediation=f.get("remediation", ""),
            resolved=f.get("resolved", False),
        )
        for f in (audit_record.findings_json or [])
    ]

    audit_data = SecurityAuditData(
        compliance_standard=audit_record.compliance_standard,
        overall_compliance_percent=float(audit_record.overall_score),
        evaluated_at=audit_record.created_at,
        total_controls=audit_record.total_controls,
        passed_controls=audit_record.passed_controls,
        failed_controls=audit_record.failed_controls,
        controls=controls_list,
        findings=findings_list,
    )

    return SecurityAuditResponse(
        success=True,
        message="Enterprise security audit completed successfully.",
        data=audit_data,
    )
