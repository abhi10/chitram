# Phase 1: Foundation

**Status:** ✅ Complete (Validated 2025-12-24)
**Branch:** `main`

---

## Learning Objectives

- Understand request/response lifecycle
- Implement basic CRUD operations for images
- Learn about file storage patterns
- Database design for metadata

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                      Client                          │
│               (Browser / Mobile App)                 │
└────────────────────────┬─────────────────────────────┘
                         │
                         ▼
               ┌─────────────────┐
               │   FastAPI App   │
               │   (Monolith)    │
               │                 │
               │  - Upload API   │
               │  - Download API │
               │  - Metadata API │
               └────────┬────────┘
                        │
                ┌───────┴───────┐
                ▼               ▼
         ┌───────────┐   ┌───────────┐
         │PostgreSQL │   │  Local    │
         │(Metadata) │   │Filesystem │
         │           │   │           │
         │7 Columns  │   │ ./uploads │
         └───────────┘   └───────────┘
```

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI | Async API with auto-docs |
| Database | PostgreSQL + asyncpg | Metadata storage |
| ORM | SQLAlchemy 2.0 (async) | Database abstraction |
| Storage | Local Filesystem | File storage (abstracted) |
| Validation | Pydantic 2.x | Request/response schemas |

---

## Database Schema

```sql
images (7 columns)
├── id (UUID, PK)
├── filename (original filename, sanitized)
├── storage_key (unique path in storage)
├── content_type (MIME type: image/jpeg or image/png)
├── file_size (bytes)
├── upload_ip (for rate limiting)
└── created_at (UTC timestamp)
```

**Deferred columns:**
- `width`, `height` → Phase 1.5 (requires Pillow)
- `checksum`, `user_id`, `is_public`, `updated_at` → Phase 2

---

## API Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/api/v1/images/upload` | Upload single image | ✅ |
| GET | `/api/v1/images/{id}` | Get image metadata | ✅ |
| GET | `/api/v1/images/{id}/file` | Download actual image | ✅ |
| DELETE | `/api/v1/images/{id}` | Delete image | ✅ |
| GET | `/health` | Health check | ✅ |

---

## Key Implementation Patterns

### 1. Storage Abstraction (Strategy Pattern)

```python
# app/services/storage_service.py
class StorageBackend(ABC):
    @abstractmethod
    async def save(self, key: str, data: bytes, content_type: str) -> str: ...
    @abstractmethod
    async def get(self, key: str) -> bytes: ...
    @abstractmethod
    async def delete(self, key: str) -> bool: ...

class LocalStorageBackend(StorageBackend):
    """Development: Local filesystem storage"""
    pass
```

**Why:** Allows swapping to MinIO/S3 in Phase 2 without changing business logic.

### 2. Lifespan Pattern

```python
# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    app.state.storage = StorageService(backend=LocalStorageBackend())
    yield
    # Shutdown
    await close_db()
```

**Why:** Clean resource initialization and cleanup.

### 3. Graceful Degradation

```python
# app/services/image_service.py
async def delete(self, image_id: str) -> bool:
    try:
        await self.storage.delete(image.storage_key)
    except Exception:
        pass  # Continue even if storage fails
    await self.db.delete(image)  # DB is source of truth
```

**Why:** Non-critical failures shouldn't block critical operations.

### 4. Structured Errors (ADR-0005)

```python
raise HTTPException(
    status_code=400,
    detail=ErrorDetail(
        code="INVALID_FILE_FORMAT",
        message="Only JPEG and PNG supported",
    ).model_dump(),
)
```

**Error Codes:**
- `INVALID_FILE_FORMAT` - Not JPEG/PNG
- `FILE_TOO_LARGE` - Exceeds 5MB
- `IMAGE_NOT_FOUND` - ID doesn't exist
- `INTERNAL_ERROR` - Server error

---

## Dependencies (9 packages)

```
fastapi>=0.115.0        # Web framework
uvicorn[standard]       # ASGI server
python-multipart        # File uploads
sqlalchemy>=2.0.35      # ORM
asyncpg>=0.30.0         # PostgreSQL driver
pydantic>=2.10.0        # Validation
pydantic-settings       # Configuration
python-dotenv           # Environment variables
aiofiles                # Async file I/O
```

---

## Validation Results

See [PHASE1_TESTING.md](../PHASE1_TESTING.md) for detailed test results.

**Summary:**
- ✅ Upload (JPEG, PNG, various sizes)
- ✅ Get metadata
- ✅ Download file
- ✅ Delete (DB + storage cleanup)
- ✅ Error handling (invalid format, 404)
- ✅ Health check

---

## What's Next

**Phase 1.5:** Add image dimensions
- Add Pillow dependency
- Extract width/height on upload
- Alembic migration for new columns

**Phase 2:** Performance
- Redis caching
- Background jobs (thumbnails)
- MinIO storage backend

---

**Document Version:** 1.0
**Last Updated:** 2025-12-24
