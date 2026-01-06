# Browser Test Overview

**Purpose:** Understanding the browser testing architecture and how it differs from backend tests

**Date:** 2026-01-05
**Status:** Active

---

## Quick Summary

Our project has **two separate test suites** that work together:

| Test Suite | Location | Runtime | Purpose |
|------------|----------|---------|---------|
| **Backend Tests** | `backend/tests/` | Python + pytest | Test code internally |
| **Browser Tests** | `browser-tests/` | Bun + Playwright | Test like a user |

**Key insight:** They test at different levels and should **stay separate**.

---

## The Testing Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │ ← browser-tests/ (Few, Slow, High Confidence)
                    │  (Playwright)   │    Tests: User workflows
                    └─────────────────┘
                           ▲
                           │ Via HTTP
                           │
                    ┌─────────────────┐
                    │  Integration    │ ← backend/tests/integration/
                    │    Tests        │    Tests: Components together
                    └─────────────────┘
                           ▲
                           │ With real DB
                           │
               ┌───────────────────────┐
               │     API Tests         │ ← backend/tests/api/
               └───────────────────────┘    Tests: HTTP endpoints
                           ▲
                           │ Direct calls
                           │
       ┌───────────────────────────────────┐
       │         Unit Tests                │ ← backend/tests/unit/
       └───────────────────────────────────┘    Tests: Functions/classes
```

**Rule of thumb:**
- **Many** unit tests (fast, focused)
- **Some** integration tests (medium speed)
- **Few** E2E tests (slow, comprehensive)

---

## Why Two Test Suites?

### Backend Tests (`backend/tests/`) - Inside View

**What they test:** Code behavior from within

```python
# backend/tests/unit/test_validation.py
from app.utils.validation import validate_image_type

def test_validate_jpeg():
    # Direct function call
    result = validate_image_type(b'\xff\xd8\xff')
    assert result == "image/jpeg"
```

**Characteristics:**
- ⚡ **Very fast** (0.01-2s per test)
- 🎯 **Precise** (test specific functions)
- 📦 **Isolated** (minimal dependencies)
- 🐍 **Python runtime** (imports backend code)

**When to use:**
- Testing business logic
- Testing validation rules
- Testing database queries
- Testing API endpoints

---

### Browser Tests (`browser-tests/`) - Outside View

**What they test:** User experience from outside

```typescript
// browser-tests/examples/smoke-test.ts
await browser.navigate('https://chitram.io')
await browser.waitForSelector('.masonry-grid')
await browser.click('a[href="/login"]')
await browser.fill('input[type="email"]', 'user@example.com')
await browser.click('button[type="submit"]')
```

**Characteristics:**
- 🐢 **Slower** (2-10s per test)
- 🌐 **Comprehensive** (full user journey)
- 🖥️ **Real browser** (Chromium rendering)
- 🦝 **Bun runtime** (no backend imports)

**When to use:**
- Testing user workflows
- Testing UI interactions
- Verifying production deployments
- Testing frontend + backend integration

---

## Visual: How They Work Differently

### Backend Tests (Direct Access)

```
┌─────────────────────────────────┐
│       Backend Codebase          │
│                                 │
│   ┌─────────────────────┐       │
│   │  app/main.py        │       │
│   │  app/services/      │       │
│   └─────────────────────┘       │
│            ▲                    │
│            │ Direct imports     │
│            │                    │
│   ┌─────────────────────┐       │
│   │  tests/unit/        │       │
│   │  tests/api/         │       │
│   │  tests/integration/ │       │
│   └─────────────────────┘       │
│                                 │
└─────────────────────────────────┘

# Example
from app.services.image_service import ImageService
service = ImageService()
result = service.upload(...)
```

### Browser Tests (HTTP Access)

```
┌─────────────────────────────────┐
│      browser-tests/             │
│                                 │
│   ┌─────────────────────┐       │
│   │  Playwright         │       │
│   │  Browser            │       │
│   └──────────┬──────────┘       │
│              │                  │
└──────────────┼──────────────────┘
               │
               │ HTTP Requests
               │ (like a user)
               ▼
┌─────────────────────────────────┐
│    Running Application          │
│                                 │
│   http://localhost:8000         │
│   or                            │
│   https://chitram.io            │
│                                 │
└─────────────────────────────────┘

