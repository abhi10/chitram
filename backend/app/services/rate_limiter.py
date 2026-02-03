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

    def _allowed_result(self, limit: int | None = None) -> RateLimitResult:
        """Return a result that allows the request."""
        lim = limit or self._limit
        return RateLimitResult(True, 0, lim, lim)

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

    async def check_auth(
        self,
        ip: str,
        email: str | None = None,
    ) -> RateLimitResult:
        """
        Check auth-specific rate limits (stricter than general rate limit).

        Implements dual rate limiting for auth endpoints:
        - Per-IP: 20 requests per 5 minutes (prevents distributed attacks)
        - Per-email: 5 requests per 5 minutes (prevents targeted brute force)

        Args:
            ip: Client IP address
            email: Email address being used (optional for registration)

        Returns:
            RateLimitResult with the most restrictive limit applied
        """
        if not self.enabled:
            return self._allowed_result(limit=settings.auth_rate_limit_per_email)

        window = settings.auth_rate_limit_window_seconds

        try:
            # Check per-IP limit
            ip_key = f"{self._key_prefix}:auth:ip:{ip}"
            ip_limit = settings.auth_rate_limit_per_ip

            async with self._client.pipeline(transaction=True) as pipe:
                pipe.incr(ip_key)
                pipe.expire(ip_key, window, nx=True)
                pipe.ttl(ip_key)
                ip_results = await pipe.execute()

            ip_count, _, ip_ttl = ip_results[0], ip_results[1], ip_results[2]

            if ip_count > ip_limit:
                logger.warning(f"Auth rate limit (IP) exceeded for {ip}: {ip_count}/{ip_limit}")
                return RateLimitResult(
                    allowed=False,
                    current_count=ip_count,
                    limit=ip_limit,
                    remaining=0,
                    retry_after=ip_ttl if ip_ttl > 0 else window,
                )

            # Check per-email limit if email provided
            if email:
                email_key = f"{self._key_prefix}:auth:email:{email.lower()}"
                email_limit = settings.auth_rate_limit_per_email

                async with self._client.pipeline(transaction=True) as pipe:
                    pipe.incr(email_key)
                    pipe.expire(email_key, window, nx=True)
                    pipe.ttl(email_key)
                    email_results = await pipe.execute()

                email_count, _, email_ttl = email_results[0], email_results[1], email_results[2]

                if email_count > email_limit:
                    logger.warning(
                        f"Auth rate limit (email) exceeded for {email}: {email_count}/{email_limit}"
                    )
                    return RateLimitResult(
                        allowed=False,
                        current_count=email_count,
                        limit=email_limit,
                        remaining=0,
                        retry_after=email_ttl if email_ttl > 0 else window,
                    )

                return RateLimitResult(
                    True,
                    email_count,
                    email_limit,
                    max(0, email_limit - email_count),
                )

            return RateLimitResult(
                True,
                ip_count,
                ip_limit,
                max(0, ip_limit - ip_count),
            )

        except RedisError as e:
            logger.warning(f"Auth rate limiter Redis error, allowing request: {e}")
            return self._allowed_result(limit=settings.auth_rate_limit_per_email)


# Global rate limiter instance (initialized in main.py lifespan)
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter | None:
    """Get the global rate limiter instance."""
    return _rate_limiter


def set_rate_limiter(limiter: RateLimiter | None) -> None:
    """Set the global rate limiter instance."""
    global _rate_limiter
    _rate_limiter = limiter
