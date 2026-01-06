# Documentation Index

Complete guide to the Image Hosting App documentation.

---

## 📚 Documentation Structure

```
docs/
├── concepts/              # Core concepts and tools
├── learning/              # Learning resources and overviews
├── architecture/          # System design and architecture
├── adr/                   # Architecture Decision Records
├── requirements/          # Phase requirements
├── deployment/            # Deployment guides
└── archive/               # Historical documents
```

---

## 🚀 Getting Started

### New to the Project?

1. **Start here:** [Main README](../README.md)
2. **Project overview:** [CLAUDE.md](../CLAUDE.md)
3. **Testing overview:** [learning/browser-test-overview.md](learning/browser-test-overview.md)

### Understanding the Codebase

1. **Architecture:** [architecture/](architecture/)
2. **Key decisions:** [adr/](adr/)
3. **Requirements:** [requirements/](requirements/)

---

## 📖 Quick Links by Topic

### Browser Testing (NEW!)

| Document | Purpose |
|----------|---------|
| [learning/browser-test-overview.md](learning/browser-test-overview.md) | Visual guide to test architecture |
| [concepts/bun-and-playwright.md](concepts/bun-and-playwright.md) | How and where to use Bun/Playwright |
| [../browser-tests/README.md](../browser-tests/README.md) | Browser test suite documentation |
| [../browser-tests/CI_CD_INTEGRATION.md](../browser-tests/CI_CD_INTEGRATION.md) | CI/CD setup and usage |
| [../browser-tests/ARCHITECTURE_DECISION.md](../browser-tests/ARCHITECTURE_DECISION.md) | Why tests are structured this way |

### Concepts

| Document | Purpose |
|----------|---------|
| [concepts/bun-and-playwright.md](concepts/bun-and-playwright.md) | Bun and Playwright usage guide |

### Learning Resources

| Document | Purpose |
|----------|---------|
| [learning/LEARNINGS.md](learning/LEARNINGS.md) | Historical learnings and insights |
| [learning/browser-test-overview.md](learning/browser-test-overview.md) | Browser testing explained visually |

### Architecture

| Document | Purpose |
|----------|---------|
| [architecture/](architecture/) | System design documents |
| [adr/](adr/) | Architecture Decision Records (ADR-0001 to ADR-0014) |

### Deployment

| Document | Purpose |
|----------|---------|
| [deployment/](deployment/) | Deployment guides and strategies |
| [CODESPACES_RUNBOOK.md](CODESPACES_RUNBOOK.md) | GitHub Codespaces setup |
| [PHASE3_UI_RUNBOOK.md](PHASE3_UI_RUNBOOK.md) | Phase 3 UI deployment |

### Testing

| Document | Purpose |
|----------|---------|
| [testing/](testing/) | Testing strategies and guides |
| [PHASE1_TESTING.md](PHASE1_TESTING.md) | Phase 1 testing documentation |
| [learning/browser-test-overview.md](learning/browser-test-overview.md) | Browser testing overview |

### Historical

| Document | Purpose |
|----------|---------|
| [PHASE2_RETRO.md](PHASE2_RETRO.md) | Phase 2 retrospective |
| [changelog.md](changelog.md) | Project changelog |
| [validation-checklist.md](validation-checklist.md) | Validation procedures |

---

## 🎯 Common Scenarios

### "I want to understand the testing strategy"

1. Read: [learning/browser-test-overview.md](learning/browser-test-overview.md)
2. Understand tools: [concepts/bun-and-playwright.md](concepts/bun-and-playwright.md)
3. See CI/CD: [../browser-tests/CI_CD_INTEGRATION.md](../browser-tests/CI_CD_INTEGRATION.md)
4. Review ADRs: [adr/0014-test-dependency-container.md](adr/0014-test-dependency-container.md)

### "I want to add a new feature"

1. Check requirements: [requirements/](requirements/)
2. Review architecture: [architecture/](architecture/)
3. Check ADRs: [adr/](adr/)
4. Write tests: [learning/browser-test-overview.md](learning/browser-test-overview.md)

### "I want to deploy the app"

1. Review strategy: [deployment/](deployment/)
2. Check runbooks: [PHASE3_UI_RUNBOOK.md](PHASE3_UI_RUNBOOK.md)
3. Setup CI/CD: [../browser-tests/CI_CD_INTEGRATION.md](../browser-tests/CI_CD_INTEGRATION.md)
4. Verify: [validation-checklist.md](validation-checklist.md)

### "I'm confused about test locations"

Read: [learning/browser-test-overview.md](learning/browser-test-overview.md)

