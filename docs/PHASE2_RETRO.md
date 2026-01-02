# Phase 2 Retrospective: MinIO Integration

**Date:** 2025-01-01
**Phase:** 2 (MinIO Storage Backend)
**Environment:** GitHub Codespaces

---

## Summary

Phase 2 introduced MinIO as the production storage backend. During Codespaces testing, we encountered **6 issues**, primarily related to missing dependencies and permission quirks. All were resolved, and the phase was completed successfully.

**Final Test Results:** ✅ 31 passed (11 API + 9 Integration + 11 Unit)

---

## Issues Encountered

### Issue #1: Missing Pillow Dependency

| | |
|---|---|
| **Symptom** | `ModuleNotFoundError: No module named 'PIL'` |
| **Cause** | Added `from PIL import Image` to `image_service.py` but didn't add Pillow to dependencies |
| **Fix** | `uv add pillow` |
| **Severity** | 🔴 Blocker |

---

### Issue #2: PostgreSQL Timeout During Setup

| | |
|---|---|
| **Symptom** | `Waiting for PostgreSQL... (1 retries left)` followed by `⚠️ PostgreSQL not ready, continuing anyway...` |
| **Cause** | PostgreSQL container took longer to start than the 30-retry limit |
| **Outcome** | Self-resolved - PostgreSQL was ready by the time the app started |
| **Severity** | 🟡 Warning (non-blocking) |

---

### Issue #3: Permission Denied for System Tools

| | |
|---|---|
| **Symptom** | `docker: Permission denied` and `pg_isready: Permission denied` |
| **Cause** | Codespaces container doesn't grant permission to all system binaries by default |
| **Workaround** | Test PostgreSQL via Python instead of `pg_isready` |
| **Severity** | 🟡 Medium |

**Workaround code:**
```bash
uv run python -c "import asyncio; import asyncpg; asyncio.run(asyncpg.connect('postgresql://app:localdev@postgres:5432/imagehost')); print('✅ PostgreSQL is reachable')"
```

---

### Issue #4: Permission Denied for pytest

| | |
|---|---|
| **Symptom** | `error: Failed to spawn: pytest` - `Permission denied (os error 13)` |
| **Cause** | The pytest executable didn't have execute permissions |
| **Fix** | Run pytest as a Python module: `uv run python -m pytest -v` |
| **Severity** | 🔴 Blocker |

---

### Issue #5: Missing Test Dependencies

| | |
|---|---|
| **Symptom** | `/usr/local/bin/python: No module named pytest` |
| **Cause** | pytest wasn't in `pyproject.toml` dependencies |
| **Fix** | `uv add pytest pytest-asyncio pytest-cov --dev` |
| **Severity** | 🔴 Blocker |

---

### Issue #6: Missing aiosqlite for API Tests

| | |
|---|---|
| **Symptom** | `ModuleNotFoundError: No module named 'aiosqlite'` |
| **Cause** | API tests use SQLite for isolation (not PostgreSQL), but async driver wasn't installed |
| **Fix** | `uv add aiosqlite --dev` |
| **Severity** | 🔴 Blocker |

---

## Root Cause Analysis

### Why So Many Dependency Misses?

| Root Cause | Contributing Factor |
|------------|---------------------|
| **1. Local vs Codespaces divergence** | Local environment had packages installed globally that weren't in `pyproject.toml` |
| **2. No CI pipeline yet** | No automated check to catch missing dependencies before merge |
| **3. Incremental development** | Dependencies added piecemeal without systematic tracking |
| **4. Test vs Prod isolation** | Test fixtures use SQLite (aiosqlite) while app uses PostgreSQL (asyncpg) - easy to miss |
| **5. Phase 1.5 Pillow addition** | Pillow was added to code but dependency wasn't committed together |

### Dependency Issues Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 1.5: Added Pillow code                               │
│      ↓                                                      │
│  Forgot to add `pillow` to pyproject.toml                   │
│      ↓                                                      │
│  Worked locally (pillow installed globally)                 │
│      ↓                                                      │
│  Failed in Codespaces (clean environment)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## What Went Well ✅

1. **MinIO integration worked first try** - Strategy pattern paid off
2. **Health checks caught issues** - PostgreSQL retry loop gave time for container startup
3. **Test suite comprehensive** - 31 tests covered all scenarios
4. **Quick fixes** - Each issue was resolved in minutes once identified
5. **Documentation created** - CODESPACES_RUNBOOK.md will prevent future issues

---

## What Needs Improvement 🔧

1. **Dependency tracking** - No automated verification
2. **CI/CD pipeline** - Would catch issues before merge
3. **Codespaces-first testing** - Should test in clean environment before merge
4. **Script permissions** - Use `python -m` pattern by default

---

## Action Items (Preventive Measures)

### Immediate (This Sprint)

| # | Action | Owner | Status |
|---|--------|-------|--------|
| 1 | Update scripts to use `python -m pytest` instead of `pytest` | Done | ✅ |
| 2 | Add dependency checklist to PR template | TODO | ⬜ |
| 3 | Document test database difference (SQLite vs PostgreSQL) | TODO | ⬜ |

### Short-term (Phase 3)

| # | Action | Priority |
|---|--------|----------|
| 1 | **Set up GitHub Actions CI** - Run tests on every PR | 🔴 High |
| 2 | **Add dependency audit step** - Verify all imports have matching deps | 🔴 High |
| 3 | **Codespaces validation gate** - Test in Codespaces before merge | 🟡 Medium |

### Process Improvements

| Practice | Implementation |
|----------|---------------|
| **Import → Dependency → Commit** | When importing a new library, add to `pyproject.toml` in the same commit |
| **Clean environment testing** | Always test in Codespaces or fresh Docker before merging |
| **Dev dependency awareness** | Check `conftest.py` to understand test infrastructure needs |
| **`python -m` by default** | Use `python -m pytest` instead of `pytest` in all scripts |

---

## PR Summary

| Category | Items Added |
|----------|-------------|
| **Dependencies** | pillow, pytest, pytest-asyncio, pytest-cov, aiosqlite |
| **Scripts** | validate-env.sh, run-tests.sh, smoke-test.sh, cleanup-test-data.sh |
| **Docs** | CODESPACES_RUNBOOK.md |
| **Config** | .gitignore update (exclude .claude/settings.local.json) |

---

## Key Takeaways

1. **Dependency hygiene:** Import → Add dependency → Commit together
2. **Codespaces quirks:** Permission issues are common; use Python-based alternatives
3. **Test isolation:** API tests use SQLite (fast, isolated) while the app uses PostgreSQL
4. **Always push:** Codespace data isn't permanent; push changes to protect your work
5. **`python -m` pattern:** Bypasses many executable permission issues
6. **CI is essential:** Manual testing will always miss something; automate it

---

## Metrics

| Metric | Value |
|--------|-------|
| Issues encountered | 6 |
| Blockers | 4 |
| Time to resolve all | ~45 minutes |
| Tests passing | 31/31 |
| Dependencies added | 5 |

---

## Related Documents

- [CODESPACES_RUNBOOK.md](./CODESPACES_RUNBOOK.md) - Testing guide created from learnings
- [TODO.md](../TODO.md) - Technical debt tracking
- [validation-checklist.md](./validation-checklist.md) - Pre-merge validation steps

---

## Next Phase Preview

**Phase 2 (continued):** Redis Caching
- Will apply learnings: add `redis` dependency upfront
- CI pipeline should be priority before more features
