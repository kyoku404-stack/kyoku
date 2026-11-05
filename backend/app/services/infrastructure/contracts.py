"""KEEP Enterprise Platform — Production Infrastructure, Scalability & Observability Domain Contracts.

Specification Source: devdocs/p3/p3.6.txt (Chapters 1-20)
Architecture Reference: docs/Architecture/production-infrastructure-scalability-observability.md
ADR Reference: ADR-062, ADR-063, ADR-064
Role: Member 1 (Project Lead & AI Architect)
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any, ClassVar
from uuid import uuid4

logger = logging.getLogger("keep.infrastructure.contracts")


# ============================================================================
# Enums
# ============================================================================

class DeploymentStrategy(str, Enum):
    """Supported production deployment orchestrations."""
    ROLLING = "ROLLING"
    BLUE_GREEN = "BLUE_GREEN"
    CANARY = "CANARY"


class DeploymentStatus(str, Enum):
    """Lifecycle states of a deployment execution."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class ServiceHealthStatus(str, Enum):
    """Subsystem and platform health probe classifications."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class MicroserviceState(str, Enum):
    """Runtime status of containerized microservices."""
    RUNNING = "RUNNING"
    STARTING = "STARTING"
    STOPPED = "STOPPED"
    CRASH_LOOP = "CRASH_LOOP"
    MAINTENANCE = "MAINTENANCE"


class BackupType(str, Enum):
    """Supported disaster recovery snapshot categories."""
    DATABASE = "DATABASE"
    FULL = "FULL"
    OBJECT_STORAGE = "OBJECT_STORAGE"
    WAL = "WAL"


class BackupStatus(str, Enum):
    """Status lifecycle of automated disaster recovery backups."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    VERIFIED = "VERIFIED"


