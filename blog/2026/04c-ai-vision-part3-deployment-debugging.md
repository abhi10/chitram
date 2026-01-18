# Deployment Debugging: How Code Duplication Caused a Production Bug (Part 3 of 3)

**Date:** 2026-01-13
**Reading Time:** 3 minutes
**Tags:** #deployment #debugging #dry-principle #production-bugs #refactoring
**Repository:** https://github.com/abhi10/chitram

---

## TL;DR

Deployed automatic AI tagging (Phase 6) expecting smooth rollout. Reality: 5 cascading infrastructure bugs, 3 hours of debugging. The final bug? Code duplication between `main.py` and `ai_tagging.py` caused storage backend mismatch - app uploaded to MinIO, worker read from local filesystem. Fix: Storage Factory Pattern. Lesson: Code duplication isn't just style - it causes production bugs.

---

## What We Expected vs What We Got

**What we expected:**
```
Deploy Phase 6 → Celery starts → AI tagging works → Done (30 minutes)
```

**What we got:**
```
Deploy → Worker crash → Fix → Redis auth error → Fix → Password quotes → Fix
  → Missing config → Fix → FileNotFoundError → Investigate 45 min → Fix → Done (3 hours)
```

**5 bugs. 5 PRs. 3 hours.**

---

## The 5 Cascading Bugs (Quick Summary)

### Bug #1: Missing `uv run` Prefix
```
celery: error: unrecognized arguments: worker --loglevel=info
```
**Fix:** `command: uv run celery -A app.celery_app worker`

### Bug #2: Redis Authentication Required
```
Cannot connect to redis://redis:6379/0: Authentication required
```
**Fix:** Pass Redis password in Celery broker URL

### Bug #3: Password Quotes Not Stripped
```
invalid username-password pair: redis://:"Y5LWC..."@redis:6379/0
```
**Fix:** Strip quotes from password: `tr -d '\n\r"'`

### Bug #4: App Missing Celery Config
```
Error 111 connecting to localhost:6379. Connection refused.
```
**Fix:** Add Celery URLs to app service (not just worker)

**Progress so far:** Worker running, tasks enqueuing, app connected... but uploads still failing.

---

## Bug #5: The Storage Backend Mismatch (The Real Problem)

**What we saw in logs:**

```
[2026-01-12 04:04:32] Task ai_tagging.tag_image received
[2026-01-12 04:04:32] FileNotFoundError: File not found: 0c9eb700-a1d7-41a6-b4b0-e976c8e111b6.jpeg
[2026-01-12 04:04:32] Task succeeded: {'success': False, 'tags_added': 0, 'error': 'File not found: ...'}
```

**Initial confusion:**
- ❓ File uploaded successfully (checked database)
- ❓ MinIO shows file exists (checked bucket)
- ❓ Worker logs show task received (Celery working)
- ❓ So why FileNotFoundError?

**45 minutes of investigation later...**

---

## The Root Cause: Code Duplication

**Problem:** Storage initialization logic was duplicated in TWO places:

**File 1: main.py (App startup)**
```python
# main.py lines 52-68
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Storage initialization for the app
    if settings.storage_backend == "minio":
        storage_backend = await MinioStorageBackend.create(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_bucket,
            secure=settings.minio_secure,
        )
    else:
        storage_backend = LocalStorageBackend(
            base_path=settings.local_storage_path
        )

    app.state.storage = StorageService(backend=storage_backend)
```

**File 2: ai_tagging.py (Celery worker)**
```python
# ai_tagging.py line 111 - HARDCODED!
storage_backend = LocalStorageBackend(base_path=settings.local_storage_path)
storage = StorageService(backend=storage_backend)
```

**The bug:**
- App reads `STORAGE_BACKEND=minio` → uploads to MinIO ✅
- Worker hardcoded to local → reads from local filesystem ❌
- **Files don't exist locally → FileNotFoundError**

**How did this happen?**

When implementing Celery worker, we copy-pasted storage initialization from `main.py` but simplified it to "just use local for now." Then we forgot to update it when we switched production to MinIO.

**Classic code duplication bug.**

---

## The Fix: Storage Factory Pattern

**Step 1: Create centralized factory**

```python
# NEW FILE: app/services/storage_factory.py

async def create_storage_backend(settings: Settings) -> StorageBackend:
    """
    Single source of truth for storage initialization.

    Used by both main.py (app) and ai_tagging.py (worker).
    """
    if settings.storage_backend == "minio":
        return await MinioStorageBackend.create(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_bucket,
            secure=settings.minio_secure,
            startup_timeout=settings.minio_startup_timeout,
        )
    elif settings.storage_backend == "local":
        return LocalStorageBackend(base_path=settings.local_storage_path)
    else:
        # Graceful fallback
        return LocalStorageBackend(base_path=settings.local_storage_path)
```

