"""Integration tests for Redis cache service.

These tests require a running Redis instance.
Tests are automatically skipped if Redis is not available.
"""

import os
from datetime import UTC, datetime

import pytest

from app.services.cache_service import CacheService

# Redis connection settings for tests
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


async def redis_available() -> bool:
    """Check if Redis is available for testing."""
    try:
        cache = CacheService(
            host=REDIS_HOST,
            port=REDIS_PORT,
            key_prefix="test",
        )
        connected = await cache.connect()
        if connected:
            await cache.close()
        return connected
    except Exception:
        return False


@pytest.fixture
async def cache_service():
    """Create a cache service connected to real Redis."""
    cache = CacheService(
        host=REDIS_HOST,
        port=REDIS_PORT,
        key_prefix="test_chitram",
        default_ttl=60,  # Short TTL for tests
    )
    cache._enabled = True
    connected = await cache.connect()
    if not connected:
        pytest.skip("Redis not available")

    yield cache

    # Cleanup: delete all test keys
    if cache._client:
        # Get all test keys and delete them
        try:
            keys = []
            async for key in cache._client.scan_iter("test_chitram:*"):
                keys.append(key)
            if keys:
                await cache._client.delete(*keys)
        except Exception:
            pass

    await cache.close()


@pytest.fixture
def sample_metadata():
    """Sample image metadata for testing."""
    return {
        "id": "test-integration-uuid",
        "filename": "integration_test.jpg",
        "storage_key": "integration123.jpg",
        "content_type": "image/jpeg",
        "file_size": 2048,
        "upload_ip": "192.168.1.1",
        "width": 200,
        "height": 150,
        "created_at": datetime.now(UTC).isoformat(),
    }


class TestRedisIntegration:
    """Integration tests for Redis cache operations."""

    @pytest.mark.asyncio
    async def test_connection(self, cache_service):
        """Test Redis connection is established."""
        assert await cache_service.is_connected() is True

    @pytest.mark.asyncio
    async def test_set_and_get_metadata(self, cache_service, sample_metadata):
        """Test setting and getting metadata from Redis."""
        image_id = sample_metadata["id"]

        # Set metadata
        set_result = await cache_service.set_image_metadata(image_id, sample_metadata)
        assert set_result is True

        # Get metadata
        retrieved = await cache_service.get_image_metadata(image_id)
        assert retrieved is not None
        assert retrieved["id"] == image_id
        assert retrieved["filename"] == "integration_test.jpg"
        assert retrieved["file_size"] == 2048

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_service):
        """Test cache miss returns None."""
        result = await cache_service.get_image_metadata("nonexistent-uuid")
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_existing(self, cache_service, sample_metadata):
        """Test invalidating an existing cache entry."""
        image_id = sample_metadata["id"]

        # Set metadata
        await cache_service.set_image_metadata(image_id, sample_metadata)

        # Verify it exists
        assert await cache_service.get_image_metadata(image_id) is not None

        # Invalidate
        invalidate_result = await cache_service.invalidate_image(image_id)
        assert invalidate_result is True

        # Verify it's gone
        assert await cache_service.get_image_metadata(image_id) is None

    @pytest.mark.asyncio
    async def test_invalidate_nonexistent(self, cache_service):
        """Test invalidating a nonexistent entry succeeds."""
        result = await cache_service.invalidate_image("never-existed")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_stats(self, cache_service):
        """Test getting cache statistics."""
        stats = await cache_service.get_stats()
        assert stats is not None
        assert "keyspace_hits" in stats
        assert "keyspace_misses" in stats

    @pytest.mark.asyncio
    async def test_custom_ttl(self, cache_service, sample_metadata):
        """Test setting metadata with custom TTL."""
        image_id = "ttl-test-uuid"
        sample_metadata["id"] = image_id

        # Set with very short TTL
        await cache_service.set_image_metadata(image_id, sample_metadata, ttl=1)

        # Should exist immediately
        assert await cache_service.get_image_metadata(image_id) is not None

        # Wait for TTL to expire (add small buffer)
        import asyncio

        await asyncio.sleep(1.5)

        # Should be gone
        result = await cache_service.get_image_metadata(image_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_key_namespacing(self, cache_service, sample_metadata):
        """Test that keys are properly namespaced."""
        image_id = sample_metadata["id"]
        await cache_service.set_image_metadata(image_id, sample_metadata)

        # Check the actual key in Redis
        expected_key = f"{cache_service.key_prefix}:image:{image_id}"
        exists = await cache_service._client.exists(expected_key)
        assert exists == 1

    @pytest.mark.asyncio
    async def test_multiple_images(self, cache_service):
        """Test caching multiple images."""
        images = [
            {"id": f"multi-test-{i}", "filename": f"image{i}.jpg", "file_size": i * 100}
            for i in range(5)
        ]

        # Set all
        for img in images:
            await cache_service.set_image_metadata(img["id"], img)

        # Verify all exist
        for img in images:
            retrieved = await cache_service.get_image_metadata(img["id"])
            assert retrieved is not None
            assert retrieved["id"] == img["id"]

        # Invalidate one
        await cache_service.invalidate_image("multi-test-2")

        # Verify only that one is gone
        assert await cache_service.get_image_metadata("multi-test-2") is None
        assert await cache_service.get_image_metadata("multi-test-0") is not None
        assert await cache_service.get_image_metadata("multi-test-4") is not None


class TestRedisGracefulDegradation:
    """Test graceful degradation when Redis is unavailable."""

    @pytest.mark.asyncio
    async def test_operations_without_connection(self):
        """Test that operations fail gracefully without connection."""
        cache = CacheService(host="nonexistent-host", port=6379)
        # Don't connect

        # All operations should return None/False without errors
        assert await cache.get_image_metadata("any-id") is None
        assert await cache.set_image_metadata("any-id", {"data": "test"}) is False
        assert await cache.invalidate_image("any-id") is False
        assert await cache.get_stats() is None

    @pytest.mark.asyncio
    async def test_failed_connection_graceful(self):
        """Test that failed connection is handled gracefully."""
        cache = CacheService(host="nonexistent-host", port=12345)
        result = await cache.connect()
        assert result is False

        # Should still work (just return None/False)
        assert await cache.get_image_metadata("test") is None
