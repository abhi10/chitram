# Phase 1 Lean Removals - Implementation Summary

**Date:** 2025-12-19
**Decision:** ADR-0008
**Goal:** Simplify Phase 1 to absolute minimum for faster validation and cleaner initial commit

---

## Overview

This document details the specific code removals for Phase 1 "Ultra-Lean" version, with preservation instructions for future phases.

**Philosophy:** Start with the simplest possible working system. Add complexity only when needed.

---

## Removals Summary

| Component | Lines Removed | Dependencies Removed | Impact |
|-----------|---------------|---------------------|--------|
| MinIO Backend | ~70 | minio | HIGH |
| Image Dimensions | ~15 | pillow | HIGH |
| Magic Bytes Library | ~10 | python-magic | MEDIUM |
| Unused Model Fields | ~15 | - | MEDIUM |
| Empty Test Dirs | 2 dirs | - | LOW |
| Unused Methods | ~5 | - | LOW |
| **TOTAL** | **~115 lines** | **3 packages** | **503MB Docker images** |

---

## Detailed Removal Instructions

### 1. MinIO Storage Backend

**Files Modified:**
- `backend/app/services/storage_service.py`
- `backend/app/config.py`
- `backend/app/main.py`
- `.devcontainer/docker-compose.yml`
- `backend/pyproject.toml`

#### backend/app/services/storage_service.py

**REMOVE:** Lines 7-9, 110-177

```python
# REMOVE these imports
from minio import Minio

# REMOVE entire MinioStorageBackend class (lines 110-177)
class MinioStorageBackend(StorageBackend):
    """MinIO/S3-compatible storage backend."""
    # ... entire class ...
```

**KEEP:**
- `StorageBackend` ABC (lines 11-61)
- `LocalStorageBackend` (lines 64-107)
- `StorageService` wrapper (lines 179-200)

**Preserved for:** Phase 2 (when adding production storage)

---

#### backend/app/config.py

**REMOVE:** Lines 26-31

```python
# REMOVE MinIO configuration
minio_endpoint: str = "localhost:9000"
minio_access_key: str = "minioadmin"
minio_secret_key: str = "minioadmin"
minio_bucket: str = "images"
minio_secure: bool = False
```

**CHANGE:** Line 21
```python
# FROM:
storage_backend: str = "minio"  # "local" or "minio"

# TO:
storage_backend: str = "local"  # Only "local" in Phase 1
```

**Preserved for:** Phase 2

---

#### backend/app/main.py

**REMOVE:** Line 15 (MinioStorageBackend import)
```python
# FROM:
from app.services.storage_service import StorageService, LocalStorageBackend, MinioStorageBackend

# TO:
from app.services.storage_service import StorageService, LocalStorageBackend
```

**REMOVE:** Lines 31-38 (MinIO initialization)
```python
# REMOVE this conditional block
if settings.storage_backend == "minio":
    storage_backend = MinioStorageBackend(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket=settings.minio_bucket,
        secure=settings.minio_secure,
    )
else:
    storage_backend = LocalStorageBackend(base_path=settings.local_storage_path)
```

**REPLACE WITH:**
```python
# Always use local storage in Phase 1
storage_backend = LocalStorageBackend(base_path=settings.local_storage_path)
```

**Preserved for:** Phase 2

---

#### .devcontainer/docker-compose.yml

**REMOVE:** Lines 40-50 (minio service), Line 53 (minio-data volume)

```yaml
# REMOVE entire minio service
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio-data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

# REMOVE from volumes section
volumes:
  postgres-data:
  minio-data:  # DELETE THIS LINE
```

**ALSO REMOVE:** Lines 12-16 (MinIO environment variables in app service)
```yaml
# REMOVE these environment variables
- STORAGE_BACKEND=minio
- MINIO_ENDPOINT=minio:9000
- MINIO_ACCESS_KEY=minioadmin
- MINIO_SECRET_KEY=minioadmin
- MINIO_BUCKET=images
```

**CHANGE:** Line 20 (remove minio from depends_on)
```yaml
# FROM:
depends_on:
  postgres:
    condition: service_healthy
  minio:
    condition: service_started

# TO:
depends_on:
  postgres:
    condition: service_healthy
```

**Preserved for:** Phase 2 (cloud deployment)

---

#### backend/pyproject.toml

**REMOVE:** Line in dependencies
```toml
# REMOVE this dependency
"minio>=7.2.0",
```

**Preserved for:** Phase 2

---

### 2. Image Dimensions (Pillow)

**Files Modified:**
- `backend/app/services/image_service.py`
- `backend/app/models/image.py`
- `backend/app/schemas/image.py`
- `backend/app/api/images.py`
- `backend/pyproject.toml`

