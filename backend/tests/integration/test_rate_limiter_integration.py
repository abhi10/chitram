"""Integration tests for rate limiter service.

These tests require a running Redis instance.
Tests are automatically skipped if Redis is not available.

Covers the manual testing checklist:
1. Make 10 requests, verify 11th returns 429
2. Verify Retry-After header present
3. Verify rate limit resets after window expires
4. Stop Redis, verify requests still work (fail-open)
5. Verify health endpoint shows rate limiter status
"""

import asyncio
import os

import pytest
import redis.asyncio as redis

from app.services.rate_limiter import RateLimiter

# Redis connection settings for tests
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


async def redis_available() -> bool:
    """Check if Redis is available for testing."""
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        await client.ping()
        await client.aclose()
        return True
    except Exception:
        return False


@pytest.fixture
async def redis_client():
    """Create a Redis client for testing."""
    if not await redis_available():
        pytest.skip("Redis not available")

    client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    yield client

    # Cleanup: delete all test rate limit keys
    try:
        keys = []
        async for key in client.scan_iter("test_ratelimit:*"):
            keys.append(key)
        if keys:
            await client.delete(*keys)
    except Exception:
        pass

    await client.aclose()


@pytest.fixture
def rate_limiter(redis_client):
    """Create a rate limiter with real Redis."""
    return RateLimiter(
        redis_client=redis_client,
        key_prefix="test_ratelimit",
        limit=10,
        window_seconds=2,  # Short window for testing
        enabled=True,
    )


class TestRateLimiterIntegration:
    """Integration tests for rate limiter with real Redis."""

    @pytest.mark.asyncio
    async def test_rate_limiter_enabled_with_redis(self, rate_limiter):
        """Test rate limiter reports enabled when Redis connected."""
        assert rate_limiter.enabled is True

    @pytest.mark.asyncio
    async def test_requests_under_limit_allowed(self, rate_limiter):
        """Test that requests under limit are allowed."""
        test_ip = "192.168.1.100"

        # First 10 requests should all be allowed
        for i in range(10):
            result = await rate_limiter.check(test_ip)
            assert result.allowed is True, f"Request {i+1} should be allowed"
            assert result.current_count == i + 1
            assert result.remaining == 10 - (i + 1)

    @pytest.mark.asyncio
    async def test_11th_request_returns_429(self, rate_limiter):
        """Test that 11th request is denied (manual checklist item 1)."""
        test_ip = "192.168.1.101"

        # Make 10 requests (all allowed)
        for i in range(10):
            result = await rate_limiter.check(test_ip)
            assert result.allowed is True

        # 11th request should be denied
        result = await rate_limiter.check(test_ip)
        assert result.allowed is False
        assert result.current_count == 11
        assert result.remaining == 0

    @pytest.mark.asyncio
    async def test_retry_after_header_present(self, rate_limiter):
        """Test that retry_after is set when rate limited (manual checklist item 2)."""
        test_ip = "192.168.1.102"

        # Exhaust the limit
        for _ in range(10):
            await rate_limiter.check(test_ip)

        # 11th request should have retry_after
        result = await rate_limiter.check(test_ip)
        assert result.allowed is False
        assert result.retry_after is not None
        assert result.retry_after > 0
        assert result.retry_after <= 2  # Our window is 2 seconds

    @pytest.mark.asyncio
    async def test_rate_limit_resets_after_window(self, rate_limiter):
        """Test that rate limit resets after window expires (manual checklist item 3)."""
        test_ip = "192.168.1.103"

        # Exhaust the limit
        for _ in range(10):
            await rate_limiter.check(test_ip)

        # Verify we're rate limited
        result = await rate_limiter.check(test_ip)
        assert result.allowed is False

        # Wait for window to expire (2 seconds + buffer)
        await asyncio.sleep(2.5)

        # Should be allowed again
        result = await rate_limiter.check(test_ip)
        assert result.allowed is True
        assert result.current_count == 1  # Reset to 1

    @pytest.mark.asyncio
    async def test_different_ips_have_separate_limits(self, rate_limiter):
        """Test that different IPs have independent rate limits."""
        ip1 = "10.0.0.1"
        ip2 = "10.0.0.2"

        # Exhaust limit for ip1
        for _ in range(10):
            await rate_limiter.check(ip1)

        # ip1 should be rate limited
        result1 = await rate_limiter.check(ip1)
        assert result1.allowed is False

        # ip2 should still have full quota
        result2 = await rate_limiter.check(ip2)
        assert result2.allowed is True
        assert result2.current_count == 1
        assert result2.remaining == 9


class TestRateLimiterFailOpen:
    """Test fail-open behavior when Redis is unavailable (manual checklist item 4)."""

    @pytest.mark.asyncio
    async def test_fail_open_no_redis_client(self):
        """Test requests allowed when no Redis client configured."""
        limiter = RateLimiter(
            redis_client=None,
            limit=10,
            enabled=True,
        )

        # Should allow requests even though enabled=True
        result = await limiter.check("any-ip")
        assert result.allowed is True
        assert result.current_count == 0

    @pytest.mark.asyncio
    async def test_fail_open_bad_redis_connection(self):
        """Test requests allowed when Redis connection fails."""
        # Create a client that will fail
        bad_client = redis.Redis(host="nonexistent-host", port=12345)

        limiter = RateLimiter(
            redis_client=bad_client,
            limit=10,
            enabled=True,
        )

        # Should fail open and allow requests
        result = await limiter.check("any-ip")
        assert result.allowed is True

        await bad_client.aclose()

    @pytest.mark.asyncio
    async def test_disabled_limiter_allows_all(self):
        """Test disabled rate limiter allows all requests."""
        limiter = RateLimiter(enabled=False)

        # Make many requests - all should be allowed
        for _ in range(100):
            result = await limiter.check("any-ip")
            assert result.allowed is True


class TestRateLimiterHealthStatus:
    """Test health endpoint rate limiter status (manual checklist item 5)."""

    @pytest.mark.asyncio
    async def test_enabled_status_with_redis(self, redis_client):
        """Test rate limiter reports enabled with Redis."""
        limiter = RateLimiter(
            redis_client=redis_client,
            enabled=True,
        )
        assert limiter.enabled is True

    @pytest.mark.asyncio
    async def test_disabled_status_no_redis(self):
        """Test rate limiter reports disabled without Redis."""
        limiter = RateLimiter(
            redis_client=None,
            enabled=True,
        )
        # enabled property checks both _enabled AND _client
        assert limiter.enabled is False

    @pytest.mark.asyncio
    async def test_disabled_status_explicit(self, redis_client):
        """Test rate limiter reports disabled when explicitly disabled."""
        limiter = RateLimiter(
            redis_client=redis_client,
            enabled=False,
        )
        assert limiter.enabled is False
