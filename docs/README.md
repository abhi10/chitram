# Documentation Index

## Sources of Truth

| Document | Purpose |
|----------|---------|
| [README.md](../README.md) | What is this, how to run it |
| [CLAUDE.md](../CLAUDE.md) | Developer guide, patterns, commands |
| [TODO.md](../TODO.md) | Progress tracking, what's done/next |

---

## Active Documentation

```
docs/
├── adr/                   # Architecture Decision Records (immutable)
├── deployment/            # Production deployment guides
├── learning/              # Reference guides and learnings
├── retrospectives/        # Incident retrospectives
├── future/                # PRDs for unimplemented features
└── archive/               # Historical docs (completed phases)
```

### ADRs (Architecture Decision Records)

Immutable records of technical decisions. **15 ADRs** covering:
- ADR-0001: FastAPI framework
- ADR-0011: JWT authentication
- ADR-0012: Background tasks strategy
- ADR-0013: HTMX for web UI
- ADR-0014: Test dependency container

[View all ADRs →](adr/)

### Deployment

Production operations and deployment guides:
- [POST_DEPLOY_CHECKLIST.md](deployment/POST_DEPLOY_CHECKLIST.md) - Verification after deploy
- [DEPLOYMENT_STRATEGY.md](deployment/DEPLOYMENT_STRATEGY.md) - Overall strategy
- [DROPLET_SETUP.md](deployment/DROPLET_SETUP.md) - Server setup

[View all deployment docs →](deployment/)

### Learning

Reference guides and learnings:
- [supabase-integration-learnings.md](learning/supabase-integration-learnings.md) - Supabase patterns
- [browser-test-overview.md](learning/browser-test-overview.md) - E2E testing guide

### Retrospectives

Incident post-mortems:
- [2026-01-08-supabase-nav-auth-bug.md](retrospectives/2026-01-08-supabase-nav-auth-bug.md)

### Future Features

PRDs for planned features:
- [PRD-pluggable-auth-system.md](future/PRD-pluggable-auth-system.md) - Auth extensions
- [PRD-search-and-ai-tagging.md](future/PRD-search-and-ai-tagging.md) - Search & AI

---

## Archive

Historical documentation for completed work. Preserved for reference but no longer maintained.

```
archive/
├── requirements/          # Phase 1-3 requirements (now in TODO.md)
├── runbooks/              # One-time setup guides
├── design/                # Implemented design docs
└── (legacy files)         # Original MVP design doc, etc.
```

---

## When to Create Docs

| Type | Location | When |
|------|----------|------|
| Decision | `adr/` | Architectural choice made |
| Ops guide | `deployment/` | Production procedure |
| Incident | `retrospectives/` | After production issue |
| Future PRD | `future/` | Planning unbuilt feature |

**Don't create:**
- Phase requirements (use TODO.md)
- One-time runbooks (archive after use)
- Code documentation (use docstrings)

---

**Last Updated:** 2026-01-08
