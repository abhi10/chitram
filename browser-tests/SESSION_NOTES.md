# Browser Tests Setup - Session Notes

**Date:** 2026-01-05
**Context:** Setting up UI automation testing for Image Hosting App using kai-browser-skill pattern

---

## What Was Accomplished

Successfully created a complete browser test suite following the **kai-browser-skill pattern** (code-first, 99% token savings vs traditional MCP).

### Files Created (12 total)

```
browser-tests/
├── src/
│   └── browser.ts                    # PlaywrightBrowser class (core automation engine)
│
├── tools/
│   └── gallery-test.ts               # CLI tool with 5 commands:
│                                     #   verify-home, verify-login, verify-upload,
│                                     #   verify-register, screenshot
│
├── workflows/
│   ├── auth-flow.md                  # Authentication flow test (register/login/logout)
│   └── gallery-flow.md               # Gallery browsing flow (browse/view/download)
│
├── examples/
│   ├── smoke-test.ts                 # Quick health check (6 tests)
│   ├── comprehensive-test.ts         # Full test suite (40+ tests, 9 categories)
│   └── screenshot-all.ts             # Visual regression (36 screenshots)
│
├── package.json                      # Dependencies: playwright@1.57.0, typescript@5.9.3
├── README.md                         # Complete usage guide (300+ lines)
├── INSTALLATION.md                   # Step-by-step installation guide
├── VERIFY.md                         # 8-point verification checklist
├── .gitignore                        # Ignores node_modules, screenshots, etc.
├── setup.sh                          # Automated installation script
└── SESSION_NOTES.md                  # This file
```

---

## Installation Status

### ✅ Completed Steps

