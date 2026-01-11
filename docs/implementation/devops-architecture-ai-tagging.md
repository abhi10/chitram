# DevOps Architecture for AI Auto-Tagging

**Date:** 2026-01-10
**Scope:** Phases 1-7 infrastructure planning
**Current Production:** DigitalOcean droplet (2GB RAM, 2 vCPU, 50GB SSD)

---

## Current Architecture (Phase 3.5)

```
┌─────────────────────────────────────────────────────────────┐
│                    DigitalOcean Droplet                     │
│                   (2GB RAM, 2 vCPU, 50GB SSD)              │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Caddy   │  │ FastAPI  │  │ Postgres │  │  MinIO   │  │
│  │  (HTTPS) │→ │  (app)   │→ │   (DB)   │  │ (S3-like)│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                      ↓                                      │
│                 ┌──────────┐                                │
│                 │  Redis   │                                │
│                 │ (Cache)  │                                │
│                 └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

**Resource Usage (Current):**
- FastAPI app: ~200-300 MB RAM
- PostgreSQL: ~100-200 MB RAM
- Redis: ~50-100 MB RAM
- MinIO: ~100-200 MB RAM
- Caddy: ~50 MB RAM
- **Total: ~500-850 MB RAM** (leaves 1.2-1.5 GB free)

---

## Phases 1-4 Architecture (Manual Tagging)

### Infrastructure Changes: **NONE** ✅

**Why:**
- Phase 1: Database schema (just tables, no new services)
- Phase 2: Tag service (Python code in existing app container)
- Phase 3: API endpoints (routes in existing FastAPI app)
- Phase 4: UI (HTML/JS templates in existing app)

**Deployment:**
```bash
# On droplet
git pull origin feat/ai-auto-tagging
docker compose --env-file .env.production down
docker compose --env-file .env.production up --build -d

# Run migration
docker compose exec app uv run alembic upgrade head
```

**Resource Impact:**
- RAM: +0 MB (no new processes)
- CPU: +0% (same request handling)
- Disk: +~500 KB (migration + code)

### ✅ No Concerns for Phases 1-4

**Confirmed:**
- No new containers needed
- No infrastructure changes
- Current 2GB droplet is sufficient
- Deploy with existing CI/CD pipeline

---

## Phases 5-6 Architecture (AI Auto-Tagging)

### Challenge: AI Model Resource Requirements

#### Option 1: Moondream2 (Local Model)

```
┌─────────────────────────────────────────────────────────────┐
│              DigitalOcean Droplet (UPGRADED!)               │
│              (8GB RAM, 4 vCPU, 80GB SSD) ~$48/mo           │
│                                                             │
│  ┌──────────┐  ┌──────────────────────────┐  ┌──────────┐ │
│  │  Caddy   │→ │      FastAPI (app)       │→ │ Postgres │ │
│  │  (HTTPS) │  │                          │  │   (DB)   │ │
│  └──────────┘  │  ┌────────────────────┐  │  └──────────┘ │
│                 │  │  Moondream2 Model  │  │               │
│                 │  │   (~4GB in RAM)    │  │  ┌──────────┐ │
│                 │  └────────────────────┘  │  │  MinIO   │ │
│                 │          ↓ (3-5s)        │  │ (S3-like)│ │
│                 │  ┌────────────────────┐  │  └──────────┘ │
│                 │  │  BackgroundTasks   │  │               │
│                 │  │  (Thread Pool)     │  │  ┌──────────┐ │
│                 │  └────────────────────┘  │  │  Redis   │ │
│                 └──────────────────────────┘  │ (Cache)  │ │
│                                               └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Resource Requirements:**
- Moondream2 model: ~4GB RAM (loaded once at startup)
- Model weights: ~4GB disk space
- Inference: 100% CPU for 2-5 seconds per image
- **Total RAM needed: ~5-6 GB** (model + existing services)

**⚠️ CRITICAL: Current 2GB droplet CANNOT run Moondream2**

