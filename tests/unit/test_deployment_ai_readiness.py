"""Unit tests for Phase 1.10 AI Deployment, Infrastructure & Production Readiness Contracts.

Specification Source: devdocs/p1/p1.10.txt (Chapters 3, 4, 5, 10, 15, 18)
Phase: 1.10 — Deployment, Infrastructure & Production Readiness
Role: Member 1 (Project Lead & AI Architect)
"""

import pytest

from backend.app.services.ai.deployment import (
    AIClusterTopologySpec,
    AIHardwareProfile,
    AIModelArtifactConfig,
    AIModelExecutionMode,
    AIProductionReadinessReport,
    AIReadinessCheckItem,
    AIReadinessCheckStatus,
    AIResourceAllocation,
    AIVectorDBDeploymentConfig,
    AIVectorDBTopology,
    AIWorkerNodeConfig,
    AIWorkerQueueType,
    DefaultAIInfrastructureValidator,
    default_ai_infrastructure_validator,
)
from backend.app.services.rag.interfaces import AIRuntimeDeploymentProfile


class TestAIInfrastructureEnums:
    """Verifies enumeration consistency and string representations for deployment."""

    def test_hardware_profiles(self) -> None:
        """Ensures all required infrastructure sizing profiles exist."""
        expected = {
            "minimum_dev",
            "recommended_prod_cpu",
            "high_perf_gpu",
            "enterprise_distributed",
        }
        actual = {p.value for p in AIHardwareProfile}
        assert expected == actual

    def test_execution_modes(self) -> None:
        """Ensures runtime execution modes conform to specification."""
        expected = {"local_gpu", "local_cpu", "remote_api", "hybrid"}
        actual = {m.value for m in AIModelExecutionMode}
        assert expected == actual

    def test_vectordb_topologies(self) -> None:
        """Ensures vector database topology options are represented."""
        expected = {
            "embedded_pgvector",
            "dedicated_pgvector",
            "standalone_qdrant",
            "managed_cloud",
        }
        actual = {t.value for t in AIVectorDBTopology}
        assert expected == actual

    def test_worker_queues(self) -> None:
        """Ensures required asynchronous AI queue identifiers are defined."""
        expected = {
            "ai_ingestion_queue",
            "ai_embedding_queue",
            "ai_graph_queue",
            "ai_batch_queue",
        }
        actual = {q.value for q in AIWorkerQueueType}
        assert expected == actual


class TestAIResourceAllocation:
    """Verifies resource allocation modeling and GPU capability detection."""

    def test_default_resource_allocation(self) -> None:
        """Checks default CPU/RAM allocations."""
        alloc = AIResourceAllocation()
        assert alloc.cpu_cores == 2.0
        assert alloc.memory_mb == 4096
        assert not alloc.is_gpu_enabled()

    def test_gpu_resource_allocation(self) -> None:
        """Validates GPU detection logic."""
        alloc_no_model = AIResourceAllocation(gpu_count=1, gpu_model=None)
        assert not alloc_no_model.is_gpu_enabled()

        alloc_valid_gpu = AIResourceAllocation(
            gpu_count=1, gpu_model="NVIDIA A10G"
        )
        assert alloc_valid_gpu.is_gpu_enabled()


