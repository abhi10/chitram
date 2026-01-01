# Dev Container Testing Runbook

**Purpose:** Step-by-step guide for testing Chitram in Dev Containers (local VS Code or GitHub Codespaces)
**Last Updated:** 2025-01-01
**Phase:** 2 (MinIO Storage Backend)

---

## Quick Reference

| Service | URL | Credentials |
|---------|-----|-------------|
| FastAPI Docs | `http://localhost:8000/docs` | None |
| MinIO Console | `http://localhost:9001` | minioadmin / minioadmin |
| PostgreSQL | `localhost:5432` | app / localdev |

---

## Launch Options

### Option A: Local VS Code with Dev Containers Extension (Recommended)

**Prerequisites:**
- Docker Desktop installed and running
- VS Code with [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

**Steps:**

1. Open the project folder in VS Code
2. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
3. Type and select: **Dev Containers: Reopen in Container**
4. Wait 2-3 minutes for container build
5. Terminal opens automatically when ready

**Alternative:** Click the green `><` button in bottom-left corner → "Reopen in Container"

### Option B: GitHub Codespaces (Cloud)

1. Go to: https://github.com/abhi10/chitram
2. Click **Code** → **Codespaces** → **Create codespace on main**
3. Wait 2-3 minutes for container build

---

## Part 1: Verify Environment

### 1.1 Check Post-Create Script Output

Look for these success messages in the terminal:

```
✅ PostgreSQL is ready!
✅ MinIO is ready!
📝 Creating .env file...
📦 Installing Python dependencies...
🗄️ Running database migrations...
=========================================
✅ Development environment ready!
=========================================
```

### 1.2 Quick Verification (Automated)

Run the validation script:

```bash
./scripts/validate-env.sh
```

Or manually check services:

```bash
# Check all containers are running
docker-compose -f .devcontainer/docker-compose.yml ps

# Verify MinIO
curl -sf http://minio:9000/minio/health/live && echo "✅ MinIO OK"

# Verify PostgreSQL
pg_isready -h postgres -U app -d imagehost && echo "✅ PostgreSQL OK"
```

**Troubleshooting:**
- If PostgreSQL not ready → Wait and retry: `docker-compose ps`
- If MinIO not ready → Check: `docker-compose logs minio`
- If migrations fail → Run: `cd backend && uv run alembic upgrade head`

---

## Part 2: Start the Application

### 2.1 Start FastAPI Server

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0
```

**Expected Output:**
```
🚀 Starting Image Hosting API...
✅ Database initialized
✅ Storage initialized (MinIO)    # <-- Confirms MinIO backend
✅ Image Hosting API ready!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2.2 Open Swagger UI

**Local VS Code:**
- Open browser: http://localhost:8000/docs

**Codespaces:**
1. VS Code will show popup: "Your application running on port 8000 is available"
2. Click **Open in Browser**
3. Append `/docs` to URL → `https://<codespace-url>/docs`

---

## Part 3: Automated Tests

### 3.1 Run All Tests (Recommended)

```bash
cd backend
uv run pytest -v
```

Or use the test script:

```bash
./scripts/run-tests.sh
```

**Expected Results:**
```
tests/api/test_images.py::TestUploadImage::test_upload_valid_jpeg PASSED
tests/api/test_images.py::TestUploadImage::test_upload_valid_png PASSED
...
tests/unit/test_minio_storage.py::TestMinioStorageBackendInit::test_init_creates_bucket_if_not_exists PASSED
...
tests/integration/test_minio_integration.py::TestMinioIntegration::test_save_and_get_roundtrip PASSED
...

==================== 31 passed in X.XXs ====================
```

**Test Breakdown:**
| Suite | Count | Description |
|-------|-------|-------------|
| API Tests | 11 | Full CRUD via HTTP endpoints |
| Unit Tests | 11 | MinIO backend with mocking |
| Integration Tests | 9 | Real MinIO server operations |

### 3.2 Run Specific Test Suites

```bash
# API regression tests only
uv run pytest tests/api -v

# MinIO unit tests only
uv run pytest tests/unit -v

# MinIO integration tests only (requires MinIO running)
uv run pytest tests/integration -v

# With coverage report
uv run pytest --cov=app --cov-report=term-missing
```

---

## Part 4: Manual Testing (MinIO)

### 4.1 Verify MinIO Console

**Local:** Open http://localhost:9001

**Codespaces:** Ports tab → Find port `9001` → Click globe icon

Login: `minioadmin` / `minioadmin`
Navigate to **Buckets** → Should see `images` bucket

### 4.2 Upload Image via API

**Using Swagger UI:**

1. Open `/docs` in browser
2. Expand `POST /api/v1/images/upload`
3. Click **Try it out**
4. Click **Choose File** → Select a JPEG or PNG (< 5MB)
5. Click **Execute**

**Expected Response (201 Created):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "photo.jpg",
  "content_type": "image/jpeg",
  "file_size": 123456,
  "url": "/api/v1/images/a1b2c3d4-e5f6-7890-abcd-ef1234567890/file",
  "created_at": "2025-01-01T12:00:00.000000",
  "width": 1920,
  "height": 1080
}
```

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/images/upload" \
  -F "file=@/path/to/image.jpg"
```

