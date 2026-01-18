# Adding AI Vision to an Image Host: Production Lessons (Part 2)

**Date:** 2026-01-13
**Reading Time:** 6 minutes
**Tags:** #ai #production #lessons-learned #architecture #trade-offs
**Repository:** https://github.com/abhi10/chitram

---

## TL;DR

Part 1 covered the OpenAI integration and Strategy pattern. This post shares what we learned shipping AI tagging to production: why we started with a manual endpoint (Phase 5) before going automatic (Phase 6), how we structured tests to avoid burning money, and the trade-offs that shaped our decisions. Key lesson: validate the hard part (AI integration) before adding distributed systems complexity.

---

## Prerequisites

Read [Part 1 - OpenAI Integration](05a-adding-ai-vision-part1-integration.md) first for context on the Strategy pattern, provider architecture, and automatic tagging implementation.

---

## What We Learned

### 1. Incremental Complexity: Manual → Automatic

**Phase 5 Decision:** Manual `/ai-tag` endpoint first, not automatic on upload.

**Why start manual:**
- ✅ Test OpenAI integration works (validate API, prompts, parsing)
- ✅ Validate cost per image in production (measure actual spend)
- ✅ Get user feedback on tag quality (iterate on prompts)
- ✅ Avoid distributed systems complexity (no Celery/Redis initially)

**Phase 6 Evolution:** Made automatic with Celery workers.

**Why this worked:**
- If OpenAI integration failed in Phase 5 → debug synchronously, fix provider code
- If it failed in Phase 6 → debug distributed system (Celery? Redis? Worker? Network?)
- **Validate the hard part (AI) before adding infrastructure complexity**

**Result:** Phase 5 proved AI works. Phase 6 made it production-grade.

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

## Architecture Evolution: Manual → Automatic

### Phase 5: Manual Triggering (Validation)

**Flow:**
```
User uploads image → Image saved → User clicks "Generate Tags" → OpenAI called → Tags saved
```

**Why start here:**
- ✅ Simple to implement (no Celery, no Redis)
- ✅ Easy to debug (synchronous flow)
- ✅ Fast to validate (test AI integration ASAP)
- ✅ Isolated failures (if it breaks, debug just the AI provider)

**Trade-offs:**
- ❌ Extra click required (worse UX)
- ❌ Blocks response for 2-3 seconds
- ❌ User might forget to tag

**Purpose:** Prove OpenAI integration works before adding infrastructure.

### Phase 6: Automatic Triggering (Production)

**Flow:**
```
User uploads image → Image saved → Background task queued → Celery worker → OpenAI → Tags saved
```

**What improved:**
- ✅ Automatic (no user action needed)
- ✅ Non-blocking (upload returns in <500ms)
- ✅ Retry logic (resilient to API failures - 3 attempts, exponential backoff)
- ✅ Better UX (seamless experience)

**New complexity:**
- ⚠️ Celery workers, Redis broker, result backend
- ⚠️ More infrastructure (worker containers, message queue)
- ⚠️ Harder to debug (async, distributed)
- ⚠️ More failure modes (Redis down, worker crash, task timeout)

**Key Learning:** Phase 5's simple manual flow made debugging Phase 6's distributed system easier. When the Celery deployment hit 5 cascading bugs (see [Phase 6 Debugging Blog Post](02-phase6-deployment-debugging.md)), we knew the AI provider code was solid - the bugs were all infrastructure-related.

### The Decision: Incremental Complexity

**Validate the hard part (AI integration) before adding distributed systems complexity.**

This approach meant:
- Phase 5 bugs were isolated to AI provider code (easy to debug)
- Phase 6 bugs were infrastructure-only (we knew AI worked)
- Faster iteration (prove AI first, optimize delivery later)

---

## Deployment Lessons: 5 Cascading Bugs

Phase 6's automatic tagging deployment wasn't smooth. What we thought would be a simple Celery worker addition turned into a 3-hour debugging session with 5 infrastructure bugs:

1. **Celery command not found** - Missing `uv run` prefix
2. **Redis connection refused** - Wrong hostname in docker-compose
3. **Broker URL mismatch** - Environment variable typo
4. **Task not registering** - Import path issues
5. **FileNotFoundError in worker** - Duplicate storage initialization code

**The Final Fix:** [Storage Factory Pattern](03-storage-factory-pattern.md)

