# ADR-0012: Background Tasks Strategy

## Status

Accepted (Revised 2026-01-03)

## Date

2026-01-02 (Original), 2026-01-03 (Revised)

## Context

### The Problem: Post-Upload Processing

After an image is uploaded, we want to generate thumbnails for faster gallery loading. The question is: how complex should this infrastructure be?

### Original Proposal: Celery + Redis

The original ADR proposed Celery with Redis as message broker. Analysis revealed this was overengineering:

| Scenario | Upload Time | User Experience |
|----------|-------------|-----------------|
| Current (no thumbnails) | ~500ms | Good |
| + Thumbnail generation | +2-3s sync | Bad |
| + Thumbnail async (any method) | ~500ms | Good |

**Key Insight:** Any async solution solves the UX problem. Celery's benefits (retries, distributed workers, persistence) aren't needed until we have:
- Multiple thumbnail sizes
- High volume (1000+ uploads/minute)
- Need for job persistence across restarts

### Evolutionary Approach

| Phase | Solution | When to Use |
|-------|----------|-------------|
| **Phase 2B** | FastAPI BackgroundTasks | Simple, no infra, good for MVP |
| **Phase 4** | Celery + Redis | When scale requires distributed workers |

## Decision

**Phase 2B: Use FastAPI BackgroundTasks** for thumbnail generation.

### Why FastAPI BackgroundTasks?

| Aspect | FastAPI BackgroundTasks | Celery |
|--------|-------------------------|--------|
| Dependencies | Built-in (zero) | celery, redis, flower |
| Infrastructure | None | Redis broker, worker process |
| Complexity | ~10 lines | ~150 lines + docker service |
| Retries | No | Yes |
| Persistence | No (lost on restart) | Yes |
| Distributed | No (same process) | Yes |
| **Fit for Phase 2B** | ✅ Perfect | ❌ Overkill |

### Implementation

```python
from fastapi import BackgroundTasks

def generate_thumbnail(image_id: str, storage: StorageService, db: AsyncSession):
    """Generate 300px thumbnail after upload."""
    try:
        # Load original image
        data = await storage.get(f"{image_id}.jpg")

        # Resize to 300px max dimension
        img = Image.open(io.BytesIO(data))
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)

        # Save thumbnail
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        thumb_key = f"thumbs/{image_id}_300.jpg"
        await storage.save(thumb_key, buffer.getvalue(), "image/jpeg")

        # Update database
        image = await db.get(Image, image_id)
        image.thumbnail_key = thumb_key
        await db.commit()

    except Exception as e:
        logger.warning(f"Thumbnail generation failed for {image_id}: {e}")
        # Graceful degradation - original image still works

@router.post("/upload")
async def upload_image(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    service: ImageService = Depends(get_image_service),
):
    image, delete_token = await service.upload(file)

    # Queue thumbnail generation - runs after response
    background_tasks.add_task(
        generate_thumbnail,
        image.id,
        service.storage,
        service.db,
    )

    return ImageUploadResponse(
        id=image.id,
        thumbnail_ready=False,  # Will be True after background task
        ...
    )
```

### What This Enables

```
User uploads image
    │
    ├──► Response in ~500ms (thumbnail_ready=False)
    │
    └──► Background: Generate thumbnail (~2s)
              │
              └──► DB update: thumbnail_key set, thumbnail_ready=True
```

### API Changes

```python
# GET /api/v1/images/{id}
{
    "id": "abc123",
    "filename": "photo.jpg",
    "thumbnail_ready": true,  # New field
    "thumbnail_url": "/api/v1/images/abc123/thumbnail"  # New field
}

# GET /api/v1/images/{id}/thumbnail
# Returns 300px thumbnail, or 404 if not ready
```

## Consequences

### Positive
- Zero new dependencies
- No infrastructure changes
- Simple implementation (~30 lines)
- Upload response time unchanged (~500ms)
- Thumbnails available for UI phase

### Negative
- No retries (thumbnail may fail silently)
- Tasks lost on server restart
- Not distributed (single process)

### Neutral
- These limitations are acceptable for MVP
- Can migrate to Celery in Phase 4 if needed

## Phase 4: When to Upgrade to Celery

Upgrade to Celery when ANY of these are true:
- Need multiple thumbnail sizes (150, 300, 600px)
- Upload volume exceeds 100/minute sustained
- Need job persistence across restarts
- Need distributed workers (multiple servers)
- Need checksum calculation
- Need image deduplication

### Phase 4 Celery Scope (Deferred)

```yaml
# docker-compose.yml (Phase 4)
celery-worker:
  build: ./backend
  command: celery -A app.celery_app worker --concurrency=4
  depends_on: [redis, postgres]
```

Features deferred to Phase 4:
- Celery with Redis broker
- Multiple thumbnail sizes
- Retry with exponential backoff
- Checksum calculation (SHA-256)
- Job monitoring (Flower)
- Image deduplication

## References

- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Celery Docs](https://docs.celeryq.dev/) (for Phase 4)
- [ADR-0009: Redis Caching](./0009-redis-caching-for-metadata.md)