class LogLevel(str, Enum):
    """Severity classification for operational log aggregation."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


class CacheNamespace(str, Enum):
    """Structured Redis cache namespace prefixes and TTL boundaries."""
    SESSION = "keep:session:"
    AUTH = "keep:auth:"
    AI_RESPONSE = "keep:ai:resp:"
    VECTOR_QUERY = "keep:vector:q:"
    DASHBOARD = "keep:dashboard:"
    RATE_LIMIT = "keep:rate_limit:"


# ============================================================================
# Data Contracts & Schemas
# ============================================================================

class DeploymentSpec:
    """Input specification for initiating a containerized service rollout."""

    def __init__(
        self,
        service_name: str,
        version: str,
        strategy: DeploymentStrategy = DeploymentStrategy.ROLLING,
        environment: str = "production",
        auto_rollback_on_failure: bool = True,
        max_surge_percent: int = 25,
        max_unavailable_percent: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.service_name = service_name
        self.version = version
        self.strategy = strategy
        self.environment = environment
        self.auto_rollback_on_failure = auto_rollback_on_failure
        self.max_surge_percent = max_surge_percent
        self.max_unavailable_percent = max_unavailable_percent
        self.metadata = metadata or {}


class DeploymentRecord:
    """Historical and live status of a platform deployment."""

    def __init__(
        self,
        deployment_id: str,
        service_name: str,
        version: str,
        strategy: DeploymentStrategy,
        status: DeploymentStatus,
        environment: str = "production",
        rollback_version: str | None = None,
        auto_rollback_on_failure: bool = True,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.deployment_id = deployment_id
        self.service_name = service_name
        self.version = version
        self.strategy = strategy
        self.status = status
        self.environment = environment
        self.rollback_version = rollback_version
        self.auto_rollback_on_failure = auto_rollback_on_failure
        self.started_at = started_at or datetime.now(UTC)
        self.completed_at = completed_at
        self.details = details or {}


class SubsystemHealth:
    """Isolated health status probe for a dependent platform subsystem."""

    def __init__(
        self,
        name: str,
        status: ServiceHealthStatus,
        latency_ms: float = 0.0,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.status = status
        self.latency_ms = latency_ms
        self.details = details or {}


class CompositeHealthAssessment:
    """Overall platform health assessment aggregating all core subsystems."""

    def __init__(
        self,
        status: ServiceHealthStatus,
        uptime_seconds: float,
        overall_score: float,
        subsystems: dict[str, SubsystemHealth],
        timestamp: datetime | None = None,
    ) -> None:
        self.status = status
        self.uptime_seconds = uptime_seconds
        self.overall_score = round(overall_score, 4)
        self.subsystems = subsystems
        self.timestamp = timestamp or datetime.now(UTC)


class MicroserviceInfo:
    """Operational state of an individual containerized service."""

    def __init__(
        self,
        service_name: str,
        status: MicroserviceState,
        replicas_desired: int,
        replicas_ready: int,
        version: str,
        uptime_hours: float,
        memory_mb: float,
        cpu_percent: float,
    ) -> None:
        self.service_name = service_name
        self.status = status
        self.replicas_desired = replicas_desired
        self.replicas_ready = replicas_ready
        self.version = version
        self.uptime_hours = uptime_hours
        self.memory_mb = memory_mb
        self.cpu_percent = cpu_percent


class BackupRecord:
    """Metadata and integrity verification record for a disaster recovery snapshot."""

    def __init__(
        self,
        backup_name: str,
        backup_type: BackupType,
        status: BackupStatus,
        size_bytes: int,
        storage_location: str,
        rpo_drift_seconds: int = 0,
        checksum_sha256: str | None = None,
        notes: str | None = None,
        verified_at: datetime | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.id = str(uuid4())
        self.backup_name = backup_name
        self.backup_type = backup_type
        self.status = status
        self.size_bytes = size_bytes
        self.storage_location = storage_location
        self.rpo_drift_seconds = rpo_drift_seconds
        self.checksum_sha256 = checksum_sha256
        self.notes = notes
        self.verified_at = verified_at
        self.created_at = created_at or datetime.now(UTC)


# ============================================================================
# Reference Engine 1: Health Scoring Engine
# ============================================================================

class HealthScoringEngine:
    """Computes deterministic platform health scores and aggregated status."""

    SUBSYSTEM_WEIGHTS: ClassVar[dict[str, float]] = {
        "database": 0.35,
        "redis": 0.20,
        "vector_database": 0.20,
        "storage": 0.15,
        "ai_workers": 0.10,
    }

    @classmethod
    def evaluate(
        cls,
        subsystems: dict[str, SubsystemHealth],
        uptime_seconds: float = 86400.0,
    ) -> CompositeHealthAssessment:
        """Calculates aggregate score and derives overall platform health classification."""
        total_score = 0.0
        total_weight = 0.0

        for key, weight in cls.SUBSYSTEM_WEIGHTS.items():
            subsystem = subsystems.get(key)
            total_weight += weight
            if not subsystem:
                continue

            if subsystem.status == ServiceHealthStatus.HEALTHY:
                # Latency penalty if subsystem latency exceeds 100ms
                score = 1.0
                if subsystem.latency_ms > 100.0:
                    score = max(0.8, 1.0 - (subsystem.latency_ms - 100.0) / 1000.0)
                total_score += weight * score
            elif subsystem.status == ServiceHealthStatus.DEGRADED:
                total_score += weight * 0.5
            elif subsystem.status == ServiceHealthStatus.CRITICAL:
                total_score += 0.0

        normalized_score = total_score / total_weight if total_weight > 0 else 0.0

        # Critical failure gating: if database is critical, entire platform is critical
        db_sub = subsystems.get("database")
        if db_sub and db_sub.status == ServiceHealthStatus.CRITICAL:
            overall_status = ServiceHealthStatus.CRITICAL
        elif normalized_score >= 0.90:
            overall_status = ServiceHealthStatus.HEALTHY
        elif normalized_score >= 0.65:
            overall_status = ServiceHealthStatus.DEGRADED
        else:
            overall_status = ServiceHealthStatus.CRITICAL

        return CompositeHealthAssessment(
            status=overall_status,
            uptime_seconds=uptime_seconds,
            overall_score=normalized_score,
            subsystems=subsystems,
        )


# ============================================================================
# Reference Engine 2: Disaster Recovery & RPO/RTO Evaluator
# ============================================================================

class DisasterRecoveryEvaluator:
    """Enforces enterprise RPO (<= 1h) and RTO (<= 4h) compliance SLAs."""

    DEFAULT_RPO_TARGET_SECONDS: int = 3600    # 1 Hour
    DEFAULT_RTO_TARGET_SECONDS: int = 14400   # 4 Hours

    @classmethod
    def calculate_rpo_drift(
        cls,
        last_backup_timestamp: datetime,
        current_timestamp: datetime | None = None,
    ) -> int:
        """Computes current RPO drift in seconds from the latest successful backup."""
        now = current_timestamp or datetime.now(UTC)
        if last_backup_timestamp.tzinfo is None:
            last_backup = last_backup_timestamp.replace(tzinfo=UTC)
        else:
            last_backup = last_backup_timestamp

        drift = int((now - last_backup).total_seconds())
        return max(0, drift)

    @classmethod
    def verify_checksum(cls, payload_bytes: bytes, expected_sha256: str) -> bool:
        """Validates payload integrity using cryptographic SHA-256 digest."""
        computed = hashlib.sha256(payload_bytes).hexdigest()
        return computed.lower() == expected_sha256.lower()

    @classmethod
    def evaluate_compliance(
        cls,
        rpo_drift_seconds: int,
        rpo_target_seconds: int = DEFAULT_RPO_TARGET_SECONDS,
    ) -> dict[str, Any]:
        """Assesses disaster recovery compliance and alerting requirements."""
        is_compliant = rpo_drift_seconds <= rpo_target_seconds
        drift_minutes = round(rpo_drift_seconds / 60.0, 1)
        target_minutes = round(rpo_target_seconds / 60.0, 1)

        alert_severity = None
        if not is_compliant:
            if rpo_drift_seconds > rpo_target_seconds * 2:
                alert_severity = LogLevel.FATAL
            else:
                alert_severity = LogLevel.ERROR

        return {
            "compliant": is_compliant,
            "rpo_drift_minutes": drift_minutes,
            "rpo_target_minutes": target_minutes,
            "alert_required": not is_compliant,
            "alert_severity": alert_severity,
        }


# ============================================================================
# Reference Engine 3: Multi-Tier Cache Manager & Namespace Partitioner
# ============================================================================

class MultiTierCacheManager:
    """Manages Redis cache key generation, TTL boundaries, and selective invalidation."""

    NAMESPACE_TTLS: ClassVar[dict[str, int]] = {
        CacheNamespace.SESSION.value: 86400,        # 24 Hours
        CacheNamespace.AUTH.value: 3600,            # 1 Hour
        CacheNamespace.AI_RESPONSE.value: 21600,    # 6 Hours
        CacheNamespace.VECTOR_QUERY.value: 7200,    # 2 Hours
        CacheNamespace.DASHBOARD.value: 300,        # 5 Minutes
        CacheNamespace.RATE_LIMIT.value: 60,        # 60 Seconds
    }

    @classmethod
    def build_cache_key(cls, namespace: CacheNamespace, identifier: str) -> str:
        """Constructs a deterministic Redis key with the given namespace prefix."""
        return f"{namespace.value}{identifier.strip()}"

    @classmethod
    def compute_query_hash(cls, query_payload: dict[str, Any] | str) -> str:
        """Generates a stable SHA-256 fingerprint for query caching."""
        if isinstance(query_payload, dict):
            serialized = json.dumps(query_payload, sort_keys=True, default=str)
        else:
            serialized = str(query_payload)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def get_ttl(cls, namespace: CacheNamespace) -> int:
        """Retrieves default TTL in seconds for a cache namespace."""
        return cls.NAMESPACE_TTLS.get(namespace.value, 300)

    @classmethod
    def resolve_namespaces_to_flush(
        cls,
        namespaces: list[str] | None,
        flush_all: bool = False,
    ) -> list[str]:
        """Resolves targeted Redis namespace prefixes for an invalidation operation."""
        if flush_all:
            return [ns.value for ns in CacheNamespace]

        if not namespaces:
            return []

        resolved: list[str] = []
        for ns_name in namespaces:
            # Map canonical names like 'ai_response' or 'keep:ai:resp:'
            normalized = ns_name.strip().lower()
            matched = False
            for enum_item in CacheNamespace:
                if (
                    normalized == enum_item.name.lower()
                    or normalized == enum_item.value.lower()
                    or normalized in enum_item.name.lower()
                ):
                    resolved.append(enum_item.value)
                    matched = True
                    break
            if not matched:
                resolved.append(ns_name if ns_name.endswith(":") else f"{ns_name}:")

        return list(dict.fromkeys(resolved))  # Deduplicate while preserving order


# ============================================================================
# Reference Engine 4: Deployment Orchestration & Rollback Simulator
# ============================================================================

class DeploymentOrchestrator:
    """Executes or validates deployment rollouts with automated rollback safeguards."""

    @classmethod
    def execute_deployment(
        cls,
        spec: DeploymentSpec,
        current_version: str,
        simulated_failure: bool = False,
        simulated_error_rate: float = 0.0,
    ) -> DeploymentRecord:
        """Executes a deployment and triggers automatic rollback if health criteria fail."""
        dep_id = f"dep-{uuid4().hex[:8]}"
        started_at = datetime.now(UTC)

        # Failure condition: explicit failure simulation or error rate > 1.0%
        if simulated_failure or simulated_error_rate > 1.0:
            if spec.auto_rollback_on_failure:
                status = DeploymentStatus.ROLLED_BACK
                rollback_version = current_version
                details = {
                    "reason": f"Deployment verification failed with {simulated_error_rate}% error rate.",
                    "action": f"Automated rollback triggered to version '{current_version}'.",
                    "previous_version": current_version,
                }
            else:
                status = DeploymentStatus.FAILED
                rollback_version = None
                details = {
                    "reason": f"Deployment verification failed with {simulated_error_rate}% error rate.",
                    "action": "Auto-rollback disabled; manual intervention required.",
                }
        else:
            status = DeploymentStatus.SUCCESS
            rollback_version = current_version
            details = {
                "message": f"Successfully deployed version '{spec.version}' using {spec.strategy.value} strategy.",
                "previous_version": current_version,
                "environment": spec.environment,
            }

        completed_at = datetime.now(UTC)

        return DeploymentRecord(
            deployment_id=dep_id,
            service_name=spec.service_name,
            version=spec.version,
            strategy=spec.strategy,
            status=status,
            environment=spec.environment,
            rollback_version=rollback_version,
            auto_rollback_on_failure=spec.auto_rollback_on_failure,
            started_at=started_at,
            completed_at=completed_at,
            details=details,
        )
