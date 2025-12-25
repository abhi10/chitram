# Phase 4: Production Readiness

**Status:** ⏸️ Not Started
**Prerequisites:** Phase 3 complete
**Branch:** `feature/phase-4` (to be created)

---

## Learning Objectives

- Implement comprehensive monitoring
- Learn circuit breaker patterns
- Understand rate limiting
- Practice graceful degradation

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OBSERVABILITY STACK                             │
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │ Prometheus  │    │   Grafana   │    │   Jaeger    │                 │
│  │  (Metrics)  │    │(Dashboards) │    │  (Tracing)  │                 │
│  └─────────────┘    └─────────────┘    └─────────────┘                 │
│         ▲                  ▲                  ▲                         │
│         └──────────────────┼──────────────────┘                         │
│                            │                                            │
└────────────────────────────┼────────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │   Application   │
                    │    Services     │
                    └─────────────────┘
```

---

## Key Patterns

### 1. Rate Limiting (Token Bucket)

```python
class RateLimiter:
    def __init__(self, redis_client, requests_per_minute: int = 60):
        self.redis = redis_client
        self.limit = requests_per_minute
        self.window = 60  # seconds

    async def is_allowed(self, key: str) -> bool:
        pipe = self.redis.pipeline()
        now = time.time()
        window_start = now - self.window

        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, self.window)

        results = await pipe.execute()
        request_count = results[2]

        return request_count <= self.limit
```

### 2. Circuit Breaker

```python
class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0

    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise
```

**Why:** Prevents cascading failures by failing fast when a dependency is unhealthy.

### 3. Graceful Degradation

```python
async def get_image_with_thumbnail(self, image_id: str):
    image = await self.get_image(image_id)

    try:
        thumbnail = await self.thumbnail_service.get(image_id)
    except (ServiceUnavailable, TimeoutError):
        # Graceful degradation: return placeholder
        thumbnail = self.get_placeholder_thumbnail()
        logger.warning(f"Thumbnail service unavailable for {image_id}")

    return ImageResponse(image=image, thumbnail=thumbnail)
```

### 4. Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10]
)

# Business metrics
UPLOADS_TOTAL = Counter('images_uploaded_total', 'Total images uploaded')
STORAGE_BYTES = Gauge('storage_bytes_used', 'Total storage used in bytes')
CACHE_HIT_RATIO = Gauge('cache_hit_ratio', 'Cache hit ratio')
```

---

## Health Check Endpoints

```python
@router.get("/health/live")
async def liveness():
    """Is the process running?"""
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness():
    """Can the service handle requests?"""
    checks = {
        "database": await check_db_connection(),
        "storage": await check_storage_connection(),
        "cache": await check_redis_connection(),
    }
    all_healthy = all(checks.values())
    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks
    }
```

---

## Deliverables

- [ ] Prometheus metrics collection
- [ ] Grafana dashboards
- [ ] Distributed tracing (Jaeger)
- [ ] Rate limiting (per IP, per user)
- [ ] Circuit breakers for external calls
- [ ] Graceful degradation patterns
- [ ] Health check endpoints (liveness/readiness)
- [ ] Alerting rules

---

## Key Metrics to Track

| Metric | Purpose | Alert Threshold |
|--------|---------|-----------------|
| Request rate | Load | > 1000 rps |
| Error rate | Reliability | > 1% |
| P95 latency | Performance | > 500ms |
| Cache hit ratio | Efficiency | < 80% |
| Queue depth | Backpressure | > 1000 |
| DB connections | Saturation | > 80% pool |

---

**Document Version:** 1.0
**Last Updated:** 2025-12-24
