"""Unit tests for Phase 1.9 AI Observability, Monitoring & Telemetry Contracts.

Specification Source: devdocs/p1/p1.9.txt (Chapters 4, 5, 6, 8, 17)
Phase: 1.9 — Logging, Monitoring & System Observability
Role: Member 1 (Project Lead & AI Architect)
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.app.services.ai.observability import (
    AIExecutionMetrics,
    AILogLevel,
    AIObservabilityEvent,
    AIOperationType,
    DefaultAICostCalculator,
    InMemoryAIObservabilityCollector,
    RAGRetrievalMetrics,
)
from backend.app.services.rag.interfaces import (
    AIQueryLogRecord,
    RAGObservabilityTelemetry,
)


class TestAIObservabilityEnums:
    """Verifies enumeration consistency and string representations."""

    def test_ai_operation_types(self) -> None:
        """Ensures all required AI lifecycle operations are represented."""
        expected_ops = {
            "embedding_generation",
            "vector_search",
            "hybrid_search",
            "llm_completion",
            "llm_stream",
            "rag_query",
            "graph_extraction",
            "graph_query",
            "document_chunking",
            "citation_grounding",
            "agent_tool_call",
        }
        actual_ops = {op.value for op in AIOperationType}
        assert expected_ops.issubset(actual_ops)

    def test_ai_log_levels(self) -> None:
        """Ensures log levels conform strictly to devdocs Chapter 6."""
        expected_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        actual_levels = {lvl.value for lvl in AILogLevel}
        assert expected_levels == actual_levels


class TestAIExecutionMetrics:
    """Verifies token computation, latency profiling, and serialization."""

    def test_auto_token_summation(self) -> None:
        """Validates that total_tokens is computed if omitted."""
        metrics = AIExecutionMetrics(
            prompt_tokens=150,
            completion_tokens=50,
            latency_ms=245.5,
            model_name="gpt-4o",
        )
        assert metrics.total_tokens == 200
        assert metrics.latency_ms == 245.5

    def test_explicit_token_count_preserved(self) -> None:
        """Validates explicit total_tokens is respected."""
        metrics = AIExecutionMetrics(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            time_to_first_token_ms=120.3,
            model_name="gpt-4o-mini",
            provider="openai",
        )
        d = metrics.to_dict()
        assert d["total_tokens"] == 150
        assert d["time_to_first_token_ms"] == 120.3
        assert d["model_name"] == "gpt-4o-mini"
        assert d["provider"] == "openai"


class TestRAGRetrievalMetrics:
    """Verifies telemetry metrics for dense/sparse RAG vector queries."""

    def test_retrieval_metrics_serialization(self) -> None:
        """Validates retrieval metrics structure and precision rounding."""
        retrieval = RAGRetrievalMetrics(
            query="enterprise security architecture",
            candidate_count=25,
            rerank_count=5,
            top_similarity_score=0.923456,
            average_similarity_score=0.812345,
            retrieval_latency_ms=18.4231,
            context_token_count=1240,
            filtered_chunk_ids=["chunk-1", "chunk-2"],
        )
        d = retrieval.to_dict()
        assert d["query"] == "enterprise security architecture"
        assert d["candidate_count"] == 25
        assert d["rerank_count"] == 5
        assert d["top_similarity_score"] == 0.9235
        assert d["average_similarity_score"] == 0.8123
        assert d["retrieval_latency_ms"] == 18.423
        assert d["filtered_chunk_count"] == 2


class TestAIObservabilityEventSchema:
    """Verifies canonical JSON log format according to devdocs Chapter 6."""

    def test_canonical_json_log_serialization(self) -> None:
        """Ensures all mandatory fields from devdocs Chapter 6 are present."""
        org_id = uuid4()
        user_id = uuid4()
        project_id = uuid4()

        exec_metrics = AIExecutionMetrics(
            prompt_tokens=500,
            completion_tokens=150,
            latency_ms=450.2,
            estimated_cost_usd=0.00475,
            model_name="gpt-4o",
        )

        event = AIObservabilityEvent(
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            request_id="req-12345",
            organization_id=org_id,
            user_id=user_id,
            project_id=project_id,
            operation_type=AIOperationType.RAG_QUERY,
            level=AILogLevel.INFO,
            status="success",
            execution_metrics=exec_metrics,
            metadata={"source": "dashboard_ai_widget", "session_id": "sess-abc"},
        )

        payload = event.to_json_dict()

        # Check required schema fields
        assert "timestamp" in payload
        assert payload["level"] == "INFO"
        assert payload["module"] == "ai_observability"
        assert payload["action"] == "rag_query"
        assert payload["status"] == "success"
        assert payload["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert payload["request_id"] == "req-12345"
        assert payload["organization_id"] == str(org_id)
        assert payload["user_id"] == str(user_id)
        assert payload["project_id"] == str(project_id)
        assert payload["execution_time_ms"] == 450.2
        assert payload["metadata"]["source"] == "dashboard_ai_widget"
        assert payload["execution_metrics"]["model_name"] == "gpt-4o"
        assert payload["execution_metrics"]["total_tokens"] == 650

    def test_failure_event_error_details(self) -> None:
        """Verifies error details propagation during execution failures."""
        event = AIObservabilityEvent(
            operation_type=AIOperationType.LLM_COMPLETION,
            level=AILogLevel.ERROR,
            status="failure",
            error_details={
                "error_code": "AI_RATE_LIMIT_EXCEEDED",
                "message": "Quota limit reached",
            },
        )
        payload = event.to_json_dict()
        assert payload["status"] == "failure"
        assert payload["level"] == "ERROR"
        assert payload["error_details"]["error_code"] == "AI_RATE_LIMIT_EXCEEDED"


class TestAICostCalculator:
    """Verifies cost calculation across cloud and self-hosted models."""

    def test_default_pricing_gpt4o(self) -> None:
        """Validates cost computation for GPT-4o."""
        calc = DefaultAICostCalculator()
        # 1,000 prompt tokens ($0.005) + 1,000 completion tokens ($0.015) = $0.020
        cost = calc.calculate_cost("gpt-4o", prompt_tokens=1000, completion_tokens=1000)
        assert pytest.approx(cost, 0.00001) == 0.020

    def test_default_pricing_gpt4o_mini(self) -> None:
        """Validates cost computation for GPT-4o-mini."""
        calc = DefaultAICostCalculator()
        # 10,000 prompt tokens ($0.0015) + 5,000 completion tokens ($0.0030) = $0.0045
        cost = calc.calculate_cost("gpt-4o-mini", prompt_tokens=10000, completion_tokens=5000)
        assert pytest.approx(cost, 0.00001) == 0.0045

    def test_default_pricing_embedding(self) -> None:
        """Validates cost computation for text-embedding-3-small."""
        calc = DefaultAICostCalculator()
        # 100,000 tokens ($0.002)
        cost = calc.calculate_cost(
            "text-embedding-3-small", prompt_tokens=100000, completion_tokens=0
        )
        assert pytest.approx(cost, 0.00001) == 0.002

    def test_zero_cost_local_models(self) -> None:
        """Validates that local models compute zero cost."""
        calc = DefaultAICostCalculator()
        cost = calc.calculate_cost("all-MiniLM-L6-v2", prompt_tokens=50000, completion_tokens=0)
        assert cost == 0.0

        cost_llama = calc.calculate_cost("llama-3-8b", prompt_tokens=5000, completion_tokens=2000)
        assert cost_llama == 0.0

    def test_unknown_model_fallback(self) -> None:
        """Validates graceful zero-cost fallback for unmapped models."""
        calc = DefaultAICostCalculator()
        cost = calc.calculate_cost("custom-proprietary-v1", prompt_tokens=1000, completion_tokens=1000)
        assert cost == 0.0


class TestInMemoryAIObservabilityCollector:
    """Verifies thread-safe collection, KPI aggregation, and tenant filtering."""

    @pytest.fixture
    def collector(self) -> InMemoryAIObservabilityCollector:
        """Creates a fresh collector instance for testing."""
        return InMemoryAIObservabilityCollector(max_events=100)

    def test_record_llm_metrics_with_auto_cost(
        self, collector: InMemoryAIObservabilityCollector
    ) -> None:
        """Validates automatic cost calculation on LLM metrics recording."""
        org_id = uuid4()
        metrics = AIExecutionMetrics(
            prompt_tokens=1000,
            completion_tokens=500,
            latency_ms=300.0,
            model_name="gpt-4o",
        )

        event = collector.record_llm_metrics(
            operation_type=AIOperationType.LLM_COMPLETION,
            metrics=metrics,
            organization_id=org_id,
            request_id="req-auto-cost",
        )

        assert event.execution_metrics is not None
        # Cost should be: (1000 * 0.005/1000) + (500 * 0.015/1000) = 0.005 + 0.0075 = 0.0125
        assert pytest.approx(event.execution_metrics.estimated_cost_usd, 0.0001) == 0.0125

    def test_record_retrieval_metrics(
        self, collector: InMemoryAIObservabilityCollector
    ) -> None:
        """Validates recording of vector retrieval metrics."""
        org_id = uuid4()
        retrieval = RAGRetrievalMetrics(
            query="financial balance sheet 2026",
            candidate_count=20,
            top_similarity_score=0.95,
            retrieval_latency_ms=14.5,
            context_token_count=800,
        )

        event = collector.record_retrieval_metrics(
            retrieval_metrics=retrieval,
            organization_id=org_id,
            request_id="req-retrieval",
        )

        assert event.operation_type == AIOperationType.VECTOR_SEARCH
        assert event.retrieval_metrics is not None
        assert event.retrieval_metrics.candidate_count == 20
        assert event.execution_metrics is not None
        assert event.execution_metrics.latency_ms == 14.5

    def test_kpi_aggregation_and_tenant_isolation(
        self, collector: InMemoryAIObservabilityCollector
    ) -> None:
        """Verifies KPI metrics aggregation with strict organization boundary isolation."""
        org_alpha = uuid4()
        org_beta = uuid4()

        # Add 3 successful events for Org Alpha
        collector.record_llm_metrics(
            operation_type=AIOperationType.RAG_QUERY,
            metrics=AIExecutionMetrics(
                prompt_tokens=100, completion_tokens=50, latency_ms=100.0, model_name="gpt-4o"
            ),
            organization_id=org_alpha,
        )
        collector.record_llm_metrics(
            operation_type=AIOperationType.RAG_QUERY,
            metrics=AIExecutionMetrics(
                prompt_tokens=200, completion_tokens=100, latency_ms=200.0, model_name="gpt-4o"
            ),
            organization_id=org_alpha,
        )
        collector.record_llm_metrics(
            operation_type=AIOperationType.RAG_QUERY,
            metrics=AIExecutionMetrics(
                prompt_tokens=300, completion_tokens=150, latency_ms=300.0, model_name="gpt-4o"
            ),
            organization_id=org_alpha,
        )

        # Add 1 failed event for Org Alpha
        collector.record_llm_metrics(
            operation_type=AIOperationType.LLM_COMPLETION,
            metrics=AIExecutionMetrics(
                prompt_tokens=50, completion_tokens=0, latency_ms=50.0, model_name="gpt-4o"
            ),
            organization_id=org_alpha,
            status="failure",
        )

        # Add 1 event for Org Beta
        collector.record_llm_metrics(
            operation_type=AIOperationType.RAG_QUERY,
            metrics=AIExecutionMetrics(
                prompt_tokens=1000, completion_tokens=500, latency_ms=500.0, model_name="gpt-4o"
            ),
            organization_id=org_beta,
        )

        # Calculate KPIs for Org Alpha
        alpha_kpis = collector.get_organization_kpis(org_alpha)
        assert alpha_kpis.total_operations == 4
        assert alpha_kpis.total_prompt_tokens == 650
        assert alpha_kpis.total_completion_tokens == 300
        assert alpha_kpis.total_tokens == 950
        assert alpha_kpis.error_count == 1
        assert alpha_kpis.error_rate_percent == 25.0
        assert alpha_kpis.operation_counts_by_type["rag_query"] == 3
        assert alpha_kpis.operation_counts_by_type["llm_completion"] == 1
        # Average latency across 4 operations: (100 + 200 + 300 + 50) / 4 = 162.5
        assert alpha_kpis.average_latency_ms == 162.5

        # Calculate KPIs for Org Beta
        beta_kpis = collector.get_organization_kpis(org_beta)
        assert beta_kpis.total_operations == 1
        assert beta_kpis.total_tokens == 1500
        assert beta_kpis.error_count == 0
        assert beta_kpis.error_rate_percent == 0.0

    def test_kpi_time_window_filtering(
        self, collector: InMemoryAIObservabilityCollector
    ) -> None:
        """Verifies filtering events by timestamp."""
        org_id = uuid4()
        now = datetime.now(UTC)

        # Event in the past
        old_event = AIObservabilityEvent(
            timestamp=now - timedelta(hours=2),
            organization_id=org_id,
            execution_metrics=AIExecutionMetrics(prompt_tokens=50, total_tokens=50),
        )
        collector.record_event(old_event)

        # Event now
        new_event = AIObservabilityEvent(
            timestamp=now,
            organization_id=org_id,
            execution_metrics=AIExecutionMetrics(prompt_tokens=100, total_tokens=100),
        )
        collector.record_event(new_event)

        # Request since 1 hour ago
        kpis = collector.get_organization_kpis(org_id, since=now - timedelta(hours=1))
        assert kpis.total_operations == 1
        assert kpis.total_prompt_tokens == 100

    def test_capacity_trimming(self) -> None:
        """Validates that collector caps memory growth at max_events."""
        tiny_collector = InMemoryAIObservabilityCollector(max_events=10)
        for i in range(15):
            tiny_collector.record_event(
                AIObservabilityEvent(metadata={"index": i})
            )

        events = tiny_collector.get_recent_events(limit=50)
        assert len(events) <= 10
        # The latest event should be present
        assert events[0].metadata["index"] == 14


class TestRAGObservabilityTelemetry:
    """Verifies end-to-end RAG telemetry data contract in services/rag/."""

    def test_rag_telemetry_serialization(self) -> None:
        """Validates complete serialization of RAG telemetry profile."""
        org_id = uuid4()
        user_id = uuid4()

        telemetry = RAGObservabilityTelemetry(
            query="summarize Q3 earnings release",
            trace_id="trace-777",
            request_id="req-999",
            organization_id=org_id,
            user_id=user_id,
            model_name="gpt-4o",
            prompt_tokens=1200,
            completion_tokens=300,
            total_tokens=1500,
            estimated_cost_usd=0.0105,
            embedding_latency_ms=22.5,
            retrieval_latency_ms=15.2,
            rerank_latency_ms=18.4,
            generation_latency_ms=450.0,
            total_latency_ms=506.1,
            candidate_chunks_count=30,
            reranked_chunks_count=5,
            top_similarity_score=0.9124,
            citation_count=4,
            is_cached=False,
            status="success",
        )

        d = telemetry.to_dict()
        assert d["query"] == "summarize Q3 earnings release"
        assert d["trace_id"] == "trace-777"
        assert d["request_id"] == "req-999"
        assert d["organization_id"] == str(org_id)
        assert d["user_id"] == str(user_id)
        assert d["total_tokens"] == 1500
        assert d["total_latency_ms"] == 506.1
        assert d["top_similarity_score"] == 0.9124
        assert d["citation_count"] == 4
        assert d["status"] == "success"

    def test_ai_query_log_record_with_observability_fields(self) -> None:
        """Validates AIQueryLogRecord with trace and cost enrichment."""
        log = AIQueryLogRecord(
            id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
            query="what is our remote work policy?",
            response="Our remote work policy permits 2 days from home...",
            tokens_used=420,
            latency_ms=315.8,
            model_name="gpt-4o",
            citations_count=2,
            trace_id="w3c-trace-001",
            request_id="req-client-001",
            cost_usd=0.0042,
        )

        assert log.trace_id == "w3c-trace-001"
        assert log.request_id == "req-client-001"
        assert log.cost_usd == 0.0042
