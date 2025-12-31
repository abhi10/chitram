# Chitram - TODO List & Progress Tracker

**Repository:** https://github.com/abhi10/chitram
**Current Phase:** Phase 2 (Full Features)
**Last Updated:** 2025-12-31

---

## 🎯 Quick Status

| Phase | Status | Branch | Duration | Notes |
|-------|--------|--------|----------|-------|
| **Phase 1 Lean** | ✅ Complete | `main` | 2-3 days | Validated 2025-12-24 |
| **Phase 1.5** | ✅ Complete | `main` | ~4 hours | Merged 2025-12-31 |
| **Phase 2** | 🟡 In Progress | `feature/phase-2` | 1-2 weeks | Full features |
| **Phase 3** | ⏸️ Pending | `feature/phase-3` | 2-3 weeks | Scaling |
| **Phase 4** | ⏸️ Pending | `feature/phase-4` | 1 week | Observability |
| **UI Layer** | 📋 Planning | `chitram-web` | TBD | Optional frontend (after Phase 2) |

---

## ✅ Phase 1 Lean - Foundation (COMPLETE)

**Goal:** Validate core CRUD operations with minimal complexity
**Status:** ✅ Complete - Validated 2025-12-24

### Code Implementation
- [x] FastAPI application structure
- [x] PostgreSQL database setup
- [x] Local filesystem storage
- [x] Image upload/download/delete endpoints
- [x] Structured error handling
- [x] Database exception handler (503 errors)
- [x] Health check endpoint
- [x] DevContainer configuration
- [x] Git repository initialized
- [x] Code pushed to GitHub
- [x] Code review (99% score)
- [x] Documentation complete

### Validation & Testing (COMPLETE)
- [x] **Install dependencies** - `cd backend && uv sync`
- [x] **Test in Codespaces** - Validated DevContainer
- [x] **Run validation checklist** - See `docs/PHASE1_TESTING.md`
  - [x] Import validation (all modules load)
  - [x] Database connection test (SQLite in-memory)
  - [x] Storage service test (local filesystem)
  - [x] Manual testing via Swagger UI
  - [x] Error scenarios verified (invalid file type, missing file)
- [x] **Create validation session log** - `docs/PHASE1_TESTING.md`
- [x] **Docs cleanup** - Reorganized into architecture/, learning/, testing/, archive/

**Branch:** `main`
**Completed:** 2025-12-24

**Note:** Alembic setup and API tests moved to Phase 1.5

---

## ✅ Phase 1.5 - Image Dimensions + Alembic (COMPLETE)

**Goal:** Add Alembic migrations, image dimensions, and run API tests
**Status:** ✅ Complete - Merged 2025-12-31
**Prerequisites:** Phase 1 Lean validated ✅

### Database Migrations (From Phase 1)
- [x] **Setup Alembic** - Initialize migrations (`backend/alembic/`)
- [x] **Create initial migration** - 7-column schema (`d2dc1766a59c_initial_schema_with_7_columns.py`)
- [x] **Create second migration** - Add width, height columns (`a11aa549249d_add_width_and_height_columns.py`)

### Pillow Integration
- [x] **Pillow dependency** - Added to dev deps with comment for Phase 1.5
- [x] **Add `get_image_dimensions()` method** to `image_service.py`
- [x] **Add width/height to `Image` model** - Nullable for backward compatibility
- [x] **Add width/height to schemas** (ImageMetadata, ImageUploadResponse)
- [x] **Update API response construction** - Include dimensions in upload response

### Testing
- [x] **Run API tests** - All 11 tests passing
- [x] **Update tests** - Added width/height assertions (100x100 test fixtures)
- [x] **Fix test assertions** - Changed `data["error"]` to `data["detail"]` (FastAPI format)

### Finalize
- [x] **Commit changes** - `feat: Phase 1.5 - Add image dimensions with Pillow integration`
- [x] **Push branch** - `phase1.5-Image-Dimension`
- [x] **Merge to main** - PR merged 2025-12-31

**Branch:** `phase1.5-Image-Dimension` (merged to `main`)
**Actual Duration:** ~4 hours
**Blockers:** None

**Reference:** `docs/architecture/phase-1-foundation.md`

---

## 🟡 Phase 2 - Full Features (CURRENT)

**Goal:** Add production features: MinIO, Redis, Auth, Background Jobs
**Status:** 🟡 In Progress
**Prerequisites:** Phase 1.5 complete ✅

