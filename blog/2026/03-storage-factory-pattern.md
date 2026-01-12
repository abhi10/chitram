# The Storage Factory Pattern: How Code Duplication Caused a Production Bug

**Date:** 2026-01-12
**Reading Time:** 10 minutes
**Tags:** #design-patterns #dry-principle #refactoring #production-bugs #python
**Repository:** https://github.com/abhi10/chitram/pull/65

---

## TL;DR

Duplicated storage initialization code between main.py and ai_tagging.py caused a production bug where the app used MinIO but the Celery worker used local filesystem, resulting in FileNotFoundError. The fix was a storage factory pattern that eliminated 17 lines of duplicate code and established a single source of truth. Lesson: Code duplication isn't just about style - it causes real production bugs when environments diverge.

---

## Who Should Read This

- Developers who've seen "works in dev, breaks in prod"
- Engineers learning the DRY (Don't Repeat Yourself) principle
- Backend developers building systems with multiple components
- Anyone who's copied if/else blocks "just to get it working"

## Prerequisites

- Basic understanding of Python async/await
- Familiarity with the Factory pattern (helpful but not required)
- Experience with multi-environment deployments

---

## The Bug That Shouldn't Exist

It was 1:00 PM on January 12th. I was 4 hours into debugging our Celery deployment. Fixed 4 bugs already. This was the 5th - and it was the worst.

```
[2026-01-12 04:04:32] Task ai_tagging.tag_image received
[2026-01-12 04:04:32] FileNotFoundError: File not found: c171dc53-c85e-4166-abe1-7f1ee03f48b6.jpeg
[2026-01-12 04:04:32] Task succeeded: {'success': False, 'tags_added': 0, 'error': 'File not found'}
```

**The file existed.** I could:
- Download it via the API (`GET /api/v1/images/{id}/file`) ✅
- See it in the MinIO console ✅
- Query it in the database ✅

But the Celery worker couldn't find it. Why?

---

## Context: The Architecture

**Chitram** has two components that access storage:

1. **FastAPI App** - Handles uploads, downloads, serves images
2. **Celery Worker** - Background tasks for AI tagging

Both need to read/write images. Simple, right?

```
         ┌─────────────┐
         │   MinIO     │ ← Where files actually live (production)
         └──────┬──────┘
                │
        ┌───────┴───────┐
        │               │
   ┌────▼────┐    ┌────▼────┐
   │   App   │    │  Worker │
   │         │    │         │
   │ Upload  │    │ AI Tag  │
   └─────────┘    └─────────┘
```

**Question:** How does each component know whether to use MinIO or local filesystem?

**Answer (naive):** Check `settings.storage_backend` and initialize accordingly.

**Problem:** I did that check in TWO places. They diverged.

---

## The Root Cause: Duplicated Logic

### What I Wrote

**main.py (lines 52-68):**
```python
# Initialize storage based on configuration
if settings.storage_backend == "minio":
    storage_backend = await MinioStorageBackend.create(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket=settings.minio_bucket,
        secure=settings.minio_secure,
        startup_timeout=settings.minio_startup_timeout,
    )
    print("✅ Storage initialized (MinIO)")
else:
    storage_backend = LocalStorageBackend(base_path=settings.local_storage_path)
    print("✅ Storage initialized (local filesystem)")

app.state.storage = StorageService(backend=storage_backend)
```

**ai_tagging.py (lines 111-126):** *[Same 17 lines copied]*

### What Happened

When I first wrote the Celery task, I copy-pasted the storage initialization from main.py. It worked locally because I used local storage for both.

Then I did a quick refactor: "Let me hardcode local storage in the worker for now, I'll fix it later."

```python
# ai_tagging.py (line 111)
storage_backend = LocalStorageBackend(base_path=settings.local_storage_path)
storage = StorageService(backend=storage_backend)
```

**"I'll fix it later"** became production deployment day. And production uses MinIO.

**Result:**
- App: `STORAGE_BACKEND=minio` → uploads to MinIO ✅
- Worker: Hardcoded local storage → reads from filesystem ❌
- Files: In MinIO, not on filesystem → FileNotFoundError

---

## The Investigation

### Step 1: Verify File Exists

```bash
$ curl https://chitram.io/api/v1/images/c171dc53-.../file --output test.jpg
# ✅ Download succeeds
```

### Step 2: Check MinIO

MinIO console → Bucket `images` → File `c171dc53-...jpeg` exists ✅

### Step 3: Check Worker Logs

```
FileNotFoundError: File not found: c171dc53-c85e-4166-abe1-7f1ee03f48b6.jpeg
```

Wait, that error comes from `LocalStorageBackend.get()`:

```python
class LocalStorageBackend(StorageBackend):
    async def get(self, key: str) -> bytes:
        file_path = self.base_path / key
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        # ...
```

**Aha!** The worker is using local storage, not MinIO.

### Step 4: Compare Code

Opened side-by-side:
- **main.py:** if/else checking `settings.storage_backend`
- **ai_tagging.py:** Hardcoded `LocalStorageBackend`

**Facepalm.**

---

## The Fix: Storage Factory Pattern

### Attempt 1: Copy-Paste the Fix

"Quick fix: copy the if/else from main.py into ai_tagging.py."

```python
# ai_tagging.py - Quick fix
if settings.storage_backend == "minio":
    storage_backend = await MinioStorageBackend.create(
        endpoint=settings.minio_endpoint,
        # ... 10 lines of config
    )
else:
    storage_backend = LocalStorageBackend(base_path=settings.local_storage_path)
```

**Commit:** `fix(celery): use MinIO storage backend in AI tagging task`

**Problem:** Now I have the SAME 17 lines in TWO places again. DRY principle violated.

**What if I add S3 support later?** Update it in 2 places? 3 places if I add another worker?

**No.** This needs a proper fix.

### Attempt 2: Factory Pattern

**Principle:** If you have complex initialization logic used in multiple places, create a factory function.

**Created:** `app/services/storage_factory.py`

```python
"""Storage backend factory.

Centralized storage initialization logic used by:
- Main application (app/main.py)
- Background tasks (app/tasks/ai_tagging.py)

This ensures consistent storage configuration across the application.
"""

from app.config import Settings
from app.services.storage_service import (
    LocalStorageBackend,
    MinioStorageBackend,
    StorageBackend,
)


async def create_storage_backend(settings: Settings) -> StorageBackend:
    """Create storage backend based on configuration.

    Single source of truth for storage initialization.
    Supports multiple backends: local filesystem, MinIO, S3, etc.

    Args:
        settings: Application settings with storage configuration

    Returns:
        Initialized storage backend ready for use

    Example:
        >>> settings = get_settings()
        >>> backend = await create_storage_backend(settings)
        >>> storage = StorageService(backend=backend)
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
        # Graceful fallback - if backend not recognized, use local
        # This provides graceful degradation
        return LocalStorageBackend(base_path=settings.local_storage_path)
```

**Updated main.py:**
```python
# Before (17 lines)
if settings.storage_backend == "minio":
    storage_backend = await MinioStorageBackend.create(...)
else:
    storage_backend = LocalStorageBackend(...)
app.state.storage = StorageService(backend=storage_backend)

# After (4 lines)
from app.services.storage_factory import create_storage_backend

storage_backend = await create_storage_backend(settings)
app.state.storage = StorageService(backend=storage_backend)
backend_name = "MinIO" if settings.storage_backend == "minio" else "local filesystem"
print(f"✅ Storage initialized ({backend_name})")
```

**Updated ai_tagging.py:**
```python
# Before (hardcoded local)
storage_backend = LocalStorageBackend(base_path=settings.local_storage_path)
storage = StorageService(backend=storage_backend)

# After (same factory)
from app.services.storage_factory import create_storage_backend

storage_backend = await create_storage_backend(settings)
storage = StorageService(backend=storage_backend)
```

**Result:**
- Eliminated: 17 lines of duplicate code (x2 = 34 lines)
- Added: 50 lines of tested factory logic
- Net: Storage initialization in ONE place

**Commit:** `refactor(storage): introduce shared storage factory pattern (DRY)`

---

## Why This Pattern Matters

### 1. Single Source of Truth

**Before:**
- main.py has storage logic
- ai_tagging.py has storage logic
- future_worker.py will need storage logic...

**After:**
- `create_storage_backend()` has storage logic
- Everyone calls the factory

**Benefit:** Change storage logic once, it propagates everywhere.

### 2. Consistency Guaranteed

**Before:**
```python
# main.py
if settings.storage_backend == "minio":
    backend = await MinioStorageBackend.create(...)

# ai_tagging.py - OOPS, forgot to check settings!
backend = LocalStorageBackend(...)
```

**After:** Impossible to get it wrong. Call factory → correct backend.

### 3. Easy to Extend

**Want to add S3 support?**

**Before:** Update 3 files (main.py, ai_tagging.py, future_worker.py)

**After:** Update 1 file (storage_factory.py):
```python
async def create_storage_backend(settings: Settings) -> StorageBackend:
    if settings.storage_backend == "s3":
        return S3StorageBackend(
            bucket=settings.s3_bucket,
            region=settings.s3_region,
        )
    elif settings.storage_backend == "minio":
        # ...
```

All consumers automatically support S3. Zero code changes needed.

### 4. Testable

**Test the factory once:**
```python
# tests/unit/test_storage_factory.py
@pytest.mark.asyncio
async def test_creates_minio_backend_when_configured():
    settings = Settings(
        storage_backend="minio",
        minio_endpoint="localhost:9000",
        minio_access_key="test",
        minio_secret_key="test",
        minio_bucket="test-bucket",
    )

    backend = await create_storage_backend(settings)

    assert isinstance(backend, MinioStorageBackend)
    assert backend.bucket == "test-bucket"
```

**Confidence:** All consumers use tested factory logic.

---

## The Broader Lesson: When to Use Factories

### Good Candidates for Factories

✅ **Complex initialization with multiple branches**
```python
if config.provider == "openai":
    return OpenAIProvider(api_key=...)
elif config.provider == "google":
    return GoogleProvider(credentials=...)
```

✅ **Same initialization used in multiple places**
- Main app + background workers
- Multiple services
- Tests + production code

✅ **Configuration-driven object creation**
- Storage backends (local, MinIO, S3, GCS)
- AI providers (OpenAI, Google, Claude)
- Auth providers (local JWT, Supabase, Auth0)

✅ **Initialization with side effects**
- Database connections
- External API clients
- Resource pooling

### Bad Candidates for Factories

❌ **Simple constructors**
```python
# Don't need a factory for this
user = User(name="Alice", email="alice@example.com")
```

❌ **One-time initialization**
```python
# If only one place needs it, inline is fine
config = Config.from_file("settings.yaml")
```

❌ **No branches or logic**
```python
# No decision-making → no factory needed
logger = Logger(level=DEBUG)
```

### The Rule of Thumb

**Create a factory when:**
1. You have (or will have) multiple callsites
2. Initialization logic has branches/decisions
3. You catch yourself copy-pasting initialization code

**Skip the factory when:**
1. Simple constructor call
2. Only one place needs it
3. No configuration logic

---

## Impact and Results

### Before Factory Pattern

```python
# main.py (17 lines)
if settings.storage_backend == "minio":
    storage_backend = await MinioStorageBackend.create(...)
else:
    storage_backend = LocalStorageBackend(...)

# ai_tagging.py (17 lines - different!)
storage_backend = LocalStorageBackend(...)  # Hardcoded
```

**Problems:**
- 34 lines of duplicate code
- Inconsistent between app and worker
- Caused production FileNotFoundError
- Hard to add new backends

### After Factory Pattern

```python
# storage_factory.py (50 lines, tested)
async def create_storage_backend(settings: Settings) -> StorageBackend:
    if settings.storage_backend == "minio":
        return await MinioStorageBackend.create(...)
    elif settings.storage_backend == "local":
        return LocalStorageBackend(...)
    else:
        return LocalStorageBackend(...)  # Graceful fallback

# main.py (1 line)
storage_backend = await create_storage_backend(settings)

# ai_tagging.py (1 line)
storage_backend = await create_storage_backend(settings)
```

**Benefits:**
- ✅ DRY: Logic in ONE place
- ✅ Consistency: Guaranteed same backend
- ✅ Fixed: Production bug resolved
- ✅ Extensible: Add S3/GCS easily
- ✅ Testable: Unit tests for factory

**Deployment Verification:**
```
[2026-01-12 04:04:32] OpenAI Vision returned 5 tags: ['bougainvillea', ...]
[2026-01-12 04:04:32] AI tagging complete: 5 tags added to image c171dc53
[2026-01-12 04:04:32] Task succeeded: {'success': True, 'tags_added': 5}
```

🎉 **Working in production!**

---

## Code Duplication: Not Just a Style Issue

**What I used to think:**
> "Code duplication is bad for maintainability and readability. But it's not a *bug*."

**What I learned:**
> **Code duplication CAUSES bugs when environments diverge.**

### The Pattern

1. **Day 1:** Copy-paste code to get it working
2. **Day 5:** Refactor one copy, forget the other
3. **Day 10:** Deploy to production (different environment)
4. **Day 10:** 🔥 Production bug 🔥

### Real-World Examples

**Storage Initialization (this post):**
- Dev: Local storage works
- Prod: MinIO fails → FileNotFoundError

**Database Connection Strings:**
- Dev: `localhost:5432` works
- Prod: `postgres:5432` fails → Connection refused

**API Keys:**
- Dev: Mock API works
- Prod: Real API with different config fails

### The Solution: DRY Principle

**Don't Repeat Yourself** isn't about code aesthetics. It's about having **one source of truth** that can't diverge.

**Factory pattern enforces this** by making it impossible to duplicate initialization logic.

---

## Action Items & Recommendations

### If You're Copy-Pasting Initialization Code

**Stop.** Ask yourself:

1. Can this logic change in different environments?
2. Will I need this in another place?
3. Does this have branches/decisions?

**If yes to any:** Create a factory instead.

### Pre-Commit Hook Idea

Add a hook to detect duplicated if/else blocks:

```bash
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: detect-duplicate-conditionals
      name: Detect duplicate if/else for storage/config
      entry: python scripts/detect_duplicates.py
      language: python
```

```python
# scripts/detect_duplicates.py
import ast
import sys

def find_duplicate_conditionals(files):
    # Parse AST, find if statements checking same variable
    # Warn if found in multiple files
    pass

if __name__ == "__main__":
    find_duplicate_conditionals(sys.argv[1:])
```

### Code Review Checklist

When reviewing PRs, watch for:
- [ ] Copy-pasted if/else blocks
- [ ] Hardcoded backends/providers
- [ ] Environment-specific initialization
- [ ] Missing abstraction for complex init

**Ask:** "Could this be a factory?"

---

## Related Resources

### From This Project
- [Phase 6 Deployment Debugging](01-phase6-deployment-debugging.md) - Full story of the 5 bugs
- [Storage Factory Source Code](https://github.com/abhi10/chitram/blob/main/backend/app/services/storage_factory.py)
- [Factory Unit Tests](https://github.com/abhi10/chitram/blob/main/backend/tests/unit/test_storage_factory.py)
- [PR #65: Storage Factory](https://github.com/abhi10/chitram/pull/65)

### Design Patterns
- [Factory Pattern - Refactoring Guru](https://refactoring.guru/design-patterns/factory-method)
- [DRY Principle - Wikipedia](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
- [Strategy Pattern (related)](https://refactoring.guru/design-patterns/strategy)

---

## Conclusion

A single line of duplicated code - `storage_backend = LocalStorageBackend(...)` - caused a production FileNotFoundError that took hours to debug. The fix was simple: a 50-line factory function that ensures consistent storage initialization.

**The real lesson?** Code duplication isn't just a code smell or style issue. **It's a bug waiting to happen** when environments diverge. Local dev works, production fails. Tests pass, deployment breaks.

**The Factory pattern solves this** by enforcing a single source of truth. You CAN'T duplicate the logic because it doesn't exist in multiple places. You call a function, get the right backend, move on.

**Next time you find yourself copy-pasting if/else initialization logic?** Stop. Create a factory. Your future self (and your production environment) will thank you.

---

## Discussion

Have you been bitten by duplicated initialization code? What patterns do you use to avoid it? How do you catch these issues before production?

Share your stories - I'd love to learn from your experiences. Comment below or open a [GitHub issue](https://github.com/abhi10/chitram/issues).

---

## About Chitram

Chitram is an open-source image hosting application built to learn distributed systems. It features automatic AI tagging with OpenAI Vision API, background job processing with Celery, and OAuth authentication with Supabase.

**Live Demo:** https://chitram.io
**Source Code:** https://github.com/abhi10/chitram
**Tech Stack:** FastAPI, PostgreSQL, MinIO, Redis, Celery

---

**License:** This post is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) - share with attribution.
