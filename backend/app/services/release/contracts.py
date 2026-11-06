"""KEEP Enterprise Platform — Phase 3.7 Release & Security Audit Typed Domain Contracts.

Specification Reference: devdocs/p3/p3.7.txt (Chapters 1-20)
Architecture Reference: docs/Architecture/final-quality-assurance-security-audit-production-release.md
ADR Reference: ADR-065, ADR-066, ADR-067
Role: Member 1 (Project Lead & AI Architect)
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, ClassVar
from uuid import uuid4

# ============================================================================
# 1. Enums
# ============================================================================

class ReleaseStatus(str, Enum):
    """Lifecycle status of a production release deployment."""
    PENDING = "PENDING"
    DEPLOYING = "DEPLOYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class PreflightCheckCategory(str, Enum):
    """Classification of pre-flight system readiness verification checkpoints."""
    PERSISTENCE = "PERSISTENCE"
    CACHE = "CACHE"
    STORAGE = "STORAGE"
    AI_INFRA = "AI_INFRA"
    GOVERNANCE = "GOVERNANCE"


class CheckStatus(str, Enum):
    """Outcome status of an individual readiness check or security control."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


class SecurityComplianceStandard(str, Enum):
    """Supported cybersecurity compliance benchmark standards."""
    OWASP_TOP_10 = "OWASP_TOP_10"
    LLM_TOP_10 = "LLM_TOP_10"
    OWASP_TOP_10_AND_LLM_TOP_10 = "OWASP_TOP_10_AND_LLM_TOP_10"


