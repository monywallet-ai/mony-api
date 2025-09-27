import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import request_logger

EXPLICIT_EXCLUDE_PATHS = ["/docs", "/redoc", "/openapi.json"]


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Simplified middleware to log HTTP requests with timing information.
    """

    def __init__(self, app, exclude_paths: list[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or EXPLICIT_EXCLUDE_PATHS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time

            request_logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                processing_time_ms=round(process_time * 1000, 2),
            )

            return response

        except Exception as e:
            process_time = time.perf_counter() - start_time

            request_logger.error(
                "request_error",
                method=request.method,
                path=request.url.path,
                processing_time_ms=round(process_time * 1000, 2),
                error=str(e),
                error_type=type(e).__name__,
            )

            raise

