"""KEEP Enterprise Platform — Main FastAPI Application Entrypoint.

Configures application lifespan, OpenAPI metadata, middleware pipeline,
global exception handlers, and versioned modular routers.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from backend.app.api.middleware import (
    LoggingMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    register_exception_handlers,
)
from backend.app.api.v1 import api_v1_router
from backend.app.api.v1.health import router as health_router
from backend.app.core.config import settings
from backend.app.core.logging import get_logger, setup_logging
from backend.app.core.metrics import metrics_registry
from backend.app.db.session import close_async_engine
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

    yield

    logger.info("Shutting down KEEP Enterprise Platform Backend Engine")
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
