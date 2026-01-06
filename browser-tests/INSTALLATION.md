# Browser Tests - Installation Guide

Quick start guide to get the browser test suite running.

---

## Prerequisites

- Your Image Hosting App backend running
- Terminal access

---

## Method 1: Automated Setup (Recommended)

```bash
cd /path/to/image-hosting-app/browser-tests
./setup.sh
```

The script will:
1. Check/install Bun
2. Install npm dependencies
3. Install Playwright browsers
4. Create necessary directories
5. Verify setup

---

## Method 2: Manual Setup

### Step 1: Install Bun

```bash
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc  # or ~/.zshrc
```

Verify:
```bash
bun --version
```

### Step 2: Install Dependencies

```bash
cd /path/to/image-hosting-app/browser-tests
bun install
```

### Step 3: Install Playwright Browsers

```bash
bunx playwright install chromium
```

### Step 4: Verify Setup

Run the verification checklist:

```bash
# See VERIFY.md for full checklist

# Quick test:
bun run tools/gallery-test.ts verify-home
```

---

## Usage After Installation

### Start Your App

```bash
# In one terminal
cd ../backend
uv run uvicorn app.main:app --reload
```

### Run Tests

```bash
# In another terminal
cd browser-tests

# Quick verification
bun run tools/gallery-test.ts verify-home

# Smoke tests
bun run examples/smoke-test.ts

# Comprehensive tests
bun run examples/comprehensive-test.ts

# Visual regression
bun run examples/screenshot-all.ts
```

---

## Troubleshooting

### "bun: command not found"

Install Bun:
```bash
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc
```

### "Executable doesn't exist at ..."

Install Playwright browsers:
```bash
bunx playwright install chromium
```

### "Connection refused"

Make sure your app is running:
```bash
cd ../backend
uv run uvicorn app.main:app --reload

# Verify it's accessible
curl http://localhost:8000/health
```

---

## Verification Checklist

After installation, verify everything works with these 8 mandatory checks:

### 1. ✅ Directory Structure

```bash
ls -la
# Should see: src/, tools/, workflows/, examples/, package.json
```

### 2. ✅ Core Files Present

```bash
ls -la src/ tools/ examples/
# Should see: browser.ts, gallery-test.ts, smoke-test.ts, etc.
```

### 3. ✅ Bun Runtime Installed

```bash
bun --version
# Should output: 1.x.x or higher
```

### 4. ✅ Dependencies Installed

```bash
ls -la node_modules/playwright
# Should exist with Playwright files
```

### 5. ✅ Playwright Browsers Installed

```bash
bunx playwright --version
# Should output version number
```

### 6. ✅ TypeScript Import Works

```bash
bun run -e "import { PlaywrightBrowser } from './src/browser'; console.log('✅ Import successful')"
# Should output: ✅ Import successful
```

### 7. ✅ App is Running

```bash
curl -s http://localhost:8000/health
# Should return: {"status":"healthy"} or similar
```

### 8. ✅ CLI Tool Test

```bash
bun run tools/gallery-test.ts verify-home http://localhost:8000
```

**Expected output:**
```
🏠 Verifying Home Page...
✅ Page loaded in XXXms
✅ Navigation bar found
✅ Gallery grid found
🎉 Home page verification passed!
```

---

## Quick Verification Script

Run all checks automatically:

```bash
#!/bin/bash
echo "1. Directory structure..." && [ -d "src" ] && [ -d "tools" ] && echo "✅ PASS" || echo "❌ FAIL"
echo "2. Core files..." && [ -f "src/browser.ts" ] && echo "✅ PASS" || echo "❌ FAIL"
echo "3. Bun runtime..." && bun --version > /dev/null 2>&1 && echo "✅ PASS" || echo "❌ FAIL"
echo "4. Dependencies..." && [ -d "node_modules/playwright" ] && echo "✅ PASS" || echo "❌ FAIL"
echo "5. Playwright browsers..." && bunx playwright --version > /dev/null 2>&1 && echo "✅ PASS" || echo "❌ FAIL"
echo "6. TypeScript import..." && bun run -e "import { PlaywrightBrowser } from './src/browser'" > /dev/null 2>&1 && echo "✅ PASS" || echo "❌ FAIL"
echo "7. App running..." && curl -s http://localhost:8000/health > /dev/null && echo "✅ PASS" || echo "❌ FAIL"
echo "8. CLI tool test..." && bun run tools/gallery-test.ts verify-home http://localhost:8000 > /dev/null 2>&1 && echo "✅ PASS" || echo "❌ FAIL"
```

**All 8 checks must pass for installation to be considered complete.**

---

## Next Steps

Once all checks pass:

1. ✅ Run smoke tests: `bun run examples/smoke-test.ts`
2. ✅ Run comprehensive tests: `bun run examples/comprehensive-test.ts`
3. ✅ Generate screenshots: `bun run examples/screenshot-all.ts`
4. ✅ Integrate with CI/CD (see [CI_CD_INTEGRATION.md](./CI_CD_INTEGRATION.md))
5. ✅ Read [README.md](./README.md) for full usage guide

---

**Installation complete! 🎉**