**What we learned:**
- Test in production-like environment (Docker Compose locally)
- Infrastructure bugs are harder to debug than application bugs
- Centralize initialization logic (avoid code duplication)

Read the full story: [Debugging 5 Cascading Infrastructure Failures](02-phase6-deployment-debugging.md)

---

## Cost Management Strategies

### Current Implementation (Phase 6)

**Per-image cost:** ~$0.004 (OpenAI gpt-4o-mini with "detail": "low")

**Monthly estimates:**
- 1,000 images: $4/month
- 5,000 images: $20/month
- 10,000 images: $40/month

**Cost controls:**
- Max 5 tags per image (shorter responses)
- Low-detail image analysis (512×512 vs full resolution)
- Max 150 tokens response limit
- Graceful degradation (upload succeeds even if AI fails)

### Future Optimizations (Phase 7)

**1. Provider switching:**
```bash
# Switch to Google Vision (62% cheaper)
AI_PROVIDER=google
GOOGLE_VISION_API_KEY=...
```
- Google Vision: $0.0015/image vs OpenAI: $0.004/image
- Savings: $12.50/month on 5,000 images

**2. Smart filtering:**
```python
# Skip low-value images
def should_tag_image(image: Image) -> bool:
    # Skip screenshots (detect via dimensions)
    if image.width == 1920 and image.height == 1080:
        return False

    # Skip duplicates (check perceptual hash)
    if image.phash in seen_hashes:
        return False

    return True
```

**3. Batch processing:**
- Tag existing images during off-peak hours
- Lower priority queue for retroactive tagging
- Budget cap: Stop if monthly limit exceeded

**4. Confidence-based filtering:**
```bash
AI_CONFIDENCE_THRESHOLD=80  # Only save high-confidence tags
```
- Google Vision provides per-tag confidence
- Filter out uncertain tags (saves storage, improves quality)

---

## Test Strategy: Don't Burn Money

### The Problem

Every integration test costs money:
- OpenAI API call: ~$0.004
- Run 100 tests: $0.40
- Run on every commit: $$$ quickly

### The Solution: Test Pyramid

**1. Unit tests (free, fast) - 95% of tests**
```python
# tests/unit/test_ai_providers.py

def test_mock_provider_returns_fake_tags():
    provider = MockAIProvider()
    tags = await provider.analyze_image(b"fake image bytes")

    assert len(tags) == 3
    assert tags[0].name == "mock-object"
    assert tags[0].confidence == 95
```

**Run on:** Every commit (CI/CD)
**Cost:** $0

**2. Integration tests (paid, manual) - 5% of tests**
```python
# tests/integration/test_openai_provider.py

@pytest.mark.manual  # Must explicitly run with -m manual
@pytest.mark.integration
async def test_openai_provider_analyzes_real_image():
    """
    Test OpenAI Vision API with real image.

    Cost: ~$0.004 per run
    Run manually: pytest -m manual
    """
    provider = OpenAIVisionProvider(api_key=os.getenv("OPENAI_API_KEY"))

    with open("tests/fixtures/sunset.jpg", "rb") as f:
        image_bytes = f.read()

    tags = await provider.analyze_image(image_bytes)

    assert len(tags) == 5
    assert all(tag.confidence >= 70 for tag in tags)
    assert any("sunset" in tag.name or "beach" in tag.name for tag in tags)
```

**Run on:** Manually before deployment
**Cost:** ~$0.004 per test

**3. CI/CD configuration**
```yaml
# .github/workflows/test.yml

test:
  - name: Run unit tests (free)
    run: pytest tests/ -v --ignore=tests/integration

  # Integration tests NOT run in CI (cost control)
  # Run manually: pytest -m manual
```

### Cost Tracking

```python
# tests/conftest.py

@pytest.fixture(autouse=True)
def track_api_costs(request):
    """Track costs for manual integration tests."""
    if "manual" in request.keywords:
        print(f"\n💰 Cost: ~$0.004 (OpenAI gpt-4o-mini)")
```

**Output:**
```
tests/integration/test_openai_provider.py::test_analyze_real_image
💰 Cost: ~$0.004 (OpenAI gpt-4o-mini)
PASSED
```

---

## What's Next: Cost Optimization

Phase 6 completed the automatic tagging implementation. Now running in production at https://chitram.io with:
- ✅ Non-blocking uploads (<500ms response time)
- ✅ Automatic AI tagging (~10 second background processing)
- ✅ Retry logic (3 attempts, exponential backoff)
- ✅ Graceful degradation (upload succeeds even if tagging fails)