**Upgrade Required:**
- From: $18/month (2GB RAM, 2 vCPU, 50GB SSD)
- To: $48/month (8GB RAM, 4 vCPU, 80GB SSD)
- Cost increase: +$30/month

**Implementation Pattern:**
```python
# app/main.py
from app.services.ai.moondream_provider import MoondreamProvider

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model ONCE at startup (like existing services)
    if settings.ai_provider == "moondream":
        ai_provider = MoondreamProvider()
        await ai_provider.load_model()  # 4GB RAM allocated
        app.state.ai_provider = ai_provider

    yield

    # Cleanup
    if hasattr(app.state, "ai_provider"):
        await app.state.ai_provider.unload_model()

# app/services/ai_tagging_service.py
async def tag_image(self, image_id: str):
    # Runs in BackgroundTasks (non-blocking)
    # Uses thread pool for CPU-bound inference
    loop = asyncio.get_event_loop()
    tags = await loop.run_in_executor(
        None,  # Default thread pool
        self.ai_provider.analyze_image,
        image_bytes
    )
```

**Pros:**
- ✅ No external API costs
- ✅ Data privacy (images stay local)
- ✅ No API rate limits
- ✅ Good accuracy for MVP
- ✅ Pattern already proven (ThumbnailService uses thread pool)

**Cons:**
- ❌ Requires droplet upgrade ($30/month)
- ❌ Slower than cloud APIs (2-5s vs 500ms)
- ❌ Blocks CPU during inference
- ❌ Model download on first deploy (~4GB)

---

#### Option 2: Google Cloud Vision API (Cloud Service)

```
┌─────────────────────────────────────────────────────────────┐
│              DigitalOcean Droplet (NO UPGRADE!)             │
│              (2GB RAM, 2 vCPU, 50GB SSD) $18/mo            │
│                                                             │
│  ┌──────────┐  ┌──────────────────────────┐  ┌──────────┐ │
│  │  Caddy   │→ │      FastAPI (app)       │→ │ Postgres │ │
│  │  (HTTPS) │  │                          │  │   (DB)   │ │
│  └──────────┘  │  ┌────────────────────┐  │  └──────────┘ │
│                 │  │  HTTP Client       │  │               │
│                 │  │  (requests)        │  │  ┌──────────┐ │
│                 │  └─────────┬──────────┘  │  │  MinIO   │ │
│                 │            │ (500ms)      │  │ (S3-like)│ │
│                 │  ┌─────────▼──────────┐  │  └──────────┘ │
│                 │  │  BackgroundTasks   │  │               │
│                 │  │  (Async I/O)       │  │  ┌──────────┐ │
│                 │  └────────────────────┘  │  │  Redis   │ │
│                 └──────────────────────────┘  │ (Cache)  │ │
│                                               └──────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
                       ▼
           ┌───────────────────────┐
           │  Google Cloud Vision  │
           │     (External API)    │
           └───────────────────────┘
```

**Resource Requirements:**
- HTTP client: ~10 MB RAM
- No model in memory
- **Total RAM: Same as current (~500-850 MB)**

**Costs:**
- API: $1.50 per 1,000 images
- **FREE tier: First 1,000 images/month**
- Example: 10,000 uploads/month = $15/month

**Implementation Pattern:**
```python
# app/services/ai/google_vision.py
from google.cloud import vision

class GoogleVisionProvider(AITaggingProvider):
    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        # Async HTTP call (non-blocking)
        image = vision.Image(content=image_bytes)
        response = await self.client.label_detection(image=image)
        return self._parse_labels(response)

# No model loading, just API calls
```

**Pros:**
- ✅ No droplet upgrade needed (keep $18/month)
- ✅ Fast (500ms per image)
- ✅ Excellent accuracy
- ✅ No CPU blocking
- ✅ Free for first 1,000 images/month
- ✅ No disk space for models

**Cons:**
- ❌ External dependency (API downtime risk)
- ❌ Costs money after free tier
- ❌ Images sent to Google (privacy concern)
- ❌ API rate limits (though generous)

---

#### Option 3: Hybrid (Recommended)

