import logging

from fastapi import HTTPException
from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)
_redis: Redis | None = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=1)
    return _redis


async def enforce_rate_limit(key: str) -> None:
    """
    Fixed-window counter in Redis: first request on a key sets a TTL, every
    request after increments it, and once the count exceeds the limit we
    reject until the window expires.

    Fails OPEN on any Redis error. A rate limiter is a protective layer, not
    the core feature — if Redis is down, degrading to "no rate limiting" is
    almost always the right call over taking the whole API down with it.
    """
    try:
        redis = get_redis()
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, settings.rate_limit_window_seconds)
    except Exception:
        logger.warning("Rate limiter unavailable, allowing request through", exc_info=True)
        return

    if current > settings.rate_limit_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