### 4.3 Verify Image in MinIO

1. Go to MinIO Console → **Buckets** → `images`
2. You should see an object with UUID filename (e.g., `a1b2c3d4-....jpg`)
3. Click to preview/download

### 4.4 Download Image via API

**Using Swagger UI:**
1. Expand `GET /api/v1/images/{image_id}/file`
2. Enter the `id` from upload response
3. Click **Execute**
4. Click **Download file**

**Using curl:**
```bash
curl "http://localhost:8000/api/v1/images/{image_id}/file" --output downloaded.jpg
```

### 4.5 Get Image Metadata

**Using Swagger UI:**
1. Expand `GET /api/v1/images/{image_id}`
2. Enter the `id` from upload response
3. Click **Execute**

**Expected Response (200 OK):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "photo.jpg",
  "content_type": "image/jpeg",
  "file_size": 123456,
  "created_at": "2025-01-01T12:00:00.000000",
  "width": 1920,
  "height": 1080
}
```

### 4.6 Delete Image

**Using Swagger UI:**
1. Expand `DELETE /api/v1/images/{image_id}`
2. Enter the `id` from upload response
3. Click **Execute**

**Expected Response:** 204 No Content

**Verify Deletion:**
1. Check MinIO Console → Object should be gone
2. Try `GET /api/v1/images/{image_id}` → Should return 404

---

## Part 5: Storage Backend Verification

### 5.1 Confirm MinIO Backend is Active

```bash
cd backend
uv run python -c "
from app.config import get_settings
settings = get_settings()
print(f'Storage Backend: {settings.storage_backend}')
print(f'MinIO Endpoint: {settings.minio_endpoint}')
print(f'MinIO Bucket: {settings.minio_bucket}')
"
```

**Expected Output:**
```
Storage Backend: minio
MinIO Endpoint: minio:9000
MinIO Bucket: images
```

### 5.2 Direct MinIO Connection Test

```bash
cd backend
uv run python -c "
from minio import Minio
client = Minio('minio:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
print('Buckets:', [b.name for b in client.list_buckets()])
print('Objects in images:', [o.object_name for o in client.list_objects('images')])
"
```

### 5.3 Test Local Storage Fallback

To test with local storage instead:

```bash
cd backend
STORAGE_BACKEND=local uv run uvicorn app.main:app --reload --host 0.0.0.0
```

**Expected Output:**
```
✅ Storage initialized (local filesystem)
```

---

## Part 6: Health Checks

### 6.1 API Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development",
  "database": "connected",
  "storage": "minio"
}
```

### 6.2 Service Health Checks

```bash
# PostgreSQL
pg_isready -h postgres -U app -d imagehost

# MinIO
curl -sf http://minio:9000/minio/health/live && echo "MinIO OK"
```

---

## Part 7: Error Scenarios

### 7.1 Invalid File Type

Upload a `.txt` file:

```bash
echo "not an image" > test.txt
curl -X POST "http://localhost:8000/api/v1/images/upload" \
  -F "file=@test.txt"
```

**Expected Response (400):**
```json
{
  "detail": {
    "code": "INVALID_FILE_FORMAT",
    "message": "Only JPEG and PNG formats are supported",
    "details": {}
  }
}
```

### 7.2 Image Not Found

```bash
curl "http://localhost:8000/api/v1/images/nonexistent-id"
```

**Expected Response (404):**
```json
{
  "detail": {
    "code": "IMAGE_NOT_FOUND",
    "message": "Image with ID 'nonexistent-id' not found",
    "details": {}
  }
}
```

### 7.3 MinIO Unavailable

Stop MinIO and test graceful handling:

```bash
# Stop MinIO (from .devcontainer directory)
docker-compose stop minio

# Try to upload - should fail with error
curl -X POST "http://localhost:8000/api/v1/images/upload" \
  -F "file=@image.jpg"

# Restart MinIO
docker-compose start minio
```

---

## Part 8: Cleanup

### 8.1 Stop Server

Press `Ctrl+C` in the terminal running uvicorn.

### 8.2 Clean Test Data

```bash
# Use the cleanup script
./scripts/cleanup-test-data.sh

# Or manually clear MinIO bucket
cd backend
uv run python -c "
from minio import Minio
client = Minio('minio:9000', access_key='minioadmin', secret_key='minioadmin', secure=False)
for obj in client.list_objects('images'):
    client.remove_object('images', obj.object_name)
    print(f'Deleted: {obj.object_name}')
print('Bucket cleared')
"
```

### 8.3 Reset Database

```bash
cd backend
uv run alembic downgrade base
uv run alembic upgrade head
```

### 8.4 Exit Dev Container

**Local VS Code:**
- Press `Cmd+Shift+P` → "Dev Containers: Reopen Folder Locally"
- Or close VS Code window

**Codespaces:**
1. Click on Codespace name in bottom-left of VS Code
2. Select **Stop Current Codespace**
3. Or let it auto-stop after 30 minutes of inactivity

---

## Automation Scripts

The following scripts automate common tasks. Located in `scripts/` directory.

### Available Scripts

| Script | Purpose |
|--------|---------|
| `validate-env.sh` | Verify all services are running |
| `run-tests.sh` | Run full test suite with coverage |
| `smoke-test.sh` | Quick API smoke test (upload → get → delete) |
| `cleanup-test-data.sh` | Clear MinIO bucket and reset DB |

### Usage

```bash
# Make scripts executable (first time only)
chmod +x scripts/*.sh

# Run validation
./scripts/validate-env.sh

# Run all tests
./scripts/run-tests.sh

# Quick smoke test
./scripts/smoke-test.sh

# Cleanup
./scripts/cleanup-test-data.sh
```

---

## Troubleshooting

### Issue: "MinIO not ready" during startup

```bash
# Check MinIO container status
docker-compose -f .devcontainer/docker-compose.yml ps

# View MinIO logs
docker-compose -f .devcontainer/docker-compose.yml logs minio

# Restart MinIO
docker-compose -f .devcontainer/docker-compose.yml restart minio
```

### Issue: Tests skip integration tests

Integration tests auto-skip if MinIO is unavailable:

```
tests/integration/test_minio_integration.py::TestMinioIntegration::test_save_and_get_roundtrip SKIPPED (MinIO server not available)
```

**Fix:** Ensure MinIO is running and accessible:
```bash
curl -sf http://minio:9000/minio/health/live
```

### Issue: "Connection refused" errors

```bash
# Check all services are running
docker-compose -f .devcontainer/docker-compose.yml ps

# Restart all services
docker-compose -f .devcontainer/docker-compose.yml restart
```

### Issue: Storage shows "local filesystem" instead of MinIO

Check environment variables:
```bash
echo $STORAGE_BACKEND  # Should be "minio"
echo $MINIO_ENDPOINT   # Should be "minio:9000"
```

If missing, source from .env or restart the server.

### Issue: Dev Container fails to build (Local VS Code)

```bash
# Check Docker is running
docker info

# Remove old containers/images
docker system prune -a

# Rebuild container
# Cmd+Shift+P → "Dev Containers: Rebuild Container"
```

---

## Quick Test Checklist

Run through this checklist for a quick validation:

- [ ] Dev Container running (local or Codespaces)
- [ ] Post-create script completed successfully
- [ ] `./scripts/validate-env.sh` → All checks pass
- [ ] `./scripts/run-tests.sh` → All 31 tests pass
- [ ] Server starts with "Storage initialized (MinIO)"
- [ ] `./scripts/smoke-test.sh` → Upload/Get/Delete works
- [ ] Health check shows `"storage": "minio"`

**Estimated Time:** 10-15 minutes

---

## Related Documentation

- [README.md](../README.md) - Quick start guide
- [PHASE1_TESTING.md](./PHASE1_TESTING.md) - Phase 1 test results
- [validation-checklist.md](./validation-checklist.md) - Full validation checklist
- [TODO.md](../TODO.md) - Project progress tracker
