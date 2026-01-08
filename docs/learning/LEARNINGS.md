# Distributed Systems Learnings

**Project:** Chitram - Image Hosting API
**Purpose:** Track learnings mapped to distributed systems building blocks

---

## Building Blocks Tracker

| Principle | Building Block | Phase | Status | Key Learning |
|-----------|---------------|-------|--------|--------------|
| **Availability** | Health Checks | 1 | ✅ | `/health` endpoint returns DB + storage status |
| **Availability** | Graceful Degradation | 1 | ✅ | Delete continues if storage fails (DB is source of truth) |
| **Performance** | Local Storage | 1 | ✅ | Simple FS for MVP, abstracted via Strategy pattern |
| **Performance** | Caching (Redis) | 2 | ⏸️ | - |
| **Performance** | Async Processing | 2 | ⏸️ | - |
| **Reliability** | DB Transactions | 1 | ✅ | SQLAlchemy async sessions with proper commit/rollback |
| **Reliability** | Structured Errors | 1 | ✅ | Error codes enable client-side handling (ADR-0005) |
| **Reliability** | Input Validation | 1 | ✅ | Magic bytes validation, not just Content-Type header |
| **Scalability** | Storage Abstraction | 1 | ✅ | Strategy pattern for easy backend swapping |
| **Scalability** | Dependency Injection | 1 | ✅ | FastAPI Depends() enables testing with overrides |
| **Scalability** | Load Balancing | 3 | ⏸️ | - |
| **Manageability** | DevContainer | 1 | ✅ | Codespaces for consistent dev environment |
| **Manageability** | Lifespan Pattern | 1 | ✅ | Clean startup/shutdown via context manager |
| **Manageability** | Logging | 1 | ⏸️ | Basic only, structured logging in Phase 4 |
| **Cost** | Lean Dependencies | 1 | ✅ | 9 deps vs 12 original (ADR-0008) |
| **Cost** | Defer Complexity | 1 | ✅ | Pillow, MinIO deferred to later phases |
| **Security** | JWT Authentication | 2A | ✅ | bcrypt + JWT, timing-safe comparisons (ADR-0011) |
| **Security** | Auth Abstraction | 3.5 | 📋 | Provider pattern for Supabase/Local switching |
| **Cost** | BaaS for Auth | 3.5 | 📋 | Supabase 20x cheaper than Auth0 at scale |
| **Availability** | Auth Fallback | 3.5 | 📋 | LocalAuthProvider fallback if Supabase down |

---

## Phase 1 Learnings (Detailed)

### What Worked Well

#### 1. Strategy Pattern for Storage
```python
class StorageBackend(ABC):
    async def save(self, key, data, content_type): ...

class LocalStorageBackend(StorageBackend): ...
class MinioStorageBackend(StorageBackend): ...  # Future
```
**Insight:** Even for MVP, building the abstraction layer pays off. Adding MinIO later will be a single class addition.

#### 2. Dependency Injection Pattern
```python
@router.get("/{image_id}")
async def get_image(
    service: ImageService = Depends(get_image_service),
):
```
**Insight:** Made testing trivial - just override `app.dependency_overrides` in conftest.py.

#### 3. Structured Error Format
```python
ErrorDetail(code="INVALID_FILE_FORMAT", message="Only JPEG and PNG supported")
```
**Insight:** Machine-readable error codes enable programmatic client handling, not just human-readable messages.

#### 4. Lifespan Context Manager
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    app.state.storage = StorageService(...)
    yield
    await close_db()
```
**Insight:** Cleaner than `@app.on_event("startup")` deprecated pattern. Resources in `app.state` accessible everywhere.

### What Was Harder Than Expected

#### 1. Async SQLAlchemy Session Management
**Challenge:** Understanding when to use `async_session()` vs `async_sessionmaker()`.
**Solution:** Use `async_sessionmaker` factory, yield session per request via `get_db()` dependency.
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
```

#### 2. File Type Validation Without python-magic
**Challenge:** python-magic requires libmagic C library (adds complexity).
**Solution:** Manual magic bytes checking for JPEG (`FF D8 FF`) and PNG (`89 50 4E 47`).
```python
MAGIC_BYTES = {
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG': 'image/png',
}
```
**Insight:** For limited file types, manual checking is simpler and has zero dependencies.

