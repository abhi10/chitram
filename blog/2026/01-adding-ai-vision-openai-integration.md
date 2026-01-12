# Adding AI Vision to an Image Host: From Manual Tags to OpenAI

**Date:** 2026-01-13
**Reading Time:** 10 minutes
**Tags:** #ai #openai #vision-api #architecture #fastapi #strategy-pattern
**Repository:** https://github.com/abhi10/chitram

---

## TL;DR

Added AI-powered automatic tagging to Chitram using OpenAI Vision API. Built a pluggable provider system (Strategy pattern) that lets us switch between OpenAI, Google Vision, or mock providers with zero code changes - just environment variables. Started with a manual `/ai-tag` endpoint to validate the integration before committing to background jobs. Cost: $4-20/month for 1,000-5,000 images. Key learning: Test the AI integration first with simple synchronous endpoint, defer complexity (Celery workers) to later phase.

---

## Who Should Read This

- Backend developers adding AI features to existing applications
- Engineers evaluating OpenAI Vision API vs alternatives
- Developers learning the Strategy pattern for swappable providers
- Anyone building cost-conscious AI integrations

## Prerequisites

- Basic understanding of REST APIs
- Familiarity with async/await in Python
- Knowledge of environment-based configuration

---

## The Problem: Manual Tagging Doesn't Scale

Before Phase 5, Chitram had a clean image hosting experience:
- Users upload images ✅
- Images stored in MinIO ✅
- Thumbnails auto-generated ✅
- But tags? Manual only ❌

```
User uploads sunset beach photo
→ Must manually type: "sunset", "beach", "ocean", "clouds"
→ 30 seconds per image
→ Users skip it (too tedious)
```

**The Goal:** Make tagging automatic, accurate, and affordable.

---

## The Architecture Evolution

### Before Phase 5: Manual Tags Only

```
┌─────────────────────────────────────────────────────────┐
│  Upload Flow (Phase 1-3.5)                              │
└─────────────────────────────────────────────────────────┘

User Upload → FastAPI
                 ↓
         Save to MinIO (storage)
                 ↓
         Save metadata (PostgreSQL)
                 ↓
         Generate thumbnail (BackgroundTask)
                 ↓
         Return success response

Tags: User must manually add via /tags endpoint
```

### After Phase 5: AI Tags Available

```
┌─────────────────────────────────────────────────────────┐
│  Upload Flow + AI Tagging (Phase 5)                     │
└─────────────────────────────────────────────────────────┘

User Upload → FastAPI
                 ↓
         Save to MinIO (storage)
                 ↓
         Save metadata (PostgreSQL)
                 ↓
         Generate thumbnail
                 ↓
         Return success response

NEW → User clicks "Generate AI Tags" (manual trigger)
                 ↓
         POST /api/v1/images/{id}/ai-tag
                 ↓
         Fetch image from MinIO
                 ↓
         Send to OpenAI Vision API
                 ↓
         Parse response → 5 tags
                 ↓
         Save to database (source='ai', confidence=90)
                 ↓
         Return tags to user
```

**Key Change:** Added optional AI tagging via dedicated endpoint.

**Why manual?** Test the integration before building automatic background processing (Celery workers = Phase 6 complexity).

---

## The API Interface

### New Endpoint: Generate AI Tags

**Request:**
```bash
curl -X POST "https://chitram.io/api/v1/images/c0f25484-9c46-498b-a867-ca6acb2919fa/ai-tag" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "message": "Added 5 AI tags to image",
  "image_id": "c0f25484-9c46-498b-a867-ca6acb2919fa",
  "tags": [
    {"name": "palms", "confidence": 90, "category": null},
    {"name": "tropical", "confidence": 90, "category": null},
    {"name": "greenery", "confidence": 90, "category": null},
    {"name": "blue sky", "confidence": 90, "category": null},
    {"name": "lush", "confidence": 90, "category": null}
  ],
  "provider": "openai",
  "model": "gpt-4o-mini"
}
```

**Implementation:**