class TestDefaultAIInfrastructureValidator:
    """Verifies individual infrastructure validation gates and readiness scoring."""

    @pytest.fixture
    def validator(self) -> DefaultAIInfrastructureValidator:
        return DefaultAIInfrastructureValidator()

    def test_compute_validation_passed(
        self, validator: DefaultAIInfrastructureValidator
    ) -> None:
        """Ensures adequate compute passes validation."""
        alloc = AIResourceAllocation(cpu_cores=4.0, memory_mb=8192)
        check = validator.validate_compute_resources(
            alloc, AIHardwareProfile.RECOMMENDED_PROD_CPU
        )
        assert check.status == AIReadinessCheckStatus.PASSED
        assert check.is_critical

    def test_compute_validation_cpu_insufficient(
        self, validator: DefaultAIInfrastructureValidator
    ) -> None:
        """Detects CPU shortages."""
        alloc = AIResourceAllocation(cpu_cores=2.0, memory_mb=8192)
        check = validator.validate_compute_resources(
            alloc, AIHardwareProfile.RECOMMENDED_PROD_CPU
        )
        assert check.status == AIReadinessCheckStatus.FAILED
        assert "Insufficient CPU" in check.message

    def test_compute_validation_memory_insufficient(
        self, validator: DefaultAIInfrastructureValidator
    ) -> None:
        """Detects RAM shortages."""
        alloc = AIResourceAllocation(cpu_cores=4.0, memory_mb=4096)
        check = validator.validate_compute_resources(
            alloc, AIHardwareProfile.RECOMMENDED_PROD_CPU
        )
        assert check.status == AIReadinessCheckStatus.FAILED
        assert "Insufficient RAM" in check.message

    def test_compute_validation_gpu_missing_when_required(
        self, validator: DefaultAIInfrastructureValidator
    ) -> None:
        """Fails when GPU profile is specified without GPU hardware."""
        alloc = AIResourceAllocation(cpu_cores=8.0, memory_mb=32768, gpu_count=0)
        check = validator.validate_compute_resources(
            alloc, AIHardwareProfile.HIGH_PERF_GPU
        )
        assert check.status == AIReadinessCheckStatus.FAILED
        assert "no GPU is provisioned" in check.message

    def test_model_artifacts_empty_warning(
        self, validator: DefaultAIInfrastructureValidator
    ) -> None:
        """Emits a warning when no model artifacts are configured."""
        checks = validator.validate_model_artifacts([])
        assert len(checks) == 1
        assert checks[0].status == AIReadinessCheckStatus.WARNING
        assert not checks[0].is_critical

    def test_model_artifacts_valid_and_invalid(
        self, validator: DefaultAIInfrastructureValidator
    ) -> None:
        """Validates cache directory configuration for model artifacts."""
        valid_artifact = AIModelArtifactConfig(
            model_name="all-MiniLM-L6-v2",
            model_type="embedding",
            local_cache_dir="/app/models/cache",
            expected_size_mb=120,
        )
        invalid_artifact = AIModelArtifactConfig(
            model_name="bge-reranker-base",
            model_type="reranker",
            local_cache_dir="",  # Missing cache directory
        )

        checks = validator.validate_model_artifacts([valid_artifact, invalid_artifact])
        assert len(checks) == 2
        assert checks[0].status == AIReadinessCheckStatus.PASSED
        assert checks[1].status == AIReadinessCheckStatus.FAILED

    def test_vector_db_validation_dimension_supported(
        self, validator: DefaultAIInfrastructureValidator
    ) -> None:
        """Verifies standard vector dimensions."""
        cfg = AIVectorDBDeploymentConfig(
            topology=AIVectorDBTopology.EMBEDDED_PGVECTOR,
            vector_dimension=1536,
            max_connections=30,
        )
        check = validator.validate_vector_db_connectivity(cfg)
        assert check.status == AIReadinessCheckStatus.PASSED

    def test_vector_db_validation_dimension_invalid(
        self, validator: DefaultAIInfrastructureValidator
    ) -> None:
        """Fails when vector dimension is not standard."""
        cfg = AIVectorDBDeploymentConfig(
            vector_dimension=512  # Non-standard
        )
        check = validator.validate_vector_db_connectivity(cfg)
        assert check.status == AIReadinessCheckStatus.FAILED
        assert "Unsupported vector dimension" in check.message

    def test_vector_db_validation_low_pool_warning(
        self, validator: DefaultAIInfrastructureValidator
    ) -> None:
        """Warns when pool size is excessively low."""
        cfg = AIVectorDBDeploymentConfig(
            vector_dimension=1536, max_connections=5
        )
        check = validator.validate_vector_db_connectivity(cfg)
        assert check.status == AIReadinessCheckStatus.WARNING

    def test_worker_cluster_empty_warning(
        self, validator: DefaultAIInfrastructureValidator
    ) -> None:
        """Warns when no dedicated workers exist."""
        check = validator.validate_worker_cluster([])
        assert check.status == AIReadinessCheckStatus.WARNING

    def test_worker_cluster_missing_embedding_queue(
        self, validator: DefaultAIInfrastructureValidator
    ) -> None:
        """Warns when required queue is omitted."""
        workers = [
            AIWorkerNodeConfig(
                node_id="worker-1",
                hostname="worker-node-1",
                queues=[AIWorkerQueueType.INGESTION_QUEUE],  # Missing embedding queue
            )
        ]
        check = validator.validate_worker_cluster(workers)
        assert check.status == AIReadinessCheckStatus.WARNING
        assert "ai_embedding_queue" in check.message

    def test_worker_cluster_fully_provisioned(
        self, validator: DefaultAIInfrastructureValidator
    ) -> None:
        """Passes when all required queues are handled."""
        workers = [
            AIWorkerNodeConfig(
                node_id="worker-1",
                hostname="worker-node-1",
                queues=[
                    AIWorkerQueueType.INGESTION_QUEUE,
                    AIWorkerQueueType.EMBEDDING_QUEUE,
                ],
            )
        ]
        check = validator.validate_worker_cluster(workers)
        assert check.status == AIReadinessCheckStatus.PASSED

    def test_full_production_readiness_audit_healthy(
        self, validator: DefaultAIInfrastructureValidator
    ) -> None:
        """Verifies complete production-ready topology audit passes."""
        spec = AIClusterTopologySpec(
            cluster_name="keep-prod-cluster",
            environment="production",
            hardware_profile=AIHardwareProfile.RECOMMENDED_PROD_CPU,
            execution_mode=AIModelExecutionMode.HYBRID,
            resource_allocation=AIResourceAllocation(cpu_cores=4.0, memory_mb=8192),
            vector_db_config=AIVectorDBDeploymentConfig(
                vector_dimension=1536, max_connections=30
            ),
            model_artifacts=[
                AIModelArtifactConfig(
                    model_name="all-MiniLM-L6-v2",
                    model_type="embedding",
                    local_cache_dir="/app/models/cache",
                )
            ],
            worker_nodes=[
                AIWorkerNodeConfig(
                    node_id="worker-1",
                    hostname="node-1",
                    queues=[
                        AIWorkerQueueType.INGESTION_QUEUE,
                        AIWorkerQueueType.EMBEDDING_QUEUE,
                    ],
                )
            ],
        )

        report = validator.run_full_production_readiness_audit(spec)
        assert report.overall_ready
        assert report.score_percentage == 100.0
        assert report.failed_count == 0
        assert len(report.checks) == 4
        assert any("READY" in r for r in report.recommendations)

    def test_full_production_readiness_audit_failed(
        self, validator: DefaultAIInfrastructureValidator
    ) -> None:
        """Verifies critical failure causes overall_ready to be False."""
        spec = AIClusterTopologySpec(
            cluster_name="keep-prod-cluster",
            environment="production",
            hardware_profile=AIHardwareProfile.RECOMMENDED_PROD_CPU,
            resource_allocation=AIResourceAllocation(
                cpu_cores=1.0, memory_mb=1024  # Critical failure
            ),
        )

        report = validator.run_full_production_readiness_audit(spec)
        assert not report.overall_ready
        assert report.failed_count > 0
        assert any("FIX" in r for r in report.recommendations)


class TestRAGDeploymentRuntimeProfile:
    """Verifies RAG runtime profile parameters for production pipelines."""

    def test_runtime_profile_defaults(self) -> None:
        """Verifies default parameters adhere to low-latency SLAs."""
        profile = AIRuntimeDeploymentProfile()
        assert profile.max_context_tokens == 8192
        assert profile.max_retrieval_chunks == 20
        assert profile.retrieval_timeout_sec == 5.0
        assert profile.hybrid_dense_weight == 0.7
        assert profile.hybrid_sparse_weight == 0.3
        assert profile.reranker_device == "cpu"
        assert profile.enable_streaming_tokens is True
