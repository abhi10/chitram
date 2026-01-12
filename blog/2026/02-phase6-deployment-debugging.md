# Debugging 5 Cascading Infrastructure Failures: A Celery Deployment Story

**Date:** 2026-01-12
**Reading Time:** 15 minutes
**Tags:** #deployment #debugging #celery #redis #infrastructure #fastapi
**Repository:** https://github.com/abhi10/chitram

---

## TL;DR

Deployed automatic AI tagging with Celery workers to production. Everything looked good - CI passed, deployment succeeded. But images weren't getting tagged. What followed was a 3-hour debugging session that uncovered 5 cascading infrastructure issues, from missing command prefixes to duplicated code causing FileNotFoundError. The final fix? A storage factory pattern that eliminated code duplication and prevented future bugs.

---

## Who Should Read This

- Backend developers deploying distributed systems
- Engineers debugging Celery/Redis integration issues
- Developers learning systematic production debugging
- Anyone who's seen "FileNotFoundError" in one environment but not another

## Prerequisites

- Basic understanding of Celery and Redis
- Familiarity with Docker Compose
- Knowledge of FastAPI or similar web frameworks

---

## The Hook

**11:15 AM, January 12, 2026.** I merged PR #60 (Phase 6: Automatic AI Tagging) and watched the CD pipeline deploy to production. Green checkmarks everywhere. I uploaded a test image to https://chitram.io, got a success response... but when I checked the database, no AI tags appeared.

```sql
SELECT t.name, it.source FROM image_tags it JOIN tags t ON it.tag_id = t.id WHERE it.source = 'ai';
```

Result: *0 rows.*

Celery worker logs showed:
```
FileNotFoundError: File not found: 0c9eb700-a1d7-41a6-b4b0-e976c8e111b6.jpeg
```

The file existed in MinIO. The upload succeeded. But the worker couldn't find it. This was going to be interesting.

---

## Context: The Project

**Chitram** is an image hosting application I'm building to learn distributed systems. The architecture:

```
User Upload → FastAPI App → MinIO Storage
                  ↓
            Celery Queue (Redis)
                  ↓
            Celery Worker → Fetches image → OpenAI Vision API → Tags saved
```

**Phase 6 Goal:** Automatic AI tagging on every upload using background jobs.

**What I deployed:**
- New Celery worker service in docker-compose
- Background task service abstraction
- AI tagging task with retry logic
- Integration into upload endpoint

**CI Tests:** 355 passing (up from 323). All green.

**What could go wrong?**

---

## The 5 Bugs: A Debugging Journey

### Bug #1: Celery Command Not Found

**11:20 AM - First deployment**

```bash
$ docker logs deploy-celery-worker-1
celery: error: unrecognized arguments: worker --loglevel=info
```

**Wait, what?** The command looked correct:
```yaml
command: celery -A app.celery_app worker --loglevel=info --concurrency=2
```

**Investigation:** Our Docker image uses `uv` (modern Python package manager) with a virtual environment. The `celery` binary isn't in PATH - it's managed by uv.

