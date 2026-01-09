# Chitram - TODO List & Progress Tracker

**Repository:** https://github.com/abhi10/chitram
**Current Phase:** Phase 3.5 Complete - Supabase Auth + Production Deployed
**Last Updated:** 2026-01-08

---

## 🎯 Quick Status

| Phase | Status | Branch | Description |
|-------|--------|--------|-------------|
| **Phase 1 Lean** | ✅ Complete | `main` | Core CRUD, validated 2025-12-24 |
| **Phase 1.5** | ✅ Complete | `main` | Alembic + Pillow, merged 2025-12-31 |
| **Phase 2A** | ✅ Complete | `main` | User Auth (JWT), 151 tests |
| **Phase 2B** | ✅ Complete | `main` | Thumbnails (FastAPI BackgroundTasks), 188 tests |
| **Phase 3** | ✅ Complete | `main` | Web UI (HTMX + Jinja2), deployed 2026-01-04 |
| **Phase 3.5** | ✅ Complete | `main` | Supabase Auth Integration, 255 tests |
| **Phase 4** | ⏸️ Future | - | Advanced Features (Celery, Dedup) |
| **Phase 5** | ⏸️ Future | - | Distributed Cache (Consistent Hashing) |
| **Phase 6** | ⏸️ Future | - | Basic Observability (Prometheus)

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
- [x] **MinIO Backend:** ✅ Complete & Tested in Codespaces
  - [x] Add MinIO to docker-compose.yml (ports 9000/9001, health check)
  - [x] Restore `MinioStorageBackend` class (async with `asyncio.to_thread`)
  - [x] Add MinIO configuration to settings (`storage_backend`, endpoint, credentials)
  - [x] Add minio dependency to pyproject.toml
  - [x] Update main.py with backend selection logic
  - [x] Update DevContainer post-create.sh (MinIO health check)
  - [x] Create unit tests (11 tests with mocking)
  - [x] Create integration tests (9 tests, auto-skip without MinIO)
  - [x] All 31 tests passing (11 API + 11 Unit + 9 Integration)
  - [x] **Codespaces Testing:** Validated full integration (see `docs/PHASE2_RETRO.md`)
- [x] **CI/CD Pipeline:** ✅ Complete
  - [x] GitHub Actions workflow (`.github/workflows/ci.yml`)
  - [x] Lint job (Black + Ruff)
  - [x] Test job (Python 3.11/3.12 with PostgreSQL + MinIO services)
  - [x] Dependency check job (catches missing imports)
- [x] **Automation Scripts:** ✅ Complete
  - [x] `scripts/validate-env.sh` - Verify all services running
  - [x] `scripts/run-tests.sh` - Run test suite with options
  - [x] `scripts/smoke-test.sh` - Quick API CRUD test
  - [x] `scripts/cleanup-test-data.sh` - Reset MinIO + DB
- [x] **Documentation:** ✅ Complete
  - [x] `docs/CODESPACES_RUNBOOK.md` - Dev Container testing guide
  - [x] `docs/PHASE2_RETRO.md` - Retrospective with learnings
- [x] **Dependency Cleanup:**
  - [x] Removed duplicate `[dependency-groups]` section from pyproject.toml
  - [x] Added missing deps: pillow, pytest, pytest-asyncio, pytest-cov, aiosqlite
- [x] **Redis Caching:** ✅ Complete (ADR-0009)
  - [x] Add Redis to docker-compose.yml (with health check, persistence)
  - [x] Add Redis dependency (redis>=5.2.0, hiredis>=3.0.0)
  - [x] Create cache service layer (Cache-Aside pattern)
  - [x] Cache metadata queries (TTL: 1 hour, configurable)
  - [x] Cache invalidation on delete
  - [x] X-Cache response header (HIT/MISS/DISABLED)
  - [x] Graceful degradation (system works without Redis)
  - [x] Health endpoint reports cache status
  - [x] Unit tests (19 tests with mocking)
  - [x] Integration tests (11 tests, auto-skip without Redis)
- [x] **Rate Limiting:** ✅ Complete
  - [x] Redis-backed rate limiter (`rate_limiter.py`)
  - [x] 10 requests/IP/minute (configurable via `RATE_LIMIT_PER_MINUTE`)
  - [x] Return 429 with Retry-After header
  - [x] Fail-open design (allows requests if Redis unavailable)
  - [x] Health endpoint reports rate limiter status
  - [x] Unit tests (22 tests with mocking)
  - [x] Rate limiting disabled in test fixtures
- [x] **Concurrency Control:** ✅ Complete (ADR-0010)
  - [x] Add `asyncio.Semaphore` for concurrent upload limits (default: 10)
  - [x] Acquire semaphore before `file.read()` (memory optimization)
  - [x] Return 503 if wait exceeds timeout threshold
  - [x] Configure `UPLOAD_CONCURRENCY_LIMIT` and `UPLOAD_CONCURRENCY_TIMEOUT` in settings
  - [x] Health endpoint reports concurrency status
  - [x] Unit tests (12 tests in `tests/unit/test_concurrency.py`)
  - [x] DRY refactor: shared dependencies in `app/api/dependencies.py`