#### backend/app/services/image_service.py

**REMOVE:** Lines 3, 7, 40-47, 78

```python
# REMOVE import
from io import BytesIO
from PIL import Image as PILImage

# REMOVE entire method (lines 40-47)
@staticmethod
def get_image_dimensions(data: bytes) -> tuple[int | None, int | None]:
    """Extract image dimensions from file data."""
    try:
        with PILImage.open(BytesIO(data)) as img:
            return img.width, img.height
    except Exception:
        return None, None

# REMOVE this line (line 78)
width, height = self.get_image_dimensions(data)

# REMOVE from Image creation (lines 89-90)
width=width,
height=height,
```

**Preserved for:** Phase 1.5 (when adding image info)

---

#### backend/app/models/image.py

**REMOVE:** Lines 36-37, 39, 46-50

```python
# REMOVE dimension fields
width: Mapped[int | None] = mapped_column(Integer, nullable=True)
height: Mapped[int | None] = mapped_column(Integer, nullable=True)

# REMOVE is_public field (not used)
is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

# REMOVE updated_at field (not critical for MVP)
updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=utc_now,
    onupdate=utc_now,
    nullable=False,
)
```

**ALSO REMOVE:** Line 6 import
```python
# FROM:
from sqlalchemy import String, Integer, DateTime, Boolean

# TO:
from sqlalchemy import String, Integer, DateTime
```

**Preserved for:**
- width/height: Phase 1.5
- is_public: Phase 2 (user accounts)
- updated_at: Phase 2 (when tracking changes matters)

---

#### backend/app/schemas/image.py

**REMOVE:** width/height from all schemas (lines 20-21, 34-35, 52-53)

```python
# REMOVE from ImageCreate (lines 20-21)
width: int | None = None
height: int | None = None

# REMOVE from ImageMetadata (lines 34-35)
width: int | None = None
height: int | None = None

# REMOVE from ImageUploadResponse (lines 52-53)
width: int | None = None
height: int | None = None
```

**Preserved for:** Phase 1.5

---

#### backend/app/api/images.py

**REMOVE:** Lines 96-97

```python
# REMOVE from response construction
width=image.width,
height=image.height,
```

**Preserved for:** Phase 1.5

---

#### backend/pyproject.toml

**REMOVE:** Line in dependencies
```toml
# REMOVE this dependency
"pillow>=11.0.0",
```

**Preserved for:** Phase 1.5

---

### 3. Python Magic Bytes Library

**Files Modified:**
- `backend/app/utils/validation.py`
- `backend/pyproject.toml`

#### backend/app/utils/validation.py

**REMOVE:** Lines 3, 22-29

```python
# REMOVE import
import magic

# REMOVE from get_mime_type_from_content function
# Keep only the fallback signature check
def get_mime_type_from_content(content: bytes) -> str | None:
    """
    Detect MIME type from file content using magic bytes.

    More secure than trusting Content-Type header.
    """
    # Check manual signatures
    for signature, mime_type in IMAGE_SIGNATURES.items():
        if content.startswith(signature):
            return mime_type
    return None
```

**SIMPLIFY:** Entire function becomes:
```python
def get_mime_type_from_content(content: bytes) -> str | None:
    """Detect MIME type from file content using magic bytes."""
    for signature, mime_type in IMAGE_SIGNATURES.items():
        if content.startswith(signature):
            return mime_type
    return None
```

**Preserved for:** Phase 2 (when supporting more formats or stricter validation)

---

#### backend/pyproject.toml

**ADD TO:** optional-dependencies (not main dependencies)
```toml
[project.optional-dependencies]
dev = [
    # ... existing dev deps ...
]

# ADD new section for future features
future = [
    "python-magic>=0.4.27",  # For Phase 2: stricter validation
    "pillow>=11.0.0",         # For Phase 1.5: image dimensions
    "minio>=7.2.0",           # For Phase 2: production storage
]
```

**Preserved for:** Phase 2

---

### 4. Unused Methods

**Files Modified:**
- `backend/app/services/image_service.py`

#### backend/app/services/image_service.py

**REMOVE:** Lines 3-4, 49-52

```python
# REMOVE imports
import hashlib

# REMOVE unused method
@staticmethod
def calculate_checksum(data: bytes) -> str:
    """Calculate SHA256 checksum of file data."""
    return hashlib.sha256(data).hexdigest()
```

**Preserved for:** Phase 2 (deduplication feature)

---

### 5. Empty Test Directories

**Files Modified:**
- Remove directories entirely

```bash
# REMOVE these directories
rm -rf backend/tests/unit/
rm -rf backend/tests/integration/
```

**KEEP:**
- `backend/tests/api/` - Has actual tests
- `backend/tests/conftest.py` - Test fixtures
- `backend/tests/__init__.py` - Package marker