### Week 1: Storage & Caching
- [x] **Create feature branch** - `git checkout -b feature/phase-2`
- [x] **MinIO Backend:** ✅ Complete
  - [x] Add MinIO to docker-compose.yml (ports 9000/9001, health check)
  - [x] Restore `MinioStorageBackend` class (async with `asyncio.to_thread`)
  - [x] Add MinIO configuration to settings (`storage_backend`, endpoint, credentials)
  - [x] Add minio dependency to pyproject.toml
  - [x] Update main.py with backend selection logic
  - [x] Update DevContainer post-create.sh (MinIO health check)
  - [x] Create unit tests (11 tests with mocking)
  - [x] Create integration tests (9 tests, auto-skip without MinIO)
  - [x] All 22 regression + unit tests passing
- [ ] **Redis Caching:**
  - [ ] Add Redis to docker-compose.yml
  - [ ] Add Redis dependency
  - [ ] Create cache service layer
  - [ ] Cache metadata queries (TTL: 1 hour)
  - [ ] Cache invalidation on delete
- [ ] **Rate Limiting:**
  - [ ] Redis-backed rate limiter
  - [ ] 10 requests/IP/minute
  - [ ] Return 429 with Retry-After header
- [ ] **Concurrency Control:** (from Graphiti patterns)
  - [ ] Add `asyncio.Semaphore` for concurrent upload limits
  - [ ] Prevent file collision on simultaneous uploads
  - [ ] Configure `SEMAPHORE_LIMIT` in settings
- [ ] **Testing & Validation:**
  - [ ] All Phase 1 functionality preserved
  - [ ] Storage switching works
  - [ ] Cache hit/miss working
  - [ ] Rate limits enforced

### Week 2: Auth & Background Jobs
- [ ] **User Authentication:**
  - [ ] Create users table
  - [ ] JWT token implementation
  - [ ] Registration endpoint
  - [ ] Login endpoint
  - [ ] Protected routes
  - [ ] Add user_id to images table
- [ ] **Delete Tokens:**
  - [ ] Generate secure token on upload
  - [ ] Store in database (encrypted)
  - [ ] Require token for deletion
  - [ ] Token expiration
- [ ] **Background Jobs (Celery):**
  - [ ] Add Celery dependency
  - [ ] Setup Celery worker
  - [ ] Thumbnail generation task (3 sizes)
  - [ ] Image optimization task
  - [ ] Checksum calculation
  - [ ] Update docker-compose.yml
- [ ] **Image Deduplication:**
  - [ ] Evaluate imagededup library (CNN/hashing-based)
  - [ ] Store perceptual hash on upload
  - [ ] Find duplicates endpoint (`GET /images/{id}/duplicates`)
  - [ ] Optional: Block duplicate uploads
  - [ ] Reference: https://deepwiki.com/idealo/imagededup/7-usage-examples
- [ ] **Advanced Validation:**
  - [ ] Restore python-magic library
  - [ ] Better file type detection
- [ ] **Model Updates:**
  - [ ] Add fields: user_id, is_public, updated_at, checksum
  - [ ] Create Alembic migration
  - [ ] Update schemas
- [ ] **Final Validation:**
  - [ ] All features working together
  - [ ] Performance testing
  - [ ] Documentation updated
- [ ] **Merge & Tag:**
  - [ ] Merge to main
  - [ ] Tag `v0.2.0`

**Branch:** `feature/phase-2`
**Time Estimate:** 1-2 weeks
**Blockers:** None

**Reference:** `docs/phase-execution-plan.md` lines 173-286

---

## 🚀 Phase 3 - Horizontal Scaling (FUTURE)

**Goal:** Scale to 1000s of concurrent users
**Status:** ⏸️ Not started
**Prerequisites:** Phase 2 complete

### Implementation Checklist
- [ ] **Create feature branch** - `git checkout -b feature/phase-3`
- [ ] **Load Balancer (Nginx):**
  - [ ] Add Nginx to docker-compose
  - [ ] Configure round-robin
  - [ ] Health checks
  - [ ] SSL termination
  - [ ] Test with 3 API instances
- [ ] **Database Replication:**
  - [ ] Setup PostgreSQL streaming replication
  - [ ] 1 primary + 2 read replicas
  - [ ] Add read/write connection pools
  - [ ] Update code to use read replicas for queries
  - [ ] Test failover
- [ ] **Storage Sharding:**
  - [ ] Implement consistent hashing
  - [ ] Shard across multiple S3 buckets
  - [ ] Update storage router
- [ ] **Redis Cluster:**
  - [ ] 3 master nodes
  - [ ] Sentinel for failover
  - [ ] Session storage
