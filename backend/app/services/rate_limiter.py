"""Rate limiter service - Redis-backed sliding window rate limiting."""

import logging

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimitResult:
    """Result of a rate limit check."""

    def __init__(
        self,
        allowed: bool,
        current_count: int,
        limit: int,
        remaining: int,
        retry_after: int | None = None,
    ):
        self.allowed = allowed
        self.current_count = current_count
        self.limit = limit
        self.remaining = remaining
        self.retry_after = retry_after  # Seconds until reset (only if not allowed)


class RateLimiter:
    """
    Redis-backed rate limiter using sliding window algorithm.

    Limits requests per IP address within a time window.

    Graceful Degradation:
    - If Redis is unavailable, requests are ALLOWED (fail-open)
    - This prioritizes availability over protection
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

    def _make_key(self, identifier: str) -> str:
        """Generate rate limit key for identifier (usually IP address)."""
        return f"{self._key_prefix}:ratelimit:{identifier}"

    async def check(self, identifier: str) -> RateLimitResult:
        """
        Check if request from identifier is allowed.

        Args:
            identifier: Unique identifier (usually client IP address)

        Returns:
            RateLimitResult with allowed status and metadata
        """
        # If disabled or no Redis, allow all requests (fail-open)
        if not self._enabled:
            return RateLimitResult(
                allowed=True,
                current_count=0,
                limit=self._limit,
                remaining=self._limit,
            )

        if not self._client:
            logger.debug("Rate limiter: No Redis client, allowing request (fail-open)")
            return RateLimitResult(
                allowed=True,
                current_count=0,
                limit=self._limit,
                remaining=self._limit,
            )

        key = self._make_key(identifier)

        try:
            # Use Redis pipeline for atomic operations
            async with self._client.pipeline(transaction=True) as pipe:
                # Increment counter
                pipe.incr(key)
                # Set expiry on first request in window
                pipe.expire(key, self._window_seconds, nx=True)
                # Get TTL to calculate retry_after
                pipe.ttl(key)
                results = await pipe.execute()

            current_count = results[0]  # Result of INCR
            ttl = results[2]  # Result of TTL

            if current_count > self._limit:
                # Rate limit exceeded
                retry_after = ttl if ttl > 0 else self._window_seconds
                logger.warning(
                    f"Rate limit exceeded for {identifier}: "
                    f"{current_count}/{self._limit} requests"
                )
                return RateLimitResult(
                    allowed=False,
                    current_count=current_count,
                    limit=self._limit,
                    remaining=0,
                    retry_after=retry_after,
                )

            # Request allowed
            remaining = max(0, self._limit - current_count)
            return RateLimitResult(
                allowed=True,
                current_count=current_count,
                limit=self._limit,
                remaining=remaining,
            )

        except RedisError as e:
            # Redis error - fail open (allow request)
            logger.warning(f"Rate limiter Redis error, allowing request: {e}")
            return RateLimitResult(
                allowed=True,
                current_count=0,
                limit=self._limit,
                remaining=self._limit,
            )

    async def reset(self, identifier: str) -> bool:
        """
        Reset rate limit counter for identifier.

        Args:
            identifier: Unique identifier to reset

        Returns:
            True if reset successful, False otherwise
        """
        if not self._client:
            return False

        key = self._make_key(identifier)
        try:
            await self._client.delete(key)
            return True
        except RedisError as e:
            logger.warning(f"Failed to reset rate limit for {identifier}: {e}")
            return False

    async def get_status(self, identifier: str) -> dict:
        """
        Get current rate limit status for identifier.

        Args:
            identifier: Unique identifier to check

        Returns:
            Dict with current count, limit, remaining, and ttl
        """
        if not self._client:
            return {
                "current_count": 0,
                "limit": self._limit,
                "remaining": self._limit,
                "ttl": 0,
            }

        key = self._make_key(identifier)
        try:
            async with self._client.pipeline(transaction=False) as pipe:
                pipe.get(key)
                pipe.ttl(key)
                results = await pipe.execute()

            count_str = results[0]
            ttl = results[1]

            current_count = int(count_str) if count_str else 0
            remaining = max(0, self._limit - current_count)

            return {
                "current_count": current_count,
                "limit": self._limit,
                "remaining": remaining,
                "ttl": max(0, ttl),
            }
        except RedisError as e:
            logger.warning(f"Failed to get rate limit status: {e}")
            return {
                "current_count": 0,
                "limit": self._limit,
                "remaining": self._limit,
                "ttl": 0,
            }


# Global rate limiter instance (initialized in main.py lifespan)
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter | None:
    """Get the global rate limiter instance."""
    return _rate_limiter


def set_rate_limiter(limiter: RateLimiter | None) -> None:
    """Set the global rate limiter instance."""
    global _rate_limiter
    _rate_limiter = limiter
