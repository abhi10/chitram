# Dev Container Testing Runbook

**Purpose:** Step-by-step guide for testing Chitram in Dev Containers (local VS Code or GitHub Codespaces)
**Last Updated:** 2026-01-02
**Phase:** 2 (MinIO Storage + Redis Caching)

---

## Quick Reference

| Service | URL | Credentials |
|---------|-----|-------------|
| FastAPI Docs | `http://localhost:8000/docs` | None |
| MinIO Console | `http://localhost:9001` | minioadmin / minioadmin |
| PostgreSQL | `localhost:5432` | app / localdev |
| Redis | `localhost:6379` | None (no password) |

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
✅ Redis is ready!
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

# Verify Redis
redis-cli -h redis ping && echo "✅ Redis OK"
```

**Troubleshooting:**
- If PostgreSQL not ready → Wait and retry: `docker-compose ps`
- If MinIO not ready → Check: `docker-compose logs minio`
- If Redis not ready → Check: `docker-compose logs redis`
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
✅ Redis cache connected          # <-- Confirms Redis caching
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
tests/unit/test_cache_service.py::TestCacheServiceConnection::test_connect_success PASSED
tests/unit/test_minio_storage.py::TestMinioStorageBackendInit::test_init_creates_bucket_if_not_exists PASSED
...
tests/integration/test_minio_integration.py::TestMinioIntegration::test_save_and_get_roundtrip PASSED
tests/integration/test_redis_integration.py::TestRedisIntegration::test_connection PASSED
...

==================== 43+ passed in X.XXs ====================
```

**Test Breakdown:**
| Suite | Count | Description |
|-------|-------|-------------|
| API Tests | 11 | Full CRUD via HTTP endpoints |
| Cache Unit Tests | 19 | Redis cache service with mocking |
| MinIO Unit Tests | 11 | MinIO backend with mocking |
| MinIO Integration | 9 | Real MinIO server operations |
| Redis Integration | 11 | Real Redis server operations |

### 3.2 Run Specific Test Suites

```bash
# API regression tests only
uv run pytest tests/api -v

# MinIO unit tests only
uv run pytest tests/unit -v

# MinIO integration tests only (requires MinIO running)
uv run pytest tests/integration/test_minio_integration.py -v

# Redis integration tests only (requires Redis running)
uv run pytest tests/integration/test_redis_integration.py -v

# Cache unit tests only
uv run pytest tests/unit/test_cache_service.py -v

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

## Part 5.5: Redis Caching Verification

### 5.5.1 Verify Cache is Working

**Step 1: Upload an image and note the ID**

```bash
# Upload test image
curl -X POST "http://localhost:8000/api/v1/images/upload" \
  -F "file=@/path/to/image.jpg"

# Note the "id" from response, e.g., "abc123-..."
```

**Step 2: First GET request (cache MISS)**

```bash
curl -i "http://localhost:8000/api/v1/images/{image_id}"
```

**Expected Headers:**
```
HTTP/1.1 200 OK
X-Cache: MISS
Content-Type: application/json
```

**Step 3: Second GET request (cache HIT)**

```bash
curl -i "http://localhost:8000/api/v1/images/{image_id}"
```

**Expected Headers:**
```
HTTP/1.1 200 OK
X-Cache: HIT
Content-Type: application/json
```

### 5.5.2 Verify Cache Keys in Redis

```bash
# Connect to Redis CLI
redis-cli -h redis

# List all cache keys
KEYS chitram:image:*

# Get specific cached metadata
GET chitram:image:{image_id}

# Check TTL (should be ~3600 seconds for new entries)
TTL chitram:image:{image_id}
```

### 5.5.3 Verify Cache Invalidation on Delete

```bash
# Delete image via API
curl -X DELETE "http://localhost:8000/api/v1/images/{image_id}"

# Check Redis - key should be gone
redis-cli -h redis GET chitram:image:{image_id}
# Returns: (nil)
```

### 5.5.4 Test Graceful Degradation

**Stop Redis and verify API still works:**

```bash
# Stop Redis container
docker-compose -f .devcontainer/docker-compose.yml stop redis

# API should still work (X-Cache: DISABLED)
curl -i "http://localhost:8000/api/v1/images/{image_id}"

# Health check shows cache disconnected
curl "http://localhost:8000/health"
# {"status": "degraded", "cache": "disconnected", ...}

# Restart Redis
docker-compose -f .devcontainer/docker-compose.yml start redis
```

### 5.5.5 Check Cache Statistics

```bash
# Connect to Redis CLI
redis-cli -h redis

# Get cache hit/miss statistics
INFO stats | grep keyspace
# keyspace_hits:XX
# keyspace_misses:XX
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
  "storage": "minio",
  "cache": "connected"
}
```

**Cache Status Values:**
- `connected` - Redis is healthy and caching is active
- `disconnected` - Redis unavailable, system running without cache
- `disabled` - Caching disabled via `CACHE_ENABLED=false`

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

### Issue: Redis not connecting / X-Cache always DISABLED

```bash
# Check Redis container is running
docker-compose -f .devcontainer/docker-compose.yml ps redis

# Test Redis connectivity
redis-cli -h redis ping
# Expected: PONG

# Check Redis logs
docker-compose -f .devcontainer/docker-compose.yml logs redis

# Verify environment variables
echo $REDIS_HOST     # Should be "redis"
echo $CACHE_ENABLED  # Should be "true" or unset

# Restart Redis
docker-compose -f .devcontainer/docker-compose.yml restart redis
```

### Issue: Redis integration tests skipping

Integration tests auto-skip if Redis is unavailable:

```
tests/integration/test_redis_integration.py::TestRedisIntegration::test_connection SKIPPED (Redis server not available)
```

**Fix:** Ensure Redis is running and accessible:
```bash
redis-cli -h redis ping
```

---

## Quick Test Checklist

Run through this checklist for a quick validation:

- [ ] Dev Container running (local or Codespaces)
- [ ] Post-create script completed successfully
- [ ] `./scripts/validate-env.sh` → All checks pass
- [ ] `./scripts/run-tests.sh` → All 43+ tests pass
- [ ] Server starts with "Storage initialized (MinIO)" and "Redis cache connected"
- [ ] `./scripts/smoke-test.sh` → Upload/Get/Delete works
- [ ] Health check shows `"storage": "minio"` and `"cache": "connected"`
- [ ] First GET returns `X-Cache: MISS`, second returns `X-Cache: HIT`

**Estimated Time:** 10-15 minutes

---

## Related Documentation

- [README.md](../README.md) - Quick start guide
- [PHASE1_TESTING.md](./PHASE1_TESTING.md) - Phase 1 test results
- [validation-checklist.md](./validation-checklist.md) - Full validation checklist
- [TODO.md](../TODO.md) - Project progress tracker