- [ ] **CDN Integration:**
  - [ ] CloudFront or Cloudflare
  - [ ] Cache image files at edge
  - [ ] Update image URLs
- [ ] **Load Testing:**
  - [ ] Use Locust for testing
  - [ ] Target: 1000 concurrent users
  - [ ] Measure p95 latency
  - [ ] Identify bottlenecks
- [ ] **Validation:**
  - [ ] No single point of failure
  - [ ] Automatic failover working
  - [ ] 10x Phase 2 load capacity
- [ ] **Merge & Tag:**
  - [ ] Merge to main
  - [ ] Tag `v0.3.0`

**Branch:** `feature/phase-3` (to be created)
**Time Estimate:** 2-3 weeks
**Blockers:** Phase 2 complete

**Reference:** `docs/phase-execution-plan.md` lines 288-413

---

## 📊 Phase 4 - Observability (FUTURE)

**Goal:** Production-ready monitoring and reliability
**Status:** ⏸️ Not started
**Prerequisites:** Phase 3 complete

### Implementation Checklist
- [ ] **Create feature branch** - `git checkout -b feature/phase-4`
- [ ] **Prometheus & Grafana:**
  - [ ] Deploy Prometheus server
  - [ ] Add instrumentation to API
  - [ ] Create Grafana dashboards
  - [ ] Track: requests/sec, errors, latency, storage
- [ ] **Logging (Loki or ELK):**
  - [ ] Structured logging setup
  - [ ] Deploy logging stack
  - [ ] Request tracing
  - [ ] Error aggregation
- [ ] **Distributed Tracing (Jaeger):**
  - [ ] Add Jaeger instrumentation
  - [ ] Trace request flow
  - [ ] Identify bottlenecks
- [ ] **Alerting:**
  - [ ] Define alert rules
  - [ ] Setup PagerDuty/Slack
  - [ ] Test alert firing
  - [ ] Create runbooks
- [ ] **Circuit Breakers:** (Graphiti pattern)
  - [ ] Add circuit breaker library (e.g., `aiobreaker`)
  - [ ] Protect storage operations (fail fast on repeated errors)
  - [ ] Protect external service calls
  - [ ] Graceful degradation with fallback responses
  - [ ] Retry with exponential backoff
- [ ] **Health Checks:**
  - [ ] Liveness probe
  - [ ] Readiness probe
  - [ ] Dependency checks
- [ ] **Validation:**
  - [ ] All metrics collecting
  - [ ] Dashboards showing real-time data
  - [ ] Alerts firing correctly
  - [ ] 99.9% uptime target
- [ ] **Merge & Tag:**
  - [ ] Merge to main
  - [ ] Tag `v1.0.0` (Production Ready!)

**Branch:** `feature/phase-4` (to be created)
**Time Estimate:** 1 week
**Blockers:** Phase 3 complete

**Reference:** `docs/phase-execution-plan.md` lines 415-502

---

## 🌐 Future: UI Layer (chitram-web)

**Goal:** Optional web frontend for the Chitram API
**Status:** 📋 Planning (not started)
**Prerequisites:** Phase 2 complete (Auth required for user-specific galleries)
**Repository:** `github.com/abhi10/chitram-web` (to be created)

### Architecture Decision

```
┌─────────────────────┐         ┌─────────────────────┐
│    chitram-web      │  HTTP   │      chitram        │
│    (Frontend)       │────────▶│      (API)          │
│                     │         │                     │
│  - Gallery UI       │         │  - REST endpoints   │
│  - Upload form      │         │  - Auth (JWT)       │
│  - User dashboard   │         │  - Storage          │
└─────────────────────┘         └─────────────────────┘
```

### Option Evaluation

| Option | Stack | Effort | Pros | Cons |
|--------|-------|--------|------|------|
| **A: HTMX + Jinja2** | Python (same repo) | ~1 day | No JS build, fast, simple | Limited interactivity |
| **B: React SPA** | TypeScript, Vite | ~1 week | Rich UX, component ecosystem | Separate build, complexity |
| **C: Next.js** | TypeScript, React | ~1 week | SSR, SEO, API routes | Node.js runtime needed |
| **D: FastAPI-Admin** | Python plugin | ~2 hours | Quick admin CRUD | Not user-facing |

**Recommendation:** Start with **Option A (HTMX)** for quick validation, migrate to **Option B/C** if richer UX needed.

### Planned Features (Phase 5+)

- [ ] **Public Pages:**
  - [ ] Home page with recent uploads
  - [ ] Image detail page (`/image/{id}`)
  - [ ] Public gallery view
