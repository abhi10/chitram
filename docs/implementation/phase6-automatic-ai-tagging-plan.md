# Phase 6: Automatic AI Tagging - Implementation Plan

**Status:** 🚧 In Progress
**Branch:** `feat/phase6-automatic-ai-tagging`
**Started:** 2026-01-11
**Prerequisites:** Phase 5 complete ✅

---

## Overview

Implement automatic AI tagging on image upload using background job queue (Celery + Redis) with retry logic and graceful error handling.

## Goals

1. **Automatic Tagging** - Tag images immediately after upload (no manual endpoint)
2. **Background Processing** - Don't block upload response (async)
3. **Retry Logic** - Handle transient failures (3 attempts, exponential backoff)
4. **Provider Fallback** - OpenAI → Google → Mock (if all fail)
5. **Graceful Degradation** - Upload succeeds even if AI tagging fails
6. **Maintainability** - Decoupled, testable, evolutionary architecture

## Non-Goals (Deferred to Phase 7+)

- ❌ Distributed Celery workers (single worker for MVP)
- ❌ Task monitoring UI (Flower)
- ❌ Advanced retry strategies (dead letter queue)
- ❌ Task prioritization
- ❌ Batch tagging of existing images

---

## Architecture Principles

### 1. Decoupled Architecture

**Goal:** Each component should be independently testable and replaceable.

```
Upload API → Background Task Service → AI Provider
     ↓              ↓                      ↓
   Image         Celery Task          OpenAI/Google/Mock
```

**Benefits:**
- Can test upload without Celery
- Can test AI tagging without upload
- Can swap task queue (Celery → RQ → Cloud Tasks)

### 2. Evolutionary Architecture

**Goal:** System can evolve without major rewrites.

**Phase 6 (MVP):**
```
Upload → Trigger Task → AI Tag → Save
```

**Future (Phase 7+):**
```
Upload → Trigger Task → [Tag Pipeline] → Save
                            ↓
                    - AI Tagging
                    - NSFW Detection
                    - Duplicate Detection
                    - Face Recognition
```

**Key:** Task service accepts generic "processors" - easy to add new ones.

### 3. DRY Principle

**Avoid:**
- Duplicating AI provider logic (use existing `create_ai_provider()`)
- Duplicating retry logic (centralize in task service)
- Duplicating error handling (consistent error wrapper)

**Reuse:**
- Existing AI provider abstraction (Phase 5)
- Existing tag service (Phase 2A)
- Existing error schemas

### 4. Ease of Maintenance

**Clear Interfaces:**
```python
class BackgroundTaskService(ABC):
    """Abstract task service - easy to swap implementations."""

    @abstractmethod
    async def enqueue_ai_tagging(self, image_id: str) -> str:
        """Enqueue AI tagging task, return task ID."""
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> TaskStatus:
        """Check task status."""
        pass
```

**Benefits:**
- Can mock for tests
- Can swap Celery for RQ
- Clear contract

### 5. Graceful Error Handling

**Principle:** Upload always succeeds, AI tagging is best-effort.

```python
# Upload endpoint
try:
    image = await image_service.create(...)
    await background_tasks.enqueue_ai_tagging(image.id)
except Exception as e:
    # Log error but don't fail upload
    logger.error(f"Failed to enqueue AI tagging: {e}")
    # Image still saved, user can tag manually or retry later
```

**Benefits:**
- User never sees AI tagging failures
- Can retry failed tasks later
- System degrades gracefully

---

## Sub-Feature Breakdown

Each sub-feature will be a separate commit following best practices.

### Sub-Feature 1: Add Celery + Redis Infrastructure

**Goal:** Set up task queue infrastructure without changing application logic.

**Files:**
- `backend/pyproject.toml` - Add celery, redis dependencies
- `backend/app/celery_app.py` - Celery app configuration
- `backend/app/config.py` - Add Celery settings
- `deploy/docker-compose.yml` - Add redis and celery worker services

**Testing:**
- Celery worker starts successfully
- Can connect to Redis
- Basic task execution works

**Commit Message:**
```
feat(phase6): add Celery and Redis infrastructure

- Add celery and redis dependencies
- Create Celery app with Redis broker
- Add Celery configuration to Settings
- Update docker-compose.yml with redis and celery worker
- Zero changes to existing API logic (decoupled)

Phase 6 Sub-Feature 1/7
```

