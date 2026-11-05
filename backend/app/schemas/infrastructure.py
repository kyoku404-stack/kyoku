"""KEEP Enterprise Platform — Production Infrastructure & Observability Pydantic v2 Schemas.

Specification: devdocs/p3/p3.6.txt (Chapter 16) & docs/api/api-contract.md (Section 18)
Author: Member 2 (Backend & Database Lead)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# 1. Health & Subsystem Diagnostics
# ============================================================================

class SubsystemDetail(BaseModel):
    """Detailed health indicators for an individual platform subsystem."""
    model_config = ConfigDict(extra="allow")

    status: str = Field(description="Subsystem status (HEALTHY, DEGRADED, CRITICAL)")
    latency_ms: float = Field(default=0.0, description="Ping round-trip latency in milliseconds")


class SystemHealthData(BaseModel):
    """Aggregated platform health diagnostic probe data."""
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(description="Overall platform status (HEALTHY, DEGRADED, CRITICAL)")
    uptime_seconds: float = Field(description="Host process and platform uptime in seconds")
    timestamp: datetime = Field(description="UTC timestamp of the probe execution")
    version: str = Field(default="3.6.0", description="Current release version")
    overall_score: float = Field(default=1.0, description="Composite health index (0.0 to 1.0)")
    subsystems: dict[str, Any] = Field(default_factory=dict, description="Granular subsystem health reports")


# ============================================================================
# 2. Performance Metrics Telemetry
# ============================================================================

class CpuMetrics(BaseModel):
    """CPU telemetry metrics."""
    percent: float = Field(description="Current total CPU utilization percentage")
    cores: int = Field(default=8, description="Allocated or visible physical/virtual CPU cores")
    load_avg_1m: float = Field(default=0.0, description="One-minute rolling load average")


class MemoryMetrics(BaseModel):
    """RAM memory utilization metrics."""
    total_mb: float = Field(description="Total system RAM in megabytes")
    used_mb: float = Field(description="Active resident memory in megabytes")
    percent: float = Field(description="Memory utilization percentage")


class DiskMetrics(BaseModel):
    """Storage filesystem utilization metrics."""
    total_gb: float = Field(description="Total persistent storage capacity in gigabytes")
    used_gb: float = Field(description="Occupied storage in gigabytes")
    percent: float = Field(description="Storage occupancy percentage")


class NetworkMetrics(BaseModel):
    """Network I/O throughput metrics."""
    rx_bytes_sec: int = Field(default=0, description="Inbound network bytes per second")
    tx_bytes_sec: int = Field(default=0, description="Outbound network bytes per second")


class ApplicationMetrics(BaseModel):
    """Application-level HTTP and concurrency telemetry."""
    requests_per_second: float = Field(default=0.0, description="Current request ingestion rate")
    p50_latency_ms: float = Field(default=0.0, description="Median request latency")
    p95_latency_ms: float = Field(default=0.0, description="95th percentile request latency")
    p99_latency_ms: float = Field(default=0.0, description="99th percentile request latency")
    error_rate_percent: float = Field(default=0.0, description="Rolling 5xx error percentage")
    active_connections: int = Field(default=0, description="Active TCP or HTTP connections")


class CacheMetrics(BaseModel):
    """Redis multi-tier cache telemetry."""
    hit_ratio_percent: float = Field(default=0.0, description="Cache hit efficiency percentage")
    total_keys: int = Field(default=0, description="Total cached keys across all namespaces")
    memory_used_mb: float = Field(default=0.0, description="Redis resident memory consumption")


class SystemMetricsData(BaseModel):
    """Consolidated performance metrics snapshot."""
    timestamp: datetime = Field(description="UTC timestamp of the telemetry capture")
    cpu: CpuMetrics
    memory: MemoryMetrics
    disk: DiskMetrics
    network: NetworkMetrics
    application: ApplicationMetrics
    cache: CacheMetrics


# ============================================================================
# 3. System Logs & Diagnostics
# ============================================================================

class SystemLogEntryData(BaseModel):
    """Individual system operational or diagnostic log record."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Unique log entry identifier")
    service_name: str = Field(description="Originating microservice name")
    severity: str = Field(description="Log severity (INFO, WARN, ERROR, FATAL)")
    message: str = Field(description="Diagnostic log message")
    trace_id: str | None = Field(default=None, description="Distributed OpenTelemetry trace correlation ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Structured diagnostic attributes")
    created_at: datetime = Field(description="UTC timestamp of log generation")


# ============================================================================
# 4. Deployment Orchestration
# ============================================================================

class DeployTriggerRequest(BaseModel):
    """Request payload for dispatching a service deployment."""
    service_name: str = Field(default="keep-backend-api", description="Target microservice name or 'all'")
    version: str = Field(description="Target version tag or container image digest")
    strategy: str = Field(default="BLUE_GREEN", description="Deployment strategy (ROLLING, BLUE_GREEN, CANARY)")
    environment: str = Field(default="production", description="Target deployment environment")
    auto_rollback_on_failure: bool = Field(default=True, description="Automatically trigger rollback on SLA violation")


