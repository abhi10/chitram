# Testing Layers - Visual Guide

Understanding the different test types in this project.

---

## The Testing Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │ ← browser-tests/ (Few, Slow, High Value)
                    │  (Playwright)   │
                    └─────────────────┘
                           ▲
                           │ Tests via HTTP
                           │
                    ┌─────────────────┐
                    │  Integration    │ ← backend/tests/integration/ (Some, Medium)
                    │    Tests        │
                    └─────────────────┘
                           ▲
                           │ Tests with real DB
                           │
               ┌───────────────────────┐
               │     API Tests         │ ← backend/tests/api/ (More, Fast)
               └───────────────────────┘
                           ▲
                           │ Tests endpoints
                           │
       ┌───────────────────────────────────┐
       │         Unit Tests                │ ← backend/tests/unit/ (Many, Very Fast)
       └───────────────────────────────────┘
                    Tests functions
```

---

## Test Type Comparison

### 1. Unit Tests (`backend/tests/unit/`)

**What:** Test individual functions/classes in isolation

**Example:**
```python
# backend/tests/unit/test_validation.py
from app.utils.validation import validate_image_type

def test_validate_jpeg():
    # Direct function call
    result = validate_image_type(b'\xff\xd8\xff')
    assert result == "image/jpeg"
```

**Characteristics:**
- ⚡ **Very fast:** <0.01s per test
- 🎯 **Focused:** One function at a time
- 📦 **Isolated:** No DB, no HTTP, no dependencies
- 🔧 **Location:** Inside backend code
- 🐍 **Runtime:** Python + pytest

---

### 2. API Tests (`backend/tests/api/`)

**What:** Test FastAPI endpoints using test client

**Example:**
```python
# backend/tests/api/test_images.py
async def test_upload_image(client, sample_image):
    # Uses FastAPI test client (in-memory)
    response = await client.post(
        "/api/v1/images/upload",
        files={"file": sample_image}
    )
    assert response.status_code == 201
```

**Characteristics:**
- ⚡ **Fast:** ~0.1s per test
- 🎯 **Endpoint-focused:** Test HTTP handlers
- 📦 **Test DB:** Uses test database
- 🔧 **Location:** Inside backend code
- 🐍 **Runtime:** Python + pytest + httpx

---

### 3. Integration Tests (`backend/tests/integration/`)

**What:** Test multiple components working together

**Example:**
```python
# backend/tests/integration/test_upload_flow.py
async def test_full_upload_flow(db, storage, auth_client):
    # Tests: auth + upload + storage + DB
    response = await auth_client.post("/api/v1/images/upload", ...)
    assert response.status_code == 201

    # Verify in DB
    image = await db.get(Image, response.json()["id"])
    assert image.filename == "test.jpg"

    # Verify in storage
    assert await storage.exists(image.storage_key)
```

**Characteristics:**
- ⏱️ **Medium:** ~0.5-2s per test
- 🔗 **Multi-component:** Tests interactions
- 📦 **Real services:** Real DB, real storage
- 🔧 **Location:** Inside backend code
- 🐍 **Runtime:** Python + pytest

---

### 4. E2E Tests (`browser-tests/`)

**What:** Test the entire application like a real user

**Example:**
```typescript
// browser-tests/examples/smoke-test.ts
await browser.navigate('https://chitram.io')
await browser.waitForSelector('.masonry-grid')
await browser.click('a[href="/login"]')
await browser.fill('input[type="email"]', 'user@example.com')
await browser.click('button[type="submit"]')
```

**Characteristics:**
- 🐢 **Slow:** ~2-10s per test
- 🌐 **Full stack:** Tests entire user journey
- 📦 **Real browser:** Chromium rendering
- 🔧 **Location:** Outside backend (via HTTP)
- 🦝 **Runtime:** Bun + Playwright

---

## Where Tests Live

### Backend Tests (Inside)

```
backend/
├── app/
│   ├── main.py                    ← Tests import this
│   └── services/
│       └── image_service.py       ← Tests import this
│
├── tests/
│   ├── unit/
│   │   └── test_validation.py     ← from app.utils.validation import ...
│   ├── api/
│   │   └── test_images.py         ← from app.main import app
│   └── integration/
│       └── test_upload_flow.py    ← from app.services import ImageService
│
└── pyproject.toml                 ← pytest configuration
```

**Key:** Tests import and call code directly

---

### Browser Tests (Outside)

```
browser-tests/
├── src/
│   └── browser.ts                 ← Playwright wrapper
├── tools/
│   └── gallery-test.ts            ← CLI tools
└── examples/
    └── smoke-test.ts              ← await browser.navigate(url)
                                     ↓
                                   HTTP
                                     ↓
                            ┌────────────────┐
                            │  Running App   │
                            │                │
                            │  localhost:8000│
                            │  or            │
                            │  chitram.io    │
                            └────────────────┘
