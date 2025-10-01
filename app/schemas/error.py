from datetime import datetime
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Individual error detail item."""

    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Specific error code")


class ErrorResponse(BaseModel):
    """
    Standardized error response schema.

    Provides consistent error information across all API endpoints.
    """

    success: bool = Field(False, description="Always false for error responses")
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )
    request_id: Optional[str] = Field(None, description="Request correlation ID")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": {"field": "total_amount", "value": -10.5},
                "timestamp": "2024-10-01T12:00:00Z",
                "request_id": "req_abc123",
            }
        }


class ValidationErrorResponse(ErrorResponse):
    """
    Specialized error response for validation errors.

    Includes detailed field-level validation errors.
    """

    error_code: str = Field("VALIDATION_ERROR", description="Validation error code")
    errors: List[ErrorDetail] = Field([], description="List of validation errors")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "errors": [
                    {
                        "field": "total_amount",
                        "message": "Must be greater than 0",
                        "code": "VALUE_ERROR",
                    },
                    {
                        "field": "merchant",
                        "message": "Field is required",
                        "code": "MISSING_FIELD",
                    },
                ],
                "timestamp": "2024-10-01T12:00:00Z",
                "request_id": "req_abc123",
            }
        }


class BusinessLogicErrorResponse(ErrorResponse):
    """Error response for business logic violations."""

    error_code: str = Field(
        "BUSINESS_LOGIC_ERROR", description="Business logic error code"
    )
    rule: Optional[str] = Field(None, description="Business rule that was violated")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_code": "BUSINESS_LOGIC_ERROR",
                "message": "Transaction amount exceeds daily limit",
                "rule": "DAILY_TRANSACTION_LIMIT",
                "details": {
                    "limit": 1000.0,
                    "current_total": 950.0,
                    "attempted_amount": 100.0,
                },
                "timestamp": "2024-10-01T12:00:00Z",
                "request_id": "req_abc123",
            }
        }


class NotFoundErrorResponse(ErrorResponse):
    """Error response for resource not found errors."""

    error_code: str = Field("RESOURCE_NOT_FOUND", description="Not found error code")
    resource: str = Field(..., description="Type of resource that was not found")
    resource_id: Optional[str] = Field(
        None, description="ID of the resource that was not found"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_code": "RESOURCE_NOT_FOUND",
                "message": "Transaction with ID 123 not found",
                "resource": "Transaction",
                "resource_id": "123",
                "timestamp": "2024-10-01T12:00:00Z",
                "request_id": "req_abc123",
            }
        }


class RateLimitErrorResponse(ErrorResponse):
    """Error response for rate limit exceeded errors."""

    error_code: str = Field("RATE_LIMIT_EXCEEDED", description="Rate limit error code")
    limit: int = Field(..., description="Rate limit threshold")
    window: str = Field(..., description="Time window for the rate limit")
    retry_after: int = Field(..., description="Seconds to wait before retrying")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded. Try again later.",
                "limit": 100,
                "window": "1 minute",
                "retry_after": 60,
                "timestamp": "2024-10-01T12:00:00Z",
                "request_id": "req_abc123",
            }
        }


class InternalServerErrorResponse(ErrorResponse):
    """Error response for internal server errors."""

    error_code: str = Field("INTERNAL_ERROR", description="Internal server error code")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "timestamp": "2024-10-01T12:00:00Z",
                "request_id": "req_abc123",
            }
        }


class FileProcessingErrorResponse(ErrorResponse):
    """Error response for file processing errors."""

    error_code: str = Field("FILE_PROCESSING_ERROR", description="File processing error code")
    filename: Optional[str] = Field(None, description="Name of the file that failed to process")
    file_type: Optional[str] = Field(None, description="Type of file that failed to process")
    error_type: Optional[str] = Field(None, description="Specific type of processing error")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_code": "FILE_PROCESSING_ERROR",
                "message": "Unable to process receipt image",
                "filename": "receipt_20241001_123456.jpg",
                "file_type": "image/jpeg",
                "error_type": "UNSUPPORTED_FORMAT",
                "details": {
                    "supported_formats": ["image/jpeg", "image/png", "application/pdf"],
                    "file_size": 5242880
                },
                "timestamp": "2024-10-01T12:00:00Z",
                "request_id": "req_abc123",
            }
        }