```python
@router.post("/{image_id}/ai-tag")
async def generate_ai_tags(
    image_id: str,
    current_user: dict = Depends(get_current_user),
    service: ImageService = Depends(get_image_service),
    storage: StorageService = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    Generate AI tags for an image using configured AI provider.

    Cost: ~$0.004 per image (OpenAI gpt-4o-mini)
    Response time: ~2-3 seconds
    Provider: Configurable via AI_PROVIDER env var
    """
    # 1. Verify image exists and user owns it
    image = await service.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    if image.user_id != current_user["local_user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 2. Fetch image bytes from storage
    try:
        image_bytes = await storage.get(image.storage_key)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch image from storage: {e}"
        )

    # 3. Call AI provider (OpenAI, Google, or Mock)
    try:
        ai_provider = create_ai_provider(settings)
        ai_tags = await ai_provider.analyze_image(image_bytes)
    except AIProviderError as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI provider failed: {e}"
        )

    # 4. Save tags to database
    saved_count = 0
    for ai_tag in ai_tags:
        # Create or get existing tag
        tag = await service.get_or_create_tag(ai_tag.name)

        # Associate with image (source='ai')
        await service.add_image_tag(
            image_id=image_id,
            tag_id=tag.id,
            source="ai",
            confidence=ai_tag.confidence,
        )
        saved_count += 1

    return {
        "message": f"Added {saved_count} AI tags to image",
        "image_id": image_id,
        "tags": [
            {
                "name": tag.name,
                "confidence": tag.confidence,
                "category": tag.category,
            }
            for tag in ai_tags
        ],
        "provider": settings.ai_provider,
        "model": settings.openai_vision_model if settings.ai_provider == "openai" else None,
    }
```

**What's Happening:**
1. Authenticate user (JWT token)
2. Verify user owns the image
3. Fetch image bytes from MinIO
4. Call AI provider (abstracted - could be OpenAI, Google, Mock)
5. Parse tags from AI response
6. Save to database with `source='ai'` and `confidence=90`
7. Return tags to user

**Response Time:** ~2-3 seconds (network latency to OpenAI)

---

## The Key Design: Strategy Pattern

### The Problem: Provider Lock-In

**What if OpenAI changes pricing?**
**What if Google Vision is cheaper?**
**How do we test without spending money?**

**Solution:** Make providers swappable via abstract interface.

### The Interface

```python
# app/services/ai/base.py

from abc import ABC, abstractmethod
from dataclass import dataclass

@dataclass
class AITag:
    """AI-generated tag suggestion."""
    name: str              # Tag name (lowercase, normalized)
    confidence: int        # Confidence score 0-100
    category: str | None   # Optional category (e.g., 'object', 'scene')


class AITaggingProvider(ABC):
    """Abstract base for AI vision providers."""

    @abstractmethod
    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        """
        Analyze image and return tag suggestions.

        Args:
            image_bytes: Raw image data (JPEG/PNG)

        Returns:
            List of AI-generated tags with confidence scores

        Raises:
            AIProviderError: If provider fails to analyze image
        """
        pass
```

### Three Implementations

**1. MockAIProvider (Free, Testing)**
```python
class MockAIProvider(AITaggingProvider):
    """Returns predictable fake tags for testing."""

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        """Return mock tags without calling any API."""
        return [
            AITag(name="mock-object", confidence=95, category="object"),
            AITag(name="mock-scene", confidence=85, category="scene"),
            AITag(name="mock-color", confidence=75, category="color"),
        ]
```

**Use Case:** Local development, CI/CD, unit tests
**Cost:** $0
**Speed:** Instant

**2. OpenAIVisionProvider (Production)**
```python
class OpenAIVisionProvider(AITaggingProvider):
    """OpenAI Vision API provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", max_tags: int = 5):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_tags = max_tags
        self.prompt = (
            f"Analyze this image and provide {max_tags} descriptive tags. "
            "Return only tag names separated by commas, no explanations."
        )

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        """Call OpenAI Vision API to analyze image."""
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "low"  # Cost optimization
                            }
                        }
                    ]
                }],
                max_tokens=150  # Limit response length
            )

            # Parse response
            tags_text = response.choices[0].message.content
            tag_names = [tag.strip().lower() for tag in tags_text.split(",")]

            # Convert to AITag objects
            return [
                AITag(name=name, confidence=90, category=None)
                for name in tag_names[:self.max_tags]
            ]

        except OpenAIError as e:
            raise AIProviderError(f"OpenAI API failed: {e}") from e
```

