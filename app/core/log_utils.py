import functools
import time
from typing import Callable, Optional

from fastapi import Request
from starlette.requests import Request

from app.core.logging import get_logger


def get_correlation_id(request: Optional[Request] = None) -> str:
    """
    Extract correlation ID from request state or generate a new one.

    Args:
        request: FastAPI request object

    Returns:
        Correlation ID string
    """
    if request and hasattr(request.state, "correlation_id"):
        return request.state.correlation_id

    import uuid

    return str(uuid.uuid4())[:8]


def log_function_call(
    logger_name: str = "mony-api", log_args: bool = False, log_result: bool = False
):
    """
    Decorator to log function calls with timing information.

    Args:
        logger_name: Name of the logger to use
        log_args: Whether to log function arguments
        log_result: Whether to log function return value
    """

    def decorator(func: Callable) -> Callable:
        logger = get_logger(logger_name)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            log_context = {
                "function": func.__name__,
                "module": func.__module__,
            }

            if log_args:
                log_context["args"] = str(args)
                log_context["kwargs"] = {k: str(v) for k, v in kwargs.items()}

            logger.info("function_started", **log_context)

            try:
                result = await func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time

                success_context = {
                    **log_context,
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "status": "success",
                }

                if log_result:
                    success_context["result"] = str(result)[
                        :200
                    ]  # Truncate large results

                logger.info("function_completed", **success_context)
                return result

            except Exception as e:
                execution_time = time.perf_counter() - start_time

                logger.error(
                    "function_failed",
                    **log_context,
                    execution_time_ms=round(execution_time * 1000, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                    status="error",
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            log_context = {
                "function": func.__name__,
                "module": func.__module__,
            }

            if log_args:
                log_context["args"] = str(args)
                log_context["kwargs"] = {k: str(v) for k, v in kwargs.items()}

            logger.info("function_started", **log_context)

            try:
                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time

                success_context = {
                    **log_context,
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "status": "success",
                }

                if log_result:
                    success_context["result"] = str(result)[
                        :200
                    ]  # Truncate large results

                logger.info("function_completed", **success_context)
                return result

            except Exception as e:
                execution_time = time.perf_counter() - start_time

                logger.error(
                    "function_failed",
                    **log_context,
                    execution_time_ms=round(execution_time * 1000, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                    status="error",
                )
                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_database_operation(operation_type: str):
    """
    Decorator specifically for database operations.

    Args:
        operation_type: Type of database operation (create, read, update, delete)
    """

    def decorator(func: Callable) -> Callable:
        logger = get_logger("mony-api.database")

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            logger.info(
                "database_operation_started",
                operation_type=operation_type,
                function=func.__name__,
            )

            try:
                result = await func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time

                logger.info(
                    "database_operation_completed",
                    operation_type=operation_type,
                    function=func.__name__,
                    execution_time_ms=round(execution_time * 1000, 2),
                    status="success",
                )
                return result

            except Exception as e:
                execution_time = time.perf_counter() - start_time

                logger.error(
                    "database_operation_failed",
                    operation_type=operation_type,
                    function=func.__name__,
                    execution_time_ms=round(execution_time * 1000, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                    status="error",
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            logger.info(
                "database_operation_started",
                operation_type=operation_type,
                function=func.__name__,
            )

            try:
                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time

                logger.info(
                    "database_operation_completed",
                    operation_type=operation_type,
                    function=func.__name__,
                    execution_time_ms=round(execution_time * 1000, 2),
                    status="success",
                )
                return result

            except Exception as e:
                execution_time = time.perf_counter() - start_time

                logger.error(
                    "database_operation_failed",
                    operation_type=operation_type,
                    function=func.__name__,
                    execution_time_ms=round(execution_time * 1000, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                    status="error",
                )
                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_openai_request(model_name: str):
    """
    Decorator specifically for OpenAI API calls.

    Args:
        model_name: The OpenAI model being used
    """

    def decorator(func: Callable) -> Callable:
        logger = get_logger("mony-api.openai")

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            logger.info(
                "openai_request_started", model=model_name, function=func.__name__
            )

            try:
                result = await func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time

                # Try to extract token usage if available
                token_usage = None
                if hasattr(result, "usage"):
                    token_usage = {
                        "prompt_tokens": result.usage.prompt_tokens,
                        "completion_tokens": result.usage.completion_tokens,
                        "total_tokens": result.usage.total_tokens,
                    }

                logger.info(
                    "openai_request_completed",
                    model=model_name,
                    function=func.__name__,
                    execution_time_ms=round(execution_time * 1000, 2),
                    token_usage=token_usage,
                    status="success",
                )
                return result

            except Exception as e:
                execution_time = time.perf_counter() - start_time

                logger.error(
                    "openai_request_failed",
                    model=model_name,
                    function=func.__name__,
                    execution_time_ms=round(execution_time * 1000, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                    status="error",
                )
                raise

        return wrapper

    return decorator


class LogContext:
    """
    Context manager for adding structured context to logs within a block.
    """

    def __init__(self, logger_name: str = "mony-api", **context):
        self.logger = get_logger(logger_name)
        self.context = context
        self.bound_logger = None

    def __enter__(self):
        self.bound_logger = self.logger.bind(**self.context)
        return self.bound_logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.bound_logger.error(
                "context_error", error=str(exc_val), error_type=exc_type.__name__
            )
        return False  # Don't suppress exceptions
