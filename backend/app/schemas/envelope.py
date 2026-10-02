"""KEEP Enterprise Platform — Standardized API Envelope Schemas.

Implements the uniform response structure defined in devdocs Chapters 14 & 15
and docs/api/api-contract.md.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Detailed error object contained within ApiErrorResponse."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error explanation")
    details: Any | None = Field(
        default=None, description="Contextual validation or error metadata"
    )

    model_config = ConfigDict(extra="allow")


class ApiErrorResponse(BaseModel):
    """Standardized API Error Envelope."""

    success: bool = Field(default=False, description="Always False for error responses")
    error: ErrorDetail = Field(..., description="Error detail container")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "code": "AUTH_INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                    "details": None,
                },
            }
        }
    )


class ApiResponse(BaseModel, Generic[T]):
    """Standardized API Success Envelope."""

    success: bool = Field(
        default=True, description="Always True for successful operations"
    )
    message: str = Field(
        default="Operation completed successfully.",
        description="Operational status message",
    )
    data: T | None = Field(default=None, description="Enclosed response payload")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed successfully.",
                "data": {},
            }
        }
    )


class PaginatedData(BaseModel, Generic[T]):
    """Standardized Paginated Collection Container."""

    items: list[T] = Field(
        default_factory=list, description="Paginated collection items"
    )
    total: int = Field(default=0, description="Total count of matching records")
    page: int = Field(default=1, description="Current page number (1-indexed)")
    page_size: int = Field(default=20, description="Number of items per page")
    total_pages: int = Field(default=0, description="Total number of available pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 120,
                "page": 1,
                "page_size": 20,
                "total_pages": 6,
            }
        }
    )