**Step 2: Update both files to use factory**

```python
# main.py (app startup)
from app.services.storage_factory import create_storage_backend

@asynccontextmanager
async def lifespan(app: FastAPI):
    storage_backend = await create_storage_backend(settings)
    app.state.storage = StorageService(backend=storage_backend)
```

```python
# ai_tagging.py (Celery worker)
from app.services.storage_factory import create_storage_backend

storage_backend = await create_storage_backend(settings)
storage = StorageService(backend=storage_backend)
```

**Result:** Both app and worker now use **exactly the same logic**. One environment variable controls both.

---

## Before vs After

**Before (17 lines duplicated):**
- main.py: 17 lines of storage init
- ai_tagging.py: 1 line (hardcoded local)
- **Total:** 18 lines, 2 different implementations

**After (DRY):**
- storage_factory.py: 20 lines (shared)
- main.py: 1 line (factory call)
- ai_tagging.py: 1 line (factory call)
- **Total:** 22 lines, 1 implementation

**Trade-off:** Slightly more lines, but:
- ✅ Single source of truth
- ✅ Consistent behavior guaranteed
- ✅ Easy to add S3, GCS, Azure Blob (change factory only)
- ✅ Unit testable (test factory in isolation)

---

## Production Verification

**After deploying the fix:**

```
[2026-01-12 04:04:32] Fetching image from MinIO: 0c9eb700-a1d7-41a6-b4b0-e976c8e111b6.jpeg
[2026-01-12 04:04:33] OpenAI Vision returned 5 tags: ['palms', 'tropical', 'greenery', 'blue sky', 'lush']
[2026-01-12 04:04:33] AI tagging complete: 5 tags added to image 0c9eb700-...
[2026-01-12 04:04:33] Task succeeded: {'success': True, 'tags_added': 5, 'error': None}
```

**🎉 AI tagging fully operational!**

**Live proof:** https://chitram.io/image/49337a614-4783-439b-8f72-16e87e1b5bdd

---

## Lessons Learned

### 1. Code Duplication ≠ Just Style

**Common misconception:** "DRY is about clean code, not correctness."

**Reality:** Duplicated logic diverges over time. What starts as "copy-paste for speed" becomes "production bug when environments differ."

**Rule:** If two files need the same complex initialization logic, create a factory.

### 2. Environment Parity Matters

**Local dev:**
- `STORAGE_BACKEND=local`
- No Redis password
- Synchronous tasks (mock provider)

**Production:**
- `STORAGE_BACKEND=minio`
- Redis password required
- Asynchronous Celery tasks

**Gap:** Hardcoded local storage in worker worked in dev, failed in prod.

**Fix:** Use environment variables everywhere. Never hardcode environment-specific values.

### 3. Integration Tests Catch Environment Bugs

**Unit tests:** 355/355 passing ✅
**E2E test:** Didn't exist ❌

**What we needed:**
```python
@pytest.mark.integration
async def test_upload_triggers_ai_tagging_end_to_end():
    """Test full flow: Upload → MinIO → Celery → OpenAI → Tags saved."""
    # Would have caught storage mismatch
```

**Lesson:** Unit tests validate logic. Integration tests validate infrastructure.

---

## Key Takeaway

**Code duplication doesn't just violate style guides - it causes production bugs when environments diverge.**

The storage factory pattern eliminated 17 lines of duplicated code and prevented this entire class of bugs. One environment variable (`STORAGE_BACKEND`) now controls both app and worker with guaranteed consistency.

**Pattern to remember:**
1. Spot duplicated initialization logic during code review
2. Create factory function as single source of truth
3. All consumers call factory (app, worker, tests)
4. Change logic once, affects all consumers

---

## Related Resources

**This Series:**
- [Part 1 - Provider System](04a-ai-vision-part1-provider-system.md)
- [Part 2 - Manual→Automatic](04b-ai-vision-part2-manual-to-automatic.md)

**Other Posts:**
- [Storage Factory Pattern](03-storage-factory-pattern.md) - Detailed implementation
- [Phase 6 Deployment Retrospective](../../docs/retrospectives/2026-01-12-phase6-deployment-debugging.md) - Full timeline

---

**Live Demo:** https://chitram.io
**Source Code:** https://github.com/abhi10/chitram

**License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
