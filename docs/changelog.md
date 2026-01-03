# Changelog

All notable changes to the Image Hosting App project documentation and decisions.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- `docs/development-workflow.md` - Lightweight development workflow guide
- [ADR-0006](adr/0006-no-kubernetes-for-mvp.md) - No Kubernetes for MVP phases
- [ADR-0007](adr/0007-use-github-codespaces.md) - Use GitHub Codespaces for development
- [ADR-0008](adr/0008-phase1-lean-defer-complexity.md) - Defer non-essential features to later phases
- `.claude/rules/python.md` - AI assistant coding guidelines
- `docs/phase1-lean-removals-summary.md` - Detailed removal instructions for Phase 1 Lean
- `docs/phase-execution-plan.md` - Phased implementation strategy (Phase 1, 1.5, 2, 3, 4)
- `docs/sessions/2025-12-19-phase1-lean-execution.md` - Session log: Phase 1 Lean execution

### Changed
- `docs/code-review-checklist.md` - Updated for Phase 1 Lean (v2.0)
- `image-hosting-mvp-distributed-systems.md` - Updated to v1.3 for Phase 1 Lean approach
  - Architectural Building Blocks diagram updated to show Phase 1 Lean
  - Tech Stack diagram simplified (removed MinIO)
  - Database schema reduced to 7 essential columns
  - Dependencies list updated to 9 packages
  - Added Phase 1 Lean explanation and ADR-0008 reference
- `backend/app/main.py` - Added database exception handler
  - Handles SQLAlchemy OperationalError and TimeoutError
  - Returns 503 Service Unavailable (vs 500 for app errors)
  - Uses existing SERVICE_UNAVAILABLE error code
  - Improves observability for database connection issues

### Removed
- `docs/IMPLEMENTATION_SUMMARY.md` - Redundant with session log
- **Phase 1 scaffolding complete:**
  - FastAPI application with lifespan pattern
  - PostgreSQL + async SQLAlchemy setup
  - MinIO/local storage backend abstraction
  - Image upload/download/delete endpoints
  - Structured error handling
  - Health check endpoint
  - Devcontainer with Postgres + MinIO
  - pytest fixtures and API tests
  - README with setup instructions

### Changed (Phase 1 Lean - Pending Implementation)
- **Simplify to local storage only:** Remove MinIO backend for initial phase
- **Defer image dimensions:** Remove Pillow dependency and width/height fields
- **Simplify validation:** Use manual magic bytes check instead of python-magic library
- **Reduce model fields:** Remove is_public, updated_at (not needed in Phase 1)
- **Remove unused code:** Empty test directories, calculate_checksum() method
- **Smaller dependencies:** Remove minio, pillow from main dependencies (~508MB savings)

### Planned
- **Immediate:** Apply Phase 1 Lean removals (ADR-0008)
- Alembic migrations setup
- Git initialization and first commit
- Validation following validation-checklist.md
- Rate limiting implementation
- **Phase 1.5:** Add back image dimensions (Pillow)
- **Phase 2:** MinIO backend, user auth, background jobs

---

## [0.1.0] - 2025-12-13

### Added

#### Documentation
- `../requirements/phase1.md` - Phase 1 functional and non-functional requirements
- `image-hosting-mvp-distributed-systems.md` - Full MVP design document with 4 phases
- `docs/adr/` - Architecture Decision Records folder

#### Architecture Decisions
- [ADR-0001](adr/0001-use-fastapi-framework.md) - Use FastAPI as web framework
- [ADR-0002](adr/0002-postgresql-for-metadata.md) - Use PostgreSQL for metadata storage
- [ADR-0003](adr/0003-anonymous-access-phase1.md) - Anonymous access for Phase 1
- [ADR-0004](adr/0004-skip-delete-token-phase1.md) - Skip delete token for Phase 1
- [ADR-0005](adr/0005-structured-error-format.md) - Use structured error response format

#### Requirements Defined
- Image upload (JPEG, PNG, max 5MB)
- Image retrieval (metadata + file download)
- Image deletion (anyone with UUID)
- Rate limiting (10/IP/min, 429 response)
- Structured error format with error codes

### Decisions Made
| Decision | Choice | ADR |
|----------|--------|-----|
| Web Framework | FastAPI | ADR-0001 |
| Database | PostgreSQL | ADR-0002 |
| Auth Model | Anonymous (Phase 1) | ADR-0003 |
| Delete Auth | No token (Phase 1) | ADR-0004 |
| Error Format | Structured with codes | ADR-0005 |

---

## Future Releases

### Phase 2 (Planned)
- Redis caching layer
- Background job processing (thumbnails)
- User authentication / API keys
- Delete tokens

### Phase 3 (Planned)
- Load balancing
- Read/write service separation
- Database replication
- Storage sharding

### Phase 4 (Planned)
- Prometheus metrics
- Grafana dashboards
- Circuit breakers
- Rate limiting enhancements

---

## Document Versions

| Document | Current Version | Last Updated |
|----------|-----------------|--------------|
| ../requirements/phase1.md | 1.1 | 2025-12-13 |
| image-hosting-mvp-distributed-systems.md | 1.3 | 2025-12-19 |

---

## How to Add Entries

When making changes:

1. **New ADR**: Create `docs/adr/XXXX-short-title.md` using template
2. **Requirements change**: Update `../requirements/phase1.md`, bump version
3. **Architecture change**: Update MVP doc, bump version
4. **Log here**: Add entry under `[Unreleased]` section

When releasing:
1. Move `[Unreleased]` items to new version section
2. Add release date
3. Create new `[Unreleased]` section
