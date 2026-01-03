# ADR-0010: Concurrency Control for Uploads

## Status

Proposed

## Date

2025-01-02

## Context

The image hosting API allows users to upload images up to 5MB each. Without concurrency control, the server is vulnerable to resource exhaustion during traffic spikes:

| Scenario | Impact |
|----------|--------|
| 100 simultaneous uploads × 5MB | 500MB memory spike |
| CPU saturation from parallel processing | All requests slow down |
| Database connection pool exhaustion | Requests fail with connection errors |

**Key distinction from rate limiting:**
- **Rate Limiting** (ADR pending): Per-client throttling (e.g., 10 requests/minute/IP) - prevents abuse
- **Concurrency Control**: Per-server resource protection (e.g., 10 simultaneous uploads) - prevents overload

A client within rate limits can still contribute to server overload if many clients upload simultaneously.

## Options Considered

### Option 1: asyncio.Semaphore (in-memory)

```python
upload_semaphore = asyncio.Semaphore(10)

async def upload_image(...):
    async with upload_semaphore:
        # Only 10 uploads processed concurrently
        await process_upload(file)
```

- **Pros:** Simple, no external dependencies, zero latency overhead
- **Cons:** Per-process only (not shared across workers), lost on restart

### Option 2: Redis-based distributed semaphore

```python
async with redis_semaphore("uploads", limit=10, timeout=30):
    await process_upload(file)
```

- **Pros:** Shared across all workers/instances, survives restarts
- **Cons:** Network latency, Redis dependency, complexity (lock expiration, cleanup)

### Option 3: Database-based locking

```python
async with db_advisory_lock("upload_slot"):
    await process_upload(file)
```

- **Pros:** Uses existing PostgreSQL, ACID guarantees
- **Cons:** Database load, connection consumption, slower than Redis

### Option 4: No concurrency control (status quo)

- **Pros:** No implementation effort
- **Cons:** Server vulnerable to resource exhaustion, unpredictable behavior under load

## Decision

**Option 1: asyncio.Semaphore** for Phase 2.

For a single-instance MVP, in-memory semaphore provides adequate protection with minimal complexity. If we scale to multiple workers/instances, we can migrate to Option 2 (Redis-based).

### Implementation Details

1. **Semaphore initialization** in `main.py` lifespan
2. **Configurable limit** via `UPLOAD_CONCURRENCY_LIMIT` (default: 10)
3. **Timeout handling**: Return 503 Service Unavailable if wait exceeds threshold
4. **Health endpoint**: Report current concurrency usage

```python
# config.py
upload_concurrency_limit: int = 10
upload_concurrency_timeout: float = 30.0  # seconds

# main.py lifespan
app.state.upload_semaphore = asyncio.Semaphore(settings.upload_concurrency_limit)

# api/images.py
try:
    async with asyncio.timeout(settings.upload_concurrency_timeout):
        async with request.app.state.upload_semaphore:
            # Process upload
except asyncio.TimeoutError:
    raise HTTPException(503, "Server busy, try again later")
```

## Rationale

1. **Simplicity**: asyncio.Semaphore is built-in, well-tested, zero external dependencies
2. **Performance**: No network round-trip, microsecond-level overhead
3. **Sufficient for MVP**: Single-instance deployment doesn't need distributed locking
4. **Migration path**: Clear upgrade path to Redis if needed for horizontal scaling
5. **Fail-safe**: If semaphore is exhausted, requests queue (with timeout) rather than crash

## Consequences

### Positive
- Predictable resource usage under load (memory, CPU, DB connections)
- Graceful degradation (503) instead of crashes or timeouts
- Simple to understand and debug
- No additional infrastructure

### Negative
- Not shared across multiple uvicorn workers (use `--workers 1` or migrate to Redis)
- Lost on process restart (acceptable for transient concurrency control)

### Neutral
- Adds ~20 lines of code
- Requires timeout tuning based on actual upload processing time

## References

- [Python asyncio.Semaphore documentation](https://docs.python.org/3/library/asyncio-sync.html#asyncio.Semaphore)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) (alternative approach)
- ADR-0009: Redis Caching for Metadata (potential future distributed semaphore backend)