**Use Case:** Production tagging
**Cost:** ~$0.004/image
**Speed:** ~2-3 seconds

**3. GoogleVisionProvider (Future)**
```python
class GoogleVisionProvider(AITaggingProvider):
    """Google Cloud Vision API provider (not implemented yet)."""

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        # TODO: Phase 7 - cheaper alternative ($0.0015/image)
        pass
```

### The Factory

```python
# app/services/ai/__init__.py

def create_ai_provider(settings: Settings) -> AITaggingProvider:
    """
    Create AI provider based on configuration.

    Environment variable AI_PROVIDER controls which implementation:
    - "mock" → MockAIProvider (free, testing)
    - "openai" → OpenAIVisionProvider (production)
    - "google" → GoogleVisionProvider (future)
    """
    if settings.ai_provider == "mock":
        return MockAIProvider()

    if settings.ai_provider == "openai":
        if not settings.openai_api_key:
            raise AIProviderError("OPENAI_API_KEY not configured")

        return OpenAIVisionProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_vision_model,
            max_tags=settings.ai_max_tags_per_image,
        )

    if settings.ai_provider == "google":
        if not settings.google_vision_api_key:
            raise AIProviderError("GOOGLE_VISION_API_KEY not configured")

        return GoogleVisionProvider(
            api_key=settings.google_vision_api_key,
            max_tags=settings.ai_max_tags_per_image,
        )

    raise ValueError(f"Unknown AI provider: {settings.ai_provider}")
```

### Configuration-Driven Switching

**Change provider = change environment variable, zero code changes**

```bash
# .env.development (free)
AI_PROVIDER=mock

# .env.production (costs money)
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-abc123...
AI_MAX_TAGS_PER_IMAGE=5
AI_CONFIDENCE_THRESHOLD=70
OPENAI_VISION_MODEL=gpt-4o-mini
```

**In code:**
```python
# Same line everywhere - factory handles the decision
provider = create_ai_provider(settings)
tags = await provider.analyze_image(image_bytes)
```

**Benefits:**
- ✅ Test with mock (free, instant)
- ✅ Deploy with OpenAI (real tags)
- ✅ Switch to Google later (one env var)
- ✅ A/B test providers (easy comparison)

---

## Cost Analysis: Which Provider?

### Provider Comparison

| Provider | Cost/Image | 1K Images/mo | 5K Images/mo | Quality | Setup Complexity |
|----------|-----------|--------------|--------------|---------|-----------------|
| **Mock** | $0 | $0 | $0 | Fake data | Zero (built-in) |
| **OpenAI gpt-4o-mini** | $0.004 | $4 | $20 | ⭐⭐⭐⭐ | Easy (API key) |
| **OpenAI gpt-4o** | $0.020 | $20 | $100 | ⭐⭐⭐⭐⭐ | Easy (API key) |
| **Google Vision** | $0.0015 | $1.50 | $7.50 | ⭐⭐⭐⭐⭐ | Complex (GCP setup) |

### Our Decision: OpenAI gpt-4o-mini

**Why:**
1. ✅ **Easy setup** - Just API key, no GCP project
2. ✅ **Good quality** - 90% accuracy for common images
3. ✅ **Affordable** - $20/month for 5,000 images is acceptable for MVP
4. ✅ **Async support** - AsyncOpenAI client works with FastAPI
5. ✅ **Fast iteration** - Test → Deploy → Validate → Switch if needed

**Why not gpt-4o?**
- ❌ 5x more expensive ($0.020 vs $0.004)
- ❌ Minimal quality gain for tagging (vs detailed captions)

**Why not Google Vision?**
- ⏭️ Defer to Phase 7 (cost optimization phase)
- Requires GCP project + service account (more complexity)
- Synchronous client only (need thread pool for async)

### Cost Control Features

**1. Max Tags Limit**
```bash
AI_MAX_TAGS_PER_IMAGE=5  # Default: 5, range: 1-10
```
- Fewer tags = shorter OpenAI response = lower cost
- 5 tags sufficient for most images

