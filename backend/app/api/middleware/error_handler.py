"""KEEP Enterprise Platform — Global Exception Handlers.

Intercepts exceptions and serializes them into the uniform ApiErrorResponse structure.
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.constants import ErrorCode
from backend.app.core.exceptions import AppException
from backend.app.core.logging import get_logger

logger = get_logger("api.error_handler")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handles custom application domain exceptions."""
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "[%s] AppException caught on %s: [%s] %s",
        request_id,
        request.url.path,
        exc.code,
        exc.message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handles FastAPI/Pydantic request payload validation errors."""
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "[%s] RequestValidationError on %s: %s",
        request_id,
        request.url.path,
        exc.errors(),
    )
    # Simplify error details for API consumers
    simplified_errors = [
        {
            "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg"),
            "type": err.get("type"),
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        content={
            "success": False,
            "error": {
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "Validation failed for request data.",
                "details": simplified_errors,
            },
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handles standard Starlette/FastAPI HTTPExceptions."""
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "[%s] HTTPException on %s: [%d] %s",
        request_id,
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    code_map = {
        400: ErrorCode.INVALID_REQUEST,
        401: ErrorCode.AUTH_UNAUTHORIZED,
        403: ErrorCode.AUTH_FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
    }
    code = code_map.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": str(exc.detail),
                "details": None,
            },
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all unhandled server exception handler."""
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        "[%s] Unhandled exception processing %s: %s",
        request_id,
        request.url.path,
        str(exc),
        exc_info=exc,
    )
    detail = str(exc) if settings.ENVIRONMENT == "development" else None
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.INTERNAL_SERVER_ERROR,
                "message": "An unexpected server error occurred.",
                "details": detail,
            },
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registers all exception handlers on the FastAPI instance."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
