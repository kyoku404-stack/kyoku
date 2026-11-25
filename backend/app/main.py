"""KEEP Enterprise Platform — Main FastAPI Application Entrypoint.

Configures application lifespan, OpenAPI metadata, middleware pipeline,
global exception handlers, and versioned modular routers.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from backend.app.agents.autonomy.repository import SqlAlchemyAutonomyRepository
from backend.app.agents.autonomy.service import AutonomousWorkflowService
from backend.app.agents.collaboration.repository import (
    SqlAlchemyCollaborationRepository,
)
from backend.app.agents.collaboration.service import CollaborationService
from backend.app.agents.events.adapters.webhook import (
    WebhookIngestionAdapter,
    WebhookSourceRegistry,
)
from backend.app.agents.events.event_store import SqlAlchemyEventStore
from backend.app.agents.memory.repository import SqlAlchemyMemoryRepository
from backend.app.agents.memory.service import MemoryService
from backend.app.agents.observability.telemetry import RuntimeMetricsCollector
from backend.app.agents.observability.workflow_tracing import WorkflowMetricsCollector
from backend.app.agents.orchestration.graphs import (
    DOCUMENT_ENRICHMENT_DEFINITION,
    build_default_workflow_registry,
    build_document_enrichment_graph,
)
from backend.app.agents.orchestration.policies import KeepWorkflowPolicyEngine
from backend.app.agents.orchestration.service import KeepOrchestrationService
from backend.app.agents.persistence.checkpoints import KeepCheckpointStore
from backend.app.agents.persistence.execution_repository import (
    SQLAlchemyExecutionRepository,
)
from backend.app.agents.persistence.graph_checkpoints import KeepGraphCheckpointStore
from backend.app.agents.persistence.plan_repository import SQLAlchemyPlanRepository
from backend.app.agents.persistence.workflow_repository import (
    SQLAlchemyWorkflowRepository,
)
from backend.app.agents.planning.orchestrator_bridge import PlanOrchestrationBridge
from backend.app.agents.planning.policies import KeepPlanningPolicyEngine
from backend.app.agents.planning.service import KeepPlanningService
from backend.app.agents.research.agent import KeepResearchAgent
from backend.app.agents.research.graph import build_default_research_agent
from backend.app.agents.research.repository import SQLAlchemyResearchRepository
from backend.app.agents.research.research_service import KeepResearchService
from backend.app.agents.runtime.executor import AgentRuntime
from backend.app.agents.runtime.policies import KeepExecutionPolicy
from backend.app.agents.service import build_orchestration_agent_registry
from backend.app.agents.tools.adapters.knowledge_search import KnowledgeSearchTool
from backend.app.agents.tools.adapters.report_draft import ReportDraftTool
from backend.app.agents.tools.audit import ToolAuditService
from backend.app.agents.tools.executor import KeepToolExecutor
from backend.app.agents.tools.policies import ToolPolicyEngine
from backend.app.agents.tools.registry import ToolRegistry
from backend.app.agents.tools.repository import ToolRepository
from backend.app.agents.triggers.repository import SqlAlchemyTriggerRepository
from backend.app.agents.triggers.service import TriggerService
from backend.app.agents.workers.execution_worker import DurableExecutionWorker
from backend.app.api.middleware import (
    LoggingMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    register_exception_handlers,
)
from backend.app.api.v1 import api_v1_router
from backend.app.api.v1.agent_collaboration import router as agent_collaboration_router
from backend.app.api.v1.autonomous_workflows import (
    router as autonomous_workflows_router,
)
from backend.app.api.v1.events import router as events_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.memory import router as memory_router
from backend.app.api.v1.triggers import router as triggers_router
from backend.app.core.config import settings
from backend.app.core.logging import get_logger, setup_logging
from backend.app.core.metrics import metrics_registry
from backend.app.db.session import async_session_factory, close_async_engine
from backend.app.services.security.agent_policy import KeepAgentPolicyEngine
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

logger = get_logger("main")

OPENAPI_TAGS = [
    {
        "name": "Root",
        "description": "Root service discovery and application metadata.",
    },
    {
        "name": "Health",
        "description": "System readiness, liveness, and component health probes.",
    },
    {
        "name": "Authentication",
        "description": "JWT authentication, token issuance, credential verification, and user profile resolution.",
    },
    {
        "name": "Users",
        "description": "Tenant user management, role inspection, and profile retrieval.",
    },
    {
        "name": "Organizations",
        "description": "Multi-tenant boundary management and organization profiles.",
    },
    {
        "name": "Documents",
        "description": "Multipart document upload, file ingestion pipeline, and catalog pagination.",
    },
    {
        "name": "Search",
        "description": "Hybrid semantic vector and BM25 keyword search across enterprise documents.",
    },
    {
        "name": "Chat",
        "description": "Citation-backed RAG question answering and real-time Server-Sent Events (SSE) token streaming.",
    },
    {
        "name": "Analytics",
        "description": "Enterprise platform usage statistics, operational metrics, and telemetry.",
    },
    {
        "name": "Agents",
        "description": "Phase 4.1 multi-agent discovery, capability metadata, and contract verification endpoints.",
    },
    {
        "name": "Tools",
        "description": "Phase 4.6 tool registry, schema discovery, execution engine, and audit trail endpoints.",
    },
    {
        "name": "Memory",
        "description": "Phase 4.7 agent memory system, scoped retrieval, proposals, and lifecycle governance.",
    },
    {
        "name": "Multi-Agent Collaboration",
        "description": "Phase 4.8 multi-agent collaboration sessions, task delegation, peer reviews, and conflict resolution.",
    },
    {
        "name": "Autonomous Workflows",
        "description": "Phase 4.9 goal-driven autonomous workflows with bounded replanning, write approvals, and audit trails.",
    },
    {
        "name": "Event Triggers",
        "description": "Phase 4.10 declarative event triggers, condition matching, and persistent schedules.",
    },
    {
        "name": "Events & Webhooks",
        "description": "Phase 4.10 event ingestion, delivery status inspection, dead-letter replay, and HMAC webhooks.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup and graceful shutdown."""
    setup_logging(settings.LOG_LEVEL)
    logger.info(
        "Starting KEEP Enterprise Platform Backend Engine (v%s)",
        settings.VERSION,
    )
    logger.info("Environment: %s", settings.ENVIRONMENT)

    # Validate production configuration & security parameters
    prod_warnings = settings.validate_production_configuration()
    for warning in prod_warnings:
        if "CRITICAL" in warning:
            logger.critical(warning)
        else:
            logger.warning(warning)

    # Ensure storage directories exist
    os.makedirs(settings.STORAGE_ROOT, exist_ok=True)
    os.makedirs(settings.UPLOAD_STORAGE_PATH, exist_ok=True)

    # Phase 4.1 / 4.2: Initialize lifespan-bound multi-agent registry, runtime & background worker
    if getattr(app.state, "agent_policy", None) is None:
        app.state.agent_policy = KeepAgentPolicyEngine()
    if getattr(app.state, "agent_checkpoints", None) is None:
        app.state.agent_checkpoints = KeepCheckpointStore(
            session_factory=async_session_factory,
            policy=app.state.agent_policy,
        )
    registry_created_by_lifespan = getattr(app.state, "agent_registry", None) is None
    if registry_created_by_lifespan:
        app.state.agent_registry = build_orchestration_agent_registry(
            checkpoint_store=app.state.agent_checkpoints,
            policy=app.state.agent_policy,
        )
    if getattr(app.state, "execution_repository", None) is None:
        app.state.execution_repository = SQLAlchemyExecutionRepository(async_session_factory)
    if getattr(app.state, "execution_policy", None) is None:
        app.state.execution_policy = KeepExecutionPolicy(security_policy=app.state.agent_policy)
    if getattr(app.state, "runtime_metrics", None) is None:
        app.state.runtime_metrics = RuntimeMetricsCollector()
    if getattr(app.state, "execution_worker", None) is None:
        app.state.execution_worker = DurableExecutionWorker()
    if getattr(app.state, "agent_runtime", None) is None:
        app.state.agent_runtime = AgentRuntime(
            registry=app.state.agent_registry,
            repository=app.state.execution_repository,
            policy=app.state.execution_policy,
            dispatcher=app.state.execution_worker,
            observer=app.state.runtime_metrics,
        )
    app.state.execution_worker.bind_handler(app.state.agent_runtime.execute_existing)
    await app.state.execution_worker.start()

    # Phase 4.3: Initialize lifespan-bound multi-agent orchestration engine
    if getattr(app.state, "workflow_registry", None) is None:
        app.state.workflow_registry = build_default_workflow_registry(
            app.state.agent_registry,
            validate_deps=registry_created_by_lifespan,
        )
    if not app.state.workflow_registry.is_registered("document_enrichment"):
        app.state.workflow_registry.register(
            DOCUMENT_ENRICHMENT_DEFINITION,
            build_document_enrichment_graph,
            validate_deps=False,
        )
    if getattr(app.state, "workflow_repository", None) is None:
        app.state.workflow_repository = SQLAlchemyWorkflowRepository(async_session_factory)
    if getattr(app.state, "graph_checkpoints", None) is None:
        app.state.graph_checkpoints = KeepGraphCheckpointStore(app.state.agent_checkpoints)
    if getattr(app.state, "workflow_policy", None) is None:
        app.state.workflow_policy = KeepWorkflowPolicyEngine(security_policy=app.state.agent_policy)
    if getattr(app.state, "workflow_metrics", None) is None:
        app.state.workflow_metrics = WorkflowMetricsCollector()
    if getattr(app.state, "workflow_worker", None) is None:
        app.state.workflow_worker = DurableExecutionWorker()
    if getattr(app.state, "orchestration_service", None) is None:
        app.state.orchestration_service = KeepOrchestrationService(
            workflow_registry=app.state.workflow_registry,
            repository=app.state.workflow_repository,
            runtime=app.state.agent_runtime,
            policy=app.state.workflow_policy,
            security_policy=app.state.agent_policy,
            checkpoint_store=app.state.graph_checkpoints,
            dispatcher=app.state.workflow_worker,
            observer=app.state.workflow_metrics,
        )
    app.state.workflow_worker.bind_handler(app.state.orchestration_service.execute_from_worker)
    await app.state.workflow_worker.start()

    # Phase 4.4: Initialize lifespan-bound Planning & Reasoning Engine
    if getattr(app.state, "plan_repository", None) is None:
        app.state.plan_repository = SQLAlchemyPlanRepository(async_session_factory)
    if getattr(app.state, "plan_orchestration_bridge", None) is None:
        app.state.plan_orchestration_bridge = PlanOrchestrationBridge(
            app.state.orchestration_service
        )
    if getattr(app.state, "planning_policy", None) is None:
        app.state.planning_policy = KeepPlanningPolicyEngine(
            security_policy=app.state.agent_policy
        )
    if getattr(app.state, "planning_service", None) is None:
        app.state.planning_service = KeepPlanningService(
            agent_registry=app.state.agent_registry,
            plan_repository=app.state.plan_repository,
            orchestrator_bridge=app.state.plan_orchestration_bridge,
            policy_engine=app.state.planning_policy,
        )

    # Phase 4.5: Initialize lifespan-bound Research Agents Service & background worker
    if getattr(app.state, "research_repository", None) is None:
        app.state.research_repository = SQLAlchemyResearchRepository(async_session_factory)
    if getattr(app.state, "research_worker", None) is None:
        app.state.research_worker = DurableExecutionWorker()
    if getattr(app.state, "research_service", None) is None:
        if app.state.agent_registry.is_registered("research_agent"):
            candidate_research = app.state.agent_registry.get("research_agent")
            research_agent = (
                candidate_research
                if isinstance(candidate_research, KeepResearchAgent)
                else build_default_research_agent(policy=app.state.agent_policy)
            )
        else:
            research_agent = build_default_research_agent(policy=app.state.agent_policy)
        app.state.research_service = KeepResearchService(
            repository=app.state.research_repository,
            research_agent=research_agent,
            agent_runtime=app.state.agent_runtime
            if app.state.agent_registry.is_registered("research_agent")
            else None,
            policy=app.state.agent_policy,
            worker=app.state.research_worker,
        )
    await app.state.research_worker.start()

    # Phase 4.6: Initialize lifespan-bound Tool-Calling Framework
    if getattr(app.state, "tool_registry", None) is None:
        tool_reg = ToolRegistry()
        tool_reg.register(KnowledgeSearchTool())
        tool_reg.register(ReportDraftTool())
        app.state.tool_registry = tool_reg

    if getattr(app.state, "tool_policy_engine", None) is None:
        app.state.tool_policy_engine = ToolPolicyEngine()
    if getattr(app.state, "tool_audit_service", None) is None:
        app.state.tool_audit_service = ToolAuditService()
    if getattr(app.state, "tool_repository", None) is None:
        app.state.tool_repository = ToolRepository(session=None)
    if getattr(app.state, "tool_executor", None) is None:
        app.state.tool_executor = KeepToolExecutor(
            registry=app.state.tool_registry,
            policy_service=app.state.tool_policy_engine,
            audit_service=app.state.tool_audit_service,
            repository=app.state.tool_repository,
        )

    # Phase 4.7: Initialize lifespan-bound Agent Memory System
    if getattr(app.state, "memory_repository", None) is None:
        app.state.memory_repository = SqlAlchemyMemoryRepository(session=None)
    if getattr(app.state, "memory_service", None) is None:
        app.state.memory_service = MemoryService(repository=app.state.memory_repository)

    # Phase 4.8: Initialize lifespan-bound Multi-Agent Collaboration System
    if getattr(app.state, "collaboration_repository", None) is None:
        app.state.collaboration_repository = SqlAlchemyCollaborationRepository(session=None)
    if getattr(app.state, "collaboration_service", None) is None:
        app.state.collaboration_service = CollaborationService(
            repository=app.state.collaboration_repository,
            registry=getattr(app.state, "agent_registry", None),
        )

    # Phase 4.9: Initialize lifespan-bound Autonomous Workflow Engine
    if getattr(app.state, "autonomy_repository", None) is None:
        app.state.autonomy_repository = SqlAlchemyAutonomyRepository(
            session_factory=async_session_factory
        )
    if getattr(app.state, "autonomy_service", None) is None:
        app.state.autonomy_service = AutonomousWorkflowService(
            repository=app.state.autonomy_repository,
            workflow_registry=getattr(app.state, "workflow_registry", None),
            agent_registry=getattr(app.state, "agent_registry", None),
            planning_service=getattr(app.state, "planning_service", None),
            runtime_service=getattr(app.state, "agent_runtime", None),
            orchestration_service=getattr(app.state, "orchestration_service", None),
            tool_executor=getattr(app.state, "tool_executor", None),
            memory_service=getattr(app.state, "memory_service", None),
            collaboration_service=getattr(app.state, "collaboration_service", None),
        )

    # Phase 4.10: Initialize lifespan-bound Event-Driven & Trigger-Based Agent Engine
    if getattr(app.state, "event_store", None) is None:
        app.state.event_store = SqlAlchemyEventStore(session_factory=async_session_factory)
    if getattr(app.state, "trigger_repository", None) is None:
        app.state.trigger_repository = SqlAlchemyTriggerRepository(
            session_factory=async_session_factory
        )
    if getattr(app.state, "trigger_service", None) is None:
        app.state.trigger_service = TriggerService(
            event_store=app.state.event_store,
            trigger_repository=app.state.trigger_repository,
            workflow_registry=getattr(app.state, "workflow_registry", None),
            orchestration_service=getattr(app.state, "orchestration_service", None),
            autonomy_service=getattr(app.state, "autonomy_service", None),
        )
    if getattr(app.state, "webhook_source_registry", None) is None:
        app.state.webhook_source_registry = WebhookSourceRegistry()
    if getattr(app.state, "webhook_adapter", None) is None:
        app.state.webhook_adapter = WebhookIngestionAdapter(
            app.state.trigger_service.ingestion_service,
            app.state.webhook_source_registry,
        )

    logger.info(
        "Initialized KEEP AgentRuntime (%d agents), Orchestration (%d workflows), Planning, Research, Tool & Memory Engine",
        app.state.agent_registry.count(),
        app.state.workflow_registry.count(),
    )

    yield

    logger.info("Shutting down KEEP Enterprise Platform Backend Engine")
    res_worker = getattr(app.state, "research_worker", None)
    if res_worker is not None:
        await res_worker.stop()
    wf_worker = getattr(app.state, "workflow_worker", None)
    if wf_worker is not None:
        await wf_worker.stop()
    worker = getattr(app.state, "execution_worker", None)
    if worker is not None:
        await worker.stop()
    # Graceful disposal of database connection pools
    await close_async_engine()


# Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="KEEP Enterprise Knowledge Extraction & Platform API Engine — Phase 1.10 Production Architecture",
    version=settings.VERSION,
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENABLE_OPENAPI_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_OPENAPI_DOCS else None,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENABLE_OPENAPI_DOCS else None,
)

# 1. Request ID Middleware
app.add_middleware(RequestIDMiddleware)

# 2. Security Headers Middleware (Production Hardening)
app.add_middleware(SecurityHeadersMiddleware)

# 3. GZip Compression Middleware (Performance Optimization)
app.add_middleware(GZipMiddleware, minimum_size=settings.GZIP_MINIMUM_SIZE)

# 4. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS
    if settings.BACKEND_CORS_ORIGINS
    else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Logging & Timing Middleware
app.add_middleware(LoggingMiddleware)

# 6. Central Exception Handling
register_exception_handlers(app)

# 7. Mount API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# 8. Mount Phase 4.7 Memory Compatibility Router (/api/memory/*)
app.include_router(memory_router, prefix="/api")

# 9. Mount Phase 4.8 Collaboration Compatibility Router (/api/collaborations/*)
app.include_router(agent_collaboration_router, prefix="/api")

# 10. Mount Phase 4.9 Autonomous Workflows Compatibility Router (/api/autonomous-workflows/*)
app.include_router(autonomous_workflows_router, prefix="/api")

# 11. Mount Phase 4.10 Triggers & Events Compatibility Routers (/api/triggers*, /api/events*, /api/webhooks*)
app.include_router(triggers_router, prefix="/api")
app.include_router(events_router, prefix="/api")

# 6. Mount Root-Level Observability & Health Probes (/health, /health/*)
app.include_router(health_router)


# Root Prometheus Metrics Exposition Endpoint
@app.get(
    "/metrics",
    tags=["Health"],
    summary="Prometheus text metrics exposition endpoint",
    description="Exposes application and infrastructure operational metrics in standard Prometheus text format.",
)
async def prometheus_metrics() -> Response:
    """Returns application and infrastructure metrics in standard Prometheus text exposition format."""
    content, content_type = metrics_registry.generate_prometheus_text()
    return Response(content=content, media_type=content_type)


# Root Discovery Endpoint
@app.get(
    "/",
    tags=["Root"],
    status_code=status.HTTP_200_OK,
    summary="Root service discovery",
    description="Returns platform health, version metadata, and documentation paths.",
)
async def root() -> dict[str, Any]:
    """Root health and discovery endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
    }
