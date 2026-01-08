# Supabase Authentication Integration - Learnings & Retrospective

## Overview

This document captures the learnings from integrating Supabase authentication into the Chitram image hosting application (Phase 3.5). It covers architecture decisions, implementation challenges, production deployment issues, and solutions.

**Duration:** ~2 sessions
**PRs Merged:** #31, #32, #33, #34
**Production URL:** https://chitram.io

---

## Architecture: Pluggable Auth with Sync-on-Auth

### Design Decision

We chose a **pluggable authentication system** with a **sync-on-auth strategy** rather than fully replacing local auth or doing a full migration.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         API Request                                  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AuthProvider Interface                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ register()   │  │ login()      │  │ verify_token()│              │
│  │ login()      │  │ returns:     │  │ returns:      │              │
│  │ verify_token │  │ (UserInfo,   │  │ UserInfo |    │              │
│  │ refresh_token│  │  TokenPair)  │  │ AuthError     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                                │
              ┌─────────────────┴─────────────────┐
              ▼                                   ▼
┌──────────────────────────┐       ┌──────────────────────────┐
│   LocalAuthProvider      │       │   SupabaseAuthProvider   │
│   ─────────────────      │       │   ────────────────────   │
│   - Password hashing     │       │   - Supabase API calls   │
│   - JWT generation       │       │   - Returns Supabase JWT │
│   - Local DB only        │       │   - Sync-on-auth to DB   │
└──────────────────────────┘       └──────────────────────────┘
              │                                   │
              └─────────────────┬─────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Local PostgreSQL                                │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ users table                                                  │    │
│  │ ─────────────                                                │    │
│  │ id (UUID) ──────────────────────┐                            │    │
│  │ email                           │ FK for images              │    │
│  │ password_hash (nullable)        │                            │    │
│  │ supabase_id (nullable, unique)  │                            │    │
│  └─────────────────────────────────┼────────────────────────────┘    │
│                                    │                                 │
│  ┌─────────────────────────────────┼────────────────────────────┐    │
│  │ images table                    │                            │    │
│  │ ────────────                    │                            │    │
│  │ id                              │                            │    │
│  │ user_id ◄───────────────────────┘                            │    │
│  │ filename, storage_key, etc.                                  │    │
│  └──────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### Sync-on-Auth Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│  Client  │────▶│   Backend    │────▶│   Supabase   │────▶│ Response │
└──────────┘     └──────────────┘     └──────────────┘     └──────────┘
     │                  │                    │                   │
     │  POST /register  │                    │                   │
     │─────────────────▶│                    │                   │
     │                  │  sign_up(email,pw) │                   │
     │                  │───────────────────▶│                   │
     │                  │                    │                   │
     │                  │◀─ user_id, session─│                   │
     │                  │                    │                   │
     │                  │  ┌─────────────────────────────────┐   │
     │                  │  │ Sync-on-Auth Logic:             │   │
     │                  │  │ 1. Find by supabase_id? Return  │   │
     │                  │  │ 2. Find by email? Link & Return │   │
     │                  │  │ 3. Create new local user        │   │
     │                  │  └─────────────────────────────────┘   │
     │                  │                    │                   │
     │◀─────────────────│ { user, token }    │                   │
     │                  │                    │                   │
```

### Why This Approach?

1. **Zero downtime migration**: Existing users keep working with local auth
2. **Gradual adoption**: Switch providers via env var, no code changes
3. **Data integrity**: Local user.id remains FK for images (no data migration)
4. **Flexibility**: Can switch back to local auth if needed
5. **Testing**: Tests use local auth (fast, no external dependencies)

---

## Implementation Timeline

### PR #31: Pluggable Auth System
**Files Changed:** 7 files, +194/-54 lines

Key changes:
- Created `AuthProvider` abstract base class
- Implemented `LocalAuthProvider` (extracted from existing code)
- Implemented `SupabaseAuthProvider` with sync-on-auth
- Added `create_auth_provider()` factory function
- Added `supabase_id` column to users table (migration)
- Updated API endpoints to use provider interface

### PR #32: E2E Auth Flow Tests
Browser-based tests for registration, login, logout flows.

### PR #33: Docker Compose Env Vars
**The Critical Fix**

Added environment variable passthrough in `deploy/docker-compose.yml`:
```yaml
# Auth Provider (Phase 3.5)
AUTH_PROVIDER: ${AUTH_PROVIDER:-local}
SUPABASE_URL: ${SUPABASE_URL:-}
SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY:-}
```

Also added test isolation in `conftest.py`:
```python
# Force local auth provider for tests
os.environ["AUTH_PROVIDER"] = "local"
```

### PR #34: Supabase Client Compatibility Fix
**The Production Bug**

Fixed `AttributeError: 'ClientOptions' object has no attribute 'storage'`

```python
# Before (broken with supabase v2.x)
from supabase.lib.client_options import ClientOptions
options = ClientOptions(
    auto_refresh_token=True,
    persist_session=False,
)
self._client = create_client(url, key, options=options)

