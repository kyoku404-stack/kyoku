"""KEEP Enterprise Platform — Health Diagnostics & Observability Schemas.

Specification Source: devdocs/p1/p1.9.txt (Chapter 7, 8, 9, 10) & docs/API/api-contract.md Section 6
Phase: 1.9 — Logging, Monitoring & System Observability
Role: Member 2 (Backend & Database Lead)
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DatabasePoolInfo(BaseModel):
    """Database connection pool metrics."""

    size: int = Field(default=20, description="Configured pool size")
    checked_out: int = Field(default=0, description="Active checked-out connections")
    overflow: int = Field(default=0, description="Active overflow connections")


class DatabaseDependencyHealth(BaseModel):
    """Database dependency status in composite health probe."""

    status: str = Field(default="healthy", description="Database status")
    latency_ms: float = Field(default=0.0, description="Query ping round-trip latency in ms")
    connection_pool: DatabasePoolInfo = Field(default_factory=DatabasePoolInfo)
    vector_extension_enabled: bool = Field(default=True, description="pgvector extension readiness")


class StorageDependencyHealth(BaseModel):
    """Storage volume dependency status in composite health probe."""

    status: str = Field(default="healthy", description="Storage status")
    latency_ms: float = Field(default=0.0, description="Filesystem probe latency in ms")
    writable: bool = Field(default=True, description="Filesystem write access")
    free_space_bytes: int = Field(default=0, description="Available bytes")
    used_percent: float = Field(default=0.0, description="Disk capacity used percentage")


class ApiDependencyHealth(BaseModel):
    """Process runtime dependency status in composite health probe."""

    status: str = Field(default="healthy", description="API runtime status")
    memory_rss_mb: float = Field(default=0.0, description="Process resident memory RSS in MB")
    active_requests: int = Field(default=0, description="Current concurrent requests")


class AuthDependencyHealth(BaseModel):
    """Authentication configuration dependency status in composite health probe."""

    status: str = Field(default="healthy", description="Auth subsystem status")
    jwt_secret_configured: bool = Field(default=True, description="JWT secret key configured")
    algorithm: str = Field(default="HS256", description="Signing algorithm")


class CompositeDependencies(BaseModel):
    """Subsystem dependencies evaluated in composite health probe."""

    database: DatabaseDependencyHealth = Field(default_factory=DatabaseDependencyHealth)
    storage: StorageDependencyHealth = Field(default_factory=StorageDependencyHealth)
    api: ApiDependencyHealth = Field(default_factory=ApiDependencyHealth)
    auth: AuthDependencyHealth = Field(default_factory=AuthDependencyHealth)


class HealthCheckResponse(BaseModel):
    """Composite platform operational health-check probe model (GET /health)."""

    status: str = Field(default="healthy", description="Overall platform status (healthy, degraded, unhealthy)")
    version: str = Field(..., description="Semantic application version")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
    uptime_seconds: float = Field(default=0.0, description="Process uptime in seconds")
    environment: str = Field(..., description="Runtime environment (production, development, test)")
    dependencies: CompositeDependencies = Field(default_factory=CompositeDependencies)


class DatabaseHealthResponse(BaseModel):
    """Isolated database probe model (GET /health/database)."""

    status: str = Field(default="healthy")
    latency_ms: float = Field(default=0.0)
    database: str = Field(default="postgresql")
    version: str = Field(default="PostgreSQL 16.4")
    vector_extension: bool = Field(default=True)
    pool: DatabasePoolInfo = Field(default_factory=DatabasePoolInfo)


class StorageHealthResponse(BaseModel):
    """Isolated storage volume probe model (GET /health/storage)."""

    status: str = Field(default="healthy")
    storage_root: str = Field(default="/app/storage")
    writable: bool = Field(default=True)
    latency_ms: float = Field(default=0.0)
    total_bytes: int = Field(default=0)
    used_bytes: int = Field(default=0)
    free_bytes: int = Field(default=0)
    used_percent: float = Field(default=0.0)


class ApiHealthResponse(BaseModel):
    """Process runtime probe model (GET /health/api)."""

    status: str = Field(default="healthy")
    uptime_seconds: float = Field(default=0.0)
    python_version: str = Field(default="3.12")
    memory_rss_mb: float = Field(default=0.0)
    cpu_percent: float = Field(default=0.0)
    active_requests: int = Field(default=0)


class AuthHealthResponse(BaseModel):
    """Authentication readiness probe model (GET /health/auth)."""

    status: str = Field(default="healthy")
    jwt_secret_configured: bool = Field(default=True)
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)
    refresh_token_expire_days: int = Field(default=7)


class SystemAlertItem(BaseModel):
    """Operational alert notice."""

    id: str = Field(..., description="Unique alert identifier")
    severity: str = Field(..., description="Severity level: INFO, WARNING, CRITICAL, SECURITY")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Detailed description")
    timestamp: str = Field(..., description="Event timestamp")


class MetricsKPIs(BaseModel):
    """Key performance indicators for platform operational telemetry."""

    requests_per_second: float = Field(default=0.0)
    p95_latency_ms: float = Field(default=0.0)
    error_rate_percent: float = Field(default=0.0)
    active_users: int = Field(default=0)
    total_documents: int = Field(default=0)
    storage_used_bytes: int = Field(default=0)
    storage_capacity_bytes: int = Field(default=0)
    storage_percent: float = Field(default=0.0)
    database_pool_usage_percent: float = Field(default=0.0)


class MetricsSummaryData(BaseModel):
    """Payload for frontend dashboard telemetry summary (GET /api/v1/metrics/summary)."""

    system_status: str = Field(default="healthy")
    uptime_seconds: float = Field(default=0.0)
    timestamp: str = Field(...)
    kpis: MetricsKPIs = Field(default_factory=MetricsKPIs)
    alerts: list[SystemAlertItem] = Field(default_factory=list)
    subsystem_health: dict[str, str] = Field(default_factory=dict)


# Backwards compatibility schemas for legacy test fixtures
class ComponentHealth(BaseModel):
    """Legacy component health indicator."""

    status: str = Field(default="healthy")
    latency_ms: float | None = Field(default=None)
    details: str | None = Field(default=None)


class DetailedHealthResponse(BaseModel):
    """Legacy detailed health response model."""

    status: str = Field(default="healthy")
    environment: str = Field(...)
    version: str = Field(...)
    timestamp: str = Field(...)
    uptime_seconds: float = Field(default=0.0)
    components: dict[str, ComponentHealth] = Field(default_factory=dict)