1. **Directory structure created** - All directories exist
2. **All source files created** - 12 files with complete implementations
3. **Bun runtime installed** - Version 1.3.5 at `~/.bun/bin/bun`
4. **Dependencies installed** - playwright, typescript, @types/bun
5. **Playwright browsers installed** - Chromium downloaded (~250MB)
6. **Screenshot directories created** - Ready for test output
7. **Scripts made executable** - setup.sh, gallery-test.ts, examples/*.ts

### ⏳ Pending Steps

1. **Start backend app** - Image Hosting App needs to be running
2. **Run first test** - Verify installation works
3. **Test all CLI commands** - Ensure all 5 commands work
4. **Generate baseline screenshots** - For visual regression

---

## Current Installation State

### Bun Location
```bash
~/.bun/bin/bun --version  # 1.3.5
```

**Note:** Bun was installed but not yet in PATH. Use full path `~/.bun/bin/bun` or add to PATH:
```bash
export PATH="$HOME/.bun/bin:$PATH"  # Add to ~/.zshrc or ~/.bashrc
```

### Dependencies Installed
```
node_modules/
├── playwright@1.57.0
├── typescript@5.9.3
└── @types/bun@1.3.5
```

### Playwright Browser Cache
```
~/Library/Caches/ms-playwright/
├── chromium-1200/
├── chromium_headless_shell-1200/
└── ffmpeg-1011/
```

---

## Backend App Context

**Your app uses:**
- **Runtime:** uv (Python package manager)
- **Framework:** FastAPI
- **Container:** Docker (via docker-compose)
- **Database:** PostgreSQL
- **Storage:** MinIO (S3-compatible)
- **Cache:** Redis (optional)

**Start command:**
```bash
cd /path/to/image-hosting-app/backend
uv run uvicorn app.main:app --reload --host 0.0.0.0
```

**Or with Docker:**
```bash
cd /path/to/image-hosting-app
docker-compose -f docker-compose.prod.yml up
```

**Default URL:** http://localhost:8000

---

## Next Steps (In Order)

### 1. Start Your Backend App

Choose one method:

**Option A: Using uv (development)**
```bash
cd /path/to/image-hosting-app/backend
uv run uvicorn app.main:app --reload --host 0.0.0.0
```

**Option B: Using Docker**
```bash
cd /path/to/image-hosting-app
docker-compose -f docker-compose.prod.yml up
# or
docker-compose -f .devcontainer/docker-compose.yml up
```

**Verify app is running:**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"} or similar
```

### 2. Run First Test

```bash
cd /path/to/image-hosting-app/browser-tests

# Add Bun to PATH (if not already)
export PATH="$HOME/.bun/bin:$PATH"

# Run verification
bun run tools/gallery-test.ts verify-home http://localhost:8000
```

**Expected output:**
```
🏠 Verifying Home Page...

✅ Page loaded in XXXms
📄 Title: "..."
✅ Navigation bar found
✅ Gallery grid found
✅ Upload link found
✅ Footer found

✅ No console errors

🎉 Home page verification passed!
```

### 3. Run All CLI Commands

```bash
# Test each command
bun run tools/gallery-test.ts verify-home
bun run tools/gallery-test.ts verify-login
bun run tools/gallery-test.ts verify-upload
bun run tools/gallery-test.ts verify-register

# Take screenshot
bun run tools/gallery-test.ts screenshot http://localhost:8000 screenshots/test.png
```

### 4. Run Test Suites

```bash
# Smoke test (quick)
bun run examples/smoke-test.ts

# Comprehensive test (detailed)
bun run examples/comprehensive-test.ts

# Visual regression (all screenshots)
bun run examples/screenshot-all.ts
```

### 5. Review Results

Check generated screenshots:
```bash
ls -la screenshots/
ls -la screenshots/comprehensive/
ls -la screenshots/visual-regression/
```

---

## Troubleshooting Guide

### Issue: "bun: command not found"

**Solution:**
```bash
# Use full path
~/.bun/bin/bun run tools/gallery-test.ts verify-home

# OR add to PATH permanently
echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Issue: "Cannot connect to localhost:8000"

**Solution:**
```bash
# Check if app is running
curl http://localhost:8000/health

# If not, start the app
cd ../backend
uv run uvicorn app.main:app --reload
```

### Issue: "Selector not found"

**Cause:** Your HTML might use different CSS classes than expected.

**Solution:** Update selectors in:
- `tools/gallery-test.ts`
- `examples/*.ts`

Common selectors to check:
- `.gallery-grid` → Your gallery container class
- `.gallery-item` or `.image-card` → Individual image cards
- `input[type="email"]` → Email input fields
- `button[type="submit"]` → Submit buttons

### Issue: Playwright browser errors

**Solution:**
```bash
# Reinstall browsers
~/.bun/bin/bunx playwright install chromium
```

---

## HTML Selectors Used

The tests assume your templates use these selectors (update if different):

| Element | Selector | Location |
|---------|----------|----------|
| Navigation bar | `nav` | All pages |
| Gallery grid | `.gallery-grid` | Home page |
| Gallery item | `.gallery-item` or `.image-card` | Home page |
| Upload link | `a[href="/upload"]` | Navigation |
| Footer | `footer` | All pages |
| Email input | `input[type="email"]` | Login, Register |
| Password input | `input[type="password"]` | Login, Register |
| Submit button | `button[type="submit"]` | Forms |
| Register link | `a[href="/register"]` | Login page |
| Login link | `a[href="/login"]` | Register page |

**Check your actual selectors:**
```bash
# View your template files
cd /path/to/image-hosting-app/backend/app/templates
cat home.html | grep -E "class=|id="
cat login.html | grep -E "class=|id="
```

---

## Cost Savings

Using this pattern vs traditional Playwright MCP:

| Usage | Traditional MCP | kai-browser CLI | Savings |
|-------|-----------------|-----------------|---------|
| 10 tests/day × 30 days | ~4.2M tokens ($60-90) | 0 tokens ($0) | **$60-90/month** |
| 100 tests/day (CI/CD) | ~42M tokens ($600-900) | 0 tokens ($0) | **$600-900/month** |

**How?** Pre-written code execution instead of AI-generated scripts.

---

## Key Concepts

### The Three-Tier Strategy

1. **Tier 1: CLI Tools (90%)** - One-command checks
2. **Tier 2: Workflows (8%)** - Multi-step scenarios
3. **Tier 3: Test Suites (2%)** - Comprehensive testing

### Exit Codes (CI/CD Ready)

All tools return proper exit codes:
- `0` = Success ✅
- `1` = Failure ❌

Perfect for CI/CD pipelines.

### Zero Token Cost

Unlike MCP approaches:
- No tools loaded into context (13,700 tokens saved)
- No AI-generated code (200+ tokens per operation saved)
- Just executes pre-written TypeScript

---

## Documentation Files

1. **README.md** (300+ lines)
   - Complete usage guide
   - API reference
   - CI/CD integration examples
   - Customization guide

2. **INSTALLATION.md**
   - Step-by-step setup
   - Prerequisites
   - Verification steps

3. **VERIFY.md**
   - 8-point verification checklist
   - Each step must pass
   - Automated verification script

4. **workflows/*.md**
   - Pre-written test scenarios
   - Copy-paste ready TypeScript code
   - Covers common user journeys

---

## CI/CD Integration (Future)

Example GitHub Actions workflow:

```yaml
# .github/workflows/ui-tests.yml
name: UI Tests

on: [push, pull_request]

jobs:
  ui-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Bun
        uses: oven-sh/setup-bun@v1

      - name: Install dependencies
        run: cd browser-tests && bun install

      - name: Install Playwright
        run: cd browser-tests && bunx playwright install chromium --with-deps

      - name: Start app
        run: |
          cd backend
          uv run uvicorn app.main:app --host 0.0.0.0 &
          sleep 5

      - name: Run smoke tests
        run: cd browser-tests && bun run examples/smoke-test.ts

      - name: Upload screenshots
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: screenshots
          path: browser-tests/screenshots/
```

---

## Questions to Answer in Next Session

1. **Are the HTML selectors correct?**
   - Check if `.gallery-grid`, `.gallery-item` match your templates
   - Update `tools/gallery-test.ts` if needed

2. **Do you want to add more test scenarios?**
   - Image upload flow?
   - Image deletion?
   - User dashboard?
   - Profile management?

3. **Ready for CI/CD integration?**
   - Should we add GitHub Actions workflow?
   - Any other CI system (GitLab, CircleCI)?

4. **Visual regression setup?**
   - Want to integrate with Percy.io or similar?
   - Set up pixelmatch for local comparisons?

---

## Quick Reference Commands

### Add Bun to PATH
```bash
echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Start Backend (choose one)
```bash
# uv
cd backend && uv run uvicorn app.main:app --reload

# Docker
docker-compose up
```

### Run Tests
```bash
cd browser-tests

# Single test
bun run tools/gallery-test.ts verify-home

# Smoke test
bun run examples/smoke-test.ts

# Full test
bun run examples/comprehensive-test.ts

# Screenshots
bun run examples/screenshot-all.ts
```

### View Results
```bash
# Check screenshots
open screenshots/

# Check comprehensive test screenshots
open screenshots/comprehensive/

# Check visual regression screenshots
open screenshots/visual-regression/
```

---

## Important Notes for Next Claude Session

1. **All files are created and ready** - No need to recreate anything
2. **Installation is 95% complete** - Just need to run tests
3. **Backend must be running** - Tests need localhost:8000 accessible
4. **Bun is installed** - Use `~/.bun/bin/bun` or add to PATH
5. **Documentation is comprehensive** - Read README.md for full details
6. **Selectors may need adjustment** - Based on actual HTML structure

---

## Resume Point

**Status:** Installation complete, ready for first test run

**Next action:**
```bash
# 1. Start backend
cd /path/to/image-hosting-app/backend
uv run uvicorn app.main:app --reload

# 2. In another terminal, run first test
cd /path/to/image-hosting-app/browser-tests
~/.bun/bin/bun run tools/gallery-test.ts verify-home
```

**If test passes:** ✅ Installation successful! Proceed with running other tests.

**If test fails:** Check selectors in `tools/gallery-test.ts` match your actual HTML.

---

## Contact Information for New Session

**Tell the new Claude instance:**

> "I have a browser-tests directory with kai-browser-skill pattern tests for my Image Hosting App. The installation is complete (Bun, Playwright, all files created). I need to:
> 1. Start my FastAPI backend (using uv or Docker)
> 2. Run the first test to verify everything works
> 3. Adjust HTML selectors if needed
>
> Please read browser-tests/SESSION_NOTES.md for full context."

---

**End of Session Notes**
