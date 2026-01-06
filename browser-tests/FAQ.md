# Browser Tests - Frequently Asked Questions

---

## Why do browser tests need database migrations?

**Short answer:** Browser tests don't directly use the database, but they test against a **running backend server** that does.

**Note:** As of 2026-01-06, browser tests use **PostgreSQL** (same as production) instead of SQLite, ensuring production parity and catching database-specific issues.

### The Architecture

```
┌─────────────────────────────────────────────────────────┐
│                GitHub Actions Workflow                  │
│                                                         │
│  1. Setup Database                                      │
│     ├─ Run Alembic migrations ────┐                    │
│     └─ Creates schema in SQLite   │                    │
│                                    ↓                    │
│  2. Start Backend Server        Uses DB                │
│     ├─ FastAPI app starts      ────┘                   │
│     └─ Listens on localhost:8000                       │
│                                    ↓                    │
│  3. Run Browser Tests           HTTP                   │
│     ├─ Playwright connects ────────┘                   │
│     └─ Tests via browser (no direct DB access)         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Why Each Test Type Needs DB

| Test Type | Needs DB? | Why? | How? |
|-----------|-----------|------|------|
| **Unit tests** | ❌ No | Test pure functions | Mock dependencies |
| **API tests** | ✅ Yes | Test endpoints with DB | Test DB via fixtures |
| **Integration tests** | ✅ Yes | Test backend + DB | Real DB connection |
| **Browser tests** | ✅ Yes (indirectly) | Backend needs DB to run | DB for backend, not tests |

---

## Is Alembic config the same across all test types?

**Yes and No** - Same migrations, different database URLs.

### Alembic Configuration

All tests use the **same migration files** in `backend/alembic/versions/`, but with different database connections:

```python
# backend/alembic/versions/001_initial.py
def upgrade():
    # Create users table
    # Create images table
    # etc.

# ← Same migration code for ALL test types
```

### Different Database URLs

| Environment | Database URL (Configured) | Driver (Used) | Purpose |
|-------------|---------------------------|---------------|---------|
| **Production** | `postgresql+asyncpg://...` | Async | Real PostgreSQL |
| **Backend tests (CI)** | `postgresql+asyncpg://app:localdev@...` | Async | Test DB |
| **Browser tests (CI)** | `postgresql+asyncpg://app:localdev@...` | Async (app) | Same as production |
| **Browser tests (Alembic)** | Converted to `postgresql://...` | Sync (migrations) | Alembic converts internally |
| **Development (optional)** | `sqlite+aiosqlite:///dev.db` | Async | Local development only |

### Why Two Drivers for Browser Tests?

```yaml
# .github/workflows/ui-tests.yml

# PostgreSQL service runs in background
services:
  postgres:
    image: postgres:16

# .env file contains ASYNC driver
DATABASE_URL=postgresql+asyncpg://app:localdev@localhost:5432/imagehost

# Step 1: Run migrations (Alembic converts to SYNC internally)
- name: Run database migrations
  run: uv run alembic upgrade head
  # Alembic strips +asyncpg → postgresql://...

# Step 2: Start app (uses ASYNC driver from .env)
- name: Start backend server
  run: uv run uvicorn app.main:app
  # Uses postgresql+asyncpg://...
```

**Why?**
- Alembic runs **synchronously** → converts async URL to sync internally
- FastAPI runs **asynchronously** → uses async driver from env
- Both connect to same PostgreSQL database, different drivers

**How Alembic Converts:**
```python
# backend/alembic/env.py
sync_database_url = settings.database_url.replace("+asyncpg", "").replace("+aiosqlite", "")
# postgresql+asyncpg://... → postgresql://...
# sqlite+aiosqlite://... → sqlite://...
```

---

## Do browser tests directly access the database?

**No!** Browser tests only interact via HTTP.

### What Browser Tests Do

