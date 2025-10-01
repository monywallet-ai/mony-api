import traceback
from typing import Union
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

from app.core.exceptions import (
    MonyAPIException,
    ValidationException,
    BusinessLogicException,
    ResourceNotFoundException,
    DatabaseException,
    RateLimitException,
    FileProcessingException,
)
from app.schemas.error import (
    ErrorResponse,
    ValidationErrorResponse,
    BusinessLogicErrorResponse,
    NotFoundErrorResponse,
    RateLimitErrorResponse,
    InternalServerErrorResponse,
    FileProcessingErrorResponse,
    ErrorDetail,
)
from app.core.logging import general_logger
from app.core.log_utils import get_correlation_id


async def mony_api_exception_handler(
    request: Request, exc: MonyAPIException
) -> JSONResponse:
    """
    Handle custom MonyAPIException and its subclasses.

    Args:
        request: FastAPI request object
        exc: The exception that was raised

    Returns:
        JSONResponse with structured error information
    """
    correlation_id = get_correlation_id(request)

    # Log the error
    general_logger.error(
        "api_exception_occurred",
        error_code=exc.error_code,
        error_message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method,
    )

    # Create appropriate response based on exception type
    if isinstance(exc, ValidationException):
        response_data = ValidationErrorResponse(
            message=exc.message,
            details=exc.details,
            request_id=correlation_id,
        )
    elif isinstance(exc, BusinessLogicException):
        response_data = BusinessLogicErrorResponse(
            message=exc.message,
            rule=exc.details.get("rule"),
            details=exc.details,
            request_id=correlation_id,
        )
    elif isinstance(exc, ResourceNotFoundException):
        response_data = NotFoundErrorResponse(
            message=exc.message,
            resource=exc.details.get("resource", "Resource"),
            resource_id=exc.details.get("resource_id"),
            details=exc.details,
            request_id=correlation_id,
        )
    elif isinstance(exc, RateLimitException):
        response_data = RateLimitErrorResponse(
            message=exc.message,
            limit=exc.details.get("limit", 0),
            window=exc.details.get("window", "unknown"),
            retry_after=exc.details.get("retry_after", 60),
            details=exc.details,
            request_id=correlation_id,
        )
    elif isinstance(exc, FileProcessingException):
        response_data = FileProcessingErrorResponse(
            message=exc.message,
            filename=exc.details.get("filename"),
            file_type=exc.details.get("file_type"),
            error_type=exc.details.get("error_type"),
            details=exc.details,
            request_id=correlation_id,
        )
    else:
        # Generic error response for other custom exceptions
        response_data = ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            request_id=correlation_id,
        )

    headers = {}
    if isinstance(exc, RateLimitException) and exc.details.get("retry_after"):
        headers["Retry-After"] = str(exc.details["retry_after"])

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data.model_dump(),
        headers=headers,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle standard HTTPException instances.

    Args:
        request: FastAPI request object
        exc: The HTTPException that was raised

    Returns:
        JSONResponse with structured error information
    """
    correlation_id = get_correlation_id(request)

    # Log the error
    general_logger.warning(
        "http_exception_occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method,
    )

    # Map HTTP status codes to appropriate error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }

    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")

    response_data = ErrorResponse(
        error_code=error_code,
        message=str(exc.detail),
        request_id=correlation_id,
    )

    headers = {}
    if hasattr(exc, "headers") and exc.headers:
        headers.update(exc.headers)

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data.model_dump(),
        headers=headers,
    )


async def validation_exception_handler(
    request: Request, exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Args:
        request: FastAPI request object
        exc: The validation error that was raised

    Returns:
        JSONResponse with detailed validation error information
    """
    correlation_id = get_correlation_id(request)

    # Log the validation error
    general_logger.warning(
        "validation_error_occurred",
        error_count=len(exc.errors()),
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method,
    )

    # Convert Pydantic errors to our error format
    errors = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"]) if error["loc"] else None
        errors.append(
            ErrorDetail(
                field=field,
                message=error["msg"],
                code=error["type"],
            )
        )

    response_data = ValidationErrorResponse(
        message="Validation failed",
        errors=errors,
        request_id=correlation_id,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data.model_dump(),
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.

    Args:
        request: FastAPI request object
        exc: The SQLAlchemy error that was raised

    Returns:
        JSONResponse with database error information
    """
    correlation_id = get_correlation_id(request)

    # Log the database error
    general_logger.error(
        "database_error_occurred",
        error_type=type(exc).__name__,
        error_message=str(exc),
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method,
    )

    # Handle specific SQLAlchemy errors
    if isinstance(exc, IntegrityError):
        message = "Data integrity constraint violation"
        error_code = "INTEGRITY_ERROR"
        status_code = status.HTTP_409_CONFLICT
    else:
        message = "Database operation failed"
        error_code = "DATABASE_ERROR"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    response_data = ErrorResponse(
        error_code=error_code,
        message=message,
        request_id=correlation_id,
    )

    return JSONResponse(
        status_code=status_code,
        content=response_data.model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Args:
        request: FastAPI request object
        exc: The unexpected exception that was raised

    Returns:
        JSONResponse with generic error information
    """
    correlation_id = get_correlation_id(request)

    # Log the unexpected error with full traceback
    general_logger.error(
        "unexpected_error_occurred",
        error_type=type(exc).__name__,
        error_message=str(exc),
        traceback=traceback.format_exc(),
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method,
    )

    response_data = InternalServerErrorResponse(
        message="An unexpected error occurred. Please try again later.",
        request_id=correlation_id,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data.model_dump(),
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    # Custom exception handlers (most specific first)
    app.add_exception_handler(MonyAPIException, mony_api_exception_handler)

    # FastAPI/Pydantic exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # Database exception handlers
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
