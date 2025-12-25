# Development Workflow

A lightweight guide for working through the Image Hosting App development.

---

## Workflow Overview

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   Spec   │ → │   Plan   │ → │  Design  │ → │  Build   │ → │   Test   │
│          │    │          │    │          │    │          │    │          │
│ What?    │    │ How big? │    │ How?     │    │ Code it  │    │ Verify   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼
requirements.md   Checklist      ADR (if new      Code +        Unit/API/
                  or TODO        decision)        Commits       Integration
```

---

## 1. Spec (What are we building?)

**When:** Before starting any feature

**Check:**
- [ ] Is this feature in `requirements.md`?
- [ ] Are acceptance criteria clear?
- [ ] Is it in scope for current phase?

**Action:** If requirements unclear, update `requirements.md` first.

---

## 2. Plan (How big is this?)

**When:** Before writing code

**Quick sizing:**

| Size | Description | Approach |
|------|-------------|----------|
| **Small** | Single file change, < 1 hour | Just do it |
| **Medium** | Multiple files, < 1 day | Write a TODO checklist |
| **Large** | Multiple days, new patterns | Create ADR + detailed plan |

**For Medium/Large:**
```markdown
## TODO: [Feature Name]
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3
- [ ] Write tests
- [ ] Update docs
```

---

## 3. Design (How will we build it?)

**When:** New architectural decisions arise

**Triggers for new ADR:**
- Choosing between multiple valid approaches
- Adding new technology/dependency
- Changing existing patterns
- Decision that's hard to reverse

**Action:** Create `docs/adr/XXXX-decision-name.md` using template.

**Skip ADR if:**
- Implementation detail (not architectural)
- Decision is obvious/standard
- Already covered by existing ADR

---

## 4. Build (Implementation)

### Git Workflow

**Branch naming:**
```
feature/short-description    # New feature
fix/short-description        # Bug fix
refactor/short-description   # Code improvement
```

**Commit messages:**
```
feat: add image upload endpoint
fix: handle missing content-type header
test: add upload API tests
docs: update requirements for rate limiting
refactor: extract storage service
```

Prefixes: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`

### Code Style

- **Formatter:** `black`
- **Linter:** `ruff`
- **Type hints:** Required for function signatures

```bash
# Before committing
black .
ruff check --fix .
```

---

## 5. Test (Verification)

### Testing Approach: Mixed TDD

| Complexity | Approach | Example |
|------------|----------|---------|
| **Complex logic** | TDD (test first) | Validation rules, business logic |
| **Simple CRUD** | Test after | Basic endpoints, DB operations |
| **Bug fixes** | Test first | Write failing test, then fix |

### Test Levels

| Level | What | When to Write |
|-------|------|---------------|
| **Unit** | Single function/class | Always for services |
| **API** | HTTP endpoints | Always for endpoints |
| **Integration** | With real DB/Redis | Key flows only |

### Running Tests

```bash
# Unit + API tests (fast, run often)
pytest tests/unit tests/api -v

# Integration tests (slower, before PR)
pytest tests/integration -v

# All tests with coverage
pytest --cov=app --cov-report=term-missing
```

### Minimum Coverage

| Area | Target |
|------|--------|
| Services | 80% |
| API endpoints | 100% of happy paths |
| Error handling | Key error cases |

---

## Definition of Done

A feature is **done** when:

- [ ] Code complete and working
- [ ] Unit tests passing
- [ ] API tests passing (if endpoint)
- [ ] No linting errors (`ruff check`)
- [ ] Code formatted (`black`)
- [ ] Swagger docs accurate (auto-generated)
- [ ] Changelog updated (if significant)
- [ ] ADR created (if new decision)

---

## Quick Reference

### File Locations

| What | Where |
|------|-------|
| Requirements | `requirements.md` |
| Design doc | `image-hosting-mvp-distributed-systems.md` |
| ADRs | `docs/adr/` |
| Changelog | `docs/changelog.md` |
| Tests | `tests/` |

### Common Commands

```bash
# Start dev environment
docker-compose up -d

# Run app locally
uvicorn app.main:app --reload

# Run tests
pytest -v

# Format + lint
black . && ruff check --fix .

# Create new ADR
cp docs/adr/0000-template.md docs/adr/XXXX-name.md
```

---

## When to Update Docs

| Event | Update |
|-------|--------|
| New requirement | `requirements.md` |
| Architecture decision | New ADR |
| Feature complete | `changelog.md` |
| API change | Swagger (auto) + changelog |

---

**Document Version:** 1.0
**Last Updated:** 2025-12-13