```typescript
// browser-tests/examples/smoke-test.ts

// ✅ Browser tests DO this:
await browser.navigate('http://localhost:8000')
await browser.click('a[href="/login"]')
await browser.fill('input[type="email"]', 'user@example.com')
await browser.click('button[type="submit"]')

// ❌ Browser tests DON'T do this:
// import { database } from 'backend'
// await database.query('SELECT * FROM users')
```

### What Actually Happens

```
Browser Test                Backend Server              Database
    │                            │                          │
    │  HTTP GET /login           │                          │
    ├──────────────────────────→ │                          │
    │                            │  SELECT * FROM users     │
    │                            ├─────────────────────────→│
    │                            │                          │
    │                            │  ← User data             │
    │                            │←─────────────────────────┤
    │  ← HTML response           │                          │
    │←────────────────────────── │                          │
    │                            │                          │
```

**Key point:** Browser tests test the **user experience**, not database operations.

---

## Why not just mock the database for browser tests?

### Option 1: Real Database (Current Approach) ✅

```yaml
- Start PostgreSQL service  # Same DB as production
- Run Alembic migrations    # Create real schema
- Start FastAPI             # Real app with real DB
- Run browser tests         # Test real behavior
```

**Pros:**
- ✅ Tests real application behavior
- ✅ Catches database-related bugs (PostgreSQL-specific)
- ✅ Tests migrations work correctly
- ✅ Realistic data flow
- ✅ **Production parity** - same DB as production (PostgreSQL)
- ✅ Catches SQL dialect differences
- ✅ Tests transaction isolation and concurrency behavior

**Cons:**
- ⚠️ Slightly slower setup (~5-10s for PostgreSQL + migrations)
- ⚠️ Requires database service in CI

### Option 2: Mock Database (Alternative) ❌

```yaml
- Start FastAPI with mocked DB
- Run browser tests
```

**Pros:**
- ⚡ Faster setup

**Cons:**
- ❌ Doesn't test real DB interactions
- ❌ Can't catch migration issues
- ❌ Might miss database-related bugs
- ❌ Not testing production-like environment

**Verdict:** Real database is better for browser tests because we want to test the whole stack.

---

## Could we skip database setup for some browser tests?

**Yes, for testing static pages!** But not for our app.

### When You Could Skip DB

If your app had purely static pages:

```typescript
// Testing a static marketing site
await browser.navigate('http://localhost:8000/about')
await browser.waitForSelector('h1')
// No backend logic, no DB needed
```

### Why Our App Needs DB

Our app is **database-backed**:

```typescript
// Home page - shows images from database
await browser.navigate('http://localhost:8000/')
await browser.waitForSelector('.masonry-grid')
// ← Backend queries: SELECT * FROM images

// Login page - authenticates against users table
await browser.fill('input[type="email"]', 'user@example.com')
await browser.click('button[type="submit"]')
// ← Backend queries: SELECT * FROM users WHERE email=...

// Upload page - creates database records
await browser.click('a[href="/upload"]')
// ← Backend queries: INSERT INTO images ...
```

**Every page needs the database!**

---

## How do integration tests differ from browser tests?

### Integration Tests (backend/tests/integration/)

```python
# backend/tests/integration/test_web_routes.py

async def test_home_page_shows_gallery(client, db, test_image):
    # Direct backend test
    response = await client.get("/")

    # Can verify database directly
    images = await db.execute(select(Image))
    assert len(images) > 0

    # Can verify HTML
    assert "masonry-grid" in response.text
```

**Characteristics:**
- Run **inside** backend codebase
- Direct access to database
- Direct access to backend code
- Use pytest fixtures
- Fast (no browser overhead)

### Browser Tests (browser-tests/)

```typescript
// browser-tests/examples/smoke-test.ts

await browser.navigate('http://localhost:8000')
await browser.waitForSelector('.masonry-grid')

// ❌ Can't do this:
// const images = await db.query('SELECT * FROM images')
```

