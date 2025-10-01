import time
from typing import Dict, Any
from fastapi import Request, HTTPException, status
from slowapi.util import get_remote_address
from redis.asyncio import Redis

from app.core.redis_client import get_redis_client
from app.core.logging import general_logger


class RedisRateLimiter:
    """Redis-based rate limiter with sliding window implementation"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def is_allowed(
        self, key: str, limit: int, window: int, identifier: str = ""
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Rate limit key (e.g., "receipts:127.0.0.1")
            limit: Maximum requests allowed
            window: Time window in seconds
            identifier: Request identifier for logging

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        current_time = int(time.time())
        window_start = current_time - window

        pipe = self.redis.pipeline()

        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        pipe.zcard(key)

        # Execute pipeline
        results = await pipe.execute()
        current_requests = results[1]

        # Calculate remaining requests and reset time
        remaining = max(0, limit - current_requests)
        reset_time = current_time + window

        rate_limit_info = {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "retry_after": window if remaining == 0 else None,
        }

        if current_requests >= limit:
            general_logger.warning(
                "rate_limit_exceeded",
                key=key,
                current_requests=current_requests,
                limit=limit,
                window=window,
                identifier=identifier,
            )
            return False, rate_limit_info

        # Add current request
        await self.redis.zadd(key, {f"{current_time}:{identifier}": current_time})
        await self.redis.expire(key, window)

        # Update remaining count
        rate_limit_info["remaining"] = remaining - 1

        general_logger.debug(
            "rate_limit_check",
            key=key,
            current_requests=current_requests + 1,
            limit=limit,
            remaining=rate_limit_info["remaining"],
        )

        return True, rate_limit_info




async def get_rate_limiter() -> RedisRateLimiter:
    """Get rate limiter with Redis client"""
    redis_client = await get_redis_client()
    return RedisRateLimiter(redis_client)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request with proxy support"""
    # Check for forwarded headers (common in load balancers/proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP if there are multiple
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to remote address
    return get_remote_address(request)


async def rate_limit_dependency(
    request: Request, limit: int = 100, window: int = 60, key_prefix: str = "general"
):
    """
    Rate limiting dependency for FastAPI routes.

    Args:
        request: FastAPI request object
        limit: Maximum requests allowed
        window: Time window in seconds
        key_prefix: Prefix for rate limit key

    Raises:
        HTTPException: When rate limit is exceeded
    """
    client_ip = get_client_ip(request)
    limiter = await get_rate_limiter()

    # Create unique key for this client and endpoint
    rate_limit_key = f"{key_prefix}:{client_ip}"
    request_id = getattr(request.state, "request_id", "unknown")

    is_allowed, rate_info = await limiter.is_allowed(
        key=rate_limit_key, limit=limit, window=window, identifier=request_id
    )

    # Add rate limit headers to response
    if hasattr(request.state, "rate_limit_headers"):
        request.state.rate_limit_headers.update(
            {
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(rate_info["reset"]),
            }
        )
    else:
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(rate_info["limit"]),
            "X-RateLimit-Remaining": str(rate_info["remaining"]),
            "X-RateLimit-Reset": str(rate_info["reset"]),
        }

    if not is_allowed:
        headers = {
            "Retry-After": str(rate_info["retry_after"]),
            **request.state.rate_limit_headers,
        }

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {limit} per {window} seconds",
                "retry_after": rate_info["retry_after"],
            },
            headers=headers,
        )


# Specific rate limiting functions for different endpoints
async def receipt_rate_limit(request: Request):
    """Rate limit for receipt upload endpoints (10 requests/minute)"""
    await rate_limit_dependency(request, limit=10, window=60, key_prefix="receipts")


async def general_rate_limit(request: Request):
    """Rate limit for general endpoints (100 requests/minute)"""
    await rate_limit_dependency(request, limit=100, window=60, key_prefix="general")


# Middleware to add rate limit headers to all responses
class RateLimitHeadersMiddleware:
    """Middleware to add rate limit headers to responses"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                request = scope.get("state", {})
                headers = dict(message.get("headers", []))

                # Add rate limit headers if they exist in request state
                if hasattr(request, "rate_limit_headers"):
                    for key, value in request.rate_limit_headers.items():
                        headers[key.lower().encode()] = str(value).encode()

                message["headers"] = list(headers.items())

            await send(message)

        await self.app(scope, receive, send_wrapper)