**Strategy:** Start with Google Vision, optionally add Moondream later.

**Phase 5-6 Deployment:**
1. Launch with Google Cloud Vision (use free tier)
2. Monitor usage and costs
3. If usage exceeds free tier AND costs matter, upgrade droplet for Moondream
4. Keep both providers (fallback pattern)

**Configuration:**
```python
# app/config.py
class Settings(BaseSettings):
    # AI Tagging
    ai_provider: str = "google"  # or "moondream"
    ai_fallback_provider: str | None = "moondream"  # optional

    # Google Cloud Vision
    google_vision_api_key: str | None = None

    # Moondream (only if using)
    moondream_model_path: str | None = None
```

**Why Hybrid:**
- ✅ Start cheap (Google free tier)
- ✅ No upfront droplet upgrade
- ✅ Test feature with real users first
- ✅ Can switch providers based on actual usage
- ✅ Fallback if one provider fails

---

## Separate Container for AI? ❌ No (for MVP)

### Why Not Separate Container?

**Current Pattern (Thumbnails):**
- ThumbnailService runs in same container as FastAPI
- Uses BackgroundTasks + thread pool
- Works well, simple to deploy
- No inter-container communication overhead

**AI Tagging Similar to Thumbnails:**
- Both are background tasks triggered on upload
- Both are CPU-bound operations (image processing)
- Both can block briefly but run in background
- Both need database access for status updates

**Separate Container Would Add:**
- ❌ Complexity: Redis queue, Celery workers, message passing
- ❌ Latency: Inter-container communication
- ❌ Debugging overhead: Logs split across containers
- ❌ More failure points: Queue, worker, network
- ❌ Not needed for MVP scale (tens/hundreds of uploads/day)

### When Would Separate Container Be Needed?

**Triggers for separation:**
1. **Scale:** >1,000 uploads/day with AI tagging
2. **Blocking issues:** AI inference blocks critical API endpoints
3. **Resource isolation:** Need dedicated CPU/RAM for AI
4. **Multiple workers:** Need horizontal scaling of AI processing

**For chitram.io MVP:**
- Expected usage: <100 uploads/day
- BackgroundTasks sufficient
- Keep simple until proven inadequate

---

## Resource Planning by Phase

### Phase 1-4: Manual Tagging

**Infrastructure:** ✅ Current droplet (2GB RAM)

| Service | RAM | CPU | Disk |
|---------|-----|-----|------|
| FastAPI | 300 MB | 10% | 50 MB |
| PostgreSQL | 200 MB | 5% | 500 MB (DB) |
| Redis | 100 MB | 1% | 50 MB |
| MinIO | 200 MB | 5% | 5 GB (images) |
| Caddy | 50 MB | 1% | 10 MB |
| **Total** | **850 MB** | **22%** | **~6 GB** |

**Headroom:** 1.15 GB RAM, 78% CPU → ✅ Healthy margins

---

### Phase 5-6: AI Tagging (Google Vision)

**Infrastructure:** ✅ Current droplet (2GB RAM)

| Service | RAM | CPU | Disk | Notes |
|---------|-----|-----|------|-------|
| FastAPI | 320 MB | 15% | 50 MB | +20 MB for HTTP client |
| PostgreSQL | 220 MB | 5% | 600 MB | +100 MB for tags table |
| Redis | 100 MB | 1% | 50 MB | - |
| MinIO | 200 MB | 5% | 5 GB | - |
| Caddy | 50 MB | 1% | 10 MB | - |
| **Total** | **890 MB** | **27%** | **~6 GB** | ✅ Still under 2GB |

**Headroom:** 1.1 GB RAM, 73% CPU → ✅ Still healthy

**External Costs:**
- First 1,000 images/month: FREE
- After: $1.50 per 1,000 images
- Estimated MVP usage: <1,000/month → **$0/month**

---

### Phase 5-6: AI Tagging (Moondream2)

**Infrastructure:** ❌ Requires upgrade to 8GB RAM droplet