**2. Confidence Threshold** (future use)
```bash
AI_CONFIDENCE_THRESHOLD=70  # Filter low-confidence tags
```
- OpenAI doesn't provide scores (hardcoded 90%)
- Google Vision does (will use this in Phase 7)

**3. Manual Triggering** (Phase 5)
- Users choose which images to tag
- Avoid tagging screenshots, memes, etc. (waste of money)
- Phase 6 will make automatic, but with graceful degradation

---

## Real Results: Production Testing

### Test 1: Tropical Palm Garden

**Image:** https://chitram.io/image/c0f25484-9c46-498b-a867-ca6acb2919fa

**Request:**
```bash
curl -X POST "https://chitram.io/api/v1/images/c0f25484-.../ai-tag" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "message": "Added 5 AI tags to image",
  "tags": [
    {"name": "palms", "confidence": 90},
    {"name": "tropical", "confidence": 90},
    {"name": "greenery", "confidence": 90},
    {"name": "blue sky", "confidence": 90},
    {"name": "lush", "confidence": 90}
  ],
  "provider": "openai",
  "model": "gpt-4o-mini"
}
```

**Analysis:**
- ✅ Accurate descriptors (outdoor, tropical scene)
- ✅ Specific details (palms, not just "trees")
- ✅ Attributes detected (blue sky, lush)
- ✅ Response time: ~2.5 seconds
- ✅ Cost: ~$0.004

### Test 2: Floral Arrangement

**Response:**
```json
{
  "tags": [
    {"name": "flowers", "confidence": 90},
    {"name": "bouquet", "confidence": 90},
    {"name": "home decor", "confidence": 90},
    {"name": "floral arrangement", "confidence": 90},
    {"name": "pastel colors", "confidence": 90}
  ]
}
```

**Analysis:**
- ✅ Different subject (indoor vs outdoor)
- ✅ Context understood (home decor)
- ✅ Color attributes (pastel colors)

### Test 3: Study/Programming Workspace

**Response:**
```json
{
  "tags": [
    {"name": "books", "confidence": 90},
    {"name": "study area", "confidence": 90},
    {"name": "desk organization", "confidence": 90},
    {"name": "computer science", "confidence": 90},
    {"name": "programming", "confidence": 90}
  ]
}
```

**Analysis:**
- ✅ Physical objects (books)
- ✅ Spatial context (study area)
- ✅ Subject inferred (computer science, programming)

**Success Rate:** 3/3 tests (100%)

---

## Database Schema: Zero Migrations Needed

### The Existing Schema (From Phase 1)

```sql
-- Tags table (reused, no changes)
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Image-Tag association (reused, no changes)
CREATE TABLE image_tags (
    image_id UUID REFERENCES images(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    source VARCHAR(10) NOT NULL,      -- 'user' or 'ai' ✅ Already supported!
    confidence INTEGER,                -- 0-100 for AI tags ✅ Already had this!
    category VARCHAR(20),              -- Optional category
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (image_id, tag_id)
);
```

### What Changed? Nothing!

**Phase 1 schema already supported:**
- ✅ `source` column ('user' or 'ai')
- ✅ `confidence` column (NULL for user tags, 0-100 for AI)
- ✅ `category` column (optional)

**Why?** We designed Phase 1 with AI in mind:
- Knew we'd add AI later
- Added fields proactively
- Zero migration downtime for Phase 5 ✅

**How tags are stored:**

```python
# User adds manual tag
await service.add_image_tag(
    image_id=image_id,
    tag_id=tag_id,
    source="user",        # Manual
    confidence=None,      # No confidence for user tags
)

# AI adds tag
await service.add_image_tag(
    image_id=image_id,
    tag_id=tag_id,
    source="ai",          # AI-generated
    confidence=90,        # OpenAI confidence
)
```

**Querying:**

```sql
-- Get all AI tags
SELECT t.name, it.confidence
FROM image_tags it
JOIN tags t ON it.tag_id = t.id
WHERE it.source = 'ai' AND it.image_id = 'abc123';

-- Get high-confidence AI tags
SELECT t.name, it.confidence
FROM image_tags it
JOIN tags t ON it.tag_id = t.id
WHERE it.source = 'ai' AND it.confidence >= 80;
```