**The Fix (PR #61):**
```yaml
command: uv run celery -A app.celery_app worker --loglevel=info --concurrency=2
```

**Lesson:** Always prefix commands with `uv run` in uv-managed environments. What works locally might fail in Docker if PATH differs.

**Verification:** `docker logs deploy-celery-worker-1` → Worker starts! But...

---

### Bug #2: Redis Authentication Required

**11:35 AM - After PR #61 deployment**

```
[ERROR] consumer: Cannot connect to redis://redis:6379/0: Authentication required..
Trying again in 4.00 seconds...
```

**Hypothesis:** Production Redis has a password (security best practice), but Celery URLs didn't include it.

**Investigation:** Checked docker-compose.yml:
```yaml
# celery-worker service (lines 247-250)
CELERY_BROKER_URL: redis://redis:6379/0  # ❌ No password!
CELERY_RESULT_BACKEND: redis://redis:6379/0
```

But Redis was configured with:
```yaml
# .env.production
REDIS_PASSWORD=Y5LWC...
```

**The Fix (PR #62):**

1. Make Celery URLs configurable:
```yaml
CELERY_BROKER_URL: ${CELERY_BROKER_URL:-redis://redis:6379/0}
CELERY_RESULT_BACKEND: ${CELERY_RESULT_BACKEND:-redis://redis:6379/0}
```

2. Update CD workflow to inject password:
```bash
# .github/workflows/cd.yml
REDIS_PASSWORD=$(grep '^REDIS_PASSWORD=' .env.production | cut -d'=' -f2-)
CELERY_URL="redis://:${REDIS_PASSWORD}@redis:6379/0"
echo "CELERY_BROKER_URL=$CELERY_URL" >> .env.production
```

**Lesson:** Never hardcode connection strings. Always use environment variables for credentials.

**Verification:** Worker connects... but new error!

---

### Bug #3: Invalid Username-Password Pair

**12:05 PM - After PR #62 deployment**

```
[ERROR] consumer: Cannot connect to redis://:**@redis:6379/0:
invalid username-password pair or user is disabled..
```

**Wait, the password is there (shown as `**`). Why "invalid"?**

**Investigation:** SSH'd into production server:
```bash
$ grep REDIS_PASSWORD .env.production
REDIS_PASSWORD="Y5LWC..."  # 🚨 QUOTES!
```

The CD workflow extracted the password WITH quotes:
```bash
redis://:"Y5LWC..."@redis:6379/0  # Quotes included in URL!
```

**The Fix (PR #63):**
```bash
# Strip quotes AND whitespace
REDIS_PASSWORD=$(grep '^REDIS_PASSWORD=' .env.production | cut -d'=' -f2- | tr -d '\n\r"')
```

**Lesson:** Always sanitize environment variable values - strip quotes, whitespace, newlines. `.env` files can have inconsistent formatting.

**Verification:** Worker connects successfully! 🎉

But wait... uploads still don't trigger tasks.

---

### Bug #4: App Can't Enqueue Tasks

**12:25 PM - After PR #63 deployment**

Uploaded test image. Checked app logs:
```
Failed to enqueue AI tagging task:
Error 111 connecting to localhost:6379. Connection refused.
```

**localhost:6379?** But Redis is at `redis:6379` on the Docker network!

**Investigation:** The **app service** in docker-compose.yml was missing Celery configuration:

```yaml
app:
  environment:
    # Lots of other env vars...
    # ❌ Missing: CELERY_BROKER_URL, CELERY_RESULT_BACKEND
```

The **worker service** had them (lines 247-250), but the **app** didn't. Without these, Celery client defaults to `localhost:6379`.

**Why wasn't this obvious?** Worker **consumes** tasks. App **produces** tasks. Both need the broker URL!

**The Fix (PR #64):**
```yaml
app:
  environment:
    # Celery Configuration (Phase 6)
    # App needs these to enqueue background tasks
    CELERY_BROKER_URL: ${CELERY_BROKER_URL:-redis://redis:6379/0}
    CELERY_RESULT_BACKEND: ${CELERY_RESULT_BACKEND:-redis://redis:6379/0}
    BACKGROUND_TASK_ENABLED: ${BACKGROUND_TASK_ENABLED:-true}
    BACKGROUND_TASK_PROVIDER: celery
```

**Lesson:** Both producers AND consumers need message broker configuration. Don't assume - verify all components.

**Verification:** Uploaded image. App logs:
```
INFO: AI tagging task enqueued: 18c9df67-... for image c171dc53-...
```

Success! Worker receives the task... and then:

```
FileNotFoundError: File not found: c171dc53-c85e-4166-abe1-7f1ee03f48b6.jpeg
```

Ugh.

---

### Bug #5: Storage Backend Mismatch (The Big One)

**1:00 PM - After PR #64 deployment**

```
[2026-01-12 04:04:32] Task ai_tagging.tag_image received
[2026-01-12 04:04:32] FileNotFoundError: File not found: c171dc53-...jpeg
[2026-01-12 04:04:32] Task succeeded: {'success': False, 'tags_added': 0, 'error': 'File not found'}
```

**This didn't make sense.** The file existed - I could download it via the API. MinIO showed it in the bucket. What was going on?

**Investigation:** Compared storage initialization code:

**main.py (lines 52-68):**
```python
if settings.storage_backend == "minio":
    storage_backend = await MinioStorageBackend.create(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        # ... MinIO config
    )
else:
    storage_backend = LocalStorageBackend(base_path=settings.local_storage_path)
```

**ai_tagging.py (line 111):**
```python
# 🚨 HARDCODED!
storage_backend = LocalStorageBackend(base_path=settings.local_storage_path)
```

**Oh no.**

- App uploads to MinIO ✅
- Worker tries to read from local filesystem ❌
- Files don't exist locally → FileNotFoundError

**Root Cause:** Code duplication. I copied the storage initialization logic from main.py when creating the Celery task, but forgot to include the if/else check. Local dev worked because I used local storage. Production failed because environments diverged.

**First Fix (Quick):** Duplicate the if/else logic into ai_tagging.py. Works, but violates DRY principle.

**Proper Fix (PR #65): Storage Factory Pattern**

Created centralized factory:
```python
# NEW FILE: app/services/storage_factory.py
async def create_storage_backend(settings: Settings) -> StorageBackend:
    """Single source of truth for storage initialization."""
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

**Updated both files:**
```python
# main.py (line 50) and ai_tagging.py (line 112)
storage_backend = await create_storage_backend(settings)
```

**Eliminated:** 17 lines of duplicate code
**Added:** 50 lines of tested factory logic
**Result:** Storage logic in ONE place

**Verification:**
```
[2026-01-12 04:04:32] OpenAI Vision returned 5 tags: ['bougainvillea', 'red flowers', 'vibrant colors', 'wooden fence', 'greenery']
[2026-01-12 04:04:32] AI tagging complete: 5 tags added to image c171dc53-...
[2026-01-12 04:04:32] Task succeeded: {'success': True, 'tags_added': 5, 'error': None}
```

**🎉 IT WORKS!**

---

## Why This Happened: Root Cause Analysis

### Immediate Causes

1. **Command format** - uv-specific syntax not documented
2. **Redis auth** - Configuration template missing password handling
3. **Password parsing** - Shell script didn't strip quotes
4. **Missing env vars** - App service config incomplete
5. **Code duplication** - Storage init logic copied, not abstracted

### Contributing Factors

**No Integration Tests:**
- Unit tests passed (352/354)
- But no end-to-end test: Upload → Task Enqueue → Worker Process → Tags Saved
- Local dev used MockTaskService (synchronous) - storage bug never triggered

**Environment Parity Gaps:**
- Local: Redis without password, local storage
- Production: Redis with password, MinIO storage
- Configuration drift not caught until deployment

**Complex Infrastructure:**
- Phase 6 added 4 new components: Redis broker, Celery worker, OpenAI API, MinIO
- Each needed consistent configuration
- Missing config in ONE place caused cascading failures

---

## Lessons Learned

### 1. Infrastructure Integration Tests Are Critical

**Problem:** Unit tests passed, but production deployment failed.

**Solution:** Add E2E integration test:
```python
@pytest.mark.integration
@pytest.mark.slow
async def test_upload_triggers_ai_tagging_e2e():
    """Test full flow: Upload → Celery → OpenAI → Tags"""
    # Upload image
    response = await client.post("/api/v1/images/upload", files=...)
    image_id = response.json()["id"]

    # Wait for Celery task (max 30s)
    for _ in range(30):
        tags = await get_image_tags(image_id)
        if any(tag.source == "ai" for tag in tags):
            break
        await asyncio.sleep(1)
    else:
        pytest.fail("AI tagging didn't complete in 30s")

    # Verify tags exist
    ai_tags = [t for t in tags if t.source == "ai"]
    assert len(ai_tags) > 0
```

### 2. Environment Parity Matters

**Problem:** "It works on my machine" masked production issues.

**Solution:**
- Create staging environment that mimics production
- Run smoke tests in staging before deploying to production
- Use same Redis password, MinIO setup, Celery config as production

### 3. Code Duplication Causes Production Bugs

**Problem:** Duplicated storage initialization diverged when environments changed.

**Solution:** Factory pattern for complex initialization:
- Single source of truth
- Easy to test
- Prevents drift
- Extensible (can add S3, GCS easily)

**Rule:** If you're copying if/else blocks for initialization, create a factory instead.

### 4. Sanitize Environment Variables

**Problem:** Quotes in `.env` file broke Redis URL.

**Solution:** Always strip quotes, whitespace, newlines:
```bash
VALUE=$(grep '^VAR=' .env | cut -d'=' -f2- | tr -d '\n\r"' | xargs)
```

### 5. Document Environment-Specific Commands

**Problem:** `uv run` prefix not in README or docker-compose comments.

**Solution:** Add comments in docker-compose.yml:
```yaml
command: uv run celery ...  # REQUIRED: uv manages virtualenv, prefix all commands
```

---

## What Went Well

**Incremental Debugging:**
- Fixed one issue at a time with separate PRs
- Verified each fix before moving to next issue
- Clear error messages guided investigation

**Production Monitoring:**
- Docker logs immediately showed errors
- Database queries confirmed missing tags
- Celery worker logs showed retry attempts

**Graceful Degradation:**
- Upload succeeded even when tagging failed
- Users not impacted by backend issues
- System degraded gracefully (Phase 6 design goal)

---

## Action Items

Based on this debugging session, here's what I'm adding to Phase 7:

### Immediate
- [x] Fix all 5 issues (PRs #61-65) ✅
- [x] Verify AI tagging works in production ✅
- [x] Document lessons learned (this post)

### Short Term (Next Sprint)
- [ ] Add E2E integration test for Celery AI tagging flow
- [ ] Create deployment checklist template
- [ ] Add `make verify-env` command to catch config drift early
- [ ] Document common docker-compose environment variable patterns

### Long Term (Next Quarter)
- [ ] Set up staging environment (DigitalOcean $12/month droplet)
- [ ] Add pre-commit hook to detect code duplication
- [ ] Implement blue-green deployments for zero-downtime updates

---

## The Bigger Picture

This debugging session taught me that **infrastructure integration is hard**. You can have 355 passing unit tests, green CI checks, and perfect code coverage - but still fail in production because of a missing environment variable or duplicated initialization code.

**The real lesson?** Test the seams. Test where components integrate:
- App ↔ Celery ↔ Redis
- App ↔ MinIO (in production config)
- Worker ↔ MinIO (different from app?)
- CD pipeline ↔ .env parsing

These integration points are where bugs hide.

---

## Related Resources

### From This Project
- [Phase 6 Implementation Summary](../../docs/implementation/phase6-automatic-ai-tagging-summary.md)
- [Phase 6 Retrospective](../../docs/retrospectives/2026-01-12-phase6-deployment-debugging.md)
- [PR #60](https://github.com/abhi10/chitram/pull/60) - Initial Phase 6 deployment
- [PR #61-65](https://github.com/abhi10/chitram/pulls) - Bug fixes
- [Storage Factory Pattern ADR](../../backend/app/services/storage_factory.py)

### External Resources
- [Celery Best Practices](https://docs.celeryq.dev/en/stable/userguide/tasks.html#best-practices)
- [The Twelve-Factor App - Dev/Prod Parity](https://12factor.net/dev-prod-parity)
- [Python uv Documentation](https://docs.astral.sh/uv/)

---

## Conclusion

What started as a simple feature deployment ("automatic AI tagging") turned into a 3-hour debugging marathon through 5 cascading infrastructure failures. But each bug taught something valuable:

1. Command execution in containerized environments
2. Authentication configuration in distributed systems
3. Shell script string handling
4. Producer/consumer configuration symmetry
5. The dangers of code duplication

**The final fix - the storage factory pattern - was the most important.** It not only solved the immediate bug but improved code quality by eliminating duplication. Future backends (S3, GCS, Azure Blob) can be added in ONE place.

**Would I have caught these bugs with better testing?** Absolutely. E2E integration tests that mimic production would have caught 4 of the 5 issues. But you can't test what you don't know you need to test. Sometimes you need to break production to learn what tests to write.

**The silver lining?** AI tagging now works flawlessly in production. Every image uploaded to https://chitram.io gets 5 AI-generated tags in ~10 seconds. And I have 5 new debugging stories to share with other developers.

---

## Discussion

Have you dealt with similar cascading infrastructure failures? What's your debugging process? How do you ensure environment parity between local and production?

I'd love to hear your stories - drop a comment or reach out on [GitHub](https://github.com/abhi10/chitram/issues).

---

## About Chitram

Chitram (చిత్రం - "image" in Telugu) is an open-source image hosting application I'm building to learn distributed systems. It features automatic AI tagging, background job processing, and OAuth authentication - all deployed on a single DigitalOcean droplet.

**Tech Stack:** FastAPI, PostgreSQL, MinIO, Redis, Celery, OpenAI Vision API
**Live Demo:** https://chitram.io
**Source Code:** https://github.com/abhi10/chitram

---

**License:** This post is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) - share with attribution.
