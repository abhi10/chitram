# Code Review Reading Order

A checklist for understanding the Image Hosting App codebase from the ground up.

**Total time:** ~90 minutes
**Total lines:** ~965 lines

---

## Dependency Flow

```
Code Review Reading Order

                      ┌─────────────────┐
                      │   main.py       │  ← 8. Entry point (ties everything)
                      └────────┬────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                              ▼
       ┌─────────────────┐           ┌─────────────────┐
       │   api/images.py │           │  api/health.py  │  ← 7. HTTP layer
       └────────┬────────┘           └─────────────────┘
                │
                ▼
       ┌─────────────────┐
       │ image_service.py│  ← 6. Business logic
       └────────┬────────┘
                │
       ┌────────┴────────┐
       ▼                  ▼
  ┌──────────┐    ┌──────────────┐
  │ models/  │    │storage_service│  ← 5. Data & Storage
  └────┬─────┘    └──────────────┘
       │
       ▼
  ┌──────────┐
  │schemas/  │  ← 4. API contracts
  └──────────┘
       │
       ▼
  ┌──────────┐
  │database.py│  ← 3. DB setup
  └──────────┘
       │
       ▼
  ┌──────────┐
  │config.py │  ← 2. Configuration
  └──────────┘
       │
       ▼
  ┌──────────────┐
  │pyproject.toml│  ← 1. START HERE (dependencies)
  └──────────────┘

```

---

## Reading Checklist

### Phase 1: Foundation (15 min)

- [X] **1. `backend/pyproject.toml`** (~80 lines, 5 min)
  - [X] Review dependencies and their purposes
  - [X] Note Python version requirement (3.11+)
  - [X] Review Ruff/Black configuration
  - [X] Review pytest configuration

  | Dependency | Purpose |
  |------------|---------|
  | fastapi | Web framework |
  | sqlalchemy + asyncpg | Async database |
  | pydantic-settings | Configuration |
  | minio | S3-compatible storage |
  | pillow | Image processing |
  | python-magic | File type detection |

- [X] **2. `backend/app/config.py`** (~60 lines, 5 min)
  - [X] Understand `Settings` class with pydantic-settings
  - [X] Note environment variables and defaults
  - [X] Review computed properties (`max_file_size_bytes`, `allowed_content_types_list`)
  - [X] Understand `@lru_cache` singleton pattern

- [X] **3. `backend/app/database.py`** (~45 lines, 5 min)
  - [X] Understand async engine creation
  - [X] Review `async_session_maker` factory
  - [X] Understand `get_db` dependency (yields session per request)
  - [X] Note `init_db` and `close_db` lifecycle functions

---

### Phase 2: Data Contracts (10 min)

