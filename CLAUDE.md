# Project: Image Hosting MVP

## Tech Stack
- FastAPI, PostgreSQL, MinIO (S3-compatible)
- SQLAlchemy 2.0 (async), Pydantic 2.x
- Local filesystem for dev, MinIO/S3 for prod
- uv for package management
- pytest for testing

## Current Status
- **Current Phase:** Phase 3 deployed to production (https://chitram.io)
- **Tests:** 225 passing
- **Production:** DigitalOcean droplet with Docker Compose, Caddy, PostgreSQL, MinIO, Redis

## Key Decisions
- Using GitHub Codespaces for development (ADR-0007)
- **Defer complexity to later phases (ADR-0008)** - Phase 1 Lean approach
- No Kubernetes for MVP phases (ADR-0006)
- Structured error format with error codes (ADR-0005)
- Anonymous access for Phase 1, no delete tokens (ADR-0003, ADR-0004)
- Storage backend abstraction (Strategy Pattern) for easy switching

### Phase 1 Lean Removals (ADR-0008)
- Remove MinIO backend (use local storage only)
- Remove Pillow/image dimensions (defer to Phase 1.5)
- Remove python-magic (use manual signature checking)
- Remove unused model fields (is_public, updated_at, width, height)
- **Impact:** ~115 lines, 3 dependencies, 508MB Docker images removed

## Project Structure
```
backend/
├── app/
│   ├── api/          # Route handlers (images.py, health.py)
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic (image_service, storage_service)
│   └── utils/        # Validation, helpers
├── tests/            # pytest tests (unit/, api/, integration/)
└── pyproject.toml    # Dependencies and tool config
```

## Common Commands
```bash
# Development
cd backend
uv sync --all-extras              # Install deps
uv run uvicorn app.main:app --reload --host 0.0.0.0  # Run server

# Testing
uv run pytest                     # All tests
uv run pytest tests/api -v        # API tests only
uv run pytest --cov=app           # With coverage

# Code Quality (runs automatically on commit via pre-commit)
uv run pre-commit run --all-files # Run all hooks manually
uv run ruff check --fix .         # Lint only
```

## Developer Workflow Tools

### Pre-commit Hooks (Automatic)
Runs automatically on every `git commit`. Catches issues before they reach CI.

**Hooks enabled:**
| Hook | Purpose |
|------|---------|
| `trailing-whitespace` | Clean up whitespace |
| `ruff` | Linting with auto-fix |
| `ruff-format` | Code formatting |
| `no-commit-to-branch` | Blocks direct commits to main |
| `detect-private-key` | Prevents credential leaks |
| `hadolint` | Dockerfile linting |

**Usage:**
```bash
# Runs automatically on commit
git commit -m "feat: add feature"

# Skip hooks (emergency only)
git commit --no-verify -m "hotfix: urgent fix"

# Run manually on all files
uv run pre-commit run --all-files
```

### Debugging Agent (Manual)
Self-contained context for debugging Chitram issues. Located at `.claude/agents/debugging.md`.

**When to use:**
- Stack traces or exceptions
- Failing tests
- Unexpected API responses (500s, wrong data)
- Cache/Redis issues

**How to invoke:**
```
"Use the debugging agent approach for this error: [paste stack trace]"
"Debug why test_upload_image is failing"
"Trace this 500 error from the logs"
```

**What it provides:**
- Chitram-specific error patterns (401/403/404/429/500/503)
- Diagnostic process (parse → trace → correlate → RCA)
- File lookup table by issue type
- Test isolation gotchas (BackgroundTasks, session_factory)

## API Endpoints
- `POST /api/v1/images/upload` - Upload image (JPEG/PNG, max 5MB)
- `GET /api/v1/images/{id}` - Get metadata
- `GET /api/v1/images/{id}/file` - Download file
- `DELETE /api/v1/images/{id}` - Delete image
- `GET /health` - Health check
- `GET /docs` - Swagger UI

## Documentation

### Planning & Requirements
- `docs/requirements/phase1.md` - Phase 1 functional/non-functional requirements
- `image-hosting-mvp-distributed-systems.md` - Full design doc (4 phases)
- `docs/phase-execution-plan.md` - Tactical execution plan (Phase 1→1.5→2→3→4)

### Architecture Decisions
- `docs/adr/` - Architecture Decision Records (14 ADRs)
- Key ADRs:
  - ADR-0014 - Test Dependency Container (production-test symmetry)
  - ADR-0012 - Background Tasks Strategy (FastAPI BackgroundTasks)
  - ADR-0011 - User Authentication with JWT
  - ADR-0010 - Concurrency Control for Uploads
  - ADR-0009 - Redis Caching for Metadata

### Implementation Guides
- `docs/development-workflow.md` - Dev workflow guide
- `docs/phase1-lean-removals-summary.md` - Detailed removal instructions
- `docs/validation-checklist.md` - Testing & validation steps
- `docs/code-review-checklist.md` - Reading order for code review

### Guidelines
- `.claude/rules/python.md` - Python coding guidelines

## Key Implementation Patterns

### 1. Lifespan Pattern (main.py:15-25)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB and storage
    await init_db()
    app.state.storage = StorageService(backend=...)
    yield
    # Shutdown: Cleanup
    await close_db()
```
**Why:** Clean startup/shutdown, resources stored in app.state

### 2. Strategy Pattern (storage_service.py)
```python
class StorageBackend(ABC)
class LocalStorageBackend(StorageBackend)
class MinioStorageBackend(StorageBackend)
class StorageService  # Facade wrapper
```
**Why:** Easy switching between local/MinIO without changing business logic

### 3. Dependency Injection (api/images.py)
```python
def get_image_service(
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage)
) -> ImageService:
    return ImageService(db=db, storage=storage)