# After (works with supabase v2.x)
self._client = create_client(url, key)
```

---

## Issues Encountered & Solutions

### Issue 1: Environment Variables Not Reaching Container

**Symptom:** App running but `AUTH_PROVIDER` was `local` instead of `supabase`

**Root Cause:** `docker-compose.yml` didn't have the Supabase env vars mapped to the container

**Solution:** Added env var mappings in docker-compose.yml environment section

**Lesson:** Docker Compose doesn't automatically pass through env vars - they must be explicitly mapped with `${VAR:-default}` syntax.

---

### Issue 2: Supabase Client API Compatibility

**Symptom:**
```
AttributeError: 'ClientOptions' object has no attribute 'storage'
```

**Root Cause:** The `supabase` Python package v2.x changed the `ClientOptions` API. The `storage` attribute was removed/renamed.

**Solution:** Removed `ClientOptions` usage entirely - defaults work fine for server-side usage.

**Lesson:** When using third-party SDKs, check for breaking changes between versions. The simplest solution is often to use defaults.

---

### Issue 3: Tests Failing with Supabase Errors

**Symptom:** Tests tried to connect to Supabase when running locally

**Root Cause:** Local `.env` had `AUTH_PROVIDER=supabase`, and tests were loading it before overriding

**Solution:** Set `os.environ["AUTH_PROVIDER"] = "local"` at the top of `conftest.py` before any app imports

**Lesson:** Test isolation requires setting env vars BEFORE importing app modules that read config at import time.

---

### Issue 4: "Invalid Credentials" on First Login

**Symptom:** Existing user couldn't log in after switching to Supabase

**Root Cause:** User existed in local DB (with password hash) but not in Supabase

**Solution:** User must register fresh in Supabase. The sync-on-auth logic then links the existing local user by email to the new Supabase account.

**Lesson:** This is expected behavior with the migration strategy. Document the user migration path clearly.

---

### Issue 5: Git Permission Issues on Droplet

**Symptom:**
```
error: unable to unlink old 'file': Permission denied
fatal: detected dubious ownership in repository
```

**Root Cause:** Files created by Docker (as root) mixed with chitram user, plus manual edits on server

**Solution:**
```bash
sudo git config --global --add safe.directory /opt/chitram
sudo git checkout -- .
sudo git clean -fd
sudo chown -R chitram:chitram .
```

**Lesson:** Avoid manual edits on production server. Use CI/CD for all deployments.

---

### Issue 6: Database Migration Without Alembic

**Symptom:** `alembic upgrade head` failed - alembic not in Docker PATH

**Root Cause:** Dockerfile doesn't include alembic directory or dev dependencies

**Solution:** Direct SQL via psql:
```bash
docker compose exec postgres psql -U chitram -d chitram \
  -c "ALTER TABLE users ADD COLUMN IF NOT EXISTS supabase_id VARCHAR(255) UNIQUE;"
```

**Lesson:** For simple schema changes in production, direct SQL is faster than fixing Alembic setup. For complex migrations, fix the Dockerfile to include Alembic.

---

## Configuration Reference

### Required Environment Variables (Production)

```bash
# In .env.production on droplet
AUTH_PROVIDER=supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1...
```

### Supabase Dashboard Setup

1. Create project at supabase.com
2. Copy Project URL and anon key from Settings > API
3. Email auth is enabled by default
4. Optional: Configure email templates, rate limits

---

## Verification Commands

### Check Auth Provider in Container
```bash
docker compose exec app env | grep -i "auth\|supabase"
```

### Verify User Linked to Supabase
```bash
docker compose exec postgres psql -U chitram -d chitram \
  -c "SELECT id, email, supabase_id FROM users;"
```

### Check Logs for Sync-on-Auth
```bash
docker compose logs app --tail=50 | grep -i "linked\|created"
```

---

## Key Takeaways

1. **Pluggable architecture pays off** - Switching providers is a config change, not a code rewrite

2. **Docker env vars need explicit mapping** - Don't assume passthrough

3. **Test isolation is critical** - Set env vars before imports

4. **SDK versions matter** - Pin versions or handle API changes

5. **Sync-on-auth enables gradual migration** - No big bang user migration needed

6. **Direct SQL for simple migrations** - Pragmatic over purist

7. **Avoid manual production edits** - Always deploy via git/CI

---

## Future Improvements

- [ ] Add Alembic to production Docker image
- [ ] Set up CI/CD for automatic deployment on merge
- [ ] Add refresh token endpoint to frontend
- [ ] Implement "Forgot Password" UI flow
- [ ] Add OAuth providers (Google, GitHub) via Supabase

---

## Related Documentation

- [ADR-0011: User Authentication with JWT](../adr/0011-user-authentication-jwt.md)
- [Phase 3.5 PRD](../requirements/phase3.5-supabase-auth-prd.md)
- [Supabase Python Client Docs](https://supabase.com/docs/reference/python/introduction)