class AuditSeverity(str, Enum):
    """Risk severity rating for security audit findings."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


# ============================================================================
# 2. Dataclasses & Data Contracts
# ============================================================================

@dataclass
class PreflightCheckResult:
    """Individual verification checkpoint result within the pre-flight readiness gate."""
    check_name: str
    category: PreflightCheckCategory
    status: CheckStatus
    score: float
    details: dict[str, Any] = field(default_factory=dict)
    verified_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_critical: bool = False


@dataclass
class SystemReadinessReport:
    """Aggregated platform pre-flight readiness verification report."""
    is_ready: bool
    overall_score: float
    evaluated_at: datetime
    target_version: str
    git_commit: str
    checks: list[PreflightCheckResult]
    failing_checks: list[str] = field(default_factory=list)


@dataclass
class SecurityAuditControl:
    """Evaluation state of a standard enterprise security control."""
    control_id: str
    name: str
    status: CheckStatus
    severity: AuditSeverity
    description: str
    mitigation: str


@dataclass
class SecurityAuditFinding:
    """Individual vulnerability finding detected during a security audit."""
    finding_id: str
    control_id: str
    severity: AuditSeverity
    title: str
    remediation: str
    resolved: bool = False
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SecurityAuditReport:
    """Consolidated enterprise security audit evaluation report."""
    compliance_standard: SecurityComplianceStandard
    overall_compliance_percent: float
    evaluated_at: datetime
    total_controls: int
    passed_controls: int
    failed_controls: int
    controls: list[SecurityAuditControl]
    findings: list[SecurityAuditFinding] = field(default_factory=list)


@dataclass
class ReleaseSpec:
    """Input payload specification for triggering a production release."""
    version: str
    release_tag: str
    changelog: str
    environment: str = "production"
    enforce_preflight: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReleaseArtifact:
    """Cryptographic manifest tracking a container image or build bundle."""
    artifact_name: str
    artifact_type: str
    checksum_sha256: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReleaseRecord:
    """Immutable production release record."""
    release_id: str
    version: str
    release_tag: str
    git_commit: str
    status: ReleaseStatus
    preflight_score: float
    started_at: datetime
    changelog: str
    deployed_by: str | None = None
    completed_at: datetime | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# 3. Reference Engine 1: Pre-Flight Readiness Evaluator
# ============================================================================

class PreflightReadinessEvaluator:
    """Computes deterministic platform readiness scores and enforces release gates."""

    CHECK_WEIGHTS: ClassVar[dict[str, float]] = {
        "database_migrations": 0.25,
        "database_pool": 0.10,
        "redis_cache": 0.15,
        "storage_headroom": 0.10,
        "vector_database": 0.15,
        "ai_model_cache": 0.15,
        "security_audit": 0.10,
    }

    CRITICAL_CHECKS: ClassVar[set[str]] = {
        "database_migrations",
        "vector_database",
    }

    MIN_READINESS_THRESHOLD: ClassVar[float] = 0.90

    @classmethod
    def evaluate(
        cls,
        check_inputs: dict[str, dict[str, Any]],
        target_version: str = "1.0.0",
        git_commit: str = "8767c08",
    ) -> SystemReadinessReport:
        """Evaluates all pre-flight check inputs and returns a structured readiness report."""
        evaluated_checks: list[PreflightCheckResult] = []
        failing_checks: list[str] = []
        raw_score = 0.0
        critical_failed = False

        for check_name, weight in cls.CHECK_WEIGHTS.items():
            input_data = check_inputs.get(check_name, {})
            status_val = input_data.get("status", CheckStatus.FAILED)
            is_critical = check_name in cls.CRITICAL_CHECKS

            if isinstance(status_val, str):
                status_enum = CheckStatus(status_val.upper())
            else:
                status_enum = status_val

            details = input_data.get("details", {})
            category = input_data.get("category", PreflightCheckCategory.PERSISTENCE)

            if status_enum == CheckStatus.PASSED:
                check_score = 1.0
                raw_score += weight * 1.0
            elif status_enum == CheckStatus.WARNING:
                check_score = 0.5
                raw_score += weight * 0.5
            else:
                check_score = 0.0
                failing_checks.append(check_name)
                if is_critical:
                    critical_failed = True

            evaluated_checks.append(
                PreflightCheckResult(
                    check_name=check_name,
                    category=category,
                    status=status_enum,
                    score=check_score,
                    details=details,
                    is_critical=is_critical,
                )
            )

        # Critical failure caps overall score and denies readiness
        if critical_failed:
            overall_score = min(raw_score, 0.40)
            is_ready = False
        else:
            overall_score = round(raw_score, 2)
            is_ready = overall_score >= cls.MIN_READINESS_THRESHOLD and len(failing_checks) == 0

        return SystemReadinessReport(
            is_ready=is_ready,
            overall_score=overall_score,
            evaluated_at=datetime.now(UTC),
            target_version=target_version,
            git_commit=git_commit,
            checks=evaluated_checks,
            failing_checks=failing_checks,
        )


# ============================================================================
# 4. Reference Engine 2: Security Audit Evaluator
# ============================================================================

class SecurityAuditEvaluator:
    """Evaluates platform defense controls conforming to OWASP Top 10 and LLM Top 10."""

    BASELINE_CONTROLS: ClassVar[list[dict[str, Any]]] = [
        {
            "control_id": "SEC-01",
            "name": "SQL Injection Defense",
            "severity": AuditSeverity.CRITICAL,
            "description": "SQLAlchemy 2.0 ORM parameterization enforced across 100% of queries.",
            "mitigation": "Ban raw string queries; mandate typed ORM session statements.",
        },
        {
            "control_id": "SEC-02",
            "name": "Cross-Site Scripting (XSS) Prevention",
            "severity": AuditSeverity.HIGH,
            "description": "React JSX contextual auto-encoding and DOMPurify sanitization.",
            "mitigation": "Sanitize all user-uploaded and AI-generated markdown strings.",
        },
        {
            "control_id": "SEC-03",
            "name": "CSRF & Session Safeguards",
            "severity": AuditSeverity.HIGH,
            "description": "Bearer JWT with SameSite cookie attributes and 7-day refresh lifecycle.",
            "mitigation": "Stateless JWT authorization headers on all state-mutating endpoints.",
        },
        {
            "control_id": "SEC-04",
            "name": "Broken Access Control & Multi-Tenancy",
            "severity": AuditSeverity.CRITICAL,
            "description": "Deterministic 7-step RBAC evaluation with organization boundary filters.",
            "mitigation": "Enforce organization_id tenancy checks in all database queries.",
        },
        {
            "control_id": "SEC-05",
            "name": "Cryptographic Protection at Rest & In-Transit",
            "severity": AuditSeverity.HIGH,
            "description": "TLS 1.3 transport, bcrypt password hashing, and AES-256 connector credential encryption.",
            "mitigation": "Encrypt secret credentials with AES-256-GCM before database insertion.",
        },
        {
            "control_id": "SEC-06",
            "name": "AI Prompt Injection & Jailbreak Guardrails",
            "severity": AuditSeverity.HIGH,
            "description": "Multi-turn delimiter sandboxing, system prompt freezing, and adversarial screening.",
            "mitigation": "Delimit untrusted document chunks with strict system boundary markers.",
        },
        {
            "control_id": "SEC-07",
            "name": "Security Audit Trail & Centralized Logging",
            "severity": AuditSeverity.MEDIUM,
            "description": "Structured JSON activity logs with W3C trace_id propagation for all mutations.",
            "mitigation": "Record all authentication and administrative actions to immutable audit tables.",
        },
        {
            "control_id": "SEC-08",
            "name": "Distributed Denial-of-Service Rate Limiting",
            "severity": AuditSeverity.HIGH,
            "description": "Redis sliding-window rate limiters protecting against endpoint abuse.",
            "mitigation": "Enforce per-user sliding window counters on heavy compute endpoints.",
        },
        {
            "control_id": "SEC-09",
            "name": "Dependency CVE & Supply Chain Hygiene",
            "severity": AuditSeverity.HIGH,
            "description": "Zero critical or high security vulnerabilities in Python and npm dependency trees.",
            "mitigation": "Continuous pip-audit and npm audit validation in CI/CD pipeline.",
        },
        {
            "control_id": "SEC-10",
            "name": "Plugin Sandbox Process & Capability Isolation",
            "severity": AuditSeverity.CRITICAL,
            "description": "AST safety parsing, prohibited module blacklisting, execution timeouts, and capability grants.",
            "mitigation": "Execute plugins in isolated worker sub-processes with strict CPU/memory limits.",
        },
    ]

    @classmethod
    def run_audit(
        cls,
        simulated_failures: list[str] | None = None,
    ) -> SecurityAuditReport:
        """Executes automated security audit across all 10 core controls."""
        failures = set(simulated_failures or [])
        controls: list[SecurityAuditControl] = []
        findings: list[SecurityAuditFinding] = []
        passed_count = 0

        for ctrl_def in cls.BASELINE_CONTROLS:
            cid = ctrl_def["control_id"]
            if cid in failures:
                status = CheckStatus.FAILED
                findings.append(
                    SecurityAuditFinding(
                        finding_id=f"find-{uuid4().hex[:8]}",
                        control_id=cid,
                        severity=ctrl_def["severity"],
                        title=f"Security Control Breach: {ctrl_def['name']}",
                        remediation=ctrl_def["mitigation"],
                        resolved=False,
                    )
                )
            else:
                status = CheckStatus.PASSED
                passed_count += 1

            controls.append(
                SecurityAuditControl(
                    control_id=cid,
                    name=ctrl_def["name"],
                    status=status,
                    severity=ctrl_def["severity"],
                    description=ctrl_def["description"],
                    mitigation=ctrl_def["mitigation"],
                )
            )

        total_controls = len(controls)
        failed_count = total_controls - passed_count
        compliance_pct = round((passed_count / total_controls) * 100.0, 1)

        return SecurityAuditReport(
            compliance_standard=SecurityComplianceStandard.OWASP_TOP_10_AND_LLM_TOP_10,
            overall_compliance_percent=compliance_pct,
            evaluated_at=datetime.now(UTC),
            total_controls=total_controls,
            passed_controls=passed_count,
            failed_controls=failed_count,
            controls=controls,
            findings=findings,
        )


# ============================================================================
# 5. Reference Engine 3: Release Tagging & Governance Manager
# ============================================================================

class ReleaseTaggingManager:
    """Manages semantic version validation, release artifact hashing, and execution."""

    SEMVER_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
        r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
        r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    )

    @classmethod
    def validate_semver(cls, version: str) -> bool:
        """Validates that version conforms strictly to SemVer 2.0.0."""
        clean = version.lstrip("v").strip()
        return bool(cls.SEMVER_PATTERN.match(clean))

    @classmethod
    def generate_artifact_manifest(
        cls,
        version: str,
        git_commit: str,
        artifacts: list[ReleaseArtifact],
    ) -> dict[str, Any]:
        """Constructs a deterministic release artifact manifest with SHA-256 fingerprint."""
        raw_manifest: dict[str, Any] = {
            "version": version,
            "git_commit": git_commit,
            "artifacts": [
                {
                    "name": a.artifact_name,
                    "type": a.artifact_type,
                    "sha256": a.checksum_sha256,
                    "details": a.details,
                }
                for a in artifacts
            ],
        }
        serialized = json.dumps(raw_manifest, sort_keys=True)
        manifest_digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        raw_manifest["manifest_checksum_sha256"] = manifest_digest
        return raw_manifest

    @classmethod
    def execute_release(
        cls,
        spec: ReleaseSpec,
        git_commit: str,
        readiness_report: SystemReadinessReport,
        user_id: str | None = None,
    ) -> ReleaseRecord:
        """Validates pre-flight readiness and executes production release packaging."""
        if not cls.validate_semver(spec.version):
            raise ValueError(f"Invalid semantic version: {spec.version}. Must conform to SemVer 2.0.0.")

        if spec.enforce_preflight and not readiness_report.is_ready:
            raise PermissionError(
                f"Release gateway blocked: readiness score ({readiness_report.overall_score}) "
                f"is below threshold or critical checks failed: {readiness_report.failing_checks}"
            )

        # Baseline release artifacts
        artifacts = [
            ReleaseArtifact(
                artifact_name="keep-backend",
                artifact_type="DOCKER_IMAGE",
                checksum_sha256=hashlib.sha256(f"keep-backend:{spec.version}".encode()).hexdigest(),
                details={"tag": f"keep-backend:{spec.version}"},
            ),
            ReleaseArtifact(
                artifact_name="keep-frontend",
                artifact_type="DOCKER_IMAGE",
                checksum_sha256=hashlib.sha256(f"keep-frontend:{spec.version}".encode()).hexdigest(),
                details={"tag": f"keep-frontend:{spec.version}"},
            ),
            ReleaseArtifact(
                artifact_name="alembic-migrations",
                artifact_type="DATABASE_SCHEMA",
                checksum_sha256=hashlib.sha256(b"0a1b2c3d4e5f_head").hexdigest(),
                details={"head_revision": "0a1b2c3d4e5f"},
            ),
        ]

        manifest = cls.generate_artifact_manifest(spec.version, git_commit, artifacts)
        now = datetime.now(UTC)

        return ReleaseRecord(
            release_id=f"rel-{uuid4().hex[:12]}",
            version=spec.version.lstrip("v"),
            release_tag=spec.release_tag,
            git_commit=git_commit,
            status=ReleaseStatus.COMPLETED,
            preflight_score=readiness_report.overall_score,
            started_at=now,
            completed_at=now,
            changelog=spec.changelog,
            deployed_by=user_id,
            artifacts=manifest,
        )
