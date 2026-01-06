# Architecture Decision: Browser Tests Location and Docker

**Date:** 2026-01-05
**Status:** Decided
**Context:** Where should browser tests live and should Dockerfile be updated?

---

## Decision

### 1. Browser Tests Location: Root Level ✅

**Decided:** Keep `browser-tests/` at project root (not inside `backend/tests/`)

**Directory Structure:**
```
image-hosting-app/
├── backend/
│   ├── app/              # Application code
│   ├── tests/            # Python pytest tests (unit, api, integration)
│   │   ├── unit/         # Test individual functions/classes
│   │   ├── api/          # Test FastAPI endpoints
│   │   └── integration/  # Test with real DB/storage
│   └── Dockerfile        # Production image (Python only)
│
├── browser-tests/        # E2E tests (separate runtime)
│   ├── src/              # Playwright wrapper
│   ├── tools/            # CLI test tools
│   ├── examples/         # Test suites
│   └── package.json      # Bun dependencies
│
└── .github/workflows/    # CI/CD (runs both test types)
```

### 2. Dockerfile: No Changes Needed ✅

**Decided:** Do NOT add Bun/Playwright to backend Dockerfile

**Current Dockerfile stays as-is:** Python + uv only

---

## Rationale

### Why Browser Tests at Root?

#### 1. **Different Testing Layers**

| Test Type | Location | Purpose | Runtime | Scope |
|-----------|----------|---------|---------|-------|
| **Unit Tests** | `backend/tests/unit/` | Test functions/classes | Python/pytest | Code-level |
| **API Tests** | `backend/tests/api/` | Test endpoints | Python/pytest | Backend-only |
| **Integration Tests** | `backend/tests/integration/` | Test with DB/storage | Python/pytest | Backend + services |
| **E2E Tests** | `browser-tests/` | Test like a user | Bun/Playwright | Full stack |

#### 2. **Separation of Runtimes**

```
backend/tests/          browser-tests/
├── Python 3.12         ├── Bun 1.x
├── pytest              ├── Playwright
├── pytest-asyncio      ├── TypeScript
└── httpx               └── Chromium browser
```

**Mixing these in one directory would be confusing.**

#### 3. **Different Execution Models**

**Backend tests (inside):**
```bash
# Run from backend directory
cd backend
uv run pytest tests/

# Tests import app code directly
from app.main import app
from app.services.image_service import ImageService
```

**Browser tests (outside):**
```bash
# Run from browser-tests directory
cd browser-tests
bun run examples/smoke-test.ts

# Tests connect via HTTP (no imports)
await browser.navigate('http://localhost:8000')
```

#### 4. **Production Testing**

Browser tests can test production **without backend code:**

```bash
# Test production deployment
bun run examples/smoke-test.ts https://chitram.io

# No backend code needed!
# Tests via HTTP only
```

**Backend tests cannot do this** - they need source code.

#### 5. **Future Frontend**

When adding a frontend:

```
image-hosting-app/
├── backend/          # FastAPI backend
├── frontend/         # React/Vue frontend
├── browser-tests/    # Tests BOTH ✅
└── .github/
```

Browser tests validate:
- ✅ Backend API endpoints
- ✅ Frontend UI rendering
- ✅ Frontend ↔ Backend integration
- ✅ Full user workflows

#### 6. **Industry Standard**

Popular projects with this structure:

- **Next.js** - `/e2e/` at root
- **RedwoodJS** - `/e2e/` at root
- **Nx monorepos** - `/e2e/` at root
- **Playwright examples** - Separate from app code

---

### Why NOT Update Dockerfile?

#### 1. **Browser Tests Run Outside Container**

**The Testing Model:**

```
┌─────────────────────────────┐
│   GitHub Actions Runner     │
│   (or Local Machine)        │
│                             │
│   ┌─────────────────────┐   │
│   │  browser-tests/     │   │
│   │  (Bun + Playwright) │   │
│   └──────────┬──────────┘   │
│              │              │
│              │ HTTP         │
│              ↓              │
│   ┌─────────────────────┐   │
│   │   Docker Container  │   │
│   │                     │   │
│   │   FastAPI App       │   │
│   │   (Python only)     │   │
│   └─────────────────────┘   │
└─────────────────────────────┘
```

**Tests connect via HTTP** - no need for test tools inside Docker.

#### 2. **Image Size Impact**

```dockerfile
# Current: 150MB (Python + app)
FROM python:3.12-slim
COPY app/ ./app/

# If we added Bun + Playwright: 450-500MB!
FROM python:3.12-slim
RUN apt-get install nodejs npm  # +80MB
RUN npm install -g bun          # +50MB
RUN bunx playwright install     # +250MB for browsers!
COPY app/ ./app/
```

**Production images should be lean.**

#### 3. **Separation of Concerns**

