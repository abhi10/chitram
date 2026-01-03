"""Rate limiter service - Redis-backed sliding window rate limiting."""

import logging
from dataclasses import dataclass

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    current_count: int
    limit: int
    remaining: int
    retry_after: int | None = None


class RateLimiter:
    """
    Redis-backed rate limiter using sliding window algorithm.
    Fail-open design: allows requests if Redis is unavailable.
    """

    def __init__(
        self,
        redis_client: redis.Redis | None = None,
        key_prefix: str = settings.cache_key_prefix,
        limit: int = settings.rate_limit_per_minute,
        window_seconds: int = settings.rate_limit_window_seconds,
        enabled: bool = settings.rate_limit_enabled,
    ):
        self._client = redis_client
        self._key_prefix = key_prefix
        self._limit = limit
        self._window_seconds = window_seconds
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        """Check if rate limiting is enabled."""
        return self._enabled and self._client is not None

    def _allowed_result(self) -> RateLimitResult:
        """Return a result that allows the request."""
        return RateLimitResult(True, 0, self._limit, self._limit)

    async def check(self, identifier: str) -> RateLimitResult:
        """Check if request from identifier is allowed."""
        if not self.enabled:
            return self._allowed_result()

        key = f"{self._key_prefix}:ratelimit:{identifier}"

        try:
            async with self._client.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, self._window_seconds, nx=True)
                pipe.ttl(key)
                results = await pipe.execute()

            count, _, ttl = results[0], results[1], results[2]

            if count > self._limit:
                logger.warning(f"Rate limit exceeded for {identifier}: {count}/{self._limit}")
                return RateLimitResult(
                    allowed=False,
                    current_count=count,
                    limit=self._limit,
                    remaining=0,
                    retry_after=ttl if ttl > 0 else self._window_seconds,
                )

            return RateLimitResult(True, count, self._limit, max(0, self._limit - count))

        except RedisError as e:
            logger.warning(f"Rate limiter Redis error, allowing request: {e}")
            return self._allowed_result()


# Global rate limiter instance (initialized in main.py lifespan)
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter | None:
    """Get the global rate limiter instance."""
    return _rate_limiter


def set_rate_limiter(limiter: RateLimiter | None) -> None:
    """Set the global rate limiter instance."""
    global _rate_limiter
    _rate_limiter = limiter
