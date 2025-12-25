# Distributed Systems Learnings

**Project:** Chitram - Image Hosting API
**Purpose:** Track learnings mapped to distributed systems building blocks

---

## Building Blocks Tracker

| Principle | Building Block | Phase | Status | Key Learning |
|-----------|---------------|-------|--------|--------------|
| **Availability** | Health Checks | 1 | ✅ | `/health` endpoint returns DB + storage status |
| **Availability** | Graceful Degradation | 1 | ✅ | Delete continues if storage fails (DB is source of truth) |
| **Performance** | Local Storage | 1 | ✅ | Simple FS for MVP, abstracted via Strategy pattern |
| **Performance** | Caching (Redis) | 2 | ⏸️ | - |
| **Performance** | Async Processing | 2 | ⏸️ | - |
| **Reliability** | DB Transactions | 1 | ✅ | SQLAlchemy async sessions with proper commit/rollback |
| **Reliability** | Structured Errors | 1 | ✅ | Error codes enable client-side handling (ADR-0005) |
| **Reliability** | Input Validation | 1 | ✅ | Magic bytes validation, not just Content-Type header |
| **Scalability** | Storage Abstraction | 1 | ✅ | Strategy pattern for easy backend swapping |
| **Scalability** | Dependency Injection | 1 | ✅ | FastAPI Depends() enables testing with overrides |
| **Scalability** | Load Balancing | 3 | ⏸️ | - |
| **Manageability** | DevContainer | 1 | ✅ | Codespaces for consistent dev environment |
| **Manageability** | Lifespan Pattern | 1 | ✅ | Clean startup/shutdown via context manager |
| **Manageability** | Logging | 1 | ⏸️ | Basic only, structured logging in Phase 4 |
| **Cost** | Lean Dependencies | 1 | ✅ | 9 deps vs 12 original (ADR-0008) |
| **Cost** | Defer Complexity | 1 | ✅ | Pillow, MinIO deferred to later phases |

---

## Phase 1 Learnings (Detailed)

### What Worked Well

#### 1. Strategy Pattern for Storage
```python
class StorageBackend(ABC):
    async def save(self, key, data, content_type): ...

class LocalStorageBackend(StorageBackend): ...
class MinioStorageBackend(StorageBackend): ...  # Future
```
**Insight:** Even for MVP, building the abstraction layer pays off. Adding MinIO later will be a single class addition.

#### 2. Dependency Injection Pattern
```python
@router.get("/{image_id}")
async def get_image(
    service: ImageService = Depends(get_image_service),
):
```
**Insight:** Made testing trivial - just override `app.dependency_overrides` in conftest.py.

#### 3. Structured Error Format
```python
ErrorDetail(code="INVALID_FILE_FORMAT", message="Only JPEG and PNG supported")
```
**Insight:** Machine-readable error codes enable programmatic client handling, not just human-readable messages.

#### 4. Lifespan Context Manager
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    app.state.storage = StorageService(...)
    yield
    await close_db()
```
**Insight:** Cleaner than `@app.on_event("startup")` deprecated pattern. Resources in `app.state` accessible everywhere.

### What Was Harder Than Expected

#### 1. Async SQLAlchemy Session Management
**Challenge:** Understanding when to use `async_session()` vs `async_sessionmaker()`.
**Solution:** Use `async_sessionmaker` factory, yield session per request via `get_db()` dependency.
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
```

#### 2. File Type Validation Without python-magic
**Challenge:** python-magic requires libmagic C library (adds complexity).
**Solution:** Manual magic bytes checking for JPEG (`FF D8 FF`) and PNG (`89 50 4E 47`).
```python
MAGIC_BYTES = {
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG': 'image/png',
}
```
**Insight:** For limited file types, manual checking is simpler and has zero dependencies.

#### 3. pyproject.toml Build Configuration
**Challenge:** Hatchling couldn't find package directory.
**Solution:** Added explicit `[tool.hatch.build.targets.wheel]` section.
```toml
[tool.hatch.build.targets.wheel]
packages = ["app"]
```

### Decisions Made

| Decision | Rationale | ADR |
|----------|-----------|-----|
| Defer Pillow | Image dimensions not critical for MVP | ADR-0008 |
| Defer MinIO | Local storage sufficient for validation | ADR-0008 |
| Skip python-magic | Manual magic bytes simpler for 2 formats | ADR-0008 |
| Use Codespaces | 8GB RAM constraint on local machine | ADR-0007 |
| Structured Errors | Enable programmatic error handling | ADR-0005 |
| No Kubernetes | Overkill for MVP phases | ADR-0006 |

---

## Phase 1.5 Learnings (To Be Added)

*Will document after implementing image dimensions feature.*

---

## Phase 2 Learnings (To Be Added)

*Will document after implementing caching and async processing.*

---

## Patterns Reference

### 1. Cache-Aside (Phase 2)
```
Read: Cache → Miss → DB → Store in Cache → Return
Write: DB → Invalidate Cache
```

### 2. Circuit Breaker (Phase 4)
```
Closed → Failure Threshold → Open → Recovery Timeout → Half-Open → Success → Closed
```

### 3. CQRS-lite (Phase 3)
```
Reads → Read Replicas (can be stale)
Writes → Primary DB (must be consistent)
```

---

## Questions for Future Exploration

1. **Cache Invalidation:** When to use TTL vs explicit invalidation?
2. **Sharding Strategy:** Hash-based vs range-based for images?
3. **Rate Limiting:** Per-IP vs per-user vs sliding window?
4. **Observability:** What metrics matter most for image hosting?

---

## External Resources Used

- [AOSA: Scalable Web Architecture](https://aosabook.org/en/v2/distsys.html) - Foundation
- [FastAPI Official Docs](https://fastapi.tiangolo.com/) - Framework patterns
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/) - Database patterns

---

**Document Version:** 1.0
**Last Updated:** 2025-12-24