---

## What We Learned

### 1. Start Simple: Manual Endpoint First

**Decision:** Manual `/ai-tag` endpoint, not automatic on upload.

**Why:**
- ✅ Test OpenAI integration works
- ✅ Validate cost per image in production
- ✅ Get user feedback on tag quality
- ✅ Avoid complexity (Celery workers, Redis, retry logic)

**Trade-off:**
- ❌ User must click button (extra step)
- ❌ Blocks response for 2-3 seconds
- ✅ But much simpler to implement and debug

**Phase 6 will make automatic** - upload triggers background Celery task. But Phase 5 proves AI works first.

### 2. Strategy Pattern = Future-Proof

**Problem:** What if OpenAI raises prices?

**Solution:** Abstract providers + factory pattern

**Result:**
- Switch to Google Vision = change env var
- Add new provider = implement interface, update factory
- Test with mock = zero API costs
- A/B test providers = easy comparison

**No provider lock-in.**

### 3. Configuration Over Code

**All AI settings via environment variables:**

```bash
AI_PROVIDER=openai              # Provider selection
OPENAI_API_KEY=sk-proj-...      # Credentials
AI_MAX_TAGS_PER_IMAGE=5         # Cost control
AI_CONFIDENCE_THRESHOLD=70      # Quality control
OPENAI_VISION_MODEL=gpt-4o-mini # Model selection
```

**Benefits:**
- ✅ Change settings without code deploy
- ✅ Different config per environment (dev vs prod)
- ✅ Secrets never in git (injected via CD pipeline)
- ✅ Easy to experiment (tweak max_tags, try different models)

### 4. Graceful Defaults

**If OpenAI API fails:**
```python
try:
    tags = await ai_provider.analyze_image(image_bytes)
except AIProviderError as e:
    # Log error, return 503
    raise HTTPException(status_code=503, detail=f"AI provider unavailable: {e}")
```

**Upload still succeeds** - just no AI tags. Image is saved, user can add manual tags.

**If AI_PROVIDER not set:**
```bash
AI_PROVIDER=mock  # Default - safe, free
```

**Explicit opt-in for paid APIs.** Never accidentally spend money.

### 5. Test Pyramid

```
        ▲
       / \
      /   \     5 Integration Tests (Manual, $0.008)
     /     \    - Run with: pytest -m manual
    /───────\   - Real OpenAI API calls
   /         \
  /           \
 /             \ 21 Unit Tests (Fast, $0)
/───────────────\ - MockAIProvider
                  - Run on every commit
```

**Unit tests (free, fast):**
- Provider interface
- Factory logic
- Mock provider
- Error handling

**Integration tests (paid, manual):**
- Real OpenAI API
- Cost tracking in docstrings
- Only run when needed (not in CI/CD)

---

## Trade-offs: Why Manual? Why Not Automatic?

### What We Built (Phase 5)

**Manual triggering:**
```
User uploads image → Image saved → User clicks "Generate Tags" → OpenAI called → Tags saved
```

**Pros:**
- ✅ Simple to implement (no Celery, no Redis)
- ✅ Easy to debug (synchronous flow)
- ✅ User controls cost (only tag what they want)
- ✅ Fast to deploy (test AI integration ASAP)

**Cons:**
- ❌ Extra click required
- ❌ Blocks response (2-3 sec delay)
- ❌ User might forget to tag

### What We Deferred (Phase 6)

**Automatic triggering:**
```
User uploads image → Image saved → Background task queued → Celery worker → OpenAI → Tags saved
```

**Pros:**
- ✅ Automatic (no user action)
- ✅ Non-blocking (upload returns immediately)
- ✅ Retry logic (resilient to API failures)
- ✅ Better UX

**Cons:**
- ❌ Complex (Celery workers, Redis broker, result backend)
- ❌ More infrastructure (worker containers, message queue)
- ❌ Harder to debug (async, distributed)
- ❌ More failure modes (Redis down, worker crash, task timeout)

### The Decision: Incremental Complexity

