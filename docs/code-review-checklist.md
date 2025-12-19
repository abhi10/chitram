# Code Review Reading Order - Phase 1 Lean

A checklist for understanding the Image Hosting App codebase from the ground up.

**Total time:** ~75 minutes
**Total lines:** ~850 lines (Phase 1 Lean - simplified)
**Phase:** Phase 1 Lean (local storage only, essential features)

> **Note:** This is Phase 1 Lean. Some features deferred to Phase 1.5 (image dimensions) and Phase 2 (MinIO, advanced validation). See ADR-0008.

---

## Dependency Flow

```
pyproject.toml → config.py → database.py → schemas/ → models/
                                              ↓
                                    storage_service.py
                                              ↓
                                    image_service.py
                                              ↓
                                      api/images.py
                                              ↓
                                        main.py
                                              ↓
                                        tests/
```

---

## Reading Checklist

### Phase 1: Foundation (15 min)

- [ ] **1. `backend/pyproject.toml`** (~50 lines, 5 min)
  - [ ] Review dependencies and their purposes
  - [ ] Note Python version requirement (3.11+)
  - [ ] Review Ruff/Black configuration
  - [ ] Review pytest configuration
  - [ ] **Note `[project.optional-dependencies.future]` for deferred features**

  | Dependency | Purpose |
  |------------|---------|
  | fastapi | Web framework |
  | sqlalchemy + asyncpg | Async database |
  | pydantic-settings | Configuration |
  | aiofiles | Async file I/O |
  | ~~minio~~ | ~~S3 storage~~ *Deferred to Phase 2* |
  | ~~pillow~~ | ~~Image processing~~ *Deferred to Phase 1.5* |
  | ~~python-magic~~ | ~~File detection~~ *Deferred to Phase 2* |

- [ ] **2. `backend/app/config.py`** (~35 lines, 3 min)
  - [ ] Understand `Settings` class with pydantic-settings
  - [ ] Note `storage_backend = "local"` (only local in Phase 1)
  - [ ] Review computed properties (`max_file_size_bytes`, `allowed_content_types_list`)
  - [ ] Understand `@lru_cache` singleton pattern
  - [ ] **Note: MinIO settings removed in Phase 1 Lean**

- [ ] **3. `backend/app/database.py`** (~45 lines, 5 min)
  - [ ] Understand async engine creation
  - [ ] Review `async_session_maker` factory
  - [ ] Understand `get_db` dependency (yields session per request)
  - [ ] Note `init_db` and `close_db` lifecycle functions

**Time checkpoint: 13 min**

---

### Phase 2: Data Contracts (10 min)