- [X] **4. `backend/app/schemas/error.py`** (~35 lines, 5 min)
  - [X] Review `ErrorDetail` structure (code, message, details)
  - [X] Review `ErrorResponse` wrapper
  - [X] Note standard error codes in `ErrorCodes` class

  | Error Code | HTTP Status | When Used |
  |------------|-------------|-----------|
  | `INVALID_FILE_FORMAT` | 400 | Not JPEG/PNG |
  | `FILE_TOO_LARGE` | 400 | > 5MB |
  | `IMAGE_NOT_FOUND` | 404 | ID doesn't exist |
  | `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
  | `INTERNAL_ERROR` | 500 | Server error |

- [X] **5. `backend/app/schemas/image.py`** (~45 lines, 5 min)
  - [X] Review schema inheritance (`ImageBase` → `ImageCreate` → `ImageResponse`)
  - [X] Note `ConfigDict(from_attributes=True)` for ORM compatibility
  - [X] Understand request vs response schemas

---

### Phase 3: Data Layer (20 min)

- [X] **6. `backend/app/models/image.py`** (~50 lines, 5 min)
  - [X] Review SQLAlchemy model with `Mapped` type hints
  - [X] Note column definitions (types, nullable, defaults)
  - [X] Understand UUID generation pattern
  - [X] Review timestamp handling (UTC)

- [X] **7. `backend/app/services/storage_service.py`** (~150 lines, 15 min)
  - [ ] **Strategy Pattern implementation:**
    - [ ] `StorageBackend` (ABC) - abstract interface
    - [ ] `LocalStorageBackend` - filesystem implementation
    - [ ] `MinioStorageBackend` - S3-compatible implementation
    - [ ] `StorageService` - wrapper/facade
  - [ ] Review each method: `save`, `get`, `delete`, `exists`
  - [ ] Note error handling in MinIO backend
  - [ ] Understand async wrapping for sync MinIO client

---

### Phase 4: Business Logic (15 min)

- [X] **8. `backend/app/services/image_service.py`** (~100 lines, 10 min)
  - [ ] Review constructor dependencies (db, storage)
  - [ ] **Static methods:**
    - [ ] `generate_storage_key` - UUID-based key generation
    - [ ] `sanitize_filename` - security (path traversal prevention)
    - [ ] `get_image_dimensions` - PIL integration
    - [ ] `calculate_checksum` - SHA256 hash
  - [ ] **Main methods:**
    - [ ] `upload()` - full upload flow
    - [ ] `get_by_id()` - metadata retrieval
    - [ ] `get_file()` - file content retrieval
    - [ ] `delete()` - graceful deletion (continues if storage fails)

- [X] **9. `backend/app/utils/validation.py`** (~60 lines, 5 min)
  - [ ] Understand magic bytes detection
  - [ ] Review `validate_image_file` function
  - [ ] Note security: validates content, not just headers

---

### Phase 5: HTTP Layer (20 min)

- [X] **10. `backend/app/api/health.py`** (~35 lines, 5 min)
  - [X] Simple endpoint to warm up
  - [ ] Note database connectivity check
  - [X] Review `HealthResponse` schema

- [X] **11. `backend/app/api/images.py`** (~100 lines, 15 min)
  - [ ] **Dependencies:**
    - [ ] `get_storage` - retrieves from app.state
    - [ ] `get_image_service` - composes service with deps
    - [ ] `get_client_ip` - extracts IP (handles X-Forwarded-For)
  - [X] **Endpoints:**
    - [ ] `POST /upload` - file validation, upload flow
    - [ ] `GET /{id}` - metadata retrieval
    - [ ] `GET /{id}/file` - file download
    - [ ] `DELETE /{id}` - deletion
  - [x] Note structured error responses
  - [X] Review response models in OpenAPI decorators

---

### Phase 6: Application Entry (10 min)

- [X] **12. `backend/app/main.py`** (~70 lines, 10 min)
  - [ ] **Lifespan pattern:**
    - [ ] Startup: init_db, create storage backend
    - [ ] Storage stored in `app.state`
    - [ ] Shutdown: close_db
  - [ ] Review CORS middleware (development only)
  - [ ] Note global exception handler
  - [ ] Review router registration

---

### Phase 7: Tests (15 min)

- [ ] **13. `backend/tests/conftest.py`** (~70 lines, 5 min)
  - [ ] **Fixtures:**
    - [ ] `sample_jpeg_bytes` / `sample_png_bytes` - test images
    - [ ] `test_db` - in-memory SQLite for tests
    - [ ] `test_storage` - temporary directory storage
    - [ ] `client` - async test client with overrides
  - [ ] Note dependency override pattern

- [ ] **14. `backend/tests/api/test_images.py`** (~100 lines, 10 min)
  - [ ] **Test classes:**
    - [ ] `TestUploadImage` - upload scenarios
    - [ ] `TestGetImageMetadata` - retrieval scenarios
    - [ ] `TestDownloadImage` - download scenarios
    - [ ] `TestDeleteImage` - deletion scenarios
    - [ ] `TestHealthCheck` - health endpoint
  - [ ] Note Arrange-Act-Assert pattern
  - [ ] Review error case coverage

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
    app.state.storage = StorageService(...)
    yield
    # Shutdown
    await close_db()
```

### 3. Strategy Pattern (Storage)
```python
class StorageBackend(ABC):
    @abstractmethod
    async def save(self, key, data, content_type): ...

class LocalStorageBackend(StorageBackend): ...
class MinioStorageBackend(StorageBackend): ...
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
# Continue even if storage delete fails
try:
    await self.storage.delete(image.storage_key)
except Exception:
    pass  # Log in production
```

---

## Review Complete

- [ ] **All files reviewed**
- [ ] **Key patterns understood**
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

**Document Version:** 1.0
**Last Updated:** 2025-12-13
