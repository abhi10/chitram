# Distributed Systems Building Blocks

**Project:** Chitram - Image Hosting API
**Purpose:** Learn distributed systems concepts through hands-on implementation

---

## Core Principles (from AOSA Paper)

These six foundational principles guide our architecture decisions:

| Principle | Description | How We Learn It |
|-----------|-------------|-----------------|
| **Availability** | System uptime, graceful degradation | Redundancy, health checks |
| **Performance** | Fast responses, low latency | Caching, CDN, async processing |
| **Reliability** | Data consistency, persistence | Database transactions, replication |
| **Scalability** | Handle increased load | Horizontal scaling, partitioning |
| **Manageability** | Easy operations, debugging | Logging, monitoring, containerization |
| **Cost** | Total cost of ownership | Right-sizing, efficient architecture |

---

## Architecture Evolution

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DISTRIBUTED SYSTEMS BUILDING BLOCKS                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Phase 1 (Current)          Phase 2              Phase 3        Phase 4 │
│  ┌─────────────────┐    ┌─────────────────┐  ┌──────────────┐  ┌──────┐│
│  │ Monolith API    │    │ Caching Layer   │  │ Load Balancer│  │Metrics│
│  │ Local Storage   │ -> │ Async Queues    │->│ Read/Write   │->│Tracing│
│  │ PostgreSQL      │    │ Reverse Proxy   │  │ Separation   │  │Alerts │
│  │ Health Checks   │    │ DB Indexes      │  │ Replication  │  │       │
│  └─────────────────┘    └─────────────────┘  └──────────────┘  └──────┘│
│                                                                         │
│  Foundation             Performance           Scalability    Production │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Building Blocks by Phase

### Phase 1: Foundation
- **Monolith API** - Single FastAPI application
- **Local Storage** - Filesystem with abstraction layer
- **PostgreSQL** - Metadata persistence
- **Health Checks** - Database connectivity monitoring
- **Structured Errors** - Consistent error format (ADR-0005)
- **Storage Abstraction** - Strategy pattern for backends

### Phase 2: Performance
- **Redis Cache** - Metadata caching (cache-aside pattern)
- **Message Queue** - Async processing (thumbnails, optimization)
- **Nginx Proxy** - Static serving, response caching
- **Database Indexes** - B-tree, Hash, GIN for fast lookups

### Phase 3: Scalability
- **Load Balancer** - Round-robin, least-conn, health checks
- **Read/Write Split** - CQRS-lite pattern
- **Database Replication** - Primary + read replicas
- **Storage Sharding** - Consistent hashing across buckets
- **CDN** - Edge caching for images

### Phase 4: Production Readiness
- **Prometheus Metrics** - Request counts, latencies, errors
- **Grafana Dashboards** - Visualization and alerting
- **Distributed Tracing** - Request flow across services
- **Circuit Breakers** - Fail-fast for unhealthy dependencies
- **Rate Limiting** - Per-IP/user request throttling

---

## Key Patterns

### 1. Storage Abstraction (Strategy Pattern)
```python
class StorageBackend(ABC):
    async def save(self, key: str, data: bytes) -> str: ...
    async def get(self, key: str) -> bytes: ...
    async def delete(self, key: str) -> bool: ...

class LocalStorageBackend(StorageBackend): ...
class MinioStorageBackend(StorageBackend): ...  # Phase 2
```
**Lesson:** Abstraction allows swapping implementations without changing business logic.

### 2. Graceful Degradation
```python
async def delete(self, image_id: str) -> bool:
    try:
        await self.storage.delete(image.storage_key)
    except Exception:
        pass  # Continue even if storage fails
    await self.db.delete(image)  # DB is source of truth
```
**Lesson:** Non-critical failures shouldn't block critical operations.

### 3. Dependency Injection
```python
@router.get("/{image_id}")
async def get_image(
    service: ImageService = Depends(get_image_service),
):
```
**Lesson:** Testability through injectable dependencies.

---

## Phase Details

- [Phase 1: Foundation](phase-1-foundation.md) - Current implementation
- [Phase 2: Performance](phase-2-performance.md) - Caching & async
- [Phase 3: Scaling](phase-3-scaling.md) - Horizontal scaling
- [Phase 4: Observability](phase-4-observability.md) - Production readiness

---

## References

- [AOSA: Scalable Web Architecture](https://aosabook.org/en/v2/distsys.html) - Source material
- [Designing Data-Intensive Applications](https://dataintensive.net/) - Deep dive

---

**Document Version:** 1.0
**Last Updated:** 2025-12-24
