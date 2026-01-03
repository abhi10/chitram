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
        mock_pipeline.execute = AsyncMock(return_value=[5, True, 45])
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


class TestRateLimiterGlobalFunctions:
    """Tests for global rate limiter functions."""

    def test_get_set_rate_limiter(self):
        """Test global get/set functions."""
        from app.services.rate_limiter import get_rate_limiter, set_rate_limiter

        original = get_rate_limiter()

        limiter = RateLimiter()
        set_rate_limiter(limiter)
        assert get_rate_limiter() is limiter

        set_rate_limiter(None)
        assert get_rate_limiter() is None

        set_rate_limiter(original)