```
Production Dockerfile:
└─ Runs the app (Python + FastAPI)
   - No test tools
   - No dev dependencies
   - Minimal attack surface

Test Environment (GitHub Actions):
└─ Runs the tests (Bun + Playwright)
   - Installs test tools
   - Runs against Docker container
   - Discarded after tests
```

#### 4. **Security**

**Smaller image = Smaller attack surface:**
- Fewer packages
- Fewer CVEs to patch
- Faster security scans

#### 5. **GitHub Actions Handles It**

Our workflow already sets up both:

```yaml
# .github/workflows/ui-tests.yml

- name: Setup Python + uv    # ← For backend
  uses: actions/setup-python@v5

- name: Start backend         # ← Run in background
  run: uv run uvicorn app.main:app &

- name: Setup Bun             # ← For tests (separate)
  uses: oven-sh/setup-bun@v1

- name: Install Playwright    # ← For tests (separate)
  run: bunx playwright install chromium

- name: Run tests             # ← Tests connect via HTTP
  run: bun run examples/smoke-test.ts http://localhost:8000
```

**Perfect separation!**

---

## Alternative Approaches Considered

### ❌ Alternative 1: Move to `backend/tests/browser/`

**Rejected because:**
- Mixes Python and Bun/Node tooling
- Confusing for developers ("Is this pytest or Playwright?")
- Different execution context (inside vs outside)
- Can't test production without backend code
- Harder to add frontend later

### ❌ Alternative 2: Add Bun to Dockerfile

**Rejected because:**
- Bloats production image (+300MB)
- Mixes app runtime with test runtime
- Security risk (more packages = more CVEs)
- Slower builds and deployments
- Unnecessary (tests run outside container)

### ❌ Alternative 3: Separate `browser-tests.Dockerfile`

**Rejected because:**
- Overkill - GitHub Actions already handles setup
- More files to maintain
- Adds complexity without benefit
- Tests don't need reproducible container (they test via HTTP)

---

## Consequences

### Positive

✅ **Clear separation:** Unit tests (inside) vs E2E tests (outside)
✅ **Lean production:** Docker image stays small and secure
✅ **Flexible testing:** Can test any deployment (local, staging, prod)
✅ **Future-proof:** Easy to add frontend without restructuring
✅ **Standard pattern:** Follows industry best practices
✅ **Fast CI/CD:** Parallel test execution, efficient caching

### Neutral

⚠️ **Two test locations:** Developers need to know both exist
⚠️ **Two runtimes:** Python (backend) and Bun (browser tests)

**Mitigation:** Clear documentation (this file + README)

### Negative

None identified.

---

## Implementation

### Current State ✅

```
image-hosting-app/
├── backend/
│   ├── tests/                    # Python tests
│   │   ├── unit/
│   │   ├── api/
│   │   └── integration/
│   └── Dockerfile                # Python only
├── browser-tests/                # E2E tests
│   ├── src/
│   ├── tools/
│   └── examples/
└── .github/workflows/
    ├── ci.yml                    # Backend tests (pytest)
    ├── ui-tests.yml              # Browser tests (Playwright)
    └── post-deployment-tests.yml # Production verification
```

**No changes needed!** ✅

### Testing Workflow

**Development:**
```bash
# Backend tests (inside code)
cd backend
uv run pytest tests/

# Browser tests (outside via HTTP)
cd browser-tests
bun run examples/smoke-test.ts http://localhost:8000
```

**CI/CD (GitHub Actions):**
```yaml
# Both run automatically
1. Backend tests → pytest
2. Start backend → Docker or uv
3. Browser tests → Playwright (via HTTP)
4. Both must pass → Merge allowed
```

**Production:**
```bash
# Verify deployed app
bun run examples/smoke-test.ts https://chitram.io
```

---

## References

### Industry Examples

1. **Playwright Documentation**
   - Recommends E2E tests separate from app code
   - https://playwright.dev/docs/intro

2. **Next.js Best Practices**
   - Uses `/e2e/` at root for Playwright tests
   - https://nextjs.org/docs/app/building-your-application/testing/playwright

3. **Test Pyramid**
   - Unit tests (many, fast, inside code)
   - Integration tests (some, medium, with services)
   - E2E tests (few, slow, via UI/HTTP)

4. **Martin Fowler on Microservice Testing**
   - E2E tests should be deployment-independent
   - https://martinfowler.com/articles/microservice-testing/

### Related ADRs

- ADR-0014: Test Dependency Container (backend/tests)
- (This document): Browser tests location and Docker

---

## Review Schedule

**Next review:** After adding frontend (Phase 4)

**Trigger for re-evaluation:**
- Adding a frontend framework
- Moving to microservices architecture
- Switching from Docker to serverless

---

**Decision stands:** Current architecture is optimal for this project. ✅