- [x] **Technical Debt & Performance Fixes:** ✅ Complete
  - [x] ~~🔴 Fix sync Pillow blocking event loop~~ - ✅ Complete (`asyncio.to_thread()` in `get_image_dimensions`)
  - [x] ~~🔴 Add rate limiting (DoS prevention)~~ - ✅ Complete (see Rate Limiting above)
  - [x] ~~🟡 Configure DB connection pool~~ - ✅ Complete (`pool_size=5`, `max_overflow=10`, `pool_recycle=3600`)
  - [x] ~~🟡 Make MinIO bucket check async with timeout~~ - ✅ Complete (`MinioStorageBackend.create()` factory method)
  - [x] ~~🟡 Add logging for storage deletion failures~~ - ✅ Complete (orphan tracking with warning logs)
  - [ ] 🟡 Consider streaming uploads (defer to Phase 3 if complex)
- [x] **Testing & Validation:** ✅ 114 tests passing
  - [x] All Phase 1 functionality preserved
  - [x] Storage switching works
  - [x] Cache hit/miss working (X-Cache header)
  - [x] Rate limits enforced (429 + Retry-After)
  - [x] Concurrency control enforced (503 on timeout)

### Rate Limiting Testing Checklist
> **Note:** Tests 2-8 are automated in `tests/integration/test_rate_limiter_integration.py`

| # | Test | Expected Result | Status |
|---|------|-----------------|--------|
| 1 | Start app with Redis | Log: "✅ Rate limiter enabled (Redis-backed)" | ⬜ Manual |
| 2 | Upload 10 images quickly | All succeed (200/201) | ✅ Automated |
| 3 | Upload 11th image | 429 Too Many Requests | ✅ Automated |
| 4 | Check response headers | `Retry-After: <seconds>` present | ✅ Automated |
| 5 | Wait for window reset | Next upload succeeds | ✅ Automated |
| 6 | Stop Redis, upload image | Request allowed (fail-open) | ✅ Automated |
| 7 | Health check | `"rate_limiter": "enabled"` | ✅ Automated |
| 8 | Set `RATE_LIMIT_ENABLED=false` | Unlimited requests allowed | ✅ Automated |

### Concurrency Control Testing Checklist
> **Note:** Tests 2-7 are automated in `tests/unit/test_concurrency.py` (12 tests)

| # | Test | Expected Result | Status |
|---|------|-----------------|--------|
| 1 | Start app | Log: "✅ Upload concurrency limit: 10" | ⬜ Manual |
| 2 | Upload single image | Succeeds normally (201) | ✅ Automated |
| 3 | Acquire within limit | All acquire calls succeed | ✅ Automated |
| 4 | Concurrent acquires respect limit | Only N succeed for limit=N | ✅ Automated |
| 5 | Exceed timeout | Returns False (503 in API) | ✅ Automated |
| 6 | Release allows new acquire | Slot freed after release | ✅ Automated |
| 7 | Health check | Reports `active/limit` status | ✅ Automated |
| 8 | Set `UPLOAD_CONCURRENCY_LIMIT=5` | Only 5 concurrent uploads allowed | ⬜ Manual |
| 9 | Set `UPLOAD_CONCURRENCY_TIMEOUT=5` | 503 after 5s wait | ⬜ Manual |
| 10 | Memory check during uploads | Peak memory bounded by limit × 5MB | ⬜ Manual |

**Testing Commands:**
```bash
# Simulate concurrent uploads (requires parallel or xargs)
seq 15 | xargs -P 15 -I {} curl -X POST -F "file=@test.jpg" http://localhost:8000/api/v1/images/upload

# Or use Python script for precise control
python -c "
import asyncio
import httpx

async def upload(n):
    async with httpx.AsyncClient() as client:
        with open('test.jpg', 'rb') as f:
            r = await client.post('http://localhost:8000/api/v1/images/upload', files={'file': f})
            print(f'{n}: {r.status_code}')

async def main():
    await asyncio.gather(*[upload(i) for i in range(15)])

asyncio.run(main())
"
```

### Phase 2A: User Authentication (ADR-0011)

**Goal:** Enable user ownership of images and secure deletion.
**Status:** ✅ Complete (151 tests passing)
**Branch:** `feature2/phase2A-auth`

**Why This Matters for Users:**
- Own their images (track uploads, manage gallery)
- Secure deletion (only owner can delete)
- Foundation for per-user features (quotas, sharing)

- [x] **Database & Models:**
  - [x] Create `users` table (id, email, password_hash, is_active, created_at)
  - [x] Add `user_id` FK to `images` table (nullable for anonymous)
  - [x] Add `delete_token_hash` to `images` table
  - [x] Create Alembic migration (`2f6a8fb30700_add_users_table_and_image_ownership.py`)
  - [x] Update SQLAlchemy models (`app/models/user.py`, `app/models/image.py`)