#### 3. pyproject.toml Build Configuration
**Challenge:** Hatchling couldn't find package directory.
**Solution:** Added explicit `[tool.hatch.build.targets.wheel]` section.
```toml
[tool.hatch.build.targets.wheel]
packages = ["app"]
```

### Decisions Made

| Decision | Rationale | ADR |
|----------|-----------|-----|
| Defer Pillow | Image dimensions not critical for MVP | ADR-0008 |
| Defer MinIO | Local storage sufficient for validation | ADR-0008 |
| Skip python-magic | Manual magic bytes simpler for 2 formats | ADR-0008 |
| Use Codespaces | 8GB RAM constraint on local machine | ADR-0007 |
| Structured Errors | Enable programmatic error handling | ADR-0005 |
| No Kubernetes | Overkill for MVP phases | ADR-0006 |

---

## Phase 1.5 Learnings (To Be Added)

*Will document after implementing image dimensions feature.*

---

## Phase 2 Learnings (To Be Added)

*Will document after implementing caching and async processing.*

---

## Supabase Integration Analysis

**Date:** 2026-01-07
**Context:** Evaluating authentication solutions for Chitram's pluggable auth system

### Why Supabase Over Alternatives?

#### Alternatives Considered

| Solution | Type | Status | Verdict |
|----------|------|--------|---------|
| **FastAPI-Users** | Library | ⚠️ Maintenance mode | Pass - No future |
| **AuthX** | Library | Active | Viable but limited |
| **FastAPI-Cloud-Auth** | Library | Active | Good for AWS/Auth0 |
| **Roll our own** | Custom | N/A | Already have this |
| **Supabase Auth** | BaaS | Active | ✅ Selected |

#### FastAPI-Users: Why We Passed