**Characteristics:**
- Run **outside** backend codebase
- No direct database access
- No direct backend code access
- Use Playwright browser
- Slower (real browser)
- Tests user experience

---

## Comparison: Integration Tests vs Browser Tests

### Same Migration Files, Different Usage

```
backend/alembic/versions/
├── 001_create_users.py
├── 002_create_images.py
└── 003_add_thumbnails.py
        ↓
        │
   ┌────┴────┐
   │         │
   ↓         ↓
Integration  Browser Tests
Tests        (for backend)
(direct)     (indirect)
```

### Different Test Execution

**Integration Tests:**
```yaml
# .github/workflows/ci.yml (backend tests)

- Setup test database (in-memory)
- Run Alembic migrations
- Run pytest
  - Tests import backend code
  - Tests use database directly
  - Tests verify business logic
```

**Browser Tests:**
```yaml
# .github/workflows/ui-tests.yml

- Setup test database (file-based)
- Run Alembic migrations
- Start backend server (uses database)
- Run Playwright
  - Tests connect via HTTP
  - Tests use browser
  - Tests verify user experience
```

---

## Why do we need both?

### Integration Tests Catch:
- ✅ Backend logic bugs
- ✅ Database query issues
- ✅ API endpoint errors
- ✅ Business rule violations

### Browser Tests Catch:
- ✅ UI rendering issues
- ✅ JavaScript errors
- ✅ User workflow problems
- ✅ Cross-browser compatibility
- ✅ Visual regressions

### Example Bug Scenarios

**Caught by Integration Tests:**
```python
# Bug: Wrong SQL query
def get_user_images(user_id):
    return db.query(Image).filter(Image.id == user_id)  # Wrong!
    # Should be: Image.user_id == user_id

# Integration test catches this:
images = await service.get_user_images(user.id)
assert len(images) == 2  # Fails! Returns 0
```

**Caught by Browser Tests:**
```typescript
// Bug: Login form doesn't submit
await browser.fill('input[type="email"]', 'user@example.com')
await browser.fill('input[type="password"]', 'password')
await browser.click('button[type="submit"]')
await browser.waitForSelector('.dashboard')  // Times out!

// Integration test wouldn't catch this:
response = await client.post("/api/auth/login", ...)
assert response.status_code == 200  // Passes! API works fine
// But the UI bug is missed
```

---

## Best Practices

### 1. Run Migrations in CI for Browser Tests ✅

```yaml
# Always do this
- Run Alembic migrations
- Start backend
- Run browser tests
```

**Why:** Ensures backend can start and tests run against realistic setup.

### 2. Use Async Driver in Environment ✅

```bash
# .env file
DATABASE_URL=sqlite+aiosqlite:///./test.db  # Async for both app and migrations
```

**Why:** FastAPI needs async driver. Alembic converts it to sync internally.

### 3. Let Alembic Handle Driver Conversion ✅

```python
# backend/alembic/env.py
sync_database_url = settings.database_url.replace("+aiosqlite", "")
```

**Why:** Alembic is synchronous, but can convert async URL to sync automatically.

### 4. Keep Migration Files DRY ✅

```
# ✅ One set of migrations
backend/alembic/versions/

# ❌ Don't duplicate
browser-tests/alembic/  # Wrong!
```

**Why:** Single source of truth for schema.

---

## Summary

| Question | Answer |
|----------|--------|
| **Do browser tests use DB directly?** | No, only via HTTP |
| **Why setup DB for browser tests?** | Backend server needs it |
| **Same Alembic config?** | Same migrations, different DB URLs |
| **Why sync + async drivers?** | Alembic is sync, FastAPI is async |
| **Could we skip DB setup?** | No, our app is database-backed |
| **Do we need both test types?** | Yes, they catch different bugs |

---

## Related Documentation

- [Browser Test Overview](../docs/learning/browser-test-overview.md)
- [Testing Layers](./TESTING_LAYERS.md)
- [Architecture Decision](./ARCHITECTURE_DECISION.md)