**TL;DR:**
- `backend/tests/` = Python tests (inside code)
- `browser-tests/` = E2E tests (outside via HTTP)

### "When should I use Bun vs Python?"

Read: [concepts/bun-and-playwright.md](concepts/bun-and-playwright.md)

**TL;DR:**
- Python/pytest = Backend code tests
- Bun/Playwright = Browser UI tests

---

## 📂 Directory Details

### concepts/

Core technical concepts and tool usage guides.

**Files:**
- `bun-and-playwright.md` - How and where to use Bun and Playwright

### learning/

Learning resources, overviews, and educational content.

**Files:**
- `LEARNINGS.md` - Historical learnings
- `browser-test-overview.md` - Visual guide to testing architecture

### architecture/

System design documents and architectural diagrams.

**Topics:**
- System architecture
- Database design
- Storage patterns
- Service abstractions

### adr/

Architecture Decision Records - why we made specific technical choices.

**Notable ADRs:**
- ADR-0001 through ADR-0014
- ADR-0014: Test Dependency Container
- ADR-0011: User Authentication with JWT
- ADR-0010: Concurrency Control

### requirements/

Functional and non-functional requirements for each phase.

**Files:**
- Phase 1, 1.5, 2, 3, 4 requirements

### deployment/

Deployment guides, strategies, and runbooks.

**Topics:**
- Production deployment
- Docker setup
- GitHub Actions workflows
- Disaster recovery

---

## 🔍 Finding Documentation

### By File Type

```bash
# All markdown files
find docs -name "*.md"

# ADRs
ls docs/adr/

# Phase requirements
ls docs/requirements/

# Deployment docs
ls docs/deployment/
```

### By Topic

Use the Quick Links section above or:

```bash
# Search all documentation
grep -r "topic" docs/

# Search specific folder
grep -r "topic" docs/concepts/
```

---

## ✅ Documentation Standards

### When to Create New Docs

**Create in `concepts/`:**
- Explaining core technologies (Bun, Playwright, Redis, etc.)
- Tool usage guides
- Core patterns and practices

**Create in `learning/`:**
- Visual guides and overviews
- Educational content
- "How things work" explanations

**Create in `adr/`:**
- Significant technical decisions
- Architecture changes
- Technology choices

**Create in `deployment/`:**
- Deployment procedures
- Runbooks
- Operations guides

### Documentation Format

```markdown
# Title

**Purpose:** One-sentence description
**Date:** YYYY-MM-DD
**Status:** Active/Archived

---

## Quick Summary

TL;DR section

---

## Main Content

Detailed content with:
- Visual diagrams
- Code examples
- Clear headings
- Tables for comparisons

---

## Related Documentation

Links to other relevant docs
```

---

## 🔄 Keeping Docs Updated

### When to Update

- After architectural changes
- After adding new features
- After significant refactors
- When ADRs are created
- After phase completions

### What to Update

1. This index (docs/README.md)
2. Related concept docs
3. Relevant learning guides
4. ADRs if decisions change
5. Main project README

---

## 📊 Documentation Statistics

**Total documentation files:** ~50+
**ADRs:** 14
**Concepts:** 1
**Learning guides:** 2
**Deployment docs:** ~10
**Architecture docs:** ~10

---

## 🆕 Recent Additions (2026-01-05)

- ✅ `concepts/bun-and-playwright.md` - Bun and Playwright usage guide
- ✅ `learning/browser-test-overview.md` - Visual testing architecture guide
- ✅ `../browser-tests/CI_CD_INTEGRATION.md` - Complete CI/CD guide
- ✅ `../browser-tests/ARCHITECTURE_DECISION.md` - Testing architecture decisions
- ✅ `../browser-tests/TESTING_LAYERS.md` - Visual testing layers guide

---

## 💡 Tips

1. **Start with the overview:** Read `learning/browser-test-overview.md` for big picture
2. **Dive into concepts:** Use `concepts/` to understand tools
3. **Check ADRs:** Understand "why" decisions were made
4. **Follow runbooks:** For deployment and operations
5. **Update as you go:** Keep docs current with code changes

---

## 🤝 Contributing to Docs

When adding documentation:

1. Choose the right folder (concepts, learning, adr, etc.)
2. Follow the documentation format
3. Add entry to this index
4. Link to related documentation
5. Update main README if significant

---

## Questions?

- Check [Main README](../README.md)
- Review [CLAUDE.md](../CLAUDE.md)
- Search existing docs
- Create an ADR if making architectural decisions

---

**Last Updated:** 2026-01-05
