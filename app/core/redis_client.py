from typing import Optional
import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.settings import settings
from app.core.logging import general_logger


# Redis client singleton
_redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    """
    Get or create Redis client singleton.

    Returns:
        Redis: Async Redis client instance

    Raises:
        Exception: If Redis connection fails
    """
    global _redis_client

    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            # Test connection
            await _redis_client.ping()
            general_logger.info(
                "redis_connection_established",
                url=_mask_redis_password(settings.redis_url),
            )
        except Exception as e:
            general_logger.error("redis_connection_failed", error=str(e))
            raise

    return _redis_client


async def close_redis_client():
    """Close Redis client connection and cleanup resources"""
    global _redis_client
    if _redis_client:
        try:
            await _redis_client.close()
            general_logger.info("redis_connection_closed")
        except Exception as e:
            general_logger.warning("redis_close_error", error=str(e))
        finally:
            _redis_client = None


async def health_check_redis() -> bool:
    """
    Check if Redis is healthy and responsive.

    Returns:
        bool: True if Redis is healthy, False otherwise
    """
    try:
        client = await get_redis_client()
        await client.ping()
        return True
    except Exception as e:
        general_logger.error("redis_health_check_failed", error=str(e))
        return False


def _mask_redis_password(url: str) -> str:
    """
    Mask password in Redis URL for logging purposes.

    Args:
        url: Redis URL that may contain password

    Returns:
        str: URL with password masked
    """
    if ":" in url and "@" in url:
        # Format: redis://:password@host:port/db
        parts = url.split("@")
        if len(parts) >= 2:
            auth_part = parts[0]
            if ":" in auth_part:
                scheme_and_user = auth_part.rsplit(":", 1)[0]
                return f"{scheme_and_user}:***@{'@'.join(parts[1:])}"
    return url