- [ ] **User Features (requires Phase 2 Auth):**
  - [ ] User registration/login
  - [ ] Personal gallery (`/my-images`)
  - [ ] Upload form with drag-and-drop
  - [ ] Batch upload support
  - [ ] Image management (delete, visibility toggle)
- [ ] **Admin Features:**
  - [ ] Dashboard with stats
  - [ ] User management
  - [ ] Storage usage monitoring
  - [ ] Moderation tools
- [ ] **UX Enhancements:**
  - [ ] Responsive design (mobile-first)
  - [ ] Dark mode toggle
  - [ ] Image lightbox/preview
  - [ ] Copy link to clipboard
  - [ ] Share buttons

### Tech Stack (Option A - HTMX)

```
chitram-web/ (or chitram/frontend/)
├── templates/
│   ├── base.html           # Layout with TailwindCSS
│   ├── home.html           # Gallery grid
│   ├── upload.html         # Upload form
│   ├── image.html          # Image detail
│   └── partials/           # HTMX fragments
│       ├── gallery-item.html
│       └── upload-progress.html
├── static/
│   ├── css/
│   └── js/
└── routes/
    └── web.py              # Jinja2 template routes
```

### Tech Stack (Option B - React)

```
chitram-web/
├── src/
│   ├── components/
│   │   ├── Gallery.tsx
│   │   ├── ImageCard.tsx
│   │   ├── UploadForm.tsx
│   │   └── Navbar.tsx
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── Upload.tsx
│   │   └── Image.tsx
│   ├── hooks/
│   │   └── useApi.ts
│   └── App.tsx
├── package.json
└── vite.config.ts
```

### API Integration Points

| Frontend Action | API Endpoint | Notes |
|-----------------|--------------|-------|
| Load gallery | `GET /api/v1/images/` | Paginated list |
| View image | `GET /api/v1/images/{id}` | Metadata |
| Display image | `GET /api/v1/images/{id}/file` | Binary stream |
| Upload | `POST /api/v1/images/upload` | Multipart form |
| Delete | `DELETE /api/v1/images/{id}` | Requires auth (Phase 2) |
| Login | `POST /api/v1/auth/login` | Phase 2 |
| Register | `POST /api/v1/auth/register` | Phase 2 |

### When to Start

```
Now (Phase 1-2):     API-only, use Swagger UI for testing
After Phase 2:       Option A (HTMX) for quick demo
After Phase 3:       Option B/C if production UI needed
```

**Decision:** Defer until Phase 2 Auth is complete. API-first approach allows any frontend later.

---

## 🧪 Testing Checklist (For Each Phase)

### Before Merging Any Phase
- [ ] All unit tests pass - `pytest tests/unit -v`
- [ ] All API tests pass - `pytest tests/api -v`
- [ ] Code coverage > 80% - `pytest --cov=app`
- [ ] Linting passes - `ruff check .`
- [ ] Formatting correct - `black . --check`
- [ ] No type errors - `mypy app/` (if strict mode)
- [ ] Manual testing via Swagger UI
- [ ] Error scenarios tested
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Session log created
- [ ] Code review performed

### Performance Testing (Phase 2+)
- [ ] Load test with Locust
- [ ] Measure baseline metrics
- [ ] Compare to previous phase
- [ ] No performance regressions
- [ ] Identify bottlenecks

**Reference:** `docs/validation-checklist.md`

---

## 🚢 Deployment Checklist

### GitHub Codespaces (Primary)
- [x] DevContainer configuration created
- [x] docker-compose.yml setup
- [x] post-create.sh script
- [ ] Test Codespace creation
- [ ] Verify all services start
- [ ] Test from fresh Codespace
- [ ] Document any issues

### Local Development
- [ ] Docker Desktop running
- [ ] Clone repository
- [ ] Run `cd backend && uv sync`
- [ ] Start services: `docker-compose up -d`
- [ ] Run app: `uv run uvicorn app.main:app --reload`
- [ ] Access Swagger: http://localhost:8000/docs

### Production (Phase 4)
- [ ] Choose hosting provider (AWS/GCP/Azure)
- [ ] Setup CI/CD pipeline
- [ ] Database backups configured
- [ ] SSL certificates setup
- [ ] Domain name configured
- [ ] Monitoring alerts setup
- [ ] Incident response plan
- [ ] Disaster recovery tested

---

## 📋 Git Workflow Checklist

### Starting New Phase
```bash
# 1. Ensure main is up-to-date
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/phase-X.X

# 3. Make changes, commit often
git add .
git commit -m "feat: descriptive message"

# 4. Push branch to GitHub
git push -u origin feature/phase-X.X
```