| Service | RAM | CPU | Disk | Notes |
|---------|-----|-----|------|-------|
| FastAPI | 300 MB | 15% | 50 MB | Base app |
| **Moondream2** | **4 GB** | **50-100%** | **4 GB** | Model loaded at startup |
| PostgreSQL | 220 MB | 5% | 600 MB | +100 MB for tags |
| Redis | 100 MB | 1% | 50 MB | - |
| MinIO | 200 MB | 5% | 5 GB | - |
| Caddy | 50 MB | 1% | 10 MB | - |
| **Total** | **~5 GB** | **77-100%** | **~10 GB** | ⚠️ Needs 8GB droplet |

**Droplet Upgrade Required:**
- From: $18/month (2GB RAM, 2 vCPU, 50GB SSD)
- To: $48/month (8GB RAM, 4 vCPU, 80GB SSD)
- **Cost: +$30/month**

**Headroom:** 3 GB RAM (good), CPU will spike to 100% during inference (acceptable for background tasks)

---

## Deployment Strategies

### Strategy 1: Phases 1-4 Only (Recommended for Now)

**Timeline:**
- Phase 1: ✅ Done (1 hour)
- Phase 2: Tag Service (2-3 hours)
- Phase 3: API Endpoints (2-3 hours)
- Phase 4: UI Manual Tagging (3-4 hours)
- **Total: 8-11 hours**

**Deployment:**
```bash
# Single deployment after Phase 4
git checkout feat/ai-auto-tagging
git push origin feat/ai-auto-tagging

# CI/CD auto-deploys to production
# OR manual:
ssh root@chitram.io
cd /root/image-hosting-app
git pull origin feat/ai-auto-tagging
docker compose --env-file .env.production down
docker compose --env-file .env.production up --build -d
docker compose exec app uv run alembic upgrade head
```

**Infrastructure:** Current 2GB droplet ✅
**Cost:** $18/month (no change)
**Features:** Manual image tagging functional

**User Value:**
- ✅ Users can tag their images
- ✅ Search by tags (Phase 7)
- ✅ Popular tags widget
- ✅ Tag autocomplete

---

### Strategy 2: Phases 1-6 (Google Vision)

**Timeline:**
- Phases 1-4: 8-11 hours
- Phase 5: AI Provider Integration (3-4 hours with Google only)
- Phase 6: Background Tagging (2-3 hours)
- **Total: 13-18 hours**

**Deployment:**
```bash
# Same as Strategy 1, plus:

# Add to .env.production on droplet
echo "AI_PROVIDER=google" >> .env.production
echo "GOOGLE_VISION_API_KEY=<your-key>" >> .env.production
echo "AI_CONFIDENCE_THRESHOLD=70" >> .env.production

# Rebuild
docker compose --env-file .env.production up --build -d
```

**Infrastructure:** Current 2GB droplet ✅
**Cost:**
- Droplet: $18/month (no change)
- Google Vision: $0-15/month (depends on usage)
- **Total: $18-33/month**

**Features:**
- ✅ Everything from Strategy 1
- ✅ AI auto-tags on upload
- ✅ AI vs user tags differentiated
- ✅ Confidence scores shown

---

### Strategy 3: Phases 1-6 (Moondream2)

**Timeline:**
- Phases 1-4: 8-11 hours
- Phase 5: AI Provider Integration (4-6 hours for Moondream + testing)
- Phase 6: Background Tagging (2-3 hours)
- **Total: 14-20 hours**

**Deployment:**
```bash
# BEFORE deployment: Upgrade droplet
# DigitalOcean Dashboard → Resize → 8GB RAM / 4 vCPU ($48/month)

# Then deploy
ssh root@chitram.io
cd /root/image-hosting-app
git pull origin feat/ai-auto-tagging

# Add to .env.production
echo "AI_PROVIDER=moondream" >> .env.production
echo "AI_CONFIDENCE_THRESHOLD=70" >> .env.production

# First build will download model (~4GB, takes 5-10 minutes)
docker compose --env-file .env.production up --build -d

# Watch logs for model download
docker compose logs -f app
```