### Sub-Feature 2: Create Background Task Service

**Goal:** Abstract task queue behind service interface (DRY + Decoupled).

**Files:**
- `backend/app/services/background/__init__.py` - Package init
- `backend/app/services/background/base.py` - Abstract interface
- `backend/app/services/background/celery_service.py` - Celery implementation
- `backend/app/services/background/mock_service.py` - Mock for tests

**Architecture:**
```python
class BackgroundTaskService(ABC):
    """Abstract base - can swap implementations."""
    async def enqueue_ai_tagging(self, image_id: str) -> str: ...
    async def get_task_status(self, task_id: str) -> TaskStatus: ...

class CeleryTaskService(BackgroundTaskService):
    """Production implementation using Celery."""

class MockTaskService(BackgroundTaskService):
    """Test implementation - runs synchronously."""
```

**Benefits:**
- Tests don't need Celery
- Can swap to RQ/Cloud Tasks later
- Clear interface

**Testing:**
- Unit tests for both implementations
- Mock service runs synchronously for fast tests

**Commit Message:**
```
feat(phase6): create background task service abstraction

- Add BackgroundTaskService ABC with clear interface
- Implement CeleryTaskService for production
- Implement MockTaskService for tests (synchronous)
- Factory function create_task_service(settings)
- Follows Strategy pattern (like AI providers)

Benefits:
- Decoupled from Celery (easy to swap)
- Fast tests (mock service)
- Evolutionary (can add task types)

Phase 6 Sub-Feature 2/7
```

### Sub-Feature 3: Create AI Tagging Celery Task

**Goal:** Define the actual background task that runs AI tagging.

**Files:**
- `backend/app/tasks/__init__.py` - Package init
- `backend/app/tasks/ai_tagging.py` - AI tagging task definition

**Task Design:**
```python
@celery_app.task(
    name="ai_tagging.tag_image",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
)
def tag_image_task(self, image_id: str) -> dict:
    """
    Background task to analyze image and add AI tags.

    Retry logic:
    - Attempt 1: Immediate
    - Attempt 2: After 1 minute
    - Attempt 3: After 2 minutes
    - Attempt 4: After 4 minutes

    Graceful degradation:
    - If all retries fail, log error but don't crash
    - Image remains without AI tags (can retry later)
    """
    try:
        # Use existing AI provider (DRY)
        ai_provider = create_ai_provider(settings)

        # Fetch image bytes
        image = db.get(Image, image_id)
        image_bytes = storage.get(image.storage_key)

        # Analyze
        tags = await ai_provider.analyze_image(image_bytes)

        # Save (reuse existing tag service - DRY)
        tag_service.add_tags(image_id, tags, source="ai")

        return {"success": True, "tags_added": len(tags)}

    except AIProviderError as e:
        # Retry on transient errors
        logger.warning(f"AI tagging failed: {e}, retrying...")
        raise self.retry(exc=e, countdown=exponential_backoff(self.request.retries))

    except Exception as e:
        # Log permanent errors but don't retry
        logger.error(f"Permanent error in AI tagging: {e}")
        return {"success": False, "error": str(e)}
```

**Testing:**
- Task executes successfully
- Retry logic works (mock failures)
- Exponential backoff delays
- Graceful degradation on permanent errors

**Commit Message:**
```
feat(phase6): create AI tagging Celery task with retry logic

- Define tag_image_task with max 3 retries
- Exponential backoff: 1min → 2min → 4min
- Reuse existing AI provider abstraction (DRY)
- Reuse existing tag service (DRY)
- Graceful error handling (log but don't crash)

Retry behavior:
- Transient errors (AIProviderError): Retry with backoff
- Permanent errors (e.g., image not found): Log and exit

Phase 6 Sub-Feature 3/7
```

### Sub-Feature 4: Integrate Background Tagging into Upload

**Goal:** Trigger AI tagging automatically on upload.

**Files:**
- `backend/app/api/images.py` - Update upload endpoint
- `backend/app/main.py` - Wire up task service in lifespan