### Merging Phase to Main
```bash
# 1. Ensure all tests pass
pytest tests/ -v

# 2. Update documentation
# - Changelog
# - Session log
# - README (if needed)

# 3. Switch to main
git checkout main
git pull origin main

# 4. Merge feature branch
git merge feature/phase-X.X

# 5. Tag release
git tag v0.X.0
git push origin main --tags

# 6. Delete feature branch (optional)
git branch -d feature/phase-X.X
git push origin --delete feature/phase-X.X
```

---

## 📚 Documentation Reference

### Essential Documents
- **Architecture:** `docs/architecture/BUILDING_BLOCKS.md` - Core DS principles
- **Phase Details:** `docs/architecture/phase-{1,2,3,4}-*.md`
- **Learnings:** `docs/learning/LEARNINGS.md` - DS building blocks tracker
- **Testing:** `docs/testing/TESTING_STRATEGY.md` - Testing approach
- **Validation:** `docs/PHASE1_TESTING.md` - Phase 1 test results
- **Code Review:** `docs/code-review-checklist.md`
- **Requirements:** `requirements.md`
- **ADRs:** `docs/adr/` (9 decisions documented)

### Archived Documents
- **Archive:** `docs/archive/` - Historical docs preserved for reference
  - Original 2200-line MVP design doc
  - Phase execution plan
  - One-time code reviews

### Key ADRs
- **ADR-0008:** Phase 1 Lean approach (defer complexity)
- **ADR-0007:** Use GitHub Codespaces
- **ADR-0006:** No Kubernetes for MVP
- **ADR-0005:** Structured error format
- **ADR-0001:** Use FastAPI framework

### External References
- **Graphiti Patterns:** https://github.com/getzep/graphiti - Storage abstraction, concurrency control, circuit breakers
- **Image Deduplication:** https://deepwiki.com/idealo/imagededup/7-usage-examples - Perceptual hashing
- **System Design Foundation:** Stages 1-5 (Core → Performance → Distributed → Reliability → Advanced)

---

## 🎯 Current Focus

**Phase 2 - In Progress:**
1. ✅ MinIO Backend setup - Complete!
2. ⏳ Redis caching layer
3. ⏳ Rate limiting implementation
4. ⏳ User authentication (JWT)
5. ⏳ Background jobs (Celery)

**Completed (Phase 2 - MinIO):**
- ✅ MinioStorageBackend implementation (Strategy Pattern)
- ✅ Docker Compose with MinIO service
- ✅ Configuration-based backend selection
- ✅ Unit tests (11) + Integration tests (9)
- ✅ All 22 tests passing (+ 9 skipped integration)

**Completed (Phase 1.5):**
- ✅ Alembic migrations setup (2 migrations)
- ✅ Pillow integration for image dimensions
- ✅ All 11 API tests passing
- ✅ Merged to main 2025-12-31

---

## 📊 Progress Summary

```
Timeline: 8 weeks total (2 months)

Week 1-2:   Phase 1 Lean ✅ (Complete - Validated 2025-12-24)
Week 2:     Phase 1.5 ✅ (Complete - Merged 2025-12-31)
Week 3-4:   Phase 2 🟡 (In Progress)
Week 5-7:   Phase 3 ⏸️ (Not started)
Week 8:     Phase 4 ⏸️ (Not started)
```

**Current Status:** 🟢 On track
**Blockers:** None
**Last Updated:** 2025-12-31

---

## 🎉 Milestones

- [x] **2025-12-13:** Project initialized, ADRs created
- [x] **2025-12-19:** Phase 1 Lean scaffolding complete
- [x] **2025-12-20:** Code review (99% score), pushed to GitHub
- [x] **2025-12-24:** Phase 1 Lean validation complete (see `docs/PHASE1_TESTING.md`)
- [x] **2025-12-24:** Docs cleanup - reorganized into architecture/, learning/, testing/, archive/
- [x] **2025-12-31:** Phase 1.5 complete - Alembic migrations + Pillow image dimensions
- [ ] **In Progress:** Phase 2 full features (MinIO, Redis, Auth, Background Jobs)
- [ ] **Next:** Phase 3 horizontal scaling
- [ ] **Next:** Phase 4 observability
- [ ] **Target:** v1.0.0 production-ready system

---

**Repository:** https://github.com/abhi10/chitram
**Project Name:** Chitram (చిత్రం - Image/Picture in Telugu)
**Author:** @abhi10
**License:** (To be added)