- [x] **Authentication Service:**
  - [x] Add dependencies: `python-jose`, `bcrypt`, `email-validator`
  - [x] Create `app/services/auth_service.py`
  - [x] Password hashing with bcrypt (work factor 12)
  - [x] JWT token generation (HS256, 24h expiry)
  - [x] JWT token validation
- [x] **Auth Endpoints:**
  - [x] `POST /api/v1/auth/register` - Create account
  - [x] `POST /api/v1/auth/login` - Get JWT token
  - [x] `POST /api/v1/auth/token` - OAuth2 token endpoint (for Swagger UI)
  - [x] `GET /api/v1/auth/me` - Current user profile
  - [ ] `GET /api/v1/users/me/images` - List user's images (deferred to Phase 2C)
- [x] **Delete Token System:**
  - [x] Generate secure token on anonymous upload (32 bytes, URL-safe)
  - [x] Return `delete_token` in upload response (anonymous only)
  - [x] Store SHA-256 hash in database (not plaintext)
  - [x] Require token for anonymous image deletion
  - [x] Skip token check if authenticated user owns image
- [x] **Protected Routes:**
  - [x] `Depends(get_current_user)` for protected endpoints
  - [x] `DELETE /api/v1/images/{id}` - Require ownership OR delete token
  - [x] Return 401 for missing/invalid JWT
  - [x] Return 403 for wrong owner/token
- [x] **Configuration:**
  - [x] `JWT_SECRET_KEY` environment variable (default for dev, required in prod)
  - [x] `JWT_ALGORITHM` (default: HS256)
  - [x] `JWT_EXPIRE_MINUTES` (default: 1440 = 24h)
- [x] **Testing:** (38 auth tests)
  - [x] Unit tests for auth service (18 tests)
  - [x] API tests for auth endpoints (12 tests)
  - [x] API tests for protected image routes (8 tests)
- [x] **Security Testing:** (See ADR-0011)
  - [x] Password Security:
    - [x] Verify bcrypt hash format (`$2b$` prefix) - tested
    - [x] Verify work factor ≥ 12 (timing: 200-400ms) - tested
    - [x] No plaintext passwords in logs/responses - verified
  - [x] JWT Security:
    - [x] Required claims present (sub, exp, iat) - tested
    - [x] Expired tokens rejected (401) - tested
    - [x] Invalid signatures rejected (401) - tested
    - [x] Algorithm confusion prevented (only HS256) - enforced
  - [x] API Security:
    - [x] No user enumeration (same error for wrong email/password) - tested
    - [ ] Rate limiting on `/auth/*` endpoints - uses existing rate limiter
    - [x] Timing-safe comparisons - using secrets.compare_digest
  - [x] Delete Token Security:
    - [x] 32-byte cryptographically random tokens - using secrets.token_urlsafe(32)
    - [x] Hash stored in DB (not plaintext) - SHA-256 hash
    - [x] Timing-safe token comparison - using secrets.compare_digest
  - [x] OWASP Alignment:
    - [x] A01: Access control tested (ownership checks)
    - [x] A02: Password hashing verified (bcrypt)
    - [x] A07: No credentials in logs (verified)
- [ ] **Validation & Merge:**
  - [x] All auth tests passing (151 tests total)
  - [x] Anonymous uploads still work (backward compatible)
  - [ ] Merge to main, tag `v0.2.0-auth`

**ADR:** [ADR-0011: User Authentication with JWT](docs/adr/0011-user-authentication-jwt.md)

---

### Phase 2B: Background Tasks - Thumbnails (ADR-0012 Revised)

**Goal:** Generate thumbnails asynchronously using FastAPI BackgroundTasks.
**Status:** ✅ Complete (188 tests passing)
**Branch:** `feature2/phase-2-redis-minio`

> **Scope Change:** Celery infrastructure deferred to Phase 4. Using built-in FastAPI BackgroundTasks for simplicity.

**Why This Matters for Users:**
- Gallery loads faster with 300px thumbnails instead of 5MB originals
- Upload response remains fast (~500ms)

- [x] **Implementation:**
  - [x] Add `thumbnail_key` column to images table (migration: `42cb2a9fa7a2`)
  - [x] Create Alembic migration
  - [x] Create `app/services/thumbnail_service.py`
  - [x] Generate single thumbnail (300px max dimension, maintain aspect ratio)
  - [x] Store thumbnail in same storage backend as original (prefix: `thumbs/`)
  - [x] Update image record with thumbnail key
  - [x] Use `asyncio.to_thread()` for CPU-bound Pillow operations
- [x] **API Integration:**
  - [x] Use `BackgroundTasks` in upload endpoint
  - [x] Add `thumbnail_ready: boolean` to image response
  - [x] Add `thumbnail_url` to image response (when ready)
  - [x] `GET /api/v1/images/{id}/thumbnail` - Return thumbnail or 404
  - [x] Add `THUMBNAIL_NOT_READY` error code
- [x] **Error Handling:**
  - [x] Log thumbnail failures (graceful degradation)
  - [x] Original image always available as fallback
  - [x] Return 404 with appropriate error codes (IMAGE_NOT_FOUND, THUMBNAIL_NOT_READY)