class DeployTriggerData(BaseModel):
    """Deployment execution record and lifecycle status."""
    model_config = ConfigDict(from_attributes=True)

    deployment_id: str = Field(description="Unique tracking ID for the deployment workflow")
    service_name: str = Field(description="Service targeted by the deployment")
    version: str = Field(description="Deployed target version")
    strategy: str = Field(description="Deployment strategy utilized")
    status: str = Field(description="Current status (PENDING, IN_PROGRESS, SUCCESS, FAILED, ROLLED_BACK)")
    started_at: datetime = Field(description="UTC start time of deployment")
    completed_at: datetime | None = Field(default=None, description="UTC completion time of deployment")
    rollback_version: str | None = Field(default=None, description="Restored rollback version if tripped")
    details: dict[str, Any] = Field(default_factory=dict, description="Deployment verification metadata")


# ============================================================================
# 5. Version & Release Information
# ============================================================================

class SystemVersionData(BaseModel):
    """Current release and runtime environment metadata."""
    version: str = Field(default="3.6.0", description="Active platform semantic version")
    git_commit: str = Field(description="Short Git commit SHA of the current build")
    build_date: str = Field(description="Build timestamp string")
    environment: str = Field(default="production", description="Running environment")
    python_version: str = Field(description="Python runtime version")
    frameworks: dict[str, str] = Field(default_factory=dict, description="Core framework version specifications")


# ============================================================================
# 6. Microservices Status Matrix
# ============================================================================

class MicroserviceStatusData(BaseModel):
    """Operational status and replica telemetry of an individual microservice."""
    model_config = ConfigDict(from_attributes=True)

    service_name: str = Field(description="Registered service identifier")
    status: str = Field(description="Service operational state (RUNNING, STARTING, STOPPED, CRASH_LOOP)")
    replicas_desired: int = Field(description="Configured target replica count")
    replicas_ready: int = Field(description="Healthy and ready replica count")
    version: str = Field(description="Active service version")
    uptime_hours: float = Field(description="Consecutive uptime in hours")
    memory_mb: float = Field(description="Resident memory consumed by service replicas")
    cpu_percent: float = Field(description="Aggregate CPU utilization percentage across replicas")


# ============================================================================
# 7. Disaster Recovery & Backups
# ============================================================================

class SystemBackupItemData(BaseModel):
    """Disaster recovery point-in-time backup record."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Unique snapshot ID")
    backup_name: str = Field(description="Human-readable backup filename")
    backup_type: str = Field(description="Snapshot category (DATABASE, FULL, OBJECT_STORAGE, WAL)")
    status: str = Field(description="Snapshot lifecycle status (PENDING, RUNNING, COMPLETED, FAILED, VERIFIED)")
    size_bytes: int = Field(description="Archive size in bytes")
    storage_location: str = Field(description="Destination URI (S3, GCS, local path)")
    rpo_drift_seconds: int = Field(description="Time elapsed from preceding backup boundary")
    checksum_sha256: str | None = Field(default=None, description="Cryptographic SHA-256 verification hash")
    notes: str | None = Field(default=None, description="Optional administrative notes")
    verified_at: datetime | None = Field(default=None, description="Timestamp of automated integrity verification")
    created_at: datetime = Field(description="Creation timestamp")


class SystemBackupsData(BaseModel):
    """Disaster recovery catalog and SLA compliance matrix."""
    rpo_target_minutes: int = Field(default=60, description="Maximum allowable data loss SLA in minutes")
    rto_target_minutes: int = Field(default=240, description="Maximum allowable recovery duration SLA in minutes")
    current_rpo_drift_minutes: float = Field(description="Elapsed minutes since most recent successful backup")
    last_successful_backup: datetime | None = Field(default=None, description="Timestamp of latest verified snapshot")
    backups: list[SystemBackupItemData] = Field(default_factory=list, description="Recent snapshot inventory")


class CreateBackupRequest(BaseModel):
    """Input payload to trigger an immediate point-in-time backup snapshot."""
    backup_type: str = Field(default="DATABASE", description="Backup type (DATABASE, FULL, OBJECT_STORAGE)")
    notes: str | None = Field(default=None, description="Optional administrative notes or change ticket reference")


class CreateBackupData(BaseModel):
    """Response returned upon initiating a backup snapshot."""
    backup_id: str = Field(description="Generated backup ID")
    backup_name: str = Field(description="Generated backup archive name")
    status: str = Field(description="Initial snapshot status")
    size_bytes: int = Field(description="Estimated or created archive size in bytes")
    created_at: datetime = Field(description="Snapshot initiation timestamp")


# ============================================================================
# 8. Cache Administration
# ============================================================================

class CacheFlushRequest(BaseModel):
    """Payload specifying cache namespaces to invalidate."""
    namespaces: list[str] = Field(default_factory=list, description="Target namespace prefixes or names")
    flush_all: bool = Field(default=False, description="Flush all cache namespaces across the cluster")


class CacheFlushData(BaseModel):
    """Result of cache flush operation."""
    flushed_namespaces: list[str] = Field(description="List of cleared Redis namespace prefixes")
    keys_removed: int = Field(description="Total count of purged cache keys")