Per [FastAPI-Users GitHub](https://github.com/fastapi-users/fastapi-users):

> "This project is now in **maintenance mode**... no new features will be added. We're working on a new Python authentication toolkit that will ultimately supersede FastAPI Users."

**Problems:**
- Successor library not yet announced
- Building on library with no future
- Would need migration to unknown replacement in 1-2 years
- No external provider support (Supabase, Auth0, etc.)

### Supabase Main Advantages

#### 1. Cost-Effectiveness (Biggest Win)

| Provider | Price per MAU | 100K users/month |
|----------|---------------|------------------|
| **Supabase** | $0.00325 | **$325** |
| Auth0 | $0.07 | $7,000 |
| Firebase | $0.0039 | $390 |
| AWS Cognito | ~$0.02 | $2,000 |

**Supabase is 20x cheaper than Auth0** at scale.

Source: [Auth Pricing Wars](https://zuplo.com/learning-center/api-authentication-pricing)

#### 2. Zero Vendor Lock-in

- **Open source** - Can self-host Supabase entirely
- **PostgreSQL native** - Data is standard SQL, not proprietary
- **Exit strategy** - Export users, run your own GoTrue server

#### 3. Features Without Code

| Feature | Lines of Code Required |
|---------|------------------------|
| Password reset emails | 0 (Supabase handles) |
| Email verification | 0 |
| OAuth (Google, GitHub) | ~20 (redirect URLs only) |
| Token refresh | ~10 (SDK call) |
| MFA/TOTP | ~30 (when ready) |
| Rate limiting on auth | 0 |
| Brute force protection | 0 |

#### 4. Alignment with Chitram's Goals

Looking at TODO.md phases:
- Phase 4: Celery, Dedup → Backend complexity
- Phase 5: Horizontal Scaling → Infrastructure
- Phase 6: Observability → Operations

**Auth is NOT our learning focus.** Offloading it lets us focus on distributed systems.

### Provider Abstraction: Still Valuable

Even with Supabase, the abstraction layer pays off:

| Scenario | Without Abstraction | With Abstraction |
|----------|---------------------|------------------|
| Supabase outage | App unusable | Fall back to local |
| Pricing change | Rewrite everything | Switch config |
| Development/testing | Need credentials | Use LocalAuthProvider |
| Enterprise wants Auth0 | Major rewrite | Add Auth0Provider |

### Integration Strategy: Sync-on-Auth

We chose the simplest viable approach:

| Approach | Complexity | Chosen |
|----------|------------|--------|
| Replace local DB with Supabase | High (rewrite FKs) | ❌ |
| Dual-write to both DBs | Medium (sync issues) | ❌ |
| **Sync user on login/register** | **Low** | ✅ |
| JWT-only verification | Low but limited | ❌ |

**Pattern:**
```
1. User logs in via API
2. SupabaseAuthProvider calls Supabase SDK
3. On success, sync user to local DB:
   - If supabase_id exists → return local user
   - If email exists → link to Supabase (migration)
   - Else → create new local user
4. Return local user.id in UserInfo
5. Image FKs use local user.id (no changes needed!)
```

### Supabase SDK: Minimal Surface Area

We only use 5 methods - that's minimal:

```python
client.auth.sign_up()                    # Register
client.auth.sign_in_with_password()      # Login
client.auth.get_user(jwt)                # Verify token
client.auth.refresh_session()            # Refresh
client.auth.reset_password_email()       # Password reset
```

### Architecture Validation

Compared against [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices):

| Best Practice | Our Implementation | Status |
|---------------|-------------------|--------|
| Dependency injection for auth | `Depends(get_auth_provider)` | ✅ |
| Chainable dependencies | `get_current_user` → `require_current_user` | ✅ |
| Separate auth from authorization | Provider = identity; Routes = permissions | ✅ |
| Domain-based exceptions | `AuthError` dataclass | ✅ |
| Async dependencies | All provider methods async | ✅ |
| Fail fast on config | Provider validation in lifespan | ✅ |

**Verdict:** Not overengineered. Single abstraction layer following established patterns.

### What Would Be Overengineering

Things we wisely avoided:
- ❌ Event bus for auth events
- ❌ Plugin architecture with dynamic loading
- ❌ Middleware-based auth (we use dependencies)
- ❌ Separate user microservice
- ❌ Abstract factory for providers
- ❌ Decorator-based auth on routes

### Evolution Roadmap

```
Phase 3 (Current)     → Web UI with current JWT auth
Phase 3.5 (New)       → Add SupabaseAuthProvider + password reset
Phase 4               → Focus on Celery, Dedup (auth is done)
Phase 4.5 (Optional)  → Add OAuth social login (2-3 days)
Phase 5+              → Auth scales automatically with Supabase
```

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| Supabase over FastAPI-Users | Active development, external provider, features |
| Keep provider abstraction | Testing, flexibility, fallback |
| Sync-on-auth strategy | Preserves FKs, minimal changes |
| Local user table retained | Source of truth for image ownership |
| Nullable password_hash | Supabase users don't need local hash |

### References

- [FastAPI-Users GitHub](https://github.com/fastapi-users/fastapi-users)
- [Awesome FastAPI - Auth](https://github.com/mjhea0/awesome-fastapi)
- [Supabase Python SDK](https://github.com/supabase/supabase-py)
- [Auth Pricing Comparison](https://zuplo.com/learning-center/api-authentication-pricing)
- [Supabase vs Auth0](https://supabase.com/alternatives/supabase-vs-auth0)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- Design Doc: `docs/design/DESIGN-pluggable-auth-system.md`
- PRD: `docs/requirements/PRD-pluggable-auth-system.md`

---

## Patterns Reference

### 1. Cache-Aside (Phase 2)
```
Read: Cache → Miss → DB → Store in Cache → Return
Write: DB → Invalidate Cache
```

### 2. Circuit Breaker (Phase 4)
```
Closed → Failure Threshold → Open → Recovery Timeout → Half-Open → Success → Closed
```

### 3. CQRS-lite (Phase 3)
```
Reads → Read Replicas (can be stale)
Writes → Primary DB (must be consistent)
```

---

## Questions for Future Exploration

1. **Cache Invalidation:** When to use TTL vs explicit invalidation?
2. **Sharding Strategy:** Hash-based vs range-based for images?
3. **Rate Limiting:** Per-IP vs per-user vs sliding window?
4. **Observability:** What metrics matter most for image hosting?

---

## External Resources Used

- [AOSA: Scalable Web Architecture](https://aosabook.org/en/v2/distsys.html) - Foundation
- [FastAPI Official Docs](https://fastapi.tiangolo.com/) - Framework patterns
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/) - Database patterns

---

**Document Version:** 1.1
**Last Updated:** 2026-01-07