**Changes:**
```python
# main.py - Add task service to app.state
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    app.state.storage = StorageService(...)
    app.state.thumbnail_service = ThumbnailService(...)
    app.state.task_service = create_task_service(settings)  # NEW
    yield
    await close_db()

# images.py - Trigger task on upload
@router.post("/upload")
async def upload_image(
    file: UploadFile,
    service: ImageService = Depends(get_image_service),
    task_service: BackgroundTaskService = Depends(get_task_service),  # NEW
):
    # 1. Save image (existing logic)
    image = await service.create(file, user_id)

    # 2. Trigger background tagging (NEW - graceful)
    try:
        task_id = await task_service.enqueue_ai_tagging(image.id)
        logger.info(f"AI tagging task enqueued: {task_id}")
    except Exception as e:
        # Log error but don't fail upload (graceful degradation)
        logger.error(f"Failed to enqueue AI tagging: {e}")

    # 3. Return response immediately (don't wait for tagging)
    return ImageUploadResponse(
        id=image.id,
        url=image.url,
        # NEW: Include task_id for status checking (optional)
        ai_tagging_task_id=task_id if task_id else None,
    )
```

**Benefits:**
- Upload still succeeds if tagging fails
- User gets immediate response
- Tags appear after a few seconds

**Testing:**
- Upload triggers background task
- Upload succeeds even if task queue down
- Task ID returned in response

**Commit Message:**
```
feat(phase6): integrate automatic AI tagging on upload

- Trigger background task after successful upload
- Use graceful error handling (upload always succeeds)
- Return task ID in response for status tracking
- Wire up task service in app lifespan
- Add dependency injection for task service

Behavior:
- Upload completes immediately (~500ms)
- AI tagging runs in background (~2-3s)
- Tags appear automatically after tagging completes

Phase 6 Sub-Feature 4/7
```

### Sub-Feature 5: Add Provider Fallback Logic

**Goal:** Try OpenAI → Google → Mock if all fail.

**Files:**
- `backend/app/services/ai/fallback_provider.py` - Fallback wrapper

**Design:**
```python
class FallbackAIProvider(AITaggingProvider):
    """
    Try providers in order until one succeeds.

    Order: OpenAI → Google → Mock

    Benefits:
    - Resilience (if OpenAI down, use Google)
    - Graceful degradation (if all fail, use mock)
    - Same interface (DRY)
    """

    def __init__(self, providers: list[AITaggingProvider]):
        self.providers = providers

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        errors = []

        for provider in self.providers:
            try:
                return await provider.analyze_image(image_bytes)
            except AIProviderError as e:
                logger.warning(f"{provider.__class__.__name__} failed: {e}")
                errors.append((provider.__class__.__name__, e))
                continue

        # All failed - log and raise
        logger.error(f"All AI providers failed: {errors}")
        raise AIProviderError(f"All providers failed: {errors}")
```

**Usage:**
```python
def create_ai_provider_with_fallback(settings):
    """Create provider with automatic fallback."""
    providers = []

    # Primary: OpenAI (if configured)
    if settings.openai_api_key:
        providers.append(OpenAIVisionProvider(settings))

    # Fallback 1: Google (if configured)
    if settings.google_api_key:
        providers.append(GoogleVisionProvider(settings))

    # Fallback 2: Mock (always available)
    providers.append(MockAIProvider())

    return FallbackAIProvider(providers)
```

**Testing:**
- OpenAI fails → Google succeeds
- OpenAI + Google fail → Mock succeeds
- All fail → Graceful error

**Commit Message:**
```
feat(phase6): add AI provider fallback mechanism

- Create FallbackAIProvider wrapper
- Try providers in order: OpenAI → Google → Mock
- Log each failure and try next provider
- Update factory to use fallback by default

Benefits:
- Resilience (if primary down, use fallback)
- Graceful degradation (mock as last resort)
- Same interface (transparent to caller)

Phase 6 Sub-Feature 5/7
```

### Sub-Feature 6: Remove Temporary Manual Endpoint

**Goal:** Clean up `/ai-tag` endpoint (no longer needed).

**Files:**
- `backend/app/api/images.py` - Remove endpoint

**Changes:**
```python
# Remove this endpoint (used for Phase 5 testing only)
# @router.post("/{image_id}/ai-tag")
# async def manual_ai_tag(image_id: str): ...
```

**Testing:**
- Endpoint returns 404
- OpenAPI docs don't show endpoint

