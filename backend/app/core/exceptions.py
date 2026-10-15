"""KEEP Enterprise Platform — Custom Domain Exceptions.

Provides structured application exceptions with mapped HTTP statuses and standardized error codes.
"""

from typing import Any

from backend.app.core.constants import ErrorCode
from fastapi import status


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


class BadRequestException(AppException):
    """Raised when a request is malformed or invalid."""

    def __init__(
        self,
        message: str = "Invalid request.",
        code: str | ErrorCode = ErrorCode.INVALID_REQUEST,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


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


class AuthorizationException(ForbiddenException):
    """Base exception for all authorization and RBAC evaluation failures."""

    def __init__(
        self,
        message: str = "Authorization failed.",
        code: str | ErrorCode = ErrorCode.AUTH_FORBIDDEN,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            details=details,
        )


class PermissionDeniedException(AuthorizationException):
    """Raised when caller lacks the required action permission for an operation."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        code: str | ErrorCode = ErrorCode.AUTH_PERMISSION_DENIED,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            details=details,
        )


class RoleRequiredException(AuthorizationException):
    """Raised when caller does not possess the minimum required role."""

    def __init__(
        self,
        message: str = "Required role not assigned.",
        code: str | ErrorCode = ErrorCode.AUTH_ROLE_REQUIRED,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            details=details,
        )


class ResourceForbiddenException(AuthorizationException):
    """Raised when target resource is forbidden (e.g. project membership missing)."""

    def __init__(
        self,
        message: str = "Resource is inaccessible.",
        code: str | ErrorCode = ErrorCode.AUTH_RESOURCE_FORBIDDEN,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            details=details,
        )


class OrganizationMismatchException(AuthorizationException):
    """Raised when cross-tenant access is attempted."""

    def __init__(
        self,
        message: str = "Cross-tenant access attempted.",
        code: str | ErrorCode = ErrorCode.AUTH_ORGANIZATION_MISMATCH,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            details=details,
        )


class PolicyFailedException(AuthorizationException):
    """Raised when centralized policy engine evaluation yields a DENY verdict."""

    def __init__(
        self,
        message: str = "Policy evaluation failed.",
        code: str | ErrorCode = ErrorCode.AUTH_POLICY_FAILED,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
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


class RateLimitExceededException(AppException):
    """Raised when an operation exceeds rate limits."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please wait before retrying.",
        code: str | ErrorCode = ErrorCode.AI_RATE_LIMIT_EXCEEDED,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=getattr(status, "HTTP_429_TOO_MANY_REQUESTS", 429),
            details=details,
        )


class StorageQuotaExceededException(AppException):
    """Raised when an upload exceeds organizational storage allowance."""

    def __init__(
        self,
        message: str = "Storage quota exceeded for this organization.",
        code: str | ErrorCode = ErrorCode.STORAGE_QUOTA_EXCEEDED,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class DuplicateFileException(ConflictException):
    """Raised when an uploaded document matches an existing active document's checksum."""

    def __init__(
        self,
        message: str = "Duplicate document detected in this organization.",
        code: str | ErrorCode = ErrorCode.DUPLICATE_FILE_DETECTED,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            details=details,
        )


class PreviewUnavailableException(AppException):
    """Raised when document preview generation or streaming fails."""

    def __init__(
        self,
        message: str = "Preview unavailable for this document format.",
        code: str | ErrorCode = ErrorCode.PREVIEW_UNAVAILABLE,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            details=details,
        )
