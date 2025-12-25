# Phase 2: Performance Optimization

**Status:** ⏸️ Not Started
**Prerequisites:** Phase 1 validated, Phase 1.5 complete
**Branch:** `feature/phase-2` (to be created)

---

## Learning Objectives

- Implement caching layers (local → distributed)
- Understand cache invalidation strategies
- Learn message queue patterns for async processing
- Implement indexes for fast lookups

---

## Architecture

```
                              ┌──────────────┐
                              │    Client    │
                              └──────┬───────┘
                                     │
                              ┌──────▼───────┐
                              │    Nginx     │ ← Static file serving
                              │   (Proxy)    │   Response caching
                              └──────┬───────┘
                                     │
                              ┌──────▼───────┐
                              │   FastAPI    │
                              │     App      │
                              └──────┬───────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          ▼                          ▼                          ▼
   ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
   │   Redis     │           │ PostgreSQL  │           │   Redis     │
   │   Cache     │           │  + Indexes  │           │   Queue     │
   │             │           │             │           │             │
   │ - Metadata  │           │ - B-tree    │           │ - Thumbnails│
   │ - Hot images│           │ - Hash      │           │ - Cleanup   │
   └─────────────┘           └─────────────┘           └─────────────┘
                                                              │
                                                              ▼
                                                       ┌─────────────┐
                                                       │   Worker    │
                                                       │  Process(es)│
                                                       └─────────────┘
```

---

## New Components

### 1. Redis Cache (Cache-Aside Pattern)

```python
class CacheService:
    async def get_image_metadata(self, image_id: str) -> dict | None:
        # Try cache first
        cached = await self.redis.get(f"image:{image_id}")
        if cached:
            return json.loads(cached)

        # Cache miss - fetch from DB
        image = await self.db.get_image(image_id)
        if image:
            await self.redis.setex(
                f"image:{image_id}",
                ttl=3600,  # 1 hour
                value=json.dumps(image.to_dict())
            )
        return image
```

**Cache Invalidation Strategies:**
- Time-based (TTL) - Simple, eventual consistency
- Write-through - Update cache on every write
- Event-based - Pub/sub for invalidation

### 2. Message Queue (Background Jobs)

```python
# Using RQ (simpler) or Celery
@task
def process_uploaded_image(image_id: str):
    image = get_image(image_id)

    # Generate thumbnails
    generate_thumbnail(image, size=(150, 150))
    generate_thumbnail(image, size=(300, 300))

    # Extract EXIF metadata
    extract_exif_metadata(image)
```

### 3. Database Indexes

```sql
-- B-tree: Range queries
CREATE INDEX idx_images_created_at ON images(created_at);

-- Hash: Exact match (O(1))
CREATE INDEX idx_images_checksum ON images USING hash(checksum);

-- Partial: Only relevant rows
CREATE INDEX idx_images_public ON images(created_at) WHERE is_public = true;
```

### 4. Nginx Reverse Proxy

```nginx
location /api/v1/images/ {
    proxy_pass http://fastapi;
    proxy_cache images_cache;
    proxy_cache_valid 200 1h;
    proxy_cache_lock on;  # Collapse identical requests
}
```

---

## New Dependencies

```
redis>=5.2.0            # Caching
hiredis>=3.0.0          # C parser for performance
rq>=2.0.0               # Simple task queue (or celery)
pillow>=11.0.0          # Image processing
minio>=7.2.0            # S3-compatible storage
```

---

## Deliverables

- [ ] Redis caching for metadata
- [ ] Background job processing (thumbnails)
- [ ] Nginx reverse proxy setup
- [ ] Database indexes optimized
- [ ] Cache invalidation strategy
- [ ] MinIO storage backend

---

## Metrics to Track

| Metric | Tool | Purpose |
|--------|------|---------|
| Cache hit ratio | Redis INFO | Measure cache effectiveness |
| Queue depth | RQ/Celery | Identify processing bottlenecks |
| P95 response time | Prometheus | Performance baseline |
| DB query time | pg_stat_statements | Identify slow queries |

---

**Document Version:** 1.0
**Last Updated:** 2025-12-24