@router.post("/upload")
async def upload_image(
    service: ImageService = Depends(get_image_service)
):
```
**Why:** Testability - can override dependencies in tests (conftest.py:42-43)

### 4. Graceful Degradation (image_service.py:95-99)
```python
async def delete(self, image_id: str) -> bool:
    try:
        await self.storage.delete(image.storage_key)
    except Exception:
        pass  # Continue even if storage fails
    await self.db.delete(image)
```
**Why:** DB is source of truth; storage failure shouldn't block deletion

### 5. Structured Errors (schemas/error.py)
```python
class ErrorDetail(BaseModel):
    code: str        # Machine-readable
    message: str     # Human-readable
    details: dict    # Additional context

# Usage in endpoints
raise HTTPException(
    status_code=400,
    detail=ErrorDetail(
        code="INVALID_FILE_FORMAT",
        message="Only JPEG and PNG supported"
    ).model_dump()
)
```
**Why:** Consistent error format for API consumers (ADR-0005)

### 6. Test Dependency Container (conftest.py) - ADR-0014
```python
@dataclass
class TestDependencies:
    """Mirrors app.state - all deps visible and controllable."""
    engine: object
    session_maker: async_sessionmaker
    session: AsyncSession
    storage: StorageService
    thumbnail_service: ThumbnailService

@pytest.fixture
async def test_deps(test_storage) -> TestDependencies:
    # Create all deps with SHARED session_factory
    session_maker = async_sessionmaker(engine, ...)
    thumbnail_service = ThumbnailService(
        storage=test_storage,
        session_factory=session_maker,  # Same factory!
    )
    return TestDependencies(...)

@pytest.fixture
async def client(test_deps: TestDependencies):
    # Wire up app.state from container (mirrors main.py lifespan)
    app.state.thumbnail_service = test_deps.thumbnail_service
```
**Why:** Services that run outside request lifecycle (BackgroundTasks) need session_factory. Test container ensures they use shared DB, not production global.

**Pattern:** Production uses `app.state` as container, tests use `TestDependencies`. Both explicit and mirrored.

## Important File Locations

| Purpose | File | Key Content |
|---------|------|-------------|
| Entry point | `backend/app/main.py` | FastAPI app, lifespan, middleware |
| Configuration | `backend/app/config.py` | Pydantic settings, env vars |
| Database setup | `backend/app/database.py` | Async engine, session factory |
| Data model | `backend/app/models/image.py` | SQLAlchemy Image model |
| API schemas | `backend/app/schemas/` | Pydantic request/response models |
| Business logic | `backend/app/services/image_service.py` | Upload, retrieval, deletion logic |
| Storage abstraction | `backend/app/services/storage_service.py` | Strategy pattern for storage |
| Validation | `backend/app/utils/validation.py` | Magic bytes, file type checking |
| API routes | `backend/app/api/images.py` | CRUD endpoints |
| Test fixtures | `backend/tests/conftest.py` | Test DB, storage, client |
| Test suite | `backend/tests/api/test_images.py` | API integration tests |

## Session Learnings

### From Existing AI App (local-ai-transcript-app)
1. **Lifespan pattern** preferred over startup/shutdown events
2. **Graceful degradation** - continue even if non-critical operations fail
3. **Provider abstraction** - use Strategy pattern for swappable backends
4. **DevContainer** - docker-compose for consistent dev environment
5. **pyproject.toml** - single file for deps + tool config (Ruff, Black, pytest)

### Code Organization
- **Separation of concerns:** schemas (API contracts) vs models (DB layer)
- **Service layer:** Business logic separate from HTTP handlers
- **Dependency injection:** All services injected via FastAPI Depends()
- **Test fixtures:** Override dependencies in conftest.py for testing

### Development Decisions
- **No over-engineering:** Start simple, add ADRs as decisions arise
- **Mixed TDD:** TDD for complex logic, tests-after for simple CRUD
- **Codespaces over Docker:** 8GB RAM constraint → cloud development
- **uv over pip:** Faster dependency resolution and locking

## Reading Order for New Contributors
See `docs/code-review-checklist.md` for step-by-step walkthrough:
1. Foundation: pyproject.toml → config.py → database.py (15 min)
2. Data Contracts: schemas/error.py → schemas/image.py (10 min)
3. Data Layer: models/image.py → storage_service.py (20 min)
4. Business Logic: image_service.py → validation.py (15 min)
5. HTTP Layer: api/health.py → api/images.py (20 min)
6. Entry Point: main.py (10 min)
7. Tests: conftest.py → test_images.py (15 min)

**Total: ~90 min, ~965 lines**

## Pending Work

See `TODO.md` for detailed phase tracking.

### Current Focus
- Phase 3 deployed to production
- Developer tooling: Pre-commit hooks, Debugging agent

### Future Phases
- **Phase 4:** Celery, Deduplication, Checksum
- **Phase 5:** Horizontal Scaling (Nginx, DB replication, Redis cluster)
- **Phase 6:** Observability (Prometheus, Grafana, Jaeger)

## Developer Tooling

| Tool | Location | Purpose |
|------|----------|---------|
| Pre-commit hooks | `.pre-commit-config.yaml` | Auto-lint/format on commit |
| Debugging agent | `.claude/agents/debugging.md` | Chitram-specific debugging context |
| Python rules | `.claude/rules/python.md` | Coding guidelines |
| Commit checklist | `.claude/rules/commit-checklist.md` | Pre-commit verification |
| Ship skill | `.claude/commands/ship.md` | Full CI/CD workflow |
| Validate skill | `.claude/commands/validate-deploy.md` | Deployment validation |
