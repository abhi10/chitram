"""Error response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Structured error detail."""

    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional error context")


class ErrorResponse(BaseModel):
    """Structured error response wrapper."""

    error: ErrorDetail


# Standard error codes (from requirements.md FR-7)
class ErrorCodes:
    """Standard error codes."""

    INVALID_FILE_FORMAT = "INVALID_FILE_FORMAT"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_REQUEST = "INVALID_REQUEST"
    IMAGE_NOT_FOUND = "IMAGE_NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
