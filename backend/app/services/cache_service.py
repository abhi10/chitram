"""Cache service - Redis caching layer with graceful degradation."""

import json
import logging
from typing import Any

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheService:
    """
    Cache service using Redis for storing image metadata.

    Implements Cache-Aside (Lazy Loading) pattern:
    - Check cache first on read
    - Load from DB on cache miss
    - Populate cache after DB read

    Graceful Degradation:
    - If Redis is unavailable, operations return None/False
    - System continues to function using database
    """

    def __init__(
        self,
        host: str = settings.redis_host,
        port: int = settings.redis_port,
        password: str | None = settings.redis_password,
        db: int = settings.redis_db,
        key_prefix: str = settings.cache_key_prefix,
        default_ttl: int = settings.cache_ttl_seconds,
    ):
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self._debug = settings.cache_debug
        self._enabled = settings.cache_enabled
        self._client: redis.Redis | None = None
        self._connection_params = {
            "host": host,
            "port": port,
            "password": password,
            "db": db,
            "decode_responses": True,
        }

    async def connect(self) -> bool:
        """
        Establish connection to Redis.

        Returns:
            True if connected successfully, False otherwise
        """
        if not self._enabled:
            self._log_debug("Cache disabled by configuration")
            return False

        try:
            self._client = redis.Redis(**self._connection_params)
            # Test connection
            await self._client.ping()
            self._log_debug("Connected to Redis")
            return True
        except RedisError as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self._client = None
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
            self._log_debug("Redis connection closed")

    async def is_connected(self) -> bool:
        """Check if Redis is connected and healthy."""
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except RedisError:
            return False

    def _make_key(self, key_type: str, key_id: str) -> str:
        """Generate namespaced cache key."""
        return f"{self.key_prefix}:{key_type}:{key_id}"

    def _log_debug(self, message: str) -> None:
        """Log debug message if cache_debug is enabled."""
        if self._debug:
            logger.info(f"[CACHE] {message}")

    async def get_image_metadata(self, image_id: str) -> dict[str, Any] | None:
        """
        Get cached image metadata.

        Args:
            image_id: The image UUID

        Returns:
            Cached metadata dict or None if not found/error
        """
        if not self._client:
            return None

        key = self._make_key("image", image_id)
        try:
            data = await self._client.get(key)
            if data:
                self._log_debug(f"CACHE HIT: {key}")
                return json.loads(data)
            self._log_debug(f"CACHE MISS: {key}")
            return None
        except RedisError as e:
            logger.warning(f"Redis get error for {key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in cache for {key}: {e}")
            # Invalid data - delete it
            await self.invalidate_image(image_id)
            return None

    async def set_image_metadata(
        self,
        image_id: str,
        metadata: dict[str, Any],
        ttl: int | None = None,
    ) -> bool:
        """
        Cache image metadata.

        Args:
            image_id: The image UUID
            metadata: Image metadata dict to cache
            ttl: Time to live in seconds (default: cache_ttl_seconds)

        Returns:
            True if cached successfully, False otherwise
        """
        if not self._client:
            return False

        key = self._make_key("image", image_id)
        ttl = ttl or self.default_ttl

        try:
            await self._client.setex(key, ttl, json.dumps(metadata, default=str))
            self._log_debug(f"CACHE SET: {key} (TTL: {ttl}s)")
            return True
        except RedisError as e:
            logger.warning(f"Redis set error for {key}: {e}")
            return False

    async def invalidate_image(self, image_id: str) -> bool:
        """
        Remove image metadata from cache.

        Args:
            image_id: The image UUID

        Returns:
            True if key was deleted or didn't exist, False on error
        """
        if not self._client:
            return False

        key = self._make_key("image", image_id)
        try:
            await self._client.delete(key)
            self._log_debug(f"CACHE INVALIDATE: {key}")
            return True
        except RedisError as e:
            logger.warning(f"Redis delete error for {key}: {e}")
            return False

    async def get_stats(self) -> dict[str, Any] | None:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats or None if unavailable
        """
        if not self._client:
            return None

        try:
            info = await self._client.info("stats")
            return {
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_connections": info.get("total_connections_received", 0),
            }
        except RedisError as e:
            logger.warning(f"Failed to get Redis stats: {e}")
            return None


# Global cache instance (initialized in main.py lifespan)
_cache_service: CacheService | None = None


def get_cache() -> CacheService | None:
    """Get the global cache service instance."""
    return _cache_service


def set_cache(cache: CacheService | None) -> None:
    """Set the global cache service instance."""
    global _cache_service
    _cache_service = cache