# Example
await browser.navigate('http://localhost:8000')
await browser.click('.upload-button')
// No imports, just HTTP
```

---

## Directory Structure

### Current Architecture (Correct ✅)

```
image-hosting-app/
│
├── backend/
│   ├── app/                    # Application code
│   │   ├── main.py
│   │   ├── services/
│   │   └── models/
│   │
│   ├── tests/                  # Python tests (INSIDE)
│   │   ├── conftest.py         # Pytest fixtures
│   │   ├── unit/               # Test functions/classes
│   │   ├── api/                # Test HTTP endpoints
│   │   └── integration/        # Test with DB/storage
│   │
│   ├── pyproject.toml          # Python dependencies
│   └── Dockerfile              # Production image (Python only)
│
├── browser-tests/              # E2E tests (OUTSIDE)
│   ├── src/
│   │   └── browser.ts          # Playwright wrapper
│   ├── tools/
│   │   └── gallery-test.ts     # CLI test tools
│   ├── examples/
│   │   ├── smoke-test.ts       # Quick health check
│   │   └── comprehensive-test.ts
│   ├── workflows/
│   │   ├── auth-flow.md        # Test scenarios
│   │   └── gallery-flow.md
│   └── package.json            # Bun dependencies
│
└── .github/workflows/
    ├── ci.yml                  # Backend tests (pytest)
    └── ui-tests.yml            # Browser tests (Playwright)
```

---

## Why NOT Combine Them?

### ❌ Bad: Everything in backend/tests/

```
backend/
└── tests/
    ├── unit/              ← Python/pytest
    ├── api/               ← Python/pytest
    ├── integration/       ← Python/pytest
    └── browser/           ← Bun/Playwright?! 🤔
        └── package.json
```

**Problems:**
1. **Confusing:** Mixing Python and Node/Bun tooling
2. **Wrong abstraction:** Browser tests don't need backend code
3. **Can't test production:** Browser tests need HTTP access, not imports
4. **Future limitations:** When you add a frontend, browser tests should test BOTH

---

### ✅ Good: Separation by Abstraction Level

```
backend/tests/          ← Tests backend code (inside)
browser-tests/          ← Tests user experience (outside)
```

**Benefits:**
- Clear separation of concerns
- Appropriate runtimes in appropriate places
- Can test production independently
- Ready for future frontend addition

---

## Real-World Example

Let's test an image upload feature at all levels:

### Level 1: Unit Test

```python
# backend/tests/unit/test_validation.py
def test_validate_jpeg_signature():
    """Test JPEG magic bytes validation"""
    jpeg_bytes = b'\xff\xd8\xff\xe0'
    assert validate_image_type(jpeg_bytes) == "image/jpeg"
```

**Tests:** Does the validation function work?
**Speed:** 0.01s
**Coverage:** One function

---

### Level 2: API Test

```python
# backend/tests/api/test_images.py
async def test_upload_endpoint(client):
    """Test upload endpoint accepts valid image"""
    response = await client.post(
        "/api/v1/images/upload",
        files={"file": ("test.jpg", jpeg_bytes, "image/jpeg")}
    )
    assert response.status_code == 201
    assert response.json()["filename"] == "test.jpg"
```

**Tests:** Does the endpoint work?
**Speed:** 0.1s
**Coverage:** Endpoint + validation + response

---

### Level 3: Integration Test

```python
# backend/tests/integration/test_upload_flow.py
async def test_full_upload_integration(db, storage):
    """Test upload saves to both DB and storage"""
    # Upload
    response = await client.post("/api/v1/images/upload", ...)
    image_id = response.json()["id"]

    # Verify DB
    image = await db.get(Image, image_id)
    assert image.filename == "test.jpg"

    # Verify storage
    assert await storage.exists(image.storage_key)
```

**Tests:** Do all components work together?
**Speed:** 1s
**Coverage:** Endpoint + DB + Storage

---

### Level 4: E2E Test

```typescript
// browser-tests/workflows/upload-flow.ts
test('User can upload image', async () => {
  // Login
  await browser.navigate('http://localhost:8000/login')
  await browser.fill('input[type="email"]', 'user@example.com')
  await browser.fill('input[type="password"]', 'password123')
  await browser.click('button[type="submit"]')

  // Upload
  await browser.click('a[href="/upload"]')
  await browser.setInputFiles('input[type="file"]', 'test-image.jpg')
  await browser.click('button[type="submit"]')

  // Verify in gallery
  await browser.navigate('http://localhost:8000/')
  await browser.waitForSelector('.masonry-grid img[alt*="test-image"]')
})
```

**Tests:** Can a real user complete the workflow?
**Speed:** 5-10s
**Coverage:** Full user journey (auth + upload + display)

---

## When Each Test Would Catch Issues

| Issue | Unit | API | Integration | E2E |
|-------|------|-----|-------------|-----|
| JPEG validation broken | ✅ | ✅ | ✅ | ✅ |
| Endpoint returns wrong status | ❌ | ✅ | ✅ | ✅ |
| Image saved to DB but not storage | ❌ | ❌ | ✅ | ✅ |
| Upload button missing from UI | ❌ | ❌ | ❌ | ✅ |
| Upload works but image doesn't show in gallery | ❌ | ❌ | ❌ | ✅ |
| Login required but redirect broken | ❌ | ❌ | ❌ | ✅ |

**Insight:** Each level catches different types of bugs!

---

## Test Execution Strategy

### Development (Local)

```bash
# 1. Run unit tests while coding (fastest feedback)
cd backend
uv run pytest tests/unit -v

