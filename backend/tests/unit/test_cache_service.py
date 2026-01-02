"""Unit tests for cache service with mocked Redis."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.services.cache_service import CacheService


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.info = AsyncMock(
        return_value={
            "keyspace_hits": 100,
            "keyspace_misses": 20,
            "total_connections_received": 50,
        }
    )
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def sample_image_metadata():
    """Sample image metadata for testing."""
    return {
        "id": "test-uuid-1234",
        "filename": "test.jpg",
        "storage_key": "abc123.jpg",
        "content_type": "image/jpeg",
        "file_size": 1024,
        "upload_ip": "127.0.0.1",
        "width": 100,
        "height": 100,
        "created_at": datetime.now(UTC).isoformat(),
    }


class TestCacheServiceConnection:
    """Tests for cache connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_redis):
        """Test successful Redis connection."""
        with patch("app.services.cache_service.redis.Redis", return_value=mock_redis):
            cache = CacheService(host="localhost", port=6379)
            result = await cache.connect()

            assert result is True
            mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test Redis connection failure."""
        from redis.exceptions import RedisError

        mock = AsyncMock()
        mock.ping = AsyncMock(side_effect=RedisError("Connection refused"))

        with patch("app.services.cache_service.redis.Redis", return_value=mock):
            cache = CacheService(host="localhost", port=6379)
            result = await cache.connect()

            assert result is False

    @pytest.mark.asyncio
    async def test_connect_disabled(self):
        """Test cache disabled by configuration."""
        with patch("app.services.cache_service.settings") as mock_settings:
            mock_settings.cache_enabled = False
            mock_settings.cache_debug = False
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.redis_password = None
            mock_settings.redis_db = 0
            mock_settings.cache_key_prefix = "chitram"
            mock_settings.cache_ttl_seconds = 3600

            cache = CacheService()
            cache._enabled = False
            result = await cache.connect()

            assert result is False

    @pytest.mark.asyncio
    async def test_is_connected_true(self, mock_redis):
        """Test is_connected returns True when Redis is healthy."""
        with patch("app.services.cache_service.redis.Redis", return_value=mock_redis):
            cache = CacheService()
            await cache.connect()

            result = await cache.is_connected()
            assert result is True

    @pytest.mark.asyncio
    async def test_is_connected_false_no_client(self):
        """Test is_connected returns False when no client."""
        cache = CacheService()
        result = await cache.is_connected()
        assert result is False

    @pytest.mark.asyncio
    async def test_close(self, mock_redis):
        """Test closing Redis connection."""
        with patch("app.services.cache_service.redis.Redis", return_value=mock_redis):
            cache = CacheService()
            await cache.connect()
            await cache.close()

            mock_redis.close.assert_called_once()
            assert cache._client is None


class TestCacheServiceOperations:
    """Tests for cache get/set/invalidate operations."""

    @pytest.mark.asyncio
    async def test_get_image_metadata_hit(self, mock_redis, sample_image_metadata):
        """Test cache hit returns metadata."""
        mock_redis.get = AsyncMock(return_value=json.dumps(sample_image_metadata))

        with patch("app.services.cache_service.redis.Redis", return_value=mock_redis):
            cache = CacheService(key_prefix="test")
            await cache.connect()

            result = await cache.get_image_metadata("test-uuid-1234")

            assert result is not None
            assert result["id"] == "test-uuid-1234"
            assert result["filename"] == "test.jpg"
            mock_redis.get.assert_called_once_with("test:image:test-uuid-1234")

    @pytest.mark.asyncio
    async def test_get_image_metadata_miss(self, mock_redis):
        """Test cache miss returns None."""
        mock_redis.get = AsyncMock(return_value=None)

        with patch("app.services.cache_service.redis.Redis", return_value=mock_redis):
            cache = CacheService(key_prefix="test")
            await cache.connect()

            result = await cache.get_image_metadata("nonexistent")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_image_metadata_no_client(self):
        """Test get returns None when not connected."""
        cache = CacheService()
        result = await cache.get_image_metadata("test-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_image_metadata_invalid_json(self, mock_redis):
        """Test handling of invalid JSON in cache."""
        mock_redis.get = AsyncMock(return_value="not-valid-json")

        with patch("app.services.cache_service.redis.Redis", return_value=mock_redis):
            cache = CacheService(key_prefix="test")
            await cache.connect()

            result = await cache.get_image_metadata("test-id")

            assert result is None
            # Should attempt to delete invalid entry
            mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_image_metadata_success(self, mock_redis, sample_image_metadata):
        """Test successful cache set."""
        with patch("app.services.cache_service.redis.Redis", return_value=mock_redis):
            cache = CacheService(key_prefix="test", default_ttl=3600)
            await cache.connect()

            result = await cache.set_image_metadata("test-uuid-1234", sample_image_metadata)

            assert result is True
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert call_args[0][0] == "test:image:test-uuid-1234"
            assert call_args[0][1] == 3600

    @pytest.mark.asyncio
    async def test_set_image_metadata_custom_ttl(self, mock_redis, sample_image_metadata):
        """Test cache set with custom TTL."""
        with patch("app.services.cache_service.redis.Redis", return_value=mock_redis):
            cache = CacheService(key_prefix="test")
            await cache.connect()

            await cache.set_image_metadata("test-id", sample_image_metadata, ttl=7200)

            call_args = mock_redis.setex.call_args
            assert call_args[0][1] == 7200

    @pytest.mark.asyncio
    async def test_set_image_metadata_no_client(self, sample_image_metadata):
        """Test set returns False when not connected."""
        cache = CacheService()
        result = await cache.set_image_metadata("test-id", sample_image_metadata)
        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_image_success(self, mock_redis):
        """Test successful cache invalidation."""
        with patch("app.services.cache_service.redis.Redis", return_value=mock_redis):
            cache = CacheService(key_prefix="test")
            await cache.connect()

            result = await cache.invalidate_image("test-uuid-1234")

            assert result is True
            mock_redis.delete.assert_called_once_with("test:image:test-uuid-1234")

    @pytest.mark.asyncio
    async def test_invalidate_image_no_client(self):
        """Test invalidate returns False when not connected."""
        cache = CacheService()
        result = await cache.invalidate_image("test-id")
        assert result is False


class TestCacheServiceStats:
    """Tests for cache statistics."""

    @pytest.mark.asyncio
    async def test_get_stats_success(self, mock_redis):
        """Test getting cache statistics."""
        with patch("app.services.cache_service.redis.Redis", return_value=mock_redis):
            cache = CacheService()
            await cache.connect()

            stats = await cache.get_stats()

            assert stats is not None
            assert stats["keyspace_hits"] == 100
            assert stats["keyspace_misses"] == 20
            assert stats["total_connections"] == 50

    @pytest.mark.asyncio
    async def test_get_stats_no_client(self):
        """Test stats returns None when not connected."""
        cache = CacheService()
        stats = await cache.get_stats()
        assert stats is None


class TestCacheServiceKeyGeneration:
    """Tests for cache key generation."""

    def test_make_key_default_prefix(self):
        """Test key generation with default prefix."""
        cache = CacheService(key_prefix="chitram")
        key = cache._make_key("image", "abc123")
        assert key == "chitram:image:abc123"

    def test_make_key_custom_prefix(self):
        """Test key generation with custom prefix."""
        cache = CacheService(key_prefix="myapp")
        key = cache._make_key("image", "xyz789")
        assert key == "myapp:image:xyz789"