- [x] **Testing:** (37 new tests)
  - [x] Unit tests for thumbnail service (25 tests)
  - [x] API tests for thumbnail endpoint (12 tests)
  - [x] Verify upload response time unchanged
- [x] **Validation & Merge:**
  - [x] All 188 tests passing
  - [x] Thumbnails generating correctly
  - [ ] Merge to main, tag `v0.2.0-thumbnails`

**ADR:** [ADR-0012: Background Tasks Strategy](docs/adr/0012-background-jobs-celery.md)

---

## ✅ Phase 3 - Web UI (COMPLETE)

**Goal:** Add web-based user interface using HTMX and Jinja2 templates
**Status:** ✅ Complete - Deployed to production 2026-01-04
**Branch:** `main` (merged from `feature/phase3A-foundation`)
**Prerequisites:** Phase 2A Auth complete ✅, Phase 2B Thumbnails complete ✅
**Deployed:** https://chitram.io

> **Architecture Decisions:**
> - [ADR-0013: Web UI with HTMX](docs/adr/0013-web-ui-htmx.md) - Technology choice
> - [ADR-0015: UI Design System](docs/adr/0015-ui-design-system.md) - Warm Minimal theme

**Why This Matters for Users:**
- Visual gallery to browse images
- Easy upload via drag-and-drop
- User dashboard to manage their images

**Design Documents:**
- [UI Design Spec](docs/architecture/ui-design-doc.md) - Full mockup analysis, wireframes, component patterns

---

### 🔬 Spike: UI Layout Design ✅ COMPLETE

> **Status:** ✅ Complete
> **Outcome:** Warm Minimal theme selected, design system documented