```

**Key:** Tests connect via HTTP, no imports

---

## When to Use Each Test Type

### Use Unit Tests When:
```
✅ Testing pure functions
✅ Testing business logic
✅ Testing validation rules
✅ Testing utilities
✅ Need very fast feedback
```

**Example:** Password hashing, image validation, URL generation

---

### Use API Tests When:
```
✅ Testing endpoints
✅ Testing request/response
✅ Testing authentication
✅ Testing error handling
✅ Need fast-ish feedback
```

**Example:** POST /upload, GET /images/{id}, auth middleware

---

### Use Integration Tests When:
```
✅ Testing DB operations
✅ Testing file storage
✅ Testing external services
✅ Testing multi-step flows
✅ Need confidence in integration
```

**Example:** Upload → Store → DB → Retrieve

---

### Use E2E Tests When:
```
✅ Testing user workflows
✅ Testing UI interactions
✅ Testing production
✅ Testing across services
✅ Need confidence for release
```

**Example:** Register → Login → Upload → View Gallery

---

## Test Execution Flow

### Development (Local)

```bash
# 1. Unit tests (fastest) - Run often
cd backend
uv run pytest tests/unit -v

# 2. API tests (fast) - Run on file save
uv run pytest tests/api -v

# 3. Integration tests (medium) - Run before commit
uv run pytest tests/integration -v

# 4. E2E tests (slow) - Run before push
cd ../browser-tests
bun run examples/smoke-test.ts
```

---

### CI/CD (GitHub Actions)

```yaml
# .github/workflows/ci.yml
Backend Tests:
  1. Unit tests        ✅ (10s)
  2. API tests         ✅ (20s)
  3. Integration tests ✅ (30s)
  ↓
  All pass → Continue

# .github/workflows/ui-tests.yml
Browser Tests:
  1. Start backend     (setup)
  2. Smoke tests       ✅ (2s)
  3. Comprehensive     ✅ (12s)
  ↓
  All pass → Deploy
```

---

## Directory Structure Decision

### ❌ Bad: Everything in backend/tests/

```
backend/
└── tests/
    ├── unit/           ← Python
    ├── api/            ← Python
    ├── integration/    ← Python
    └── browser/        ← Bun?! 🤔 CONFUSING!
        └── package.json
```

**Problems:**
- Mixes Python and Node/Bun
- Confusing for developers
- Can't test production without backend code
- Different runtime in same directory

---

### ✅ Good: Separation by Runtime

```
image-hosting-app/
├── backend/
│   └── tests/          ← All Python tests
│       ├── unit/
│       ├── api/
│       └── integration/
│
└── browser-tests/      ← All Bun/Playwright tests
    ├── tools/
    └── examples/
```

**Benefits:**
- Clear separation
- Different runtimes in different directories
- Can test production independently
- Easy to add frontend later

---

## Future: Adding Frontend

```
image-hosting-app/
├── backend/            ← FastAPI
│   └── tests/          ← Python tests (backend only)
│
├── frontend/           ← React/Vue
│   └── tests/          ← Jest tests (frontend only)
│
└── browser-tests/      ← Playwright tests (BOTH!) ✅
    └── examples/
        ├── gallery-flow.ts      ← Tests backend API
        ├── upload-flow.ts       ← Tests frontend UI
        └── auth-flow.ts         ← Tests both together
```

**Browser tests validate the whole stack!**

---

## Analogy: Building Testing

Think of testing an apartment building:

```
┌─────────────────────────────────┐
│  🏢 Apartment Building          │  ← E2E Tests (browser-tests/)
│                                 │    Test: Can tenant move in and live comfortably?
│  ┌─────────────────────────┐   │
│  │  🚪 Apartment Unit       │   │  ← Integration Tests (backend/tests/integration/)
│  │                          │   │    Test: Do plumbing + electrical work together?
│  │  ┌────────┐  ┌────────┐ │   │
│  │  │ 🚿 Bath│  │ 🔌 Elec│ │   │  ← API Tests (backend/tests/api/)
│  │  │        │  │        │ │   │    Test: Does each system work?
│  │  └────────┘  └────────┘ │   │
│  │                          │   │
│  │  🔩 Individual pipes,    │   │  ← Unit Tests (backend/tests/unit/)
│  │     wires, switches      │   │    Test: Does each component work?
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

**You test at different levels:**
- 🔩 Unit: Does this wire conduct electricity?
- 🔌 API: Does the outlet work?
- 🚪 Integration: Do all outlets in the apartment work together?
- 🏢 E2E: Can a tenant live here comfortably?

**You don't test wires from outside the building!**
→ Similarly, you don't need browser tests inside backend code.

---

## Summary

| Aspect | Backend Tests | Browser Tests |
|--------|--------------|---------------|
| **Location** | `backend/tests/` | `browser-tests/` |
| **Runtime** | Python + pytest | Bun + Playwright |
| **Scope** | Code-level (inside) | User-level (outside) |
| **Speed** | Fast | Slow |
| **Quantity** | Many | Few |
| **Connection** | Direct imports | HTTP |
| **Can test prod?** | No (needs source) | Yes (via HTTP) |

**Both are essential!**
- Backend tests: Find bugs in code
- Browser tests: Find bugs in user experience

---

**Questions?** See [ARCHITECTURE_DECISION.md](./ARCHITECTURE_DECISION.md) for the full rationale.
