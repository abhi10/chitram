# ADR-0009: Use Redis for Image Metadata Caching

## Status

Accepted

## Date

2026-01-02

## Context

As the Image Hosting API grows, repeated database queries for frequently accessed image metadata create unnecessary load on PostgreSQL. We need a caching layer to:
- Reduce database query latency
- Decrease PostgreSQL load for read-heavy workloads
- Learn distributed caching patterns (Cache-Aside/Lazy Loading)
- Prepare for Phase 2 rate limiting (which also requires Redis)
- Support horizontal scaling with shared cache across instances

## Options Considered

### Option 1: Redis
- **Pros:**
  - Industry standard for caching
  - Excellent async Python support (`redis-py` with `hiredis`)
  - Sub-millisecond latency
  - TTL support built-in
  - Also needed for rate limiting and future session storage
  - Simple key-value model fits our use case
  - Persistence options (AOF/RDB) if needed
- **Cons:**
  - Additional infrastructure component
  - Requires connection management
  - Cache invalidation complexity
  - Memory-based (costs at scale)

### Option 2: In-Memory (Python dict / LRU cache)
- **Pros:**
  - Zero infrastructure
  - Extremely simple to implement
  - No network latency
- **Cons:**
  - Not shared across multiple API instances
  - Lost on process restart
  - Memory tied to application process
  - Doesn't scale horizontally
  - Inconsistent cache state across instances

### Option 3: Memcached
- **Pros:**
  - Simple, battle-tested
  - Multi-threaded (good for multi-core)
  - Lower memory overhead per key
- **Cons:**
  - No persistence
  - No native data structures (only strings)
  - Would need separate solution for rate limiting
  - Less feature-rich than Redis
  - Smaller ecosystem

### Option 4: Database Query Caching (PostgreSQL pg_stat_statements)
- **Pros:**
  - No additional infrastructure
  - Transparent to application
- **Cons:**
  - Limited control over what's cached
  - Still hits the database
  - Doesn't reduce connection overhead

## Decision

Use **Redis** for caching image metadata with the **Cache-Aside (Lazy Loading)** pattern.

## Rationale

1. **Multi-purpose** - Redis will be used for caching, rate limiting, and potentially session storage
2. **Horizontal scaling** - Shared cache works across multiple API instances
3. **Industry standard** - Learning Redis is valuable for production systems
4. **Graceful degradation** - System continues working when Redis is unavailable
5. **Feature-rich** - TTL, pub/sub, data structures enable future features
6. **Async support** - `redis-py` has excellent asyncio support
7. **Performance** - `hiredis` C parser provides optimal performance

## Implementation Details

### Cache-Aside Pattern
```python
async def get_by_id(image_id: str) -> Image | None:
    # 1. Check cache first
    cached = await cache.get(f"chitram:image:{image_id}")
    if cached:
        return Image(**cached)  # Cache HIT

    # 2. Cache MISS - fetch from DB
    image = await db.get(Image, image_id)

    # 3. Populate cache for next request
    if image:
        await cache.setex(key, TTL, serialize(image))

    return image
```

### Key Design
- Prefix: `chitram:image:{uuid}` (namespaced to avoid collisions)
- TTL: 3600 seconds (1 hour) by default, configurable
- Value: JSON-serialized image metadata

### Cache Invalidation
- **On DELETE**: Explicitly invalidate cache entry
- **On UPDATE**: Invalidate cache entry (write-invalidate, not write-through)
- **TTL expiry**: Automatic cleanup of stale entries

### Observability
- `X-Cache` response header: `HIT`, `MISS`, or `DISABLED`
- Health endpoint reports cache status
- Debug logging when `CACHE_DEBUG=true`

## Consequences

### Positive
- Reduced database load (80%+ cache hit rate expected for hot images)
- Lower p95 latency for metadata reads (< 50ms with cache hit)
- Prepares infrastructure for rate limiting
- Learn distributed caching patterns
- Graceful degradation maintains availability

### Negative
- Additional infrastructure dependency
- Cache invalidation adds complexity
- Potential stale data within TTL window
- Memory costs for Redis instance

### Neutral
- Configuration via environment variables (12-factor app)
- Cache disabled by default in tests
- Integration tests require running Redis (auto-skip otherwise)

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_PASSWORD` | `None` | Redis password (if auth enabled) |
| `REDIS_DB` | `0` | Redis database number |
| `CACHE_ENABLED` | `true` | Enable/disable caching |
| `CACHE_TTL_SECONDS` | `3600` | Cache entry TTL |
| `CACHE_KEY_PREFIX` | `chitram` | Key namespace prefix |
| `CACHE_DEBUG` | `false` | Log cache operations |

## Validation Checklist

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | Start app with Redis | Log: "Redis cache connected" |
| 2 | Upload image | Cache key created |
| 3 | GET metadata (first) | X-Cache: MISS, DB queried |
| 4 | GET metadata (second) | X-Cache: HIT, no DB query |
| 5 | DELETE image | Cache key invalidated |
| 6 | Stop Redis, GET metadata | Fallback to DB, no error |
| 7 | Health check | `"cache": "connected"` or `"disconnected"` |

## References

- [requirements-phase2.md](../.../requirements/phase2.md) - FR-2.2 Redis Caching requirements
- [phase-2-performance.md](../architecture/phase-2-performance.md) - Architecture overview
- [Redis Documentation](https://redis.io/docs/)
- [redis-py Documentation](https://redis-py.readthedocs.io/)
- [Cache-Aside Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/cache-aside)