**Decisions Made:**
- [x] Visual style: **Warm Minimal** (cream bg, terracotta accents, serif logo)
- [x] Page layouts: Masonry gallery, glassmorphism detail view
- [x] Responsive: Desktop-first with Tailwind breakpoints
- [x] Colors: Terracotta (#C4956A), Cream (#FAF8F5)
- [x] Typography: Playfair Display (headings), Source Sans 3 (body)
- [x] TailwindCSS: CDN with custom config (no build step for MVP)

**MVP Scope Decisions:**
| Feature | Decision | Rationale |
|---------|----------|-----------|
| Image titles | Use filename | Already in API |
| EXIF data | Defer to Part 2 | Requires backend work |
| Color palette | Defer to Part 2 | Additional service needed |
| Tags/hashtags | Defer to Part 2 | New DB tables |
| Filters sidebar | Omit for MVP | Keep simple |
| Pagination | "Load More" button | HTMX-friendly |

---

### Phase 3A: Foundation (Days 1-2) ✅ COMPLETE

> **Status:** ✅ Complete (2026-01-03)
> **Branch:** `feature/phase3A-foundation`
> **Runbook:** [docs/PHASE3_UI_RUNBOOK.md](docs/PHASE3_UI_RUNBOOK.md)

- [x] **FastAPI Template Setup:**
  - [x] Add `jinja2` dependency to pyproject.toml
  - [x] Configure Jinja2Templates in main.py
  - [x] Mount static files directory
  - [x] Create `backend/app/templates/` directory
  - [x] Create `backend/app/static/` directory
- [x] **Base Template:**
  - [x] `base.html` with TailwindCSS CDN config
  - [x] Google Fonts (Playfair Display, Source Sans 3)
  - [x] HTMX script include
  - [x] Custom Tailwind colors (terracotta, cream)
- [x] **Navigation Partial:**
  - [x] `partials/nav.html` - Logo, nav links
  - [x] Conditional auth state (Login vs Profile)
  - [x] Mobile hamburger menu (responsive)
- [x] **Cookie-Based Auth:**
  - [x] Create `get_current_user_from_cookie` dependency
  - [ ] ⏳ Migrate to httpOnly cookies (currently JS-accessible)
  - [ ] ⏳ Add CSRF protection middleware
- [x] **Web Router:**
  - [x] Create `backend/app/api/web.py`
  - [x] All page routes implemented

---

### Phase 3B: Core Pages (Days 2-4) ✅ COMPLETE

> **Status:** ✅ Complete (2026-01-03) - Implemented alongside 3A

- [x] **Gallery Page (`home.html`):**
  - [x] CSS columns masonry layout
  - [x] Fetch recent images from API
  - [x] Thumbnail cards with hover effect
  - [x] "Load More" button (HTMX)
  - [x] `partials/gallery_item.html` for HTMX swap
- [x] **Image Detail Page (`image.html`):**
  - [x] Dark background with glassmorphism card
  - [x] Full-size image display
  - [x] Metadata panel (filename, size, dimensions, date)
  - [x] "Copy Link" button (JS clipboard)
  - [x] "Download" button
  - [x] Delete button (owner only, HTMX confirm)
- [x] **Upload Form (`upload.html`):**
  - [x] File input with drag-and-drop zone
  - [x] File preview before upload
  - [x] Client-side validation (type, size)
  - [x] JS form submission (fetch API)
  - [x] Progress indicator
  - [x] Redirect to detail on success

---

### Phase 3C: Auth + Dashboard (Days 4-5) ✅ COMPLETE

> **Status:** ✅ Complete (2026-01-03) - Implemented alongside 3A

- [x] **Login Page (`login.html`):**
  - [x] Email + password form
  - [x] JS form submission (fetch API)
  - [x] Inline error display
  - [x] Link to registration
  - [x] Set JWT cookie on success
- [x] **Register Page (`register.html`):**
  - [x] Email + password form
  - [x] Client-side password validation
  - [x] JS form submission (fetch API)
  - [x] Auto-login on success
- [x] **Logout:**
  - [x] Clear JWT cookie
  - [x] Redirect to home
- [x] **My Images Page (`my_images.html`):**
  - [x] Profile header (email, image count)
  - [x] Filtered gallery grid (user's images only)
  - [x] Delete button on each card
  - [x] JS delete with confirmation modal
- [x] **Anonymous Upload Flow:**
  - [x] Warning message about saving token (in upload form)
  - [ ] ⏳ Display delete token prominently after upload
  - [ ] ⏳ Copy token button

---

### Phase 3D: Polish (Day 6)

> **Status:** 🟡 Partially Complete

- [x] **Responsive Design:**
  - [x] Mobile breakpoints (< 640px) - CSS columns
  - [x] Tablet breakpoints (640-1024px) - CSS columns
  - [ ] Test all pages on mobile/tablet/desktop
- [x] **Error Handling:**
  - [x] Inline error messages in forms
  - [x] 404 page template
  - [ ] ⏳ `partials/toast.html` for global messages
  - [ ] ⏳ HTMX error event handling
  - [ ] ⏳ JWT expiry → redirect to login
- [x] **Accessibility:**
  - [x] Alt text on all images (filename)
  - [x] Form labels
  - [ ] ⏳ Keyboard navigation audit
  - [ ] ⏳ Focus states audit
- [ ] **Testing:**
  - [ ] Template route tests
  - [ ] Auth flow tests (cookie-based)
  - [ ] HTMX interaction tests
  - [ ] Responsive layout verification

---

### Phase 3 Summary

All core UI features implemented:
- ✅ Gallery with masonry layout and "Load More" pagination
- ✅ Image detail page with metadata and actions
- ✅ Login/Register forms with inline validation
- ✅ My Images dashboard with delete functionality
- ✅ Upload form with drag-and-drop, preview, progress
- ✅ Responsive navigation with mobile hamburger menu
- ✅ Cookie-based JWT authentication

**Deferred to future:**
- ⏳ httpOnly cookies (currently JS-accessible)
- ⏳ CSRF protection middleware
- ⏳ Toast notifications
- ⏳ Keyboard navigation audit

**Requirements:** [docs/requirements/phase3.md](./docs/requirements/phase3.md)
**ADR:** [ADR-0013: Web UI with HTMX](docs/adr/0013-web-ui-htmx.md)

---

## ✅ Phase 3.5 - Supabase Auth Integration (COMPLETE)

**Goal:** Replace local JWT auth with Supabase Auth for production-ready authentication
**Status:** ✅ Complete - Deployed 2026-01-07
**Branch:** `main` (merged from PRs #31-34)
**Tests:** 255 passing

> **Architecture Decision:** Pluggable auth provider pattern allows switching between local JWT and Supabase without code changes.

**Why This Matters:**
- Production-ready auth (Supabase handles password reset, email verification)
- Social login ready (OAuth providers)
- Simpler deployment (no JWT secret management)

### Implementation
- [x] **Pluggable Auth Provider:**
  - [x] Create `app/services/auth/` package with provider abstraction
  - [x] `AuthProvider` abstract base class with `verify_token()`, `login()`, `register()`
  - [x] `LocalAuthProvider` - existing JWT auth (for tests)
  - [x] `SupabaseAuthProvider` - Supabase client integration
  - [x] `create_auth_provider()` factory function
  - [x] Configuration via `AUTH_PROVIDER` env var (local|supabase)
- [x] **Supabase Integration:**
  - [x] Add `supabase` dependency to pyproject.toml
  - [x] Create Supabase project (chitram.supabase.co)
  - [x] Configure `SUPABASE_URL` and `SUPABASE_ANON_KEY` in .env
  - [x] Verify tokens using Supabase JWT verification
  - [x] Create users in local DB on first Supabase login
- [x] **Web UI Cookie Auth Fix (PR #36):**
  - [x] Update `get_current_user_from_cookie()` to use pluggable provider
  - [x] Fix nav bar showing "Login" after Supabase login
  - [x] Incident retrospective documented
- [x] **Security Fix (PR #38):**
  - [x] Enforce FR-4.1 "unlisted model" - home shows only user's images
  - [x] Anonymous users redirected to login
  - [x] Direct URL access still works for any image
- [x] **Testing:**
  - [x] Unit tests for both auth providers (67 tests)
  - [x] Integration tests with mock Supabase responses
  - [x] E2E browser tests for auth flow
  - [x] All 255 tests passing
- [x] **Documentation:**
  - [x] Supabase integration learnings (`docs/learning/supabase-integration-learnings.md`)
  - [x] Incident retrospective (`docs/retrospectives/2026-01-08-supabase-nav-auth-bug.md`)
  - [x] Post-deploy checklist (`docs/deployment/POST_DEPLOY_CHECKLIST.md`)
  - [x] Auth provider pattern in CLAUDE.md

### Key Pattern: Pluggable Auth Provider

**CRITICAL:** Always use `create_auth_provider()` for token verification:

```python
# CORRECT - Works with both local and Supabase
from app.services.auth import create_auth_provider
provider = create_auth_provider(db=db, settings=settings)
result = await provider.verify_token(token)

# WRONG - Only works with local JWT
from app.services.auth_service import AuthService
auth_service = AuthService(db)
user_id = auth_service.verify_token(token)  # Fails for Supabase!
```

**Related PRs:**
- [PR #31](https://github.com/abhi10/chitram/pull/31) - Pluggable auth provider infrastructure
- [PR #32](https://github.com/abhi10/chitram/pull/32) - Supabase provider implementation
- [PR #33](https://github.com/abhi10/chitram/pull/33) - Web UI integration
- [PR #34](https://github.com/abhi10/chitram/pull/34) - Bug fixes and deployment
- [PR #36](https://github.com/abhi10/chitram/pull/36) - Nav auth state fix
- [PR #38](https://github.com/abhi10/chitram/pull/38) - FR-4.1 security fix

---

## 🔧 Phase 4 - Advanced Features (FUTURE)

**Goal:** Add advanced backend features deferred from earlier phases
**Status:** ⏸️ Not started
**Branch:** `feature/phase-4`
**Prerequisites:** Phase 3 complete

> **Note:** Features moved here from Phase 2B/2C to keep earlier phases lean.

### Celery + Redis for Background Jobs (ADR-0012)
- [ ] **Infrastructure:**
  - [ ] Add Celery to docker-compose.yml
  - [ ] Configure Redis as message broker
  - [ ] Celery worker process
  - [ ] Flower for job monitoring (optional)
- [ ] **Multiple Thumbnail Sizes:**
  - [ ] Generate 3 sizes: 150px, 300px, 600px
  - [ ] Store all thumbnails in same storage backend
  - [ ] Update API to return all thumbnail URLs
- [ ] **Retry with Exponential Backoff:**
  - [ ] Configure retry policy for failed tasks
  - [ ] Dead letter queue for permanent failures

### Checksum Calculation (SHA-256)
- [ ] **Implementation:**
  - [ ] Calculate SHA-256 hash during upload
  - [ ] Store hash in database
  - [ ] API endpoint to verify file integrity
- [ ] **Use Cases:**
  - [ ] Detect corrupted uploads
  - [ ] Cache validation
  - [ ] Deduplication foundation

### Image Deduplication
- [ ] **Hash-based Deduplication:**
  - [ ] Check if identical image already exists (by hash)
  - [ ] Return existing image instead of re-storing
  - [ ] Track reference count for shared storage
- [ ] **Perceptual Hashing (Optional):**
  - [ ] Detect visually similar images
  - [ ] Use imagededup library
  - [ ] Near-duplicate detection

### User Features
- [ ] `GET /api/v1/users/me/images` - List user's images (paginated)
- [ ] User quota management (storage limits)
- [ ] Image sharing/visibility controls

### Testing
- [ ] Celery task tests
- [ ] Checksum verification tests
- [ ] Deduplication tests

### Validation & Merge
- [ ] All tests passing
- [ ] Celery jobs processing correctly
- [ ] Merge to main, tag `v0.4.0`

**Reference:** [ADR-0012](docs/adr/0012-background-jobs-celery.md) (Phase 4 section)

---

## 🚀 Phase 5 - Distributed Cache (FUTURE)

**Goal:** Learn distributed systems through hands-on cache implementation
**Status:** ⏸️ Not started
**Branch:** `feature/phase-5-distributed-cache`
**Prerequisites:** Phase 4 complete (or can be done independently)

> **Learning Focus:** Implement distributed cache with consistent hashing.
> This is the core distributed systems building block from the AOSA paper.
> See: https://aosabook.org/en/v2/distsys.html (Caches section)

### Why Distributed Cache?
- **Current state:** Single Redis instance (local cache)
- **Target state:** Data partitioned across multiple Redis nodes
- **Learning outcome:** Understand consistent hashing, data partitioning, node failure handling

### Implementation Checklist

#### Phase 5A: Client-Side Consistent Hashing
- [ ] **Create feature branch** - `git checkout -b feature/phase-5-distributed-cache`
- [ ] **Algorithm Implementation:**
  - [ ] Implement consistent hashing ring in `app/services/hash_ring.py`
  - [ ] Use MD5 or SHA-256 for key hashing
  - [ ] Support virtual nodes (150 per physical node)
  - [ ] Add/remove nodes with minimal key redistribution
- [ ] **Distributed Cache Service:**
  - [ ] Create `app/services/distributed_cache_service.py`
  - [ ] Replace single Redis connection with node pool
  - [ ] Route keys to correct node using hash ring
  - [ ] Graceful degradation when node unavailable
- [ ] **Configuration:**
  - [ ] `REDIS_NODES` env var (comma-separated host:port)
  - [ ] `CACHE_VIRTUAL_NODES` (default: 150)
  - [ ] Backward compatible with single Redis
- [ ] **Testing:**
  - [ ] Unit tests for hash ring (key distribution, node addition/removal)
  - [ ] Integration tests with 3 Redis instances in docker-compose
  - [ ] Verify key distribution is balanced (~33% per node)

#### Phase 5B: Node Failure Handling
- [ ] **Health Monitoring:**
  - [ ] Periodic health check for each Redis node
  - [ ] Mark unhealthy nodes as down in hash ring
  - [ ] Automatic failover to next node on ring
- [ ] **Metrics:**
  - [ ] Cache hit/miss rate per node
  - [ ] Key distribution visualization (optional)
- [ ] **Documentation:**
  - [ ] ADR for distributed cache design
  - [ ] Learnings document

### Descoped (Deferred to Later)
The following items were removed from MVP scope:

| Item | Reason |
|------|--------|
| ~~Storage Sharding~~ | Overkill for image hosting scale |
| ~~Database Replication~~ | Single PostgreSQL sufficient for now |
| ~~Load Balancer (Nginx)~~ | Caddy already handles this in production |
| ~~Redis Sentinel/Cluster~~ | Client-side hashing is simpler to learn |
| ~~CDN Integration~~ | Can add later without code changes |

**Reference:** `docs/architecture/BUILDING_BLOCKS.md`

---

## 📊 Phase 6 - Basic Observability (FUTURE)

**Goal:** Add metrics to visualize cache behavior and API performance
**Status:** ⏸️ Not started
**Branch:** `feature/phase-6-observability`
**Prerequisites:** Phase 5 complete (or can be done independently)

> **Learning Focus:** Understand application metrics and visualization.
> Essential for validating distributed cache performance.

### Why Observability Now?
- **Distributed Cache needs metrics:** Can't verify key distribution without visibility
- **API performance baseline:** Understand latency before/after changes
- **Simple to add:** `prometheus-fastapi-instrumentator` is plug-and-play

### Implementation Checklist

#### Phase 6A: Prometheus Metrics
- [ ] **Create feature branch** - `git checkout -b feature/phase-6-observability`
- [ ] **Add Instrumentation:**
  - [ ] Add `prometheus-fastapi-instrumentator` dependency
  - [ ] Enable `/metrics` endpoint
  - [ ] Auto-instrumented: request count, latency, status codes
- [ ] **Custom Metrics:**
  - [ ] Cache hit/miss counter (per node if distributed)
  - [ ] Upload size histogram
  - [ ] Concurrent uploads gauge
- [ ] **Configuration:**
  - [ ] `METRICS_ENABLED` env var (default: true)
  - [ ] `/metrics` endpoint (Prometheus format)

#### Phase 6B: Grafana Dashboard (Optional)
- [ ] **Local Development:**
  - [ ] Add Grafana to docker-compose.yml
  - [ ] Pre-configured dashboard JSON
  - [ ] Visualize: request rate, latency p50/p95/p99, cache hit rate
- [ ] **Production:**
  - [ ] Grafana Cloud free tier (or self-hosted)
  - [ ] Alert on high error rate (>1%)

### Descoped (Deferred to Later)
The following items were removed from MVP scope:

| Item | Reason |
|------|--------|
| ~~Distributed Tracing (Jaeger)~~ | Overkill for single-service architecture |
| ~~Circuit Breakers~~ | Already have graceful degradation |
| ~~Loki/ELK Logging Stack~~ | Docker logs sufficient for now |
| ~~PagerDuty/Slack Alerting~~ | Can add when needed |

**Reference:** `docs/architecture/BUILDING_BLOCKS.md`

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
- **Runbook:** `docs/CODESPACES_RUNBOOK.md` - Dev Container testing guide
- **Retrospectives:** `docs/PHASE2_RETRO.md` - Phase 2 learnings
- **Code Review:** `docs/code-review-checklist.md`
- **Requirements:**
  - `docs/requirements/phase1.md` - Phase 1 requirements
  - `docs/requirements/phase2.md` - Phase 2 requirements (EARS format)
  - `docs/requirements/phase3.md` - Phase 3 UI requirements (EARS format)
- **ADRs:** `docs/adr/` (13 decisions documented)
- **CI/CD:** `.github/workflows/ci.yml` - GitHub Actions pipeline

### Archived Documents
- **Archive:** `docs/archive/` - Historical docs preserved for reference
  - Original 2200-line MVP design doc
  - Phase execution plan
  - One-time code reviews

### Key ADRs
- **ADR-0013:** Web UI with HTMX (Phase 3)
- **ADR-0012:** Background Tasks Strategy (FastAPI BackgroundTasks → Celery in Phase 4)
- **ADR-0011:** User Authentication with JWT (implemented)
- **ADR-0010:** Concurrency control for uploads (asyncio.Semaphore)
- **ADR-0009:** Redis caching for metadata (Cache-Aside pattern)
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

**Current State:** Phase 3.5 Complete - Production deployed at https://chitram.io

**Recently Completed:**
- ✅ Supabase Auth Integration (Phase 3.5)
- ✅ FR-4.1 Security Fix - Private galleries
- ✅ Web UI with HTMX (Phase 3)
- ✅ CD Pipeline with GitHub Actions
- ✅ Production deployment on DigitalOcean
- ✅ Descoped Phase 5/6 for MVP focus

**Up Next (Phase 5 - Distributed Cache):**
- [ ] Implement consistent hashing ring algorithm
- [ ] Create distributed cache service with multi-node support
- [ ] Add integration tests with 3 Redis instances

> **Note:** Phase 5 can be done independently of Phase 4. Phase 4 (Celery, Dedup) is optional and can be skipped.

**Production Status:**
- 🌐 Live at: https://chitram.io
- 🔒 Auth: Supabase (production) / Local JWT (tests)
- 📊 Tests: 255 passing
- 🚀 CD: Auto-deploy on merge to main

---

## 📊 Progress Summary

```
Phase Roadmap:

Phase 1 Lean    ✅ Complete (Validated 2025-12-24)
Phase 1.5       ✅ Complete (Merged 2025-12-31)
Phase 2A Auth   ✅ Complete (151 tests, 2026-01-03)
Phase 2B        ✅ Complete (188 tests, 2026-01-03)
Phase 3         ✅ Complete (Web UI deployed 2026-01-04)
Phase 3.5       ✅ Complete (Supabase Auth, 255 tests, 2026-01-08)
Phase 4         ⏸️ Future - Advanced Features (Celery, Dedup) [Optional]
Phase 5         ⏸️ Future - Distributed Cache (Consistent Hashing) ← Next
Phase 6         ⏸️ Future - Basic Observability (Prometheus)
```

**Current Status:** 🟢 Production deployed
**Production URL:** https://chitram.io
**Blockers:** None
**Last Updated:** 2026-01-08

---

## 🎉 Milestones

- [x] **2025-12-13:** Project initialized, ADRs created
- [x] **2025-12-19:** Phase 1 Lean scaffolding complete
- [x] **2025-12-20:** Code review (99% score), pushed to GitHub
- [x] **2025-12-24:** Phase 1 Lean validation complete (see `docs/PHASE1_TESTING.md`)
- [x] **2025-12-24:** Docs cleanup - reorganized into architecture/, learning/, testing/, archive/
- [x] **2025-12-31:** Phase 1.5 complete - Alembic migrations + Pillow image dimensions
- [x] **2025-12-31:** Phase 2 MinIO backend merged to main (PR #4)
- [x] **2026-01-01:** Phase 2 MinIO validated in Codespaces (31 tests passing)
- [x] **2026-01-01:** GitHub Actions CI pipeline added
- [x] **2026-01-01:** Phase 2 Retrospective documented (6 issues, 4 blockers resolved)
- [x] **2026-01-02:** Phase 2 Redis caching complete (ADR-0009, 43+ tests passing)
- [x] **2026-01-02:** Phase 2 Rate limiting complete (83 tests passing)
- [x] **2026-01-02:** Phase 2 Concurrency control complete (ADR-0010, 99 tests passing)
- [x] **2026-01-02:** Phase 2 Technical debt fixes complete (114 tests passing)
- [x] **2026-01-03:** Phase 2A Auth complete (ADR-0011, 151 tests passing)
- [x] **2026-01-03:** Phase restructuring - Phase 3 (UI), Phase 4 (Advanced), Phase 5 (Scaling), Phase 6 (Observability)
- [x] **2026-01-03:** Phase 2B Thumbnails complete (FastAPI BackgroundTasks, 37 new tests, 188 total)
- [x] **2026-01-04:** Phase 3 Web UI complete (HTMX + Jinja2 templates)
- [x] **2026-01-04:** 🚀 First production deployment to DigitalOcean (https://chitram.io)
- [x] **2026-01-05:** CD pipeline implemented (auto-deploy on merge to main)
- [x] **2026-01-07:** Phase 3.5 Supabase Auth integrated (PRs #31-34)
- [x] **2026-01-08:** Nav auth state bug fixed (PR #36) - Incident retrospective created
- [x] **2026-01-08:** FR-4.1 security fix - Private galleries (PR #38)
- [x] **2026-01-08:** Post-deploy checklist and auth retro action items (PR #39)
- [x] **2026-01-08:** Descoped Phase 5/6 for MVP focus (removed over-engineering)
- [ ] **Future:** Phase 5 Distributed Cache (Consistent Hashing) ← Learning focus
- [ ] **Future:** Phase 6 Basic Observability (Prometheus)
- [ ] **Optional:** Phase 4 Advanced Features (Celery, Dedup)
- [ ] **Target:** v1.0.0 production-ready system

---

**Repository:** https://github.com/abhi10/chitram
**Project Name:** Chitram (చిత్రం - Image/Picture in Telugu)
**Author:** @abhi10
**License:** (To be added)