**Infrastructure:** 8GB RAM droplet ⚠️ Requires upgrade
**Cost:**
- Droplet: $48/month (+$30)
- AI: $0 (local model)
- **Total: $48/month**

**Features:** Same as Strategy 2, but:
- ✅ No external API dependency
- ✅ No per-image costs
- ✅ Data stays local
- ⚠️ Slower (2-5s vs 500ms)

---

## Recommended Approach

### 🎯 Recommended: **Hybrid Strategy**

**Phase 1-4 (This Week):**
1. Complete Phases 1-4 (manual tagging)
2. Deploy to production on current 2GB droplet
3. Get user feedback on tagging UX

**Phase 5-6 (Later):**
1. Implement Google Vision provider FIRST
2. Deploy with free tier (no cost, no upgrade)
3. Monitor usage and user satisfaction
4. If usage > 1,000 images/month OR API costs concern, THEN:
   - Implement Moondream provider
   - Upgrade droplet to 8GB
   - Switch to Moondream

**Why This Approach:**
- ✅ Fastest time to value (manual tagging works immediately)
- ✅ No upfront infrastructure investment
- ✅ Test feature demand before scaling costs
- ✅ Iterative: Can always add Moondream later
- ✅ Strategy pattern makes provider swap trivial

**Decision Tree:**
```
Deploy Phases 1-4 → Get user feedback
                         ↓
                    Users love tagging?
                    ╱              ╲
                 Yes               No
                  ↓                 ↓
         Add AI (Phase 5-6)    Keep manual only
                  ↓
         Start with Google Vision (free tier)
                  ↓
         Monitor usage for 1 month
                  ↓
         Usage > 1,000 images/month?
         ╱              ╲
       Yes               No
        ↓                 ↓
   Evaluate costs    Keep Google (free)
        ↓
   Costs > $15/month?
   ╱              ╲
 Yes               No
  ↓                 ↓
Upgrade droplet  Keep Google (paid)
Add Moondream
Switch provider
```

---

## Concerns & Mitigations

### Concern 1: Moondream Model Download Time

**Issue:** First deployment downloads ~4GB model (5-10 minutes)
**Mitigation:**
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Pre-download model during build (not runtime)
RUN if [ "$AI_PROVIDER" = "moondream" ]; then \
      python -c "from transformers import AutoModelForCausalLM; \
                 AutoModelForCausalLM.from_pretrained('vikhyatk/moondream2')"; \
    fi
```

**Result:** Model baked into Docker image, no runtime download.

---

### Concern 2: CPU Blocking During Inference

**Issue:** Moondream uses 100% CPU for 2-5 seconds per image
**Mitigation:**
- ✅ Runs in BackgroundTasks (non-blocking for API)
- ✅ Thread pool limits concurrent inferences
- ✅ 4 vCPUs in upgraded droplet (can handle 1-2 concurrent)
- ✅ Users don't wait for tags (background)

**Configuration:**
```python
# app/config.py
ai_max_concurrent_inferences: int = 2  # Limit to 2 at once
ai_inference_timeout_seconds: int = 30  # Fail if stuck
```

---

### Concern 3: Memory Leaks from Model

**Issue:** AI models can leak memory if not managed properly
**Mitigation:**
```python
# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model once
    if settings.ai_provider == "moondream":
        ai_provider = MoondreamProvider()
        await ai_provider.load_model()
        app.state.ai_provider = ai_provider

    yield

    # CRITICAL: Cleanup on shutdown
    if hasattr(app.state, "ai_provider"):
        await app.state.ai_provider.unload_model()
        del app.state.ai_provider
        import gc; gc.collect()  # Force garbage collection