- [ ] **4. `backend/app/schemas/error.py`** (~35 lines, 5 min)
  - [ ] Review `ErrorDetail` structure (code, message, details)
  - [ ] Review `ErrorResponse` wrapper
  - [ ] Note standard error codes in `ErrorCodes` class

  | Error Code | HTTP Status | When Used |
  |------------|-------------|-----------|
  | `INVALID_FILE_FORMAT` | 400 | Not JPEG/PNG |
  | `FILE_TOO_LARGE` | 400 | > 5MB |
  | `IMAGE_NOT_FOUND` | 404 | ID doesn't exist |
  | `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
  | `INTERNAL_ERROR` | 500 | Server error |

- [ ] **5. `backend/app/schemas/image.py`** (~49 lines, 5 min)
  - [ ] Review schema inheritance (`ImageBase` → `ImageCreate` → `ImageResponse`)
  - [ ] Note `ConfigDict(from_attributes=True)` for ORM compatibility
  - [ ] Understand request vs response schemas
  - [ ] **Note: No `width` or `height` fields in Phase 1 Lean**

**Time checkpoint: 23 min**

---

### Phase 3: Data Layer (15 min)

- [ ] **6. `backend/app/models/image.py`** (~44 lines, 5 min)
  - [ ] Review SQLAlchemy model with `Mapped` type hints
  - [ ] Note **7 essential columns** (Phase 1 Lean):
    - `id` (UUID primary key)
    - `filename` (sanitized)
    - `storage_key` (UUID-based)
    - `content_type` (MIME type)
    - `file_size` (bytes)
    - `upload_ip` (for rate limiting)
    - `created_at` (timestamp)
  - [ ] Understand UUID generation pattern
  - [ ] Review timestamp handling (UTC)
  - [ ] **Removed fields:** ~~width~~, ~~height~~, ~~is_public~~, ~~updated_at~~

- [ ] **7. `backend/app/services/storage_service.py`** (~128 lines, 10 min)
  - [ ] **Strategy Pattern implementation (simplified):**
    - [ ] `StorageBackend` (ABC) - abstract interface
    - [ ] `LocalStorageBackend` - filesystem implementation
    - [ ] ~~MinioStorageBackend~~ *Deferred to Phase 2*
    - [ ] `StorageService` - wrapper/facade
  - [ ] Review each method: `save`, `get`, `delete`, `exists`
  - [ ] Note async file operations with `aiofiles`
  - [ ] Understand path-based storage with `Path`
  - [ ] **Phase 1 Lean: Only local storage, MinIO removed**

**Time checkpoint: 38 min**

---

### Phase 4: Business Logic (12 min)

- [ ] **8. `backend/app/services/image_service.py`** (~75 lines, 8 min)
  - [ ] Review constructor dependencies (db, storage)
  - [ ] **Static methods:**
    - [ ] `generate_storage_key` - UUID-based key generation
    - [ ] `sanitize_filename` - security (path traversal prevention)
    - [ ] ~~get_image_dimensions~~ *Deferred to Phase 1.5*
    - [ ] ~~calculate_checksum~~ *Deferred to Phase 2*
  - [ ] **Main methods:**
    - [ ] `upload()` - simplified upload flow (no dimensions)
    - [ ] `get_by_id()` - metadata retrieval
    - [ ] `get_file()` - file content retrieval
    - [ ] `delete()` - graceful deletion (continues if storage fails)
  - [ ] **Phase 1 Lean: Removed Pillow/PIL imports, no image processing**

- [ ] **9. `backend/app/utils/validation.py`** (~50 lines, 4 min)
  - [ ] Understand magic bytes detection (manual signatures)
  - [ ] Review `validate_image_file` function
  - [ ] Note security: validates content, not just headers
  - [ ] **Phase 1 Lean: Manual signature check only (JPEG/PNG)**
  - [ ] Removed: ~~python-magic library fallback~~

**Time checkpoint: 50 min**

---

### Phase 5: HTTP Layer (15 min)

- [ ] **10. `backend/app/api/health.py`** (~35 lines, 3 min)
  - [ ] Simple endpoint to warm up
  - [ ] Note database connectivity check
  - [ ] Review `HealthResponse` schema

- [ ] **11. `backend/app/api/images.py`** (~98 lines, 12 min)
  - [ ] **Dependencies:**
    - [ ] `get_storage` - retrieves from app.state
    - [ ] `get_image_service` - composes service with deps
    - [ ] `get_client_ip` - extracts IP (handles X-Forwarded-For)
  - [ ] **Endpoints:**
    - [ ] `POST /upload` - file validation, upload flow
    - [ ] `GET /{id}` - metadata retrieval
    - [ ] `GET /{id}/file` - file download
    - [ ] `DELETE /{id}` - deletion
  - [ ] Note structured error responses
  - [ ] Review response models in OpenAPI decorators
  - [ ] **Phase 1 Lean: Response doesn't include width/height**

**Time checkpoint: 65 min**

---

### Phase 6: Application Entry (8 min)

- [ ] **12. `backend/app/main.py`** (~84 lines, 8 min)
  - [ ] **Lifespan pattern:**
    - [ ] Startup: init_db, create storage backend
    - [ ] **Phase 1 Lean: Always uses `LocalStorageBackend`**
    - [ ] Storage stored in `app.state`
    - [ ] Shutdown: close_db
  - [ ] Review CORS middleware (development only)
  - [ ] Note global exception handler
  - [ ] Review router registration
  - [ ] **Simplified: No MinIO conditional logic**

**Time checkpoint: 73 min**

---

### Phase 7: Tests (10 min)

- [ ] **13. `backend/tests/conftest.py`** (~70 lines, 4 min)
  - [ ] **Fixtures:**
    - [ ] `sample_jpeg_bytes` / `sample_png_bytes` - test images
    - [ ] `test_db` - in-memory SQLite for tests
    - [ ] `test_storage` - temporary directory storage
    - [ ] `client` - async test client with overrides
  - [ ] Note dependency override pattern

- [ ] **14. `backend/tests/api/test_images.py`** (~100 lines, 6 min)
  - [ ] **Test classes:**
    - [ ] `TestUploadImage` - upload scenarios
    - [ ] `TestGetImageMetadata` - retrieval scenarios
    - [ ] `TestDownloadImage` - download scenarios
    - [ ] `TestDeleteImage` - deletion scenarios
    - [ ] `TestHealthCheck` - health endpoint
  - [ ] Note Arrange-Act-Assert pattern
  - [ ] Review error case coverage
  - [ ] **Phase 1 Lean: No width/height assertions**

**Time checkpoint: 83 min** (buffer included)

---

## Key Patterns to Note

### 1. Dependency Injection
```python
# FastAPI Depends() for testability
@router.get("/{image_id}")
async def get_image(
    service: ImageService = Depends(get_image_service),
):
```

### 2. Lifespan Context Manager
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    storage_backend = LocalStorageBackend(...)  # Phase 1: Always local
    app.state.storage = StorageService(backend=storage_backend)
    yield
    # Shutdown
    await close_db()
```

