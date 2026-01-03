# ADR-0012: Background Jobs with Celery

## Status

Proposed

## Date

2026-01-02

## Context

### The Problem: Synchronous Processing Bottleneck

Currently, image uploads are processed synchronously in the request-response cycle:

```
User Request ──► Upload ──► Validate ──► Store ──► [Response]
                                           │
                            ┌──────────────┴──────────────┐
                            │ All processing blocks here: │
                            │ • Thumbnail generation      │
                            │ • Checksum calculation      │
                            │ • Dimension extraction      │
                            │ • Deduplication check       │
                            └─────────────────────────────┘
```

**Real Impact on Users:**

| Task | Time | User Experience |
|------|------|-----------------|
| Upload 5MB image | ~500ms | Acceptable |
| + Generate 3 thumbnails | +2-3s | Slow |
| + Calculate SHA-256 | +200ms | Slow |
| + CNN deduplication | +1-2s | Very slow |
| **Total** | **4-6 seconds** | **Unacceptable** |

Users expect uploads to feel instant. Waiting 4-6 seconds for a single image upload is poor UX.

### The Solution: Asynchronous Processing

```
User Request ──► Upload ──► Validate ──► Store ──► [Response: 201 Created]
                                           │            │
                                           │      User gets response
                                           │      in ~500ms ✓
                                           ▼
                              ┌─────────────────────────┐
                              │   Background Queue      │
                              │   (Redis)               │
                              └───────────┬─────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
              [Thumbnail Job]      [Checksum Job]      [Dedupe Job]
                    │                     │                     │
                    ▼                     ▼                     ▼
              Save thumbnails      Update DB record      Find duplicates
```

**Now the user gets a response immediately**, and CPU-intensive work happens in the background.

## Decision

**Celery with Redis Broker** for background task processing.

### Why Celery?

| Option | Verdict | Reason |
|--------|---------|--------|
| **Celery + Redis** | ✅ Chosen | Mature, Redis already in stack, retries built-in |
| FastAPI BackgroundTasks | ❌ | No persistence, no retries, same process |
| Dramatiq | ❌ | Smaller community |
| arq | ❌ | Less mature |

### Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     Docker Compose                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────┐ │
│  │   FastAPI    │     │    Redis     │     │   MinIO    │ │
│  │   (API)      │◄───►│   (Broker +  │     │  (Storage) │ │
│  │              │     │    Cache)    │     │            │ │
│  └──────────────┘     └──────┬───────┘     └────────────┘ │
│         │                    │                     ▲       │
│         │                    │                     │       │
│         │              ┌─────▼─────┐               │       │
│         │              │  Celery   │───────────────┘       │
│         └─────────────►│  Worker   │                       │
│         (queue tasks)  │           │                       │
│                        └───────────┘                       │
│                                                            │
│  ┌──────────────┐                                         │
│  │  PostgreSQL  │◄──── (both API and Worker connect)      │
│  │  (Database)  │                                         │
│  └──────────────┘                                         │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## Implementation

### Task Example

```python
@celery_app.task(bind=True, max_retries=3)
def generate_thumbnails(self, image_id: str):
    image = get_image(image_id)
    for size in [(150, 150), (300, 300), (600, 600)]:
        thumbnail = resize(image, size)
        save_thumbnail(image_id, size, thumbnail)
    update_db(image_id, thumbnails_ready=True)
```

### Configuration

```python
# celeryconfig.py
broker_url = "redis://localhost:6379/1"
result_backend = "redis://localhost:6379/2"

# Safeguards
worker_max_memory_per_child = 200_000  # 200MB, restart after
worker_max_tasks_per_child = 100       # Prevent memory leaks
task_time_limit = 300                  # 5 min hard kill
task_soft_time_limit = 240             # 4 min soft limit
worker_prefetch_multiplier = 1         # Don't grab too many tasks
task_acks_late = True                  # Requeue on crash
result_expires = 3600                  # Cleanup after 1 hour
```

### Docker Compose

```yaml
celery-worker:
  build: ./backend
  command: celery -A app.celery_app worker --concurrency=4
  depends_on: [redis, postgres]
```

## Capacity & Limits

### Breaking Points

| Resource | Safe | Warning | Breaking |
|----------|------|---------|----------|
| Queue depth | <1,000 | 1,000-5,000 | >10,000 (Redis OOM) |
| Worker memory | <70% | 70-85% | >90% (OOM killer) |
| Task latency | <5 min | 5-15 min | >30 min |

### Concrete Breaking Scenario

```
1000 users upload simultaneously
→ 1000 thumbnail tasks queued
→ Worker processes 80/minute (4 workers × 20 tasks/min)
→ Queue depth: 1000 - 80 = 920 after 1 min
→ Time to clear: 1000/80 = 12.5 minutes
→ Last user waits 12+ minutes for thumbnails ❌
```

### MVP Settings (2GB RAM server)

| Setting | Value |
|---------|-------|
| `--concurrency` | 4 |
| `worker_max_memory_per_child` | 200MB |
| Queue alert threshold | 500 |

**Safe envelope:** ~50-100 concurrent uploads, queue <500 tasks

### Horizontal Scaling

```
┌──────────────────────────────────────────────────────────────────┐
│  HORIZONTAL SCALING                                              │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Worker 1   │  │  Worker 2   │  │  Worker 3   │  ...         │
│  │ concurrency │  │ concurrency │  │ concurrency │              │
│  │     =4      │  │     =4      │  │     =4      │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          ▼                                       │
│                    ┌──────────┐                                  │
│                    │  Redis   │                                  │
│                    │ (Broker) │                                  │
│                    └──────────┘                                  │
└──────────────────────────────────────────────────────────────────┘
```

```bash
docker-compose up --scale celery-worker=5
```

## Consequences

| Type | Impact |
|------|--------|
| ✅ Positive | Upload <1s, thumbnails async, workers scale independently |
| ❌ Negative | Extra process to manage, eventual consistency |
| ➡️ Neutral | ~150 lines code, 1 new docker service |

## Monitoring

```bash
# Flower web UI
celery -A app.celery_app flower --port=5555

# CLI
celery -A app.celery_app inspect active
```

## References

- [Celery Docs](https://docs.celeryq.dev/)
- [ADR-0009: Redis Caching](./0009-redis-caching-for-metadata.md)
