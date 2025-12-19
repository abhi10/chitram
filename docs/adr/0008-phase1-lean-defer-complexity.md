# ADR-0008: Defer Non-Essential Features to Later Phases (Phase 1 Lean)

## Status

Accepted

## Date

2025-12-19

## Context

Phase 1 scaffolding created comprehensive functionality including:
- MinIO/S3-compatible storage backend
- Image dimension extraction (Pillow)
- Advanced file validation (python-magic)
- Extra model fields (is_public, updated_at, width, height)

**Problem:** Before validation, we're carrying complexity that:
1. Has never been tested (scaffolding not validated)
2. Adds dependencies that increase Docker image size by ~508MB
3. Requires additional services (MinIO) that complicate local dev
4. Includes fields not required by Phase 1 requirements

**Goal:** Validate the simplest possible working system before adding complexity.

## Decision

**Defer the following to later phases:**

### Remove for Phase 1
1. **MinIO storage backend** - Use local filesystem only
2. **Image dimensions** - Defer Pillow dependency
3. **python-magic library** - Use manual signature checking
4. **Unused model fields** - Remove is_public, updated_at, width, height
5. **Unused methods** - Remove calculate_checksum()
6. **Empty test directories** - Remove unit/ and integration/

### Phase 1 Lean Will Include
- FastAPI + PostgreSQL only
- Local filesystem storage (LocalStorageBackend)
- Basic CRUD operations
- Essential fields only (id, filename, storage_key, content_type, file_size, upload_ip, created_at)
- Manual magic bytes validation (JPEG/PNG signatures)
- API tests (functional tests in tests/api/)

## Rationale

### Why Remove MinIO?
1. **Local dev simplicity** - One less Docker service to manage
2. **Faster startup** - No waiting for MinIO to initialize
3. **Phase 1 requirements** - Specs don't mandate S3-compatible storage
4. **Easy restoration** - Strategy pattern preserves abstraction
5. **Size reduction** - Saves 500MB Docker image

**When to restore:** Phase 2 (cloud deployment / production)

### Why Remove Image Dimensions?
1. **Heavy dependency** - Pillow is 3MB+ with native dependencies
2. **Not required** - Phase 1 requirements don't mandate returning dimensions
3. **Nice-to-have** - Can add back quickly when needed
4. **API simplicity** - Fewer fields in response = clearer contract

**When to restore:** Phase 1.5 (image info features)

### Why Remove python-magic?
1. **System dependency** - Requires libmagic installation
2. **Fallback exists** - Manual signature checking works for JPEG/PNG
3. **Limited formats** - Phase 1 only supports 2 formats
4. **Setup complexity** - One less thing that can break

**When to restore:** Phase 2 (when supporting more formats)

### Why Remove Unused Fields?
1. **is_public** - No auth system in Phase 1, all images are "public"
2. **updated_at** - No update operations exist in Phase 1
3. **width/height** - Covered above (Pillow removal)
4. **Simpler schema** - Easier to understand and migrate

**When to restore:**
- is_public: Phase 2 (user accounts)
- updated_at: Phase 2+ (if update operations added)

### Why Remove Empty Test Directories?
1. **No content** - Only `__init__.py` files
2. **Create when needed** - Easy to add back with first test
3. **Less clutter** - Clearer project structure

**When to restore:** Phase 1.5+ (when writing unit/integration tests)

## Consequences

### Positive
1. **Faster validation** - Less to test, simpler setup
2. **Cleaner first commit** - Only essential code
3. **Learning clarity** - Start simple, add complexity incrementally
4. **Smaller images** - Docker container is 508MB smaller
5. **Fewer dependencies** - 3 packages removed from main dependencies
6. **Easier debugging** - Less code to reason about

### Negative
1. **Multiple phases needed** - Must add back features incrementally
2. **Schema migrations** - Will need Alembic migrations for Phase 1.5/2
3. **API changes** - Response format will evolve (no width/height initially)
4. **Documentation overhead** - Must track what was removed and why

### Neutral
1. **Strategy pattern preserved** - Can swap storage backend later
2. **Test structure unchanged** - API tests still work (with adjustments)
3. **Development workflow** - Same process, less code

## Implementation

See detailed removal instructions: `docs/phase1-lean-removals-summary.md`

**Estimated effort:** 45-60 minutes to apply all removals

**Key changes:**
- Remove ~115 lines of code
- Remove 3 dependencies from pyproject.toml
- Remove 1 Docker service (MinIO)
- Remove 4 model fields
- Update 10 files

## Validation Criteria

Phase 1 Lean is successfully implemented when:
- [ ] Application starts with only Postgres (no MinIO)
- [ ] Upload works with local filesystem storage
- [ ] No imports reference minio, pillow, or python-magic
- [ ] API responses don't include width, height
- [ ] Database schema has 7 columns (not 10)
- [ ] All tests pass (after updating assertions)
- [ ] Docker Compose only defines postgres service
- [ ] pyproject.toml has 9 dependencies (not 12)

## Restoration Plan

### Phase 1.5 (Image Info) - Add Back
- Pillow dependency
- width, height fields
- get_image_dimensions() method
- Alembic migration for schema change

**Estimated effort:** 30 minutes

### Phase 2 (Full Features) - Add Back
- MinIO dependencies and configuration
- MinioStorageBackend class
- MinIO Docker service
- is_public, updated_at fields
- python-magic for stricter validation
- calculate_checksum() for deduplication

**Estimated effort:** 2-3 hours

## Alternatives Considered

### Alternative 1: Keep Everything
**Pros:**
- No rework needed later
- Feature-complete from start

**Cons:**
- Never validated complex codebase
- Harder to debug if issues arise
- Violates "start simple" principle

**Rejected:** Goes against lean startup methodology

### Alternative 2: Remove Even More
Could remove:
- upload_ip field (needed for rate limiting)
- Client IP detection (get_client_ip function)
- Structured errors (use plain strings)

**Rejected:** These are core Phase 1 requirements or critical patterns

### Alternative 3: Make MinIO Optional
Keep the code but disable by default

**Rejected:** Dead code in initial commit is confusing

## References

- [Phase 1 Requirements](../../requirements.md) - No MinIO/dimensions required
- [Removal Summary](../phase1-lean-removals-summary.md) - Detailed instructions
- [Phase Execution Plan](../phase-execution-plan.md) - Phased approach
- [ADR-0001](0001-use-fastapi-framework.md) - FastAPI decision
- [ADR-0002](0002-postgresql-for-metadata.md) - PostgreSQL decision

## Notes

**Key insight:** The Strategy pattern (StorageBackend abstraction) makes this decision reversible with minimal code changes. We can restore MinIO in Phase 2 by just adding the class back—no refactoring of business logic needed.

**Learning objective:** Experience the difference between "works in theory" (Phase 1 original) and "validated working system" (Phase 1 Lean). Testing simple systems builds confidence before adding complexity.
