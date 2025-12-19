# Phase 1 Validation Checklist

**Purpose:** Verify scaffolding is functional before adding features
**Status:** 🔴 Not started
**Last Updated:** 2025-12-13

---

## Pre-Validation Setup

### Environment Choice

- [ ] **Choose validation environment:**
  - [ ] Option A: GitHub Codespaces (recommended - zero local setup)
  - [ ] Option B: Local DevContainer (requires Docker Desktop)
  - [ ] Option C: Manual local setup (requires PostgreSQL + MinIO)

---

## Phase 1: Missing Files & Configuration

### 1.1 Python Package Files
**Status:** ⚠️ Missing __init__.py files

- [ ] Create `backend/app/__init__.py` (can be empty)
- [ ] Create `backend/app/api/__init__.py` (can be empty)
- [ ] Create `backend/app/models/__init__.py` (can be empty)
- [ ] Create `backend/app/schemas/__init__.py` (can be empty)
- [ ] Create `backend/app/services/__init__.py` (can be empty)
- [ ] Create `backend/app/utils/__init__.py` (can be empty)
- [ ] Create `backend/tests/__init__.py` (can be empty)
- [ ] Create `backend/tests/api/__init__.py` (can be empty)

**Expected:** Python recognizes directories as packages

### 1.2 Alembic Setup
**Status:** 🔴 Not created (will block database initialization)