**Preserved for:** Phase 1.5+ (add back when writing more tests)

---

### 6. DevContainer Post-Create Script

**Files Modified:**
- `.devcontainer/post-create.sh`

**REMOVE:** MinIO bucket creation section

```bash
# REMOVE lines related to MinIO bucket creation
echo "⏳ Creating MinIO bucket..."
uv run python -c "
from minio import Minio
# ... MinIO setup code ...
"
```

---

## Dependencies Summary

### Before (Phase 1 Original)
```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "python-multipart>=0.0.12",
    "sqlalchemy>=2.0.35",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "minio>=7.2.0",           # ← REMOVE
    "aiofiles>=24.1.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "pillow>=11.0.0",         # ← REMOVE
    "python-magic>=0.4.27",   # ← MOVE TO optional-dependencies
]
```

### After (Phase 1 Lean)
```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "python-multipart>=0.0.12",
    "sqlalchemy>=2.0.35",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "aiofiles>=24.1.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
]
```

---

## Database Schema Changes

### Before
```sql
CREATE TABLE images (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    storage_key VARCHAR(255) UNIQUE NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,
    width INTEGER,              -- REMOVE
    height INTEGER,             -- REMOVE
    upload_ip VARCHAR(45) NOT NULL,
    is_public BOOLEAN DEFAULT TRUE NOT NULL,  -- REMOVE
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL  -- REMOVE
);
```

### After (Phase 1 Lean)
```sql
CREATE TABLE images (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    storage_key VARCHAR(255) UNIQUE NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,
    upload_ip VARCHAR(45) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

**7 columns → 7 columns** (but simpler types)

---

## API Response Changes

### Before
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "photo.jpg",
  "content_type": "image/jpeg",
  "file_size": 102400,
  "width": 1920,      // REMOVED
  "height": 1080,     // REMOVED
  "url": "/api/v1/images/123e4567-e89b-12d3-a456-426614174000/file",
  "created_at": "2025-12-19T10:30:00Z"
}
```

### After (Phase 1 Lean)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "photo.jpg",
  "content_type": "image/jpeg",
  "file_size": 102400,
  "url": "/api/v1/images/123e4567-e89b-12d3-a456-426614174000/file",
  "created_at": "2025-12-19T10:30:00Z"
}
```

---

## Testing Impact

### Files Removed
- `backend/tests/unit/` (empty)
- `backend/tests/integration/` (empty)

### Files Kept
- `backend/tests/conftest.py` (fixtures)
- `backend/tests/api/test_images.py` (API tests)

**Test Changes Needed:**
1. Remove assertions for `width` and `height` in `test_images.py`
2. Update fixture expectations

---

## Docker Image Size Impact

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| MinIO | 500 MB | 0 MB | 500 MB |
| Pillow | 3 MB | 0 MB | 3 MB |
| python-magic | System lib | 0 | ~5 MB |
| **Total** | **~508 MB** | **0 MB** | **508 MB** |

---

## Migration Path for Future Phases

### Phase 1.5 (Image Info)
**Add back:**
1. `pillow>=11.0.0` to dependencies
2. `width`, `height` to model, schemas, API
3. `get_image_dimensions()` method
4. Update Alembic migration: `ALTER TABLE images ADD COLUMN width INTEGER, ADD COLUMN height INTEGER`

**Estimated effort:** 30 minutes

---

### Phase 2 (Full Features)
**Add back:**
1. `minio>=7.2.0` to dependencies
2. MinIO configuration to `config.py`
3. `MinioStorageBackend` class to `storage_service.py`
4. MinIO service to `docker-compose.yml`
5. `is_public`, `updated_at` to model
6. `python-magic` for stricter validation
7. `calculate_checksum()` for deduplication

**Estimated effort:** 2-3 hours

---

## Validation Checklist (Post-Removal)

After applying all removals:

- [ ] All imports resolve (no `ModuleNotFoundError`)
- [ ] Application starts without errors
- [ ] Upload endpoint works with local storage
- [ ] Download endpoint works
- [ ] Delete endpoint works
- [ ] Tests pass (with width/height assertions removed)
- [ ] Swagger UI shows correct schemas (no width/height)
- [ ] Docker Compose starts only Postgres (no MinIO)
- [ ] `.env` file doesn't require MinIO variables

---

## References

- **ADR-0008:** Defer complexity to later phases
- **Phase Execution Plan:** `docs/phase-execution-plan.md`
- **Original Design:** `image-hosting-mvp-distributed-systems.md`

---

**Status:** Ready for implementation
**Estimated time to apply all removals:** 45-60 minutes
**Lines of code reduction:** ~115 lines (~12% of backend code)
