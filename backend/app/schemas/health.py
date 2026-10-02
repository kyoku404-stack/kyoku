"""KEEP Enterprise Platform — Health Schemas."""

from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Central system health-check response model."""

    status: str = Field(default="healthy", description="Service status indicator")
    environment: str = Field(..., description="Active server runtime environment")
    version: str = Field(..., description="Semantic version of the application")
    timestamp: str = Field(..., description="Current ISO-8601 UTC timestamp")


class ComponentHealth(BaseModel):
    """Health indicator of an individual infrastructure component."""

    status: str = Field(default="healthy", description="Component status")
    latency_ms: float | None = Field(
        default=None, description="Ping latency in milliseconds"
    )
    details: str | None = Field(default=None, description="Additional status message")


class DetailedHealthResponse(BaseModel):
    """Detailed system diagnostic health model."""

    status: str = Field(default="healthy")
    environment: str = Field(...)
    version: str = Field(...)
    timestamp: str = Field(...)
    uptime_seconds: float = Field(default=0.0)
    components: dict[str, ComponentHealth] = Field(default_factory=dict)