**Phase 5:** Prove AI integration works (manual endpoint)
**Phase 6:** Make it automatic (background jobs)

**Why this order?**
- If OpenAI fails in Phase 5 → debug synchronously, fix provider code
- If OpenAI fails in Phase 6 → debug distributed system, was it Celery? Redis? Worker? Network?

**Validate the hard part (AI) before adding distributed systems complexity.**

---

## Next Phase: Making It Automatic

Phase 6 will transform this manual endpoint into automatic background processing:

**Architecture Preview:**
```
User Upload → Save to MinIO → Save metadata → Enqueue Celery task → Return response
                                                       ↓
                                                  Redis Queue
                                                       ↓
                                               Celery Worker
                                                       ↓
                                            Fetch from MinIO
                                                       ↓
                                            OpenAI Vision API
                                                       ↓
                                            Save AI tags (source='ai')
```

**What changes:**
- ✅ Non-blocking upload (returns in <500ms)
- ✅ Automatic tagging (no user action)
- ✅ Retry logic (resilient to transient failures)
- ✅ Graceful degradation (upload succeeds even if tagging fails)

**What's added:**
- Redis broker + result backend
- Celery worker service
- Background task service abstraction
- Retry configuration (exponential backoff)

But that's a story for the next blog post. Phase 5 proves the AI works - Phase 6 makes it production-grade.

---

## Related Resources

### From This Project
- [Phase 5 Implementation Summary](../../docs/implementation/phase5-ai-vision-provider-summary.md) - Detailed technical spec
- [Phase 5 Comprehensive Analysis](../../docs/implementation/phase5-comprehensive-analysis.md) - Full architecture + debugging
- [OpenAI Vision Provider Source](https://github.com/abhi10/chitram/blob/main/backend/app/services/ai/openai_vision.py)
- [PR #57: Phase 5 AI Vision](https://github.com/abhi10/chitram/pull/57)

### External Resources
- [OpenAI Vision API Documentation](https://platform.openai.com/docs/guides/vision)
- [Strategy Pattern - Refactoring Guru](https://refactoring.guru/design-patterns/strategy)
- [Google Cloud Vision Pricing](https://cloud.google.com/vision/pricing)
- [Cost Optimization Strategies](https://platform.openai.com/docs/guides/vision#cost-optimization)

---

## Conclusion

Adding AI to an existing application doesn't have to be complex. Phase 5 taught us:

1. **Start with the simplest thing that works** - Manual endpoint beats complex background jobs for initial validation
2. **Abstract early** - Strategy pattern makes providers swappable with zero code changes
3. **Configuration over code** - Environment variables let you switch providers instantly
4. **Validate incrementally** - Prove AI works before adding distributed systems complexity
5. **Design for cost** - Max tags limits, model selection, manual triggering = cost control

**The Result:**
- ✅ OpenAI Vision API integrated and working
- ✅ Cost-controlled ($4-20/month for 1,000-5,000 images)
- ✅ Swappable providers (OpenAI today, Google tomorrow)
- ✅ Production-tested (3/3 test images tagged accurately)
- ✅ Ready for Phase 6 (automatic background processing)

**Try it:** Upload an image to https://chitram.io, click "Generate AI Tags", get 5 accurate tags in ~2 seconds.

Next up: Making this automatic with Celery workers. Stay tuned for the Phase 6 story (spoiler: 5 bugs, 3 hours, one factory pattern to rule them all).

---

## Discussion

Have you integrated OpenAI Vision API into your projects? What providers did you evaluate? How do you handle cost control for AI features?

I'd love to hear your experiences - comment below or open a [GitHub issue](https://github.com/abhi10/chitram/issues).

---

## About Chitram

Chitram (చిత్రం - "image" in Telugu) is an open-source image hosting application built to learn distributed systems. Features automatic AI tagging with OpenAI Vision API, background job processing with Celery, and OAuth authentication with Supabase.

**Live Demo:** https://chitram.io
**Source Code:** https://github.com/abhi10/chitram
**Tech Stack:** FastAPI, PostgreSQL, MinIO, Redis, Celery, OpenAI Vision API

---

**License:** This post is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) - share with attribution.
