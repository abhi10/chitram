"""Unit tests for rate limiter service."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.exceptions import RedisError

from app.services.rate_limiter import RateLimiter, RateLimitResult


class TestRateLimitResult:
    """Tests for RateLimitResult dataclass."""

    def test_allowed_result(self):
        """Test creating an allowed result."""
        result = RateLimitResult(
            allowed=True,
            current_count=5,
            limit=10,
            remaining=5,
        )
        assert result.allowed is True
        assert result.current_count == 5
        assert result.limit == 10
        assert result.remaining == 5
        assert result.retry_after is None

    def test_denied_result(self):
        """Test creating a denied result with retry_after."""
        result = RateLimitResult(
            allowed=False,
            current_count=11,
            limit=10,
            remaining=0,
            retry_after=45,
        )
        assert result.allowed is False
        assert result.current_count == 11
        assert result.retry_after == 45


class TestRateLimiterInit:
    """Tests for RateLimiter initialization."""

    def test_init_with_defaults(self):
        """Test rate limiter with default settings."""
        limiter = RateLimiter()
        assert limiter._key_prefix == "chitram"
        assert limiter._limit == 10
        assert limiter._window_seconds == 60

    def test_init_with_custom_values(self):
        """Test rate limiter with custom settings."""
        mock_client = MagicMock()
        limiter = RateLimiter(
            redis_client=mock_client,
            key_prefix="test",
            limit=100,
            window_seconds=120,
            enabled=True,
        )
        assert limiter._key_prefix == "test"
        assert limiter._limit == 100
        assert limiter._window_seconds == 120
        assert limiter._client == mock_client

    def test_enabled_property_true(self):
        """Test enabled property when properly configured."""
        mock_client = MagicMock()
        limiter = RateLimiter(redis_client=mock_client, enabled=True)
        assert limiter.enabled is True

    def test_enabled_property_false_no_client(self):
        """Test enabled property when no Redis client."""
        limiter = RateLimiter(redis_client=None, enabled=True)
        assert limiter.enabled is False

    def test_enabled_property_false_disabled(self):
        """Test enabled property when explicitly disabled."""
        mock_client = MagicMock()
        limiter = RateLimiter(redis_client=mock_client, enabled=False)
        assert limiter.enabled is False


class TestRateLimiterKeyGeneration:
    """Tests for key generation."""

    def test_make_key_default_prefix(self):
        """Test key generation with default prefix."""
        limiter = RateLimiter(key_prefix="chitram")
        key = limiter._make_key("192.168.1.1")
        assert key == "chitram:ratelimit:192.168.1.1"

    def test_make_key_custom_prefix(self):
        """Test key generation with custom prefix."""
        limiter = RateLimiter(key_prefix="myapp")
        key = limiter._make_key("10.0.0.1")
        assert key == "myapp:ratelimit:10.0.0.1"


class TestRateLimiterCheck:
    """Tests for rate limit checking."""

    @pytest.mark.asyncio
    async def test_check_disabled_allows_all(self):
        """Test that disabled rate limiter allows all requests."""
        limiter = RateLimiter(enabled=False)
        result = await limiter.check("192.168.1.1")

        assert result.allowed is True
        assert result.current_count == 0
        assert result.remaining == 10  # Default limit

    @pytest.mark.asyncio
    async def test_check_no_client_allows_all(self):
        """Test that missing Redis client allows all requests (fail-open)."""
        limiter = RateLimiter(redis_client=None, enabled=True)
        result = await limiter.check("192.168.1.1")

        assert result.allowed is True
        assert result.current_count == 0

    @pytest.mark.asyncio
    async def test_check_under_limit(self):
        """Test request under rate limit is allowed."""
        mock_client = MagicMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.incr = MagicMock()
        mock_pipeline.expire = MagicMock()
        mock_pipeline.ttl = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=[5, True, 45])  # count, expire result, ttl
        mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
        mock_pipeline.__aexit__ = AsyncMock(return_value=None)
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)

        limiter = RateLimiter(redis_client=mock_client, limit=10, enabled=True)
        result = await limiter.check("192.168.1.1")

        assert result.allowed is True
        assert result.current_count == 5
        assert result.remaining == 5
        assert result.retry_after is None

    @pytest.mark.asyncio
    async def test_check_at_limit(self):
        """Test request at exact limit is allowed."""
        mock_client = MagicMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.incr = MagicMock()
        mock_pipeline.expire = MagicMock()
        mock_pipeline.ttl = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=[10, True, 30])
        mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
        mock_pipeline.__aexit__ = AsyncMock(return_value=None)
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)

        limiter = RateLimiter(redis_client=mock_client, limit=10, enabled=True)
        result = await limiter.check("192.168.1.1")

        assert result.allowed is True
        assert result.current_count == 10
        assert result.remaining == 0

    @pytest.mark.asyncio
    async def test_check_over_limit(self):
        """Test request over rate limit is denied."""
        mock_client = MagicMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.incr = MagicMock()
        mock_pipeline.expire = MagicMock()
        mock_pipeline.ttl = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=[11, True, 45])
        mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
        mock_pipeline.__aexit__ = AsyncMock(return_value=None)
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)

        limiter = RateLimiter(redis_client=mock_client, limit=10, enabled=True)
        result = await limiter.check("192.168.1.1")

        assert result.allowed is False
        assert result.current_count == 11
        assert result.remaining == 0
        assert result.retry_after == 45

    @pytest.mark.asyncio
    async def test_check_redis_error_allows_request(self):
        """Test that Redis error allows request (fail-open)."""
        mock_client = MagicMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.incr = MagicMock()
        mock_pipeline.expire = MagicMock()
        mock_pipeline.ttl = MagicMock()
        mock_pipeline.execute = AsyncMock(side_effect=RedisError("Connection failed"))
        mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
        mock_pipeline.__aexit__ = AsyncMock(return_value=None)
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)

        limiter = RateLimiter(redis_client=mock_client, limit=10, enabled=True)
        result = await limiter.check("192.168.1.1")

        assert result.allowed is True  # Fail-open


class TestRateLimiterReset:
    """Tests for rate limit reset."""

    @pytest.mark.asyncio
    async def test_reset_success(self):
        """Test successful rate limit reset."""
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=1)

        limiter = RateLimiter(redis_client=mock_client, key_prefix="test")
        result = await limiter.reset("192.168.1.1")

        assert result is True
        mock_client.delete.assert_called_once_with("test:ratelimit:192.168.1.1")

    @pytest.mark.asyncio
    async def test_reset_no_client(self):
        """Test reset with no Redis client."""
        limiter = RateLimiter(redis_client=None)
        result = await limiter.reset("192.168.1.1")

        assert result is False

    @pytest.mark.asyncio
    async def test_reset_redis_error(self):
        """Test reset handles Redis error gracefully."""
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(side_effect=RedisError("Connection failed"))

        limiter = RateLimiter(redis_client=mock_client)
        result = await limiter.reset("192.168.1.1")

        assert result is False


class TestRateLimiterGetStatus:
    """Tests for getting rate limit status."""

    @pytest.mark.asyncio
    async def test_get_status_success(self):
        """Test getting rate limit status."""
        mock_client = MagicMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.get = MagicMock()
        mock_pipeline.ttl = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=["5", 30])  # count as string, ttl
        mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
        mock_pipeline.__aexit__ = AsyncMock(return_value=None)
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)

        limiter = RateLimiter(redis_client=mock_client, limit=10)
        status = await limiter.get_status("192.168.1.1")

        assert status["current_count"] == 5
        assert status["limit"] == 10
        assert status["remaining"] == 5
        assert status["ttl"] == 30

    @pytest.mark.asyncio
    async def test_get_status_no_client(self):
        """Test get_status with no Redis client."""
        limiter = RateLimiter(redis_client=None, limit=10)
        status = await limiter.get_status("192.168.1.1")

        assert status["current_count"] == 0
        assert status["limit"] == 10
        assert status["remaining"] == 10
        assert status["ttl"] == 0

    @pytest.mark.asyncio
    async def test_get_status_no_existing_key(self):
        """Test get_status when key doesn't exist."""
        mock_client = MagicMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.get = MagicMock()
        mock_pipeline.ttl = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=[None, -2])  # No key, negative ttl
        mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
        mock_pipeline.__aexit__ = AsyncMock(return_value=None)
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)

        limiter = RateLimiter(redis_client=mock_client, limit=10)
        status = await limiter.get_status("192.168.1.1")

        assert status["current_count"] == 0
        assert status["remaining"] == 10
        assert status["ttl"] == 0


class TestRateLimiterGlobalFunctions:
    """Tests for global rate limiter functions."""

    def test_get_set_rate_limiter(self):
        """Test global get/set functions."""
        from app.services.rate_limiter import get_rate_limiter, set_rate_limiter

        # Initially None
        original = get_rate_limiter()

        # Set a rate limiter
        limiter = RateLimiter()
        set_rate_limiter(limiter)
        assert get_rate_limiter() is limiter

        # Reset to None
        set_rate_limiter(None)
        assert get_rate_limiter() is None

        # Restore original state
        set_rate_limiter(original)
