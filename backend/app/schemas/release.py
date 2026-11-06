"""KEEP Enterprise Platform — Phase 3.7 Release & Security Audit Pydantic v2 Schemas.

Specification: devdocs/p3/p3.7.txt Section 19 & docs/api/api-contract.md
Author: Member 2 (Backend & Database Lead)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# 1. Pre-Flight Readiness Schemas
# ============================================================================

class PreflightCheckDetail(BaseModel):
    """Detailed result for an individual pre-flight readiness check."""
    model_config = ConfigDict(extra="allow", from_attributes=True)

    check_name: str = Field(description="Unique checkpoint identifier")
    category: str = Field(description="Check category (PERSISTENCE, CACHE, STORAGE, AI_INFRA, GOVERNANCE)")
    status: str = Field(description="Status of the check (PASSED, FAILED, WARNING, SKIPPED)")
    score: float = Field(default=1.0, description="Normalized score contribution (0.0 to 1.0)")
    details: dict[str, Any] = Field(default_factory=dict, description="Diagnostic telemetry attributes")
    verified_at: datetime = Field(description="UTC timestamp of the check evaluation")


class SystemReadinessData(BaseModel):
    """Aggregated pre-flight readiness data."""
    model_config = ConfigDict(from_attributes=True)

    is_ready: bool = Field(description="Whether the platform satisfies production release gates")
    overall_score: float = Field(description="Composite pre-flight readiness score (0.0 to 1.0)")
    evaluated_at: datetime = Field(description="UTC timestamp of the readiness evaluation")
    target_version: str = Field(default="1.0.0", description="Target release semantic version")
    git_commit: str = Field(default="8767c08", description="Current release commit SHA")
    checks: list[PreflightCheckDetail] = Field(default_factory=list, description="Granular subsystem checks")
    failing_checks: list[str] = Field(default_factory=list, description="List of failing checkpoints, if any")


class SystemReadinessResponse(BaseModel):
    """Top-level envelope for GET /api/v1/system/readiness."""
    success: bool = True
    message: str = "System pre-flight readiness evaluation completed."
    data: SystemReadinessData


# ============================================================================
# 2. Production Release Deployment Schemas
# ============================================================================

class ReleaseDeployRequest(BaseModel):
    """Request payload for dispatching a production release deployment."""
    version: str = Field(default="1.0.0", description="Target semantic version (SemVer 2.0.0)")
    release_tag: str = Field(default="v1.0.0", description="Git release tag")
    changelog: str = Field(description="Markdown changelog describing the release")
    environment: str = Field(default="production", description="Target deployment environment")
    enforce_preflight: bool = Field(default=True, description="Strictly require pre-flight readiness approval")


class ReleaseDeployData(BaseModel):
    """Execution status and artifact manifest for a deployed release."""
    model_config = ConfigDict(from_attributes=True)

    release_id: str = Field(description="Unique tracking ID for the release")
    version: str = Field(description="Deployed semantic version")
    release_tag: str = Field(description="Git release tag")
    git_commit: str = Field(description="Git commit SHA")
    status: str = Field(description="Release lifecycle state (PENDING, DEPLOYING, COMPLETED, FAILED, ROLLED_BACK)")
    preflight_score: float = Field(description="Readiness score at release execution")
    deployed_by: str | None = Field(default=None, description="UUID of the deploying administrator")
    started_at: datetime = Field(description="UTC timestamp of release initiation")
    completed_at: datetime | None = Field(default=None, description="UTC timestamp of release completion")
    changelog: str = Field(description="Markdown release notes")
    artifacts: dict[str, Any] = Field(default_factory=dict, description="Artifact manifest and SHA-256 digests")


class ReleaseDeployResponse(BaseModel):
    """Top-level envelope for POST /api/v1/system/release."""
    success: bool = True
    message: str = "Production release deployment initiated successfully."
    data: ReleaseDeployData


class ReleaseHistoryItemData(BaseModel):
    """Catalog summary of an individual historical production release."""
    model_config = ConfigDict(from_attributes=True)

    release_id: str = Field(description="Unique tracking ID for the release")
    version: str = Field(description="Release semantic version")
    release_tag: str = Field(description="Git release tag")
    git_commit: str = Field(description="Git commit SHA")
    status: str = Field(description="Release lifecycle status")
    preflight_score: float = Field(description="Readiness score")
    deployed_by: str | None = Field(default=None, description="Deployer UUID")
    created_at: datetime = Field(description="Creation UTC timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion UTC timestamp")


class ReleaseHistoryResponse(BaseModel):
    """Top-level envelope for GET /api/v1/system/releases."""
    success: bool = True
    data: list[ReleaseHistoryItemData] = Field(default_factory=list)


# ============================================================================
# 3. Security Audit Schemas
# ============================================================================

class SecurityControlData(BaseModel):
    """Status of an individual enterprise security control."""
    model_config = ConfigDict(from_attributes=True)

    control_id: str = Field(description="Standard control ID (e.g. SEC-01)")
    name: str = Field(description="Human-readable control name")
    status: str = Field(description="Control outcome (PASSED, FAILED, WARNING)")
    severity: str = Field(description="Risk severity level (CRITICAL, HIGH, MEDIUM, LOW)")
    description: str = Field(description="Control specification details")
    mitigation: str = Field(description="Required architectural defense or mitigation")


class SecurityFindingData(BaseModel):
    """Vulnerability finding detected during security assessment."""
    model_config = ConfigDict(from_attributes=True)

    finding_id: str = Field(description="Unique vulnerability finding tracking ID")
    control_id: str = Field(description="Violated control ID")
    severity: str = Field(description="Finding severity")
    title: str = Field(description="Vulnerability summary")
    remediation: str = Field(description="Recommended fix or remediation step")
    resolved: bool = Field(default=False, description="Whether the issue has been resolved")


class SecurityAuditData(BaseModel):
    """Aggregated enterprise security audit report."""
    model_config = ConfigDict(from_attributes=True)

    compliance_standard: str = Field(default="OWASP_TOP_10_AND_LLM_TOP_10", description="Compliance standard")
    overall_compliance_percent: float = Field(description="Compliance rating percentage (0.0 to 100.0%)")
    evaluated_at: datetime = Field(description="Evaluation UTC timestamp")
    total_controls: int = Field(default=10, description="Total audited controls")
    passed_controls: int = Field(default=10, description="Passing control count")
    failed_controls: int = Field(default=0, description="Failing control count")
    controls: list[SecurityControlData] = Field(default_factory=list, description="Audited control inventory")
    findings: list[SecurityFindingData] = Field(default_factory=list, description="Detected findings, if any")


class SecurityAuditResponse(BaseModel):
    """Top-level envelope for GET /api/v1/system/security/audit."""
    success: bool = True
    message: str = "Enterprise security audit completed successfully."
    data: SecurityAuditData