```

---

### Concern 4: Google Vision API Costs

**Issue:** Could get expensive at scale
**Mitigation:**
- Free tier: 1,000 images/month
- Monitor usage via Cloud Console
- Set billing alerts at $10, $25, $50
- Can switch to Moondream if costs exceed threshold

**Cost Calculator:**
| Images/Month | Cost (after free tier) |
|--------------|------------------------|
| 1,000 | $0 (free tier) |
| 5,000 | $6 |
| 10,000 | $15 |
| 50,000 | $75 |

**Break-even:** If usage > 20,000 images/month, Moondream pays for itself ($48 vs $15 + $30 = $45).

---

### Concern 5: External API Dependency

**Issue:** Google Vision downtime affects tagging
**Mitigation:**
```python
# app/services/ai_tagging_service.py
async def tag_image(self, image_id: str) -> list[ImageTag]:
    try:
        tags = await self.ai_provider.analyze_image(image_bytes)
    except ExternalAPIError:
        # Graceful degradation
        logger.warning(f"AI tagging failed for {image_id}, marking as pending")
        await self._mark_tagging_failed(image_id)
        # User can still manually tag
        return []

    # Save tags
    return await self.tag_service.save_ai_tags(image_id, tags)
```

**Result:** Image upload still works, just no AI tags. User can add manually.

---

### Concern 6: Database Migration in Production

**Issue:** Schema changes can cause downtime
**Mitigation:**
- ✅ Migration is additive (no breaking changes)
- ✅ Backward compatible (existing images work without tags)
- ✅ Can run migration during low-traffic window
- ✅ Rollback script ready

**Deployment Window:**
```bash
# Check production traffic (choose low-traffic time)
# Usually early morning or late night

# Maintenance window approach
docker compose --env-file .env.production down
docker compose --env-file .env.production up --build -d
docker compose exec app uv run alembic upgrade head

# Verify
curl https://chitram.io/health
```

**Downtime:** ~30 seconds (container restart + migration)

---

## Summary & Decision Matrix

### Phases 1-4 (Manual Tagging)

| Factor | Status |
|--------|--------|
| New containers? | ❌ No |
| Droplet upgrade? | ❌ No |
| Cost increase? | ❌ No |
| Infrastructure changes? | ❌ No |
| Deployment complexity? | ✅ Same as current |
| **Ready to deploy?** | ✅ **YES** |

**Recommendation:** **Proceed immediately after Phase 4 complete**

---

### Phases 5-6 (AI Tagging)

| Option | Google Vision | Moondream2 | Hybrid |
|--------|--------------|------------|--------|
| **Droplet Upgrade** | ❌ Not needed | ✅ Required (8GB) | ❌ Not needed (initially) |
| **Cost** | $18 + API costs | $48/month | $18 + API costs → $48 |
| **Performance** | Fast (500ms) | Slower (2-5s) | Best of both |
| **Privacy** | ⚠️ External | ✅ Local | Flexible |
| **Complexity** | Low | Medium | Medium |
| **Scalability** | Pay-per-use | Fixed cost | Adaptable |
| **Risk** | External dependency | Resource constraints | Minimal |
| **Recommended for MVP?** | ✅ **YES** | ⚠️ Later | ✅ **IDEAL** |

**Recommendation:** **Start with Google Vision, add Moondream when needed**

---

## Action Items

### Immediate (Phases 1-4)
- [ ] Complete Phase 2 (Tag Service)
- [ ] Complete Phase 3 (API Endpoints)
- [ ] Complete Phase 4 (UI Manual Tagging)
- [ ] Deploy to production (no infrastructure changes)
- [ ] Monitor user adoption

### Future (Phases 5-6) - When Ready
- [ ] Create Google Cloud account
- [ ] Enable Vision API + get API key
- [ ] Set billing alerts ($10, $25, $50)
- [ ] Implement GoogleVisionProvider
- [ ] Deploy with Google Vision (current droplet)
- [ ] Monitor usage for 1 month
- [ ] If costs exceed $15/month, evaluate Moondream upgrade

### Optional (Moondream Path)
- [ ] Test Moondream locally (Phase 5)
- [ ] Benchmark accuracy vs Google Vision
- [ ] Plan droplet upgrade to 8GB ($48/month)
- [ ] Implement MoondreamProvider
- [ ] Deploy to upgraded droplet

---

**Status:** Ready to proceed with Phases 2-4 ✅
**Next:** Implement Phase 2 (Tag Service)
