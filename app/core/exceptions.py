from typing import Any, Dict, Optional


class MonyAPIException(Exception):
    """
    Base exception class for all custom application exceptions.

    Provides structured error information and consistent error handling.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class ValidationException(MonyAPIException):
    """Exception raised for data validation errors."""

    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = value

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=error_details,
        )


class BusinessLogicException(MonyAPIException):
    """Exception raised for business logic violations."""

    def __init__(
        self,
        message: str = "Business logic violation",
        rule: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if rule:
            error_details["rule"] = rule

        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            status_code=400,
            details=error_details,
        )


class ResourceNotFoundException(MonyAPIException):
    """Exception raised when a requested resource is not found."""

    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Optional[Any] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if not message:
            message = f"{resource} not found"
            if resource_id:
                message = f"{resource} with ID {resource_id} not found"

        error_details = details or {}
        error_details["resource"] = resource
        if resource_id:
            error_details["resource_id"] = str(resource_id)

        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=error_details,
        )


class DatabaseException(MonyAPIException):
    """Exception raised for database-related errors."""

    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if operation:
            error_details["operation"] = operation

        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=error_details,
        )


class RateLimitException(MonyAPIException):
    """Exception raised when rate limits are exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        window: Optional[str] = None,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if limit:
            error_details["limit"] = limit
        if window:
            error_details["window"] = window
        if retry_after:
            error_details["retry_after"] = retry_after

        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=error_details,
        )


class FileProcessingException(MonyAPIException):
    """Exception raised for file processing errors."""

    def __init__(
        self,
        message: str = "File processing failed",
        filename: Optional[str] = None,
        file_type: Optional[str] = None,
        error_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if filename:
            error_details["filename"] = filename
        if file_type:
            error_details["file_type"] = file_type
        if error_type:
            error_details["error_type"] = error_type

        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            status_code=422,  # Unprocessable Entity
            details=error_details,
        )
