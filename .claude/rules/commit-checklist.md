# Commit Checklist Rule

Before committing changes for a feature, verify that all related tasks are complete.

---

## Pre-Commit Checklist

### 1. Code Quality
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] Linting passes: `uv run ruff check .`
- [ ] Formatting correct: `uv run black . --check`

### 2. Documentation Updates
Verify these files are updated to reflect the completed work:

| File | What to Update |
|------|----------------|
| `TODO.md` | Mark related tasks as `[x]` complete |
| `requirements-phase2.md` | Update acceptance criteria checkboxes |
| `CLAUDE.md` | Update if architecture or patterns changed |
| `docs/adr/` | Create ADR if architectural decision was made |

### 3. Task Verification Commands

```bash
# Quick verification before commit
uv run pytest tests/ -v          # All tests pass
uv run ruff check .              # No lint errors
uv run black . --check           # Formatting OK

# Check for uncommitted TODO updates
git diff TODO.md requirements-phase2.md
```

### 4. Feature-Specific Checks

For **new services** (cache, rate limiter, concurrency):
- [ ] Unit tests added (`tests/unit/test_*.py`)
- [ ] Integration tests added if external service (`tests/integration/test_*.py`)
- [ ] Health endpoint updated to report status
- [ ] Configuration added to `config.py`
- [ ] Disabled in test fixtures (`conftest.py`)

For **new endpoints**:
- [ ] API tests added (`tests/api/test_*.py`)
- [ ] Error responses use structured format (`ErrorDetail`)
- [ ] OpenAPI docs updated (check `/docs`)

For **new dependencies**:
- [ ] Added to `pyproject.toml`
- [ ] Import test passes (CI dependency-check)

---

## Commit Message Format

```
<type>: <short description>

- Bullet point details
- Reference ADR if applicable

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

---

## Example Workflow

```bash
# 1. Run tests
uv run pytest tests/ -v

# 2. Check lint/format
uv run ruff check . && uv run black . --check

# 3. Review TODO/requirements updates
git diff TODO.md requirements-phase2.md

# 4. Stage and commit
git add .
git commit -m "feat: add concurrency control for uploads (ADR-0010)

- asyncio.Semaphore limits concurrent uploads to 10
- 503 returned if wait exceeds 30s timeout
- Semaphore acquired before file.read() for memory optimization

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Why This Matters

- **Consistency**: TODO.md and requirements stay in sync with code
- **Traceability**: Easy to see what's done vs pending
- **Onboarding**: New contributors see accurate project state
- **Review**: PRs include documentation updates, not just code
