# ADR-0014: Test Dependency Container Pattern

## Status
Accepted

## Date
2026-01-03

## Context

During Phase 2B (Thumbnails) implementation, we encountered a **hidden coupling** issue in our test fixtures. The `ThumbnailService` needed to create its own database sessions (via `session_factory`) because it runs in `BackgroundTasks` after the request completes.

### The Problem

```python
# Production: ThumbnailService gets session_factory from app
thumbnail_service = ThumbnailService(
    storage=app.state.storage,
    session_factory=async_session_maker,  # Global session factory
)

# Test: We override get_db, but ThumbnailService uses its own factory!
async def override_get_db():
    yield test_session  # This session is ignored by ThumbnailService
```

Result: Tests failed with "column not found" errors because `ThumbnailService` was using a different database (production `async_session_maker`) than the test database.

### Root Cause Analysis

1. **Production uses `app.state` as an implicit container** - All services stored on `app.state`
2. **Tests didn't mirror this pattern** - Fixtures were scattered and passed dependencies via hidden attributes
3. **Services with lifecycle-independent DB access bypass DI** - `ThumbnailService` creates sessions outside request scope

## Decision

Introduce an **explicit `TestDependencies` container** that mirrors the production `app.state` pattern.

### Before (Scattered, Hidden)
```python
@pytest.fixture
async def test_db(test_storage):
    # Hidden coupling: store deps as private attributes
    session._test_thumbnail_service = thumbnail_service  # type: ignore
    yield session

@pytest.fixture
async def client(test_db, test_storage):
    # Extract hidden attributes
    thumbnail_service = test_db._test_thumbnail_service  # type: ignore
    app.state.thumbnail_service = thumbnail_service
```

### After (Explicit Container)
```python
@dataclass
class TestDependencies:
    """Mirrors app.state - all deps visible and controllable."""
    engine: object
    session_maker: async_sessionmaker
    session: AsyncSession
    storage: StorageService
    thumbnail_service: ThumbnailService
    cache: CacheService | None = None
    rate_limiter: RateLimiter | None = None

@pytest.fixture
async def test_deps(test_storage) -> TestDependencies:
    # Create all deps with SHARED session_factory
    session_maker = async_sessionmaker(engine, ...)
    thumbnail_service = ThumbnailService(
        storage=test_storage,
        session_factory=session_maker,  # Same factory!
    )
    return TestDependencies(
        session_maker=session_maker,
        thumbnail_service=thumbnail_service,
        ...
    )

@pytest.fixture
async def client(test_deps: TestDependencies):
    # Wire up app.state from container (mirrors main.py lifespan)
    app.state.thumbnail_service = test_deps.thumbnail_service
```

## Consequences

### Positive
- **Explicit over implicit** - All dependencies visible in one place
- **Mirrors production** - Test setup matches `lifespan()` in `main.py`
- **Prevents coupling issues** - Services use shared `session_factory`
- **Self-documenting** - `TestDependencies` class documents what tests need
- **Easy to extend** - Adding new services is obvious

### Negative
- **One more fixture** - `test_deps` fixture required
- **Migration** - Existing tests may need updates (mitigated by backward-compatible `test_db` fixture)

## Pattern: Production-Test Symmetry

| Production | Test |
|------------|------|
| `app.state.storage` | `test_deps.storage` |
| `app.state.thumbnail_service` | `test_deps.thumbnail_service` |
| `lifespan()` creates deps | `test_deps` fixture creates deps |
| `async_session_maker` shared | `session_maker` shared |

## Prevention Checklist

When adding a new service that needs DB access outside request lifecycle:

1. ✅ Accept `session_factory` as constructor parameter
2. ✅ Add service to `TestDependencies` dataclass
3. ✅ Create service in `test_deps` fixture using shared `session_maker`
4. ✅ Wire to `app.state` in `client` fixture
5. ✅ Document the lifecycle requirement in service docstring

## References

- Phase 2B implementation discussion
- [Dependency Injection in FastAPI](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [pytest fixtures best practices](https://docs.pytest.org/en/stable/explanation/fixtures.html)
