"""KEEP Enterprise Platform — Core Constants & Enumerations.

Defines standardized error codes, role definitions, and system states.
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    """Standardized API Error Codes matching devdocs Chapter 14 and docs/api/api-contract.md."""

    # Authentication & Authorization
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_UNAUTHORIZED = "AUTH_UNAUTHORIZED"
    AUTH_FORBIDDEN = "AUTH_FORBIDDEN"

    # Validation & Requests
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    FILE_SIZE_EXCEEDED = "FILE_SIZE_EXCEEDED"

    # Resource & Data
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    DATABASE_ERROR = "DATABASE_ERROR"
    TENANT_MISMATCH = "TENANT_MISMATCH"

    # AI & Pipeline
    AI_INFERENCE_ERROR = "AI_INFERENCE_ERROR"
    SEARCH_QUERY_ERROR = "SEARCH_QUERY_ERROR"

    # Server Errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class UserRole(StrEnum):
    """User access control roles within an organization."""

    SUPER_ADMIN = "SuperAdmin"
    ORG_ADMIN = "OrgAdmin"
    MANAGER = "Manager"
    MEMBER = "Member"
    VIEWER = "Viewer"


class DocumentStatus(StrEnum):
    """Ingestion & processing lifecycle statuses for documents."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class EnvironmentType(StrEnum):
    """Runtime environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"
