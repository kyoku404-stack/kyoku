"""KEEP Enterprise Platform — Custom Domain Exceptions.

Provides structured application exceptions with mapped HTTP statuses and standardized error codes.
"""

from typing import Any
from fastapi import status
from backend.app.core.constants import ErrorCode


class AppException(Exception):
    """Base exception for all application-level errors."""

    def __init__(
        self,
        message: str = "An internal error occurred.",
        code: str | ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Any | None = None,
    ) -> None:
        self.message = message
        self.code = str(code)
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class NotFoundException(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        message: str = "Resource not found.",
        code: str | ErrorCode = ErrorCode.NOT_FOUND,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class UnauthorizedException(AppException):
    """Raised when authentication fails or is missing."""

    def __init__(
        self,
        message: str = "Authentication credentials invalid or missing.",
        code: str | ErrorCode = ErrorCode.AUTH_UNAUTHORIZED,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ForbiddenException(AppException):
    """Raised when the user lacks required permissions."""

    def __init__(
        self,
        message: str = "Access forbidden.",
        code: str | ErrorCode = ErrorCode.AUTH_FORBIDDEN,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ValidationException(AppException):
    """Raised when request payload fails business validation rules."""

    def __init__(
        self,
        message: str = "Validation failed.",
        code: str | ErrorCode = ErrorCode.VALIDATION_ERROR,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            details=details,
        )


class ConflictException(AppException):
    """Raised when a unique constraint or resource state conflict occurs."""

    def __init__(
        self,
        message: str = "Resource conflict.",
        code: str | ErrorCode = ErrorCode.CONFLICT,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class DatabaseException(AppException):
    """Raised when a database error occurs."""

    def __init__(
        self,
        message: str = "Database operation failed.",
        code: str | ErrorCode = ErrorCode.DATABASE_ERROR,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )
