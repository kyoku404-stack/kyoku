"""Typed Domain Contracts & Interfaces for AI Deployment & Production Readiness.

Owner: Member 1 (Project Lead & AI Architect)
Domain: /backend/app/services/ai/deployment.py
Specification: devdocs/p1/p1.10.txt (Chapters 3, 4, 5, 6, 10, 11, 16, 18)
Phase: 1.10 — Deployment, Infrastructure & Production Readiness
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class AIModelExecutionMode(str, Enum):
    """Runtime execution mode for AI and RAG workloads."""

    LOCAL_GPU = "local_gpu"
    LOCAL_CPU = "local_cpu"
    REMOTE_API = "remote_api"
    HYBRID = "hybrid"


class AIHardwareProfile(str, Enum):
    """Sizing and compute profile classification for AI infrastructure."""

    MINIMUM_DEV = "minimum_dev"
    RECOMMENDED_PROD_CPU = "recommended_prod_cpu"
    HIGH_PERF_GPU = "high_perf_gpu"
    ENTERPRISE_DISTRIBUTED = "enterprise_distributed"


class AIVectorDBTopology(str, Enum):
    """Architectural deployment topology for vector storage."""

    EMBEDDED_PGVECTOR = "embedded_pgvector"
    DEDICATED_PGVECTOR = "dedicated_pgvector"
    STANDALONE_QDRANT = "standalone_qdrant"
    MANAGED_CLOUD = "managed_cloud"


class AIReadinessCheckStatus(str, Enum):
    """Validation status for production readiness inspection gates."""

    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class AIWorkerQueueType(str, Enum):
    """Dedicated background task queues for asynchronous AI operations."""

    INGESTION_QUEUE = "ai_ingestion_queue"
    EMBEDDING_QUEUE = "ai_embedding_queue"
    GRAPH_EXTRACTION_QUEUE = "ai_graph_queue"
    LLM_BATCH_QUEUE = "ai_batch_queue"


@dataclass
class AIResourceAllocation:
    """Compute and memory resource allocations for AI workloads."""

    cpu_cores: float = 2.0
    memory_mb: int = 4096
    gpu_count: int = 0
    gpu_model: str | None = None
    max_concurrent_tasks: int = 4
    worker_concurrency: int = 2

    def is_gpu_enabled(self) -> bool:
        """Determines if GPU acceleration is provisioned."""
        return self.gpu_count > 0 and self.gpu_model is not None


@dataclass
class AIModelArtifactConfig:
    """Configuration and cache policies for local/remote model artifacts."""

    model_name: str
    model_type: str  # "embedding", "llm", "reranker", "ocr"
    version: str = "latest"
    artifact_path: str = ""
    local_cache_dir: str = "/app/models/cache"
    download_on_startup: bool = False
    expected_size_mb: int = 500
    checksum_sha256: str | None = None
    extra_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AIVectorDBDeploymentConfig:
    """Deployment parameters and indexing strategies for vector storage."""

    topology: AIVectorDBTopology = AIVectorDBTopology.EMBEDDED_PGVECTOR
    host: str = "postgres"
    port: int = 5432
    database_name: str = "keep_db"
    max_connections: int = 30
    index_type: str = "hnsw"  # "hnsw" or "ivfflat"
    vector_dimension: int = 1536
    storage_volume_mount: str = "postgres_data:/var/lib/postgresql/data"
    hnsw_m: int = 16
    hnsw_ef_construction: int = 64
    hnsw_ef_search: int = 40


@dataclass
class AIWorkerNodeConfig:
    """Worker node topology configuration for asynchronous AI task processing."""

    node_id: str
    hostname: str
    queues: list[AIWorkerQueueType] = field(default_factory=lambda: [AIWorkerQueueType.INGESTION_QUEUE])
    concurrency: int = 2
    prefetch_multiplier: int = 1
    heartbeat_interval_sec: int = 15
    max_memory_mb: int = 2048


@dataclass
class AIReadinessCheckItem:
    """Individual readiness evaluation gate result."""

    name: str
    category: str  # "compute", "storage", "models", "workers", "security"
    status: AIReadinessCheckStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    is_critical: bool = True
    latency_ms: float = 0.0


@dataclass
class AIProductionReadinessReport:
    """Comprehensive readiness audit report for Phase 2 AI orchestration."""

    report_id: UUID = field(default_factory=uuid4)
    overall_ready: bool = False
    score_percentage: float = 0.0
    passed_count: int = 0
    warning_count: int = 0
    failed_count: int = 0
    checks: list[AIReadinessCheckItem] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    recommendations: list[str] = field(default_factory=list)


@dataclass
class AIClusterTopologySpec:
    """Master specification blueprint for the KEEP AI cluster deployment."""

    cluster_name: str = "keep-ai-cluster"
    environment: str = "production"
    hardware_profile: AIHardwareProfile = AIHardwareProfile.RECOMMENDED_PROD_CPU
    execution_mode: AIModelExecutionMode = AIModelExecutionMode.HYBRID
    resource_allocation: AIResourceAllocation = field(default_factory=AIResourceAllocation)
    worker_nodes: list[AIWorkerNodeConfig] = field(default_factory=list)
    vector_db_config: AIVectorDBDeploymentConfig = field(default_factory=AIVectorDBDeploymentConfig)
    model_artifacts: list[AIModelArtifactConfig] = field(default_factory=list)
    max_batch_size: int = 32
    rate_limit_rpm: int = 120


class BaseAIInfrastructureValidator(ABC):
    """Abstract interface for validating infrastructure readiness for AI workloads."""

    @abstractmethod
    def validate_compute_resources(
        self, allocation: AIResourceAllocation, profile: AIHardwareProfile
    ) -> AIReadinessCheckItem:
        """Evaluates CPU, RAM, and GPU sizing against production workload profiles."""

    @abstractmethod
    def validate_model_artifacts(
        self, artifacts: list[AIModelArtifactConfig]
    ) -> list[AIReadinessCheckItem]:
        """Validates model artifact configurations, cache directories, and sizing."""

    @abstractmethod
    def validate_vector_db_connectivity(
        self, config: AIVectorDBDeploymentConfig
    ) -> AIReadinessCheckItem:
        """Verifies vector storage topology, dimension compatibility, and connection bounds."""

    @abstractmethod
    def validate_worker_cluster(
        self, workers: list[AIWorkerNodeConfig]
    ) -> AIReadinessCheckItem:
        """Verifies asynchronous worker node queue allocations and concurrency limits."""

    @abstractmethod
    def run_full_production_readiness_audit(
        self, spec: AIClusterTopologySpec
    ) -> AIProductionReadinessReport:
        """Executes full diagnostic suite and returns unified readiness score."""


class DefaultAIInfrastructureValidator(BaseAIInfrastructureValidator):
    """Concrete production infrastructure readiness validator."""

    def validate_compute_resources(
        self, allocation: AIResourceAllocation, profile: AIHardwareProfile
    ) -> AIReadinessCheckItem:
        min_cpus = {
            AIHardwareProfile.MINIMUM_DEV: 1.0,
            AIHardwareProfile.RECOMMENDED_PROD_CPU: 4.0,
            AIHardwareProfile.HIGH_PERF_GPU: 4.0,
            AIHardwareProfile.ENTERPRISE_DISTRIBUTED: 8.0,
        }
        min_ram_mb = {
            AIHardwareProfile.MINIMUM_DEV: 2048,
            AIHardwareProfile.RECOMMENDED_PROD_CPU: 8192,
            AIHardwareProfile.HIGH_PERF_GPU: 16384,
            AIHardwareProfile.ENTERPRISE_DISTRIBUTED: 32768,
        }

        req_cpu = min_cpus.get(profile, 2.0)
        req_ram = min_ram_mb.get(profile, 4096)

        if allocation.cpu_cores < req_cpu:
            return AIReadinessCheckItem(
                name="compute_cpu_cores",
                category="compute",
                status=AIReadinessCheckStatus.FAILED,
                message=f"Insufficient CPU cores: {allocation.cpu_cores} allocated, {req_cpu} required for {profile.value}",
                details={"allocated": allocation.cpu_cores, "required": req_cpu},
                is_critical=True,
            )

        if allocation.memory_mb < req_ram:
            return AIReadinessCheckItem(
                name="compute_memory_headroom",
                category="compute",
                status=AIReadinessCheckStatus.FAILED,
                message=f"Insufficient RAM: {allocation.memory_mb}MB allocated, {req_ram}MB required for {profile.value}",
                details={"allocated_mb": allocation.memory_mb, "required_mb": req_ram},
                is_critical=True,
            )

        if profile == AIHardwareProfile.HIGH_PERF_GPU and not allocation.is_gpu_enabled():
            return AIReadinessCheckItem(
                name="compute_gpu_provisioning",
                category="compute",
                status=AIReadinessCheckStatus.FAILED,
                message="Profile specifies HIGH_PERF_GPU but no GPU is provisioned",
                details={"gpu_count": allocation.gpu_count, "gpu_model": allocation.gpu_model},
                is_critical=True,
            )

        return AIReadinessCheckItem(
            name="compute_resources",
            category="compute",
            status=AIReadinessCheckStatus.PASSED,
            message=f"Compute resources meet or exceed requirements for {profile.value}",
            details={"cpu_cores": allocation.cpu_cores, "memory_mb": allocation.memory_mb},
            is_critical=True,
        )

    def validate_model_artifacts(
        self, artifacts: list[AIModelArtifactConfig]
    ) -> list[AIReadinessCheckItem]:
        results: list[AIReadinessCheckItem] = []
        if not artifacts:
            results.append(
                AIReadinessCheckItem(
                    name="model_artifacts_catalog",
                    category="models",
                    status=AIReadinessCheckStatus.WARNING,
                    message="No model artifacts configured in topology spec",
                    details={"count": 0},
                    is_critical=False,
                )
            )
            return results

        for artifact in artifacts:
            if not artifact.local_cache_dir:
                results.append(
                    AIReadinessCheckItem(
                        name=f"model_{artifact.model_name}_cache",
                        category="models",
                        status=AIReadinessCheckStatus.FAILED,
                        message=f"Model {artifact.model_name} lacks local cache directory configuration",
                        details={"model_name": artifact.model_name},
                        is_critical=True,
                    )
                )
            else:
                results.append(
                    AIReadinessCheckItem(
                        name=f"model_{artifact.model_name}_config",
                        category="models",
                        status=AIReadinessCheckStatus.PASSED,
                        message=f"Model {artifact.model_name} [{artifact.model_type}] configured with {artifact.expected_size_mb}MB footprint",
                        details={
                            "model_name": artifact.model_name,
                            "type": artifact.model_type,
                            "cache_dir": artifact.local_cache_dir,
                            "expected_size_mb": artifact.expected_size_mb,
                        },
                        is_critical=False,
                    )
                )

        return results

    def validate_vector_db_connectivity(
        self, config: AIVectorDBDeploymentConfig
    ) -> AIReadinessCheckItem:
        if config.vector_dimension not in (384, 768, 1536, 3072):
            return AIReadinessCheckItem(
                name="vector_db_dimension",
                category="storage",
                status=AIReadinessCheckStatus.FAILED,
                message=f"Unsupported vector dimension: {config.vector_dimension}. Expected 384, 768, 1536, or 3072",
                details={"dimension": config.vector_dimension},
                is_critical=True,
            )

        if config.max_connections < 10:
            return AIReadinessCheckItem(
                name="vector_db_pool_sizing",
                category="storage",
                status=AIReadinessCheckStatus.WARNING,
                message=f"Low connection pool allocation: {config.max_connections}. Recommended >= 20",
                details={"max_connections": config.max_connections},
                is_critical=False,
            )

        return AIReadinessCheckItem(
            name="vector_db_configuration",
            category="storage",
            status=AIReadinessCheckStatus.PASSED,
            message=f"Vector DB [{config.topology.value}] configured at {config.host}:{config.port} ({config.index_type.upper()} index)",
            details={
                "topology": config.topology.value,
                "dimension": config.vector_dimension,
                "index_type": config.index_type,
                "max_connections": config.max_connections,
            },
            is_critical=True,
        )

    def validate_worker_cluster(
        self, workers: list[AIWorkerNodeConfig]
    ) -> AIReadinessCheckItem:
        if not workers:
            return AIReadinessCheckItem(
                name="ai_worker_cluster",
                category="workers",
                status=AIReadinessCheckStatus.WARNING,
                message="No dedicated AI worker nodes configured. Background operations will execute on primary API nodes",
                details={"worker_count": 0},
                is_critical=False,
            )

        all_queues = {q for w in workers for q in w.queues}
        required_queues = {
            AIWorkerQueueType.INGESTION_QUEUE,
            AIWorkerQueueType.EMBEDDING_QUEUE,
        }
        missing_queues = required_queues - all_queues

        if missing_queues:
            return AIReadinessCheckItem(
                name="ai_worker_queue_coverage",
                category="workers",
                status=AIReadinessCheckStatus.WARNING,
                message=f"Worker cluster lacks dedicated workers for: {[q.value for q in missing_queues]}",
                details={"missing": [q.value for q in missing_queues]},
                is_critical=False,
            )

        return AIReadinessCheckItem(
            name="ai_worker_cluster",
            category="workers",
            status=AIReadinessCheckStatus.PASSED,
            message=f"Worker cluster configured with {len(workers)} node(s) covering {len(all_queues)} queue(s)",
            details={"worker_count": len(workers), "queues": [q.value for q in all_queues]},
            is_critical=True,
        )

    def run_full_production_readiness_audit(
        self, spec: AIClusterTopologySpec
    ) -> AIProductionReadinessReport:
        checks: list[AIReadinessCheckItem] = []

        # 1. Compute resources
        checks.append(
            self.validate_compute_resources(
                spec.resource_allocation, spec.hardware_profile
            )
        )

        # 2. Vector DB
        checks.append(self.validate_vector_db_connectivity(spec.vector_db_config))

        # 3. Model artifacts
        checks.extend(self.validate_model_artifacts(spec.model_artifacts))

        # 4. Worker cluster
        checks.append(self.validate_worker_cluster(spec.worker_nodes))

        # Compute aggregate scores
        passed = sum(1 for c in checks if c.status == AIReadinessCheckStatus.PASSED)
        warnings = sum(1 for c in checks if c.status == AIReadinessCheckStatus.WARNING)
        failed = sum(1 for c in checks if c.status == AIReadinessCheckStatus.FAILED)
        total = len(checks)

        critical_failed = any(
            c.status == AIReadinessCheckStatus.FAILED and c.is_critical for c in checks
        )
        score = (passed / total * 100.0) if total > 0 else 0.0
        overall_ready = (not critical_failed) and (score >= 75.0)

        recommendations: list[str] = []
        for c in checks:
            if c.status == AIReadinessCheckStatus.FAILED:
                recommendations.append(f"FIX: {c.message}")
            elif c.status == AIReadinessCheckStatus.WARNING:
                recommendations.append(f"OPT: {c.message}")

        if overall_ready:
            recommendations.append("READY: Environment meets Phase 2 AI orchestration deployment standards.")

        return AIProductionReadinessReport(
            overall_ready=overall_ready,
            score_percentage=round(score, 1),
            passed_count=passed,
            warning_count=warnings,
            failed_count=failed,
            checks=checks,
            recommendations=recommendations,
        )


default_ai_infrastructure_validator = DefaultAIInfrastructureValidator()