**Future optimizations:**

### Phase 7: Cost Optimization
- Switch to Google Vision API ($0.0015 vs $0.004 per image - 62% savings)
- Smart filtering (skip screenshots, memes, duplicate images)
- Batch processing for retroactive tagging
- A/B test providers (compare quality vs cost)

### Phase 8: Advanced Features
- Multi-language tag support
- Custom tag categories (auto-categorize as "object", "scene", "color")
- Tag confidence tuning (only save tags above threshold)
- User feedback loop (thumbs up/down on AI tags → improve prompts)

**Read the deployment story:** The automatic implementation had its challenges - see [Phase 6 Debugging Blog Post](02-phase6-deployment-debugging.md) for the full story of 5 cascading bugs and 3 hours of debugging that led to the [Storage Factory Pattern](03-storage-factory-pattern.md).

---

## Key Takeaways

| Lesson | Why It Matters | How We Applied It |
|--------|----------------|-------------------|
| **Start simple, then optimize** | Validate core functionality before adding complexity | Phase 5 manual → Phase 6 automatic |
| **Strategy pattern for providers** | Avoid vendor lock-in, enable A/B testing | OpenAI today, Google tomorrow |
| **Configuration over code** | Change behavior without deploys | All settings via env vars |
| **Test pyramid** | Balance coverage with cost | 95% unit tests (free), 5% integration (paid) |
| **Graceful degradation** | Upload succeeds even if AI fails | Celery retry + fallback logic |
| **Incremental complexity** | Debug AI before debugging infrastructure | Isolated Phase 5 bugs from Phase 6 bugs |

---

## Conclusion

Adding AI to an existing application doesn't have to be complex. The Phase 5 → Phase 6 journey taught us:

1. **Start with the simplest thing that works** - Manual endpoint beats complex background jobs for initial validation
2. **Abstract early** - Strategy pattern makes providers swappable with zero code changes
3. **Configuration over code** - Environment variables let you switch providers instantly
4. **Validate incrementally** - Prove AI works before adding distributed systems complexity
5. **Design for cost** - Max tags limits, model selection, graceful degradation = cost control

**The Result (Phase 6 - Production):**
- ✅ OpenAI Vision API integrated and working
- ✅ Fully automatic tagging (no user action required)
- ✅ Non-blocking uploads (<500ms response time)
- ✅ Background processing with Celery + Redis
- ✅ Cost-controlled ($4-20/month for 1,000-5,000 images)
- ✅ Swappable providers (OpenAI today, Google tomorrow)
- ✅ Production-tested at https://chitram.io

**Try it live:** Upload an image to https://chitram.io - tags appear automatically within ~10 seconds. No clicking required.

**Read the sequel:** The Phase 6 deployment wasn't smooth sailing - see [Debugging 5 Cascading Infrastructure Failures](02-phase6-deployment-debugging.md) for the full story of what went wrong and how the [Storage Factory Pattern](03-storage-factory-pattern.md) saved the day.

---

## Related Posts

### This Series
- [Part 1 - OpenAI Integration](05a-adding-ai-vision-part1-integration.md) - Strategy pattern, providers, API
- [Phase 6 Deployment Debugging](02-phase6-deployment-debugging.md) - 5 cascading bugs story
- [Storage Factory Pattern](03-storage-factory-pattern.md) - How we fixed the FileNotFoundError

### Other Chitram Posts
- [Zero-Token Browser Testing](../01-zero-token-browser-testing.md)
- [Test Architecture](../02-chitram-test-architecture.md)
- [FastAPI + Supabase Integration](../03-fastapi-supabase-integration.md)

---

## Discussion

Have you integrated OpenAI Vision API into your projects? How do you handle the trade-off between simplicity and automation? What's your strategy for cost control on AI features?

I'd love to hear your experiences - comment below or open a [GitHub issue](https://github.com/abhi10/chitram/issues).

---

## About Chitram

Chitram (చిత్రం - "image" in Telugu) is an open-source image hosting application built to learn distributed systems. Features automatic AI tagging with OpenAI Vision API, background job processing with Celery, and OAuth authentication with Supabase.

**Live Demo:** https://chitram.io
**Source Code:** https://github.com/abhi10/chitram
**Tech Stack:** FastAPI, PostgreSQL, MinIO, Redis, Celery, OpenAI Vision API

---

**License:** This post is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) - share with attribution.