**Commit Message:**
```
refactor(phase6): remove temporary manual AI tagging endpoint

- Remove POST /api/v1/images/{id}/ai-tag endpoint
- No longer needed (automatic tagging implemented)
- Simplifies API surface

Phase 6 Sub-Feature 6/7
```

### Sub-Feature 7: Add Tests for Background Jobs

**Goal:** Comprehensive test coverage.

**Files:**
- `backend/tests/unit/test_background_task_service.py`
- `backend/tests/unit/test_fallback_provider.py`
- `backend/tests/integration/test_automatic_tagging.py`

**Test Coverage:**
- Background task service (mock and Celery)
- Fallback provider logic
- Upload → task trigger flow
- Retry logic
- Error handling

**Commit Message:**
```
test(phase6): add comprehensive tests for background AI tagging

- Unit tests for task service abstraction
- Unit tests for fallback provider
- Integration tests for automatic tagging flow
- Test retry logic and exponential backoff
- Test graceful error handling

Coverage: Background tagging fully tested

Phase 6 Sub-Feature 7/7
```

---

## Implementation Order

1. **Infrastructure First** - Celery + Redis setup
2. **Abstraction Layer** - Task service interface
3. **Task Definition** - AI tagging task with retry
4. **Integration** - Wire into upload endpoint
5. **Resilience** - Fallback provider
6. **Cleanup** - Remove manual endpoint
7. **Testing** - Comprehensive coverage

---

## Testing Strategy

### Unit Tests
- Task service abstraction (mock vs Celery)
- Fallback provider logic
- Retry backoff calculations

### Integration Tests
- Upload → task enqueued
- Task executes and adds tags
- Retry on failure
- Graceful degradation

### Manual Testing
- Upload image → tags appear after 2-3s
- OpenAI fails → Google/Mock works
- Task monitoring with Celery logs

---

## Deployment Considerations

### Environment Variables
```bash
# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Background Task Configuration
BACKGROUND_TASK_ENABLED=true  # Disable in tests
BACKGROUND_TASK_PROVIDER=celery  # or "mock" for tests

# AI Provider Fallback Order
AI_FALLBACK_PROVIDERS=openai,google,mock
```

### Docker Compose Changes
```yaml
services:
  redis:
    image: redis:7-alpine
    # Already exists from Phase 2

  celery-worker:
    build: backend/
    command: celery -A app.celery_app worker --loglevel=info
    depends_on:
      - redis
      - postgres
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CELERY_BROKER_URL=redis://redis:6379/0
```

### Production Rollout
1. Deploy redis (already exists)
2. Deploy celery worker
3. Deploy updated backend
4. Monitor task execution
5. Gradually enable for all uploads

---

## Success Criteria

### Functional
- ✅ Image upload triggers background AI tagging automatically
- ✅ Tags appear within 3-5 seconds of upload
- ✅ Retry logic handles transient failures
- ✅ Provider fallback works (OpenAI → Google → Mock)
- ✅ Upload succeeds even if tagging fails

### Technical
- ✅ Decoupled architecture (can swap task queue)
- ✅ Evolutionary (easy to add new processors)
- ✅ DRY (reuses existing AI provider abstraction)
- ✅ Maintainable (clear interfaces)
- ✅ Graceful error handling (no user-facing failures)

### Testing
- ✅ All unit tests passing
- ✅ All integration tests passing
- ✅ Manual testing successful
- ✅ Production monitoring shows successful tagging

---

## Rollback Plan

If Phase 6 causes issues:

1. **Disable background tagging:**
   ```bash
   BACKGROUND_TASK_ENABLED=false
   ```

2. **Revert to manual endpoint:**
   - Users can manually trigger tagging
   - Keep endpoint temporarily

3. **Full rollback:**
   - Revert to Phase 5 (manual tagging only)
   - Celery worker can stay deployed (no harm)

---

## Future Enhancements (Phase 7+)

- Task monitoring UI (Flower)
- Dead letter queue for failed tasks
- Task prioritization (VIP users first)
- Batch tagging of existing images
- Multiple tag processors (NSFW, faces, etc.)
- Distributed Celery workers
- Task result webhooks

---

**Created:** 2026-01-11
**Purpose:** Guide Phase 6 implementation with best practices
**Principles:** Decoupled, Evolutionary, DRY, Maintainable, Graceful