# 2. Run API tests when changing endpoints
uv run pytest tests/api -v

# 3. Run integration tests before committing
uv run pytest tests/integration -v

# 4. Run browser smoke tests before pushing
cd ../browser-tests
bun run examples/smoke-test.ts
```

---

### CI/CD (GitHub Actions)

```yaml
# Both run automatically on every push/PR

Backend Pipeline:
  ✅ Unit tests (10s)
  ✅ API tests (20s)
  ✅ Integration tests (30s)

Browser Pipeline:
  ✅ Smoke tests (2s)
  ✅ Comprehensive tests (12s)

Total: ~75s
```

---

### Production Verification

```bash
# Only browser tests can test production!
bun run examples/smoke-test.ts https://chitram.io

# Backend tests can't - they need source code
cd backend
pytest tests/  # ❌ Can't test https://chitram.io
```

**Key advantage:** Browser tests verify the deployed application.

---

## Future: Adding a Frontend

When you add a React/Vue frontend:

```
image-hosting-app/
├── backend/
│   └── tests/              ← Tests backend only
│
├── frontend/               ← New React/Vue app
│   └── tests/              ← Tests frontend only
│
└── browser-tests/          ← Tests BOTH together! ✅
    └── examples/
        ├── upload-flow.ts  ← Frontend UI + Backend API
        └── gallery-flow.ts ← Full stack integration
```

**Browser tests become even more valuable** - they test the entire stack.

---

## Common Questions

### Q: Why not put everything in backend/tests/browser/?

**A:** Different abstraction levels need different locations:
- Backend tests: Test code (need imports)
- Browser tests: Test user experience (need HTTP)

Mixing them creates confusion about what's being tested.

---

### Q: Should we update the Dockerfile to include Bun/Playwright?

**A:** No! Browser tests run **outside** the Docker container.

```
[GitHub Actions: Bun + Playwright]
         │
         │ HTTP
         ↓
[Docker Container: Python + FastAPI]
```

Adding Bun to Dockerfile would:
- Bloat image from 150MB → 500MB
- Add unnecessary dependencies to production
- Violate separation of concerns

---

### Q: How do browser tests run if they're separate?

**A:** They connect via HTTP:

```typescript
// No imports needed!
await browser.navigate('http://localhost:8000')
await browser.click('.button')

// Works against any URL:
await browser.navigate('https://chitram.io')
```

This is the **key advantage** - test any deployment without needing source code.

---

### Q: Which tests should I run while developing?

**A:** Depends on what you're changing:

| Change | Run |
|--------|-----|
| Adding a function | Unit tests |
| Adding an endpoint | API tests |
| Changing DB schema | Integration tests |
| Adding a UI feature | Browser smoke tests |
| Before pushing | All tests |

---

## Analogy: Testing a Restaurant

Think of testing a restaurant:

### Unit Tests = Test Ingredients
```
Chef: "Is this tomato fresh?"
Test: Smell, feel, taste the tomato
Fast, focused, inside the kitchen
```

### API Tests = Test Individual Dishes
```
Chef: "Is the pasta cooked correctly?"
Test: Taste the pasta alone
Medium speed, focused on one dish
```

### Integration Tests = Test Complete Meal
```
Chef: "Do all dishes work together?"
Test: Full course meal (appetizer + main + dessert)
Slower, tests combinations
```

### E2E Tests = Customer Experience
```
Customer: Walk in, order, eat, pay, leave
Test: Full dining experience
Slowest, most comprehensive
```

**You need all levels** - great ingredients don't guarantee great dining experience!

---

## Key Takeaways

1. ✅ **Two test suites are correct** - backend tests (inside) and browser tests (outside)

2. ✅ **Keep them separate** - different runtimes, different abstraction levels

3. ✅ **No Dockerfile changes** - browser tests run via HTTP, not inside Docker

4. ✅ **Both are essential** - backend tests find code bugs, browser tests find UX bugs

5. ✅ **Different speeds** - run unit tests often, E2E tests before release

6. ✅ **Production testing** - only browser tests can verify deployed apps

---

## Related Documentation

- **Deep dive:** [`browser-tests/ARCHITECTURE_DECISION.md`](../../browser-tests/ARCHITECTURE_DECISION.md)
- **Test layers:** [`browser-tests/TESTING_LAYERS.md`](../../browser-tests/TESTING_LAYERS.md)
- **CI/CD setup:** [`browser-tests/CI_CD_INTEGRATION.md`](../../browser-tests/CI_CD_INTEGRATION.md)
- **Quick start:** [`browser-tests/README.md`](../../browser-tests/README.md)

---

## Next Steps

1. ✅ Understand why tests are separate
2. ✅ Run backend tests: `cd backend && uv run pytest`
3. ✅ Run browser tests: `cd browser-tests && bun run examples/smoke-test.ts`
4. ✅ See both in CI/CD: Check GitHub Actions
5. ✅ Add new tests at the appropriate level

**Remember:** Right test for the right job! 🎯