- [ ] Run `cd backend && uv run alembic init alembic`
- [ ] Edit `backend/alembic.ini`:
  - [ ] Update `sqlalchemy.url` to use env var or remove (we'll use env.py)
- [ ] Edit `backend/alembic/env.py`:
  - [ ] Import `from app.config import get_settings`
  - [ ] Import `from app.database import engine`
  - [ ] Import `from app.models.image import Image` (for metadata)
  - [ ] Update `target_metadata = Image.metadata`
  - [ ] Update `config.set_main_option("sqlalchemy.url", get_settings().database_url)`
  - [ ] Configure async support (use `run_async`)
- [ ] Create initial migration:
  ```bash
  uv run alembic revision --autogenerate -m "Initial schema: images table"
  ```
- [ ] Review generated migration file
- [ ] Apply migration: `uv run alembic upgrade head`

**Expected:** `alembic_version` and `images` tables created in PostgreSQL

### 1.3 Git Setup (If Not Done)
- [ ] Run `git init` (if not a repo)
- [ ] Add remote: `git remote add origin <YOUR_REPO_URL>`
- [ ] Initial commit:
  ```bash
  git add .
  git commit -m "feat: Phase 1 scaffolding

  - FastAPI backend structure
  - PostgreSQL + MinIO integration
  - DevContainer configuration
  - Test suite scaffolding
  - Documentation (ADRs, workflow, requirements)"
  ```
- [ ] Push to GitHub: `git push -u origin main`

**Expected:** Code on GitHub, ready for Codespaces

---

## Phase 2: Environment Validation

### 2.1 Codespaces Setup (If Using)
- [ ] Go to GitHub repo → Code → Codespaces → Create codespace
- [ ] Wait for container build (~2-3 minutes first time)
- [ ] Check post-create.sh output:
  - [ ] ✅ PostgreSQL is ready
  - [ ] ✅ MinIO is ready
  - [ ] ✅ .env file created
  - [ ] ✅ Dependencies installed
  - [ ] ⚠️ Migrations (will fail until Alembic set up)
  - [ ] ✅ MinIO bucket created

**Troubleshooting:**
- PostgreSQL not ready? Check `docker-compose.yml` health check
- MinIO not ready? Check port 9000 accessible
- Migrations failed? Expected - do Alembic setup (1.2)

### 2.2 Local Setup (If Using)
- [ ] Start services: `cd .devcontainer && docker-compose up -d`
- [ ] Verify PostgreSQL: `docker-compose ps` (should show healthy)
- [ ] Verify MinIO: Visit http://localhost:9001 (user: minioadmin/minioadmin)
- [ ] Install deps: `cd ../backend && uv sync`
- [ ] Copy env: `cp .env.example .env`
- [ ] Run post-create.sh manually: `bash ../.devcontainer/post-create.sh`

**Expected:** All services running, dependencies installed

---

## Phase 3: Code Validation

### 3.1 Import Validation
**Purpose:** Catch syntax errors, missing imports, circular dependencies

```bash
cd backend
```

- [ ] Test config import: `uv run python -c "from app.config import get_settings; print(get_settings())"`
- [ ] Test database import: `uv run python -c "from app.database import get_db; print('DB OK')"`
- [ ] Test models import: `uv run python -c "from app.models.image import Image; print(Image.__tablename__)"`
- [ ] Test schemas import: `uv run python -c "from app.schemas.image import ImageResponse; print('Schemas OK')"`
- [ ] Test services import: `uv run python -c "from app.services.storage_service import StorageService; print('Storage OK')"`
- [ ] Test services import: `uv run python -c "from app.services.image_service import ImageService; print('ImageService OK')"`
- [ ] Test API import: `uv run python -c "from app.api.images import router; print('API OK')"`
- [ ] Test main import: `uv run python -c "from app.main import app; print('Main OK')"`

**Expected:** All imports succeed with no errors

**Common Issues:**
- `ModuleNotFoundError` → Missing __init__.py or wrong import path
- `ImportError: cannot import name` → Typo in class/function name
- `ImportError: circular import` → Reorganize imports (use TYPE_CHECKING)

### 3.2 Database Connection
```bash
cd backend
```

- [ ] Run connection test:
  ```python
  uv run python -c "
  import asyncio
  from app.database import engine
  from sqlalchemy import text

  async def test():
      async with engine.connect() as conn:
          result = await conn.execute(text('SELECT 1'))
          print('DB Connected:', result.scalar())

  asyncio.run(test())
  "
  ```

**Expected:** Output: `DB Connected: 1`

### 3.3 Storage Service Validation
```bash
cd backend
```

- [ ] Test MinIO connection:
  ```python
  uv run python -c "
  from minio import Minio
  client = Minio('minio:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
  print('MinIO connected:', client.bucket_exists('images'))
  "
  ```

**Expected:** Output: `MinIO connected: True`

---

## Phase 4: Test Suite Validation

### 4.1 Run All Tests
```bash
cd backend
```

- [ ] Run with verbose output: `uv run pytest -v`
- [ ] Check test results:
  - [ ] All tests pass (green)
  - [ ] No import errors
  - [ ] No fixture errors
  - [ ] Coverage report generated

**Expected Output:**
```
tests/api/test_images.py::TestUploadImage::test_upload_valid_jpeg PASSED
tests/api/test_images.py::TestUploadImage::test_upload_valid_png PASSED
tests/api/test_images.py::TestUploadImage::test_upload_invalid_format PASSED
...
========== X passed in Y.YYs ==========
```

### 4.2 Test Coverage
- [ ] Run with coverage: `uv run pytest --cov=app --cov-report=term-missing`
- [ ] Review coverage percentage (target: >80% for Phase 1)
- [ ] Identify untested code paths

**Expected:** Coverage report showing tested lines

### 4.3 Fix Test Failures
For each failing test:
- [ ] Read error message and stack trace
- [ ] Identify root cause (fixture? assertion? logic?)
- [ ] Fix code or test
- [ ] Re-run: `uv run pytest tests/api/test_images.py::test_name -v`
- [ ] Document fix in `docs/sessions/2025-12-13-validation.md`

---

## Phase 5: Application Validation

### 5.1 Start Server
```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0
```

- [ ] Server starts without errors
- [ ] See output: `Application startup complete`
- [ ] See output: `Uvicorn running on http://0.0.0.0:8000`
- [ ] No import errors in startup
- [ ] Lifespan events execute (check logs)

**Troubleshooting:**
- Import errors? Go back to Phase 3.1
- Database connection error? Check PostgreSQL is running
- Storage error? Check MinIO is running

### 5.2 Swagger UI Validation
- [ ] Open browser: http://localhost:8000/docs
- [ ] Swagger UI loads successfully
- [ ] See all endpoints:
  - [ ] `POST /api/v1/images/upload`
  - [ ] `GET /api/v1/images/{image_id}`
  - [ ] `GET /api/v1/images/{image_id}/file`
  - [ ] `DELETE /api/v1/images/{image_id}`
  - [ ] `GET /health`
- [ ] Click endpoint → See schema documentation
- [ ] Request/response models visible

**Expected:** Clean Swagger UI with all endpoints documented

### 5.3 Health Check Endpoint
- [ ] In Swagger: Execute `GET /health`
- [ ] Response status: 200 OK
- [ ] Response body:
  ```json
  {
    "status": "healthy",
    "database": "connected"
  }
  ```

**Expected:** Health check passes, DB connection confirmed

### 5.4 Upload Image (Happy Path)
- [ ] Prepare test image (JPEG or PNG, < 5MB)
- [ ] In Swagger: Execute `POST /api/v1/images/upload`
- [ ] Upload file
- [ ] Response status: 201 Created
- [ ] Response contains:
  - [ ] `id` (UUID)
  - [ ] `filename`
  - [ ] `content_type`
  - [ ] `size_bytes`
  - [ ] `width`, `height`
  - [ ] `checksum`
  - [ ] `uploaded_at`
- [ ] Copy `id` for next tests

**Expected:** Image uploaded successfully, metadata returned

### 5.5 Get Image Metadata
- [ ] In Swagger: Execute `GET /api/v1/images/{image_id}` with ID from 5.4
- [ ] Response status: 200 OK
- [ ] Response matches upload response
- [ ] All fields present

**Expected:** Metadata retrieved successfully

### 5.6 Download Image File
- [ ] In Swagger: Execute `GET /api/v1/images/{image_id}/file`
- [ ] Response status: 200 OK
- [ ] Response headers:
  - [ ] `Content-Type: image/jpeg` or `image/png`
  - [ ] `Content-Disposition: inline; filename="..."`
- [ ] Download file
- [ ] Open file → Verify it's the correct image

**Expected:** Image downloads and opens correctly

### 5.7 Delete Image
- [ ] In Swagger: Execute `DELETE /api/v1/images/{image_id}`
- [ ] Response status: 204 No Content
- [ ] Try to get metadata again: `GET /api/v1/images/{image_id}`
- [ ] Response status: 404 Not Found
- [ ] Error response:
  ```json
  {
    "code": "IMAGE_NOT_FOUND",
    "message": "Image not found",
    "details": {}
  }
  ```

**Expected:** Image deleted, subsequent requests return 404

### 5.8 Error Scenarios
Test error handling:

- [ ] **Invalid format:**
  - Upload .txt file → Expect 400 with `INVALID_FILE_FORMAT`

- [ ] **File too large:**
  - Upload 6MB image → Expect 400 with `FILE_TOO_LARGE`

- [ ] **Non-existent image:**
  - GET `/api/v1/images/00000000-0000-0000-0000-000000000000`
  - Expect 404 with `IMAGE_NOT_FOUND`

**Expected:** All errors return structured format with proper codes

---

## Phase 6: Code Quality Validation

### 6.1 Linting
```bash
cd backend
```

- [ ] Run Ruff: `uv run ruff check .`
- [ ] Fix issues: `uv run ruff check --fix .`
- [ ] No errors remain

**Expected:** `All checks passed!`

### 6.2 Formatting
```bash
cd backend
```

- [ ] Run Black: `uv run black . --check`
- [ ] If needed, format: `uv run black .`

**Expected:** `All done! ✨ 🍰 ✨`

### 6.3 Type Checking (Optional)
```bash
cd backend
```

- [ ] Run mypy: `uv run mypy app/`
- [ ] Review type errors (if strict mode enabled)

---

## Phase 7: Documentation Validation

### 7.1 README Accuracy
- [ ] Follow README Quick Start instructions
- [ ] Verify all commands work
- [ ] Check links to documentation files
- [ ] Verify API endpoint list matches implementation

### 7.2 Code Review Checklist
- [ ] Open `docs/code-review-checklist.md`
- [ ] Follow reading order for one phase
- [ ] Verify file references are correct (file:line)
- [ ] Check if patterns described match implementation

### 7.3 ADR Consistency
- [ ] Review each ADR in `docs/adr/`
- [ ] Verify code matches decisions (e.g., ADR-0001 says FastAPI → using FastAPI)
- [ ] Check no contradictions

---

## Validation Summary

### Results Tracking

| Phase | Status | Issues Found | Notes |
|-------|--------|--------------|-------|
| 1. Missing Files | ⬜ | | |
| 2. Environment | ⬜ | | |
| 3. Code | ⬜ | | |
| 4. Tests | ⬜ | | |
| 5. Application | ⬜ | | |
| 6. Code Quality | ⬜ | | |
| 7. Documentation | ⬜ | | |

**Legend:** ⬜ Not Started | 🔄 In Progress | ✅ Passed | ❌ Failed

### Issues Log

Document issues found during validation:

```markdown
1. [Phase X.Y] Issue description
   - Root cause: ...
   - Fix applied: ...
   - Status: ✅ Fixed / 🔄 In Progress / ⏸️ Deferred

2. ...
```

---

## Post-Validation Tasks

After all phases pass:

- [ ] Create validation session log: `docs/sessions/2025-12-13-validation.md`
- [ ] Update `CLAUDE.md` current status to "Phase 1 validated ✅"
- [ ] Update `CLAUDE.md` pending work (remove completed items)
- [ ] Git commit validation fixes:
  ```bash
  git add .
  git commit -m "fix: Phase 1 validation fixes

  - Add missing __init__.py files
  - Set up Alembic migrations
  - Fix import errors
  - All tests passing
  - API endpoints verified working"
  git push
  ```
- [ ] Tag release: `git tag v0.1.0-alpha -m "Phase 1 scaffolding validated"`
- [ ] Celebrate! 🎉

---

## Appendix: Common Issues & Fixes

### Import Errors
```
ModuleNotFoundError: No module named 'app'
→ Add missing __init__.py files
→ Check PYTHONPATH or run from backend/ directory
```

### Database Connection Errors
```
Connection refused [Errno 61]
→ PostgreSQL not running: docker-compose up -d postgres
→ Wrong host: Check .env DATABASE_URL (use 'postgres' in Docker, 'localhost' locally)
```

### MinIO Errors
```
S3Error: NoSuchBucket
→ Bucket not created: Run Python snippet in post-create.sh manually
```

### Alembic Errors
```
Can't locate revision identified by 'head'
→ Alembic not initialized: Run alembic init alembic
→ No migrations: Run alembic revision --autogenerate
```

### Test Failures
```
fixture 'client' not found
→ Missing __init__.py in tests/
→ conftest.py not in correct location
```

---

**Validation started:** ___________
**Validation completed:** ___________
**Total issues found:** ___________
**Scaffolding status:** 🔴 Not Validated / ✅ Validated
