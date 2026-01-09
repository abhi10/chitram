# Risk Patterns Catalog - Chitram Image Hosting

**Purpose:** "What if?" scenarios for QA testing and risk assessment
**Last Updated:** 2026-01-08
**Source:** Code analysis + incident retrospectives

---

## Pattern Format

Each pattern includes:
- **What if:** The risk scenario question
- **Impact:** What breaks or could break
- **Domain:** Category (file_upload, storage, auth, api, etc.)
- **Non-obvious score:** 1-5 (5 = most devs wouldn't think of this)
- **Status:** Mitigated / Not mitigated / Intentional
- **Code location:** Where to find related code

---

## High Priority Patterns (Score 4-5)

### 1. Pillow Memory DoS from Corrupt EXIF

- **What if:** An attacker uploads a JPEG with malicious EXIF dimensions (e.g., 100000x100000)?
- **Impact:** Pillow attempts to allocate gigabytes of memory, causing OOM kill or server hang. Semaphore slot is held during decode, blocking other uploads.
- **Domain:** image_processing
- **Non-obvious score:** 5/5
- **Status:** Not mitigated
- **Code location:** `backend/app/services/image_service.py:62-65`, `backend/app/services/thumbnail_service.py:67-81`

### 2. Auth Provider Mismatch Between Components (ACTUAL INCIDENT)

- **What if:** Web UI uses local JWT verification but API uses Supabase?
- **Impact:** Users appear logged out despite valid Supabase tokens. Nav shows "Login" instead of user email. Happened Jan 8, 2026 - took 12 hours to detect.
- **Domain:** auth
- **Non-obvious score:** 5/5
- **Status:** Fixed (PR #36), but pattern could recur
- **Code location:** `backend/app/api/web.py:41-74` (fixed), `backend/app/api/auth.py:37-56`
- **Incident:** [docs/retrospectives/2026-01-08-supabase-nav-auth-bug.md](../retrospectives/2026-01-08-supabase-nav-auth-bug.md)

### 3. Cross-Cutting Concerns Applied Inconsistently

- **What if:** A new auth/caching/logging pattern is added to API routes but not web routes?
- **Impact:** Two different code paths for the same feature. One works, one breaks. Users see inconsistent behavior.
- **Domain:** architecture
- **Non-obvious score:** 5/5
- **Status:** Requires manual audit
- **Prevention:** `grep -r "AuthService\|verify_token" --include="*.py"` when changing auth

### 4. Orphaned Files from Failed Deletion

- **What if:** Storage deletion fails but database deletion succeeds?
- **Impact:** Files remain in S3/MinIO forever, consuming storage costs. No cleanup mechanism exists. Code explicitly says "File may be orphaned" and continues.
- **Domain:** storage
- **Non-obvious score:** 4/5
- **Status:** Not mitigated
- **Code location:** `backend/app/services/image_service.py:355-365`

### 5. Memory Exhaustion from Concurrent Uploads

- **What if:** 10 users upload 5MB files simultaneously?
- **Impact:** 50MB in file buffers + 100-150MB for Pillow decoded images = 150-200MB peak memory. With more concurrent users, OOM possible.
- **Domain:** file_upload
- **Non-obvious score:** 4/5
- **Status:** Not mitigated (semaphore limits concurrency but not memory)
- **Code location:** `backend/app/api/images.py:126-141`, `backend/app/services/image_service.py:68-81`

### 6. Rate Limiter Bypass via X-Forwarded-For Spoofing

- **What if:** Attacker sends different X-Forwarded-For headers with each request?
- **Impact:** Each spoofed IP gets its own rate limit bucket. Attacker bypasses 10 req/min limit entirely.
- **Domain:** api
- **Non-obvious score:** 4/5
- **Status:** Not mitigated
- **Code location:** `backend/app/api/images.py:57-63`, `backend/app/services/rate_limiter.py:60`

### 7. Thumbnail Generation Hangs Indefinitely

- **What if:** Pillow gets stuck on a corrupt image during thumbnail generation?
- **Impact:** Background task runs forever, no timeout. Memory held until server restart. No monitoring of task completion.
- **Domain:** image_processing
- **Non-obvious score:** 4/5
- **Status:** Not mitigated
- **Code location:** `backend/app/services/thumbnail_service.py:112-175`

### 8. Test Environment Differs from Production

- **What if:** Tests use `AUTH_PROVIDER=local` but production uses `supabase`?
- **Impact:** All tests pass locally, production breaks immediately. This exact scenario caused the Jan 8 incident.
- **Domain:** deployment
- **Non-obvious score:** 4/5
- **Status:** Documented, requires manual verification
- **Related:** [docs/learning/supabase-integration-learnings.md](supabase-integration-learnings.md)

### 9. Docker Env Vars Not Passed Through

- **What if:** docker-compose.yml doesn't explicitly map environment variables?
- **Impact:** Container runs with defaults instead of production values. App appears to work but uses wrong config (e.g., local auth instead of Supabase).
- **Domain:** deployment
- **Non-obvious score:** 4/5
- **Status:** Fixed for known vars, new vars could have same issue
- **Code location:** `deploy/docker-compose.yml`

### 10. Config Loaded at Import Time

- **What if:** Tests import app modules before setting test environment variables?
- **Impact:** Tests try to connect to real Supabase instead of using mock. Tests fail with external service errors.
- **Domain:** testing
- **Non-obvious score:** 4/5
- **Status:** Fixed in conftest.py
- **Code location:** `backend/tests/conftest.py` (line 1-10)

---

## Medium Priority Patterns (Score 3)

### 11. PNG Transparency Lost in JPEG Thumbnail

- **What if:** User uploads PNG with alpha channel, thumbnail is generated as JPEG?
- **Impact:** Transparency converted to white/black background. User's logo with transparent background becomes opaque. No warning given.
- **Domain:** image_processing
- **Non-obvious score:** 3/5
- **Status:** Not mitigated
- **Code location:** `backend/app/services/thumbnail_service.py:69-70`

### 12. Rate Limiter Fails Open During Redis Outage

- **What if:** Redis goes down during a traffic spike or DDoS?
- **Impact:** All rate limiting disabled. API completely unprotected. Intentional design choice (availability over protection).
- **Domain:** api
- **Non-obvious score:** 3/5
- **Status:** Intentional (fail-open design)
- **Code location:** `backend/app/services/rate_limiter.py:83-85`

### 13. Delete Token Leakage Enables Unauthorized Deletion

- **What if:** Anonymous delete token is logged, stored in localStorage, or visible in browser history?
- **Impact:** Anyone with the token can delete the image. No rate limiting on delete endpoint. Token only shown once at upload.
- **Domain:** auth
- **Non-obvious score:** 3/5
- **Status:** Not mitigated
- **Code location:** `backend/app/api/images.py:162-187`, `backend/app/services/image_service.py:283-323`

### 14. Concurrent Upload Timeout Without Client Backoff

- **What if:** Many clients get 503 "Server busy" and immediately retry?
- **Impact:** Server returns `Retry-After` header, but clients may ignore it. Retry storm amplifies load. No exponential backoff enforced.
- **Domain:** file_upload
- **Non-obvious score:** 3/5
- **Status:** Partially mitigated (has Retry-After header)
- **Code location:** `backend/app/api/images.py:128-137`

### 15. Magic Bytes Check Only Validates File Header

- **What if:** Attacker creates polyglot file with JPEG header + executable payload?
- **Impact:** File passes validation (only first 3-4 bytes checked). If served directly without content-type header, browser might execute it.
- **Domain:** file_upload
- **Non-obvious score:** 3/5
- **Status:** Partially mitigated (content-type header set on storage)
- **Code location:** `backend/app/utils/validation.py:12-22`

### 16. SDK Version Breaking Changes

- **What if:** Third-party SDK updates its API between versions?
- **Impact:** `AttributeError: 'ClientOptions' object has no attribute 'storage'` - production crash on startup. Supabase v2.x changed the API.
- **Domain:** dependencies
- **Non-obvious score:** 3/5
- **Status:** Fixed for Supabase, could recur with other deps
- **Related:** [docs/learning/supabase-integration-learnings.md](supabase-integration-learnings.md)

### 17. Existing User Can't Login After Auth Migration

- **What if:** User exists in local DB but not in Supabase?
- **Impact:** "Invalid Credentials" error even with correct password. User must re-register in Supabase to link accounts.
- **Domain:** auth
- **Non-obvious score:** 3/5
- **Status:** Expected behavior (documented)
- **Related:** Sync-on-auth pattern in Supabase learnings

---

## Lower Priority Patterns (Score 1-2) - Well Handled

### 18. Storage Backend Unavailable During Upload

- **What if:** MinIO is down when saving file?
- **Impact:** Clean failure - HTTP 500 returned, no DB record created, no orphaned data.
- **Domain:** storage
- **Non-obvious score:** 2/5
- **Status:** Properly handled
- **Code location:** `backend/app/services/image_service.py:120-137`

### 19. Redis Cache Unavailable

- **What if:** Redis is down for 30 minutes?
- **Impact:** Graceful degradation - falls back to DB queries. System slower but functional.
- **Domain:** cache
- **Non-obvious score:** 1/5
- **Status:** Properly handled
- **Code location:** `backend/app/services/cache_service.py:110-123`

### 20. Thumbnail Task Runs After Image Deleted

- **What if:** User deletes image before thumbnail background task executes?
- **Impact:** Task queries DB, finds no image, logs warning, exits cleanly.
- **Domain:** background_tasks
- **Non-obvious score:** 2/5
- **Status:** Properly handled
- **Code location:** `backend/app/services/thumbnail_service.py:126-134`

### 21. Manual Production Edits Create Permission Issues

- **What if:** Someone manually edits files on the production server?
- **Impact:** Git fails with `unable to unlink old file: Permission denied` and `dubious ownership` errors. Requires `chown` and `git clean` to fix.
- **Domain:** deployment
- **Non-obvious score:** 2/5
- **Status:** Documented, avoid manual edits
- **Related:** [docs/learning/supabase-integration-learnings.md](supabase-integration-learnings.md)

### 22. Alembic Not Available in Production Container

- **What if:** You need to run a database migration but Alembic isn't in the Docker image?
- **Impact:** `alembic upgrade head` fails. Must use raw SQL via `psql` as workaround.
- **Domain:** deployment
- **Non-obvious score:** 2/5
- **Status:** Known limitation, use direct SQL

---

## Summary by Domain

| Domain | Count | High (4-5) | Medium (3) | Low (1-2) |
|--------|-------|------------|------------|-----------|
| image_processing | 3 | 2 | 1 | 0 |
| auth | 4 | 2 | 2 | 0 |
| deployment | 4 | 3 | 0 | 1 |
| file_upload | 3 | 1 | 2 | 0 |
| storage | 2 | 1 | 0 | 1 |
| api | 2 | 1 | 1 | 0 |
| testing | 1 | 1 | 0 | 0 |
| architecture | 1 | 1 | 0 | 0 |
| dependencies | 1 | 0 | 1 | 0 |
| background_tasks | 1 | 0 | 0 | 1 |
| cache | 1 | 0 | 0 | 1 |

---

## Summary by Mitigation Status

| Status | Count | Examples |
|--------|-------|----------|
| Not mitigated | 10 | Pillow DoS, orphaned files, X-Forwarded-For spoofing |
| Fixed | 4 | Auth provider mismatch (PR #36), Docker env vars |
| Intentional | 1 | Rate limiter fail-open |
| Properly handled | 4 | Cache fallback, storage failure, thumbnail race |
| Documented | 3 | Auth migration, manual edits, Alembic limitation |

---

## Prevention Checklist

When implementing changes, check:

### Auth Changes
```bash
grep -r "AuthService\|verify_token\|get_current_user" --include="*.py" app/
```

### Cross-Cutting Concerns
- [ ] Applied to API routes?
- [ ] Applied to web routes?
- [ ] Applied to background tasks?
- [ ] Tests cover all paths?

### Configuration Changes
- [ ] Added to docker-compose.yml?
- [ ] Added to .env.example?
- [ ] Tests mock/override correctly?
- [ ] Defaults are safe?

### External Dependencies
- [ ] Version pinned in pyproject.toml?
- [ ] Breaking changes documented?
- [ ] Fallback if unavailable?

---

## References

- [Incident Retrospective: Nav Auth Bug](../retrospectives/2026-01-08-supabase-nav-auth-bug.md)
- [Supabase Integration Learnings](supabase-integration-learnings.md)
- [Post-Deploy Checklist](../deployment/POST_DEPLOY_CHECKLIST.md)
- [ADR-0010: Concurrency Control](../adr/0010-upload-concurrency-control.md)
- [ADR-0009: Redis Caching](../adr/0009-redis-metadata-caching.md)

---

**Document Version:** 1.0
**Created:** 2026-01-08
**Source:** Code analysis + retrospectives
