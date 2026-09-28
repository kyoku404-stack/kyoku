"""KEEP Enterprise Platform — Main FastAPI Application Entrypoint.

Configures application lifespan, middleware, routers, and global exception handlers.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from backend.app.core.config import settings
from backend.app.core.logging import get_logger, setup_logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup and graceful shutdown."""
    setup_logging(settings.LOG_LEVEL)
    logger.info(
        "Starting KEEP Enterprise Platform Backend Engine (v%s)", settings.VERSION
    )
    logger.info("Environment: %s", settings.ENVIRONMENT)

    yield

    logger.info("Shutting down KEEP Enterprise Platform Backend Engine")


# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise Knowledge Extraction & Platform API Engine",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS
    if settings.BACKEND_CORS_ORIGINS
    else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unhandled exceptions and returns standardized error response."""
    logger.error(
        "Unhandled exception processing request %s: %s",
        request.url,
        str(exc),
        exc_info=exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected server error occurred.",
            "detail": str(exc) if settings.ENVIRONMENT == "development" else None,
        },
    )


# Root Endpoint
@app.get("/", tags=["Root"])
async def root() -> dict[str, Any]:
    """Root health and discovery endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
    }


# Health Check Endpoint
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """Central system health-check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
    }