### 3. Strategy Pattern (Storage) - **Simplified**
```python
class StorageBackend(ABC):
    @abstractmethod
    async def save(self, key, data, content_type): ...

class LocalStorageBackend(StorageBackend):
    # Phase 1 Lean: Only local filesystem implementation
    ...

# MinioStorageBackend deferred to Phase 2
```

### 4. Structured Errors
```python
raise HTTPException(
    status_code=400,
    detail=ErrorDetail(
        code="INVALID_FILE_FORMAT",
        message="Only JPEG and PNG supported",
    ).model_dump(),
)
```

### 5. Graceful Degradation
```python
# Continue even if storage delete fails (DB is source of truth)
try:
    await self.storage.delete(image.storage_key)
except Exception:
    pass  # Log in production, but continue to delete DB record
```

### 6. Manual Magic Bytes Validation - **Phase 1 Lean**
```python
# Simple signature check without python-magic library
IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
}

def get_mime_type_from_content(content: bytes) -> str | None:
    for signature, mime_type in IMAGE_SIGNATURES.items():
        if content.startswith(signature):
            return mime_type
    return None
```

---

## Phase 1 Lean Simplifications

| Feature | Status | Restored In |
|---------|--------|-------------|
| **MinIO Storage** | ❌ Removed | Phase 2 |
| **Image Dimensions** | ❌ Removed | Phase 1.5 |
| **python-magic** | ❌ Removed | Phase 2 |
| **Unused Fields** | ❌ Removed | Phase 2 |
| Local Storage | ✅ Active | - |
| Manual Magic Bytes | ✅ Active | - |
| Core CRUD | ✅ Active | - |

**Rationale:** Start with simplest working system, validate core functionality, then add complexity incrementally.

See [ADR-0008](adr/0008-phase1-lean-defer-complexity.md) for full reasoning.

---

## Review Complete

- [ ] **All files reviewed**
- [ ] **Key patterns understood**
- [ ] **Phase 1 Lean simplifications noted**
- [ ] **Questions documented for follow-up**

---

## Notes & Questions

_Use this space to document questions or observations during review:_

```
1.

2.

3.
```

---

## Comparison: Phase 1 Full vs Phase 1 Lean

| Metric | Phase 1 Full | Phase 1 Lean | Change |
|--------|--------------|--------------|--------|
| **Total Lines** | ~965 | ~850 | -115 (-12%) |
| **Dependencies** | 12 | 9 | -3 |
| **Docker Services** | 3 | 2 | -1 (MinIO) |
| **Model Fields** | 10 | 7 | -3 |
| **Storage Backends** | 2 | 1 | -1 (MinIO) |
| **Reading Time** | ~90 min | ~75 min | -15 min |

---

**Document Version:** 2.0 (Phase 1 Lean)
**Last Updated:** 2025-12-19
**Previous Version:** 1.0 (Phase 1 Full - 2025-12-13)
