# Browser Tests - Installation Verification

**8-point mandatory verification checklist**

All checks must pass before the browser test suite is considered installed.

---

## Prerequisites

Before running verification:
1. Your Image Hosting App backend must be running
2. Access the app at `http://localhost:8000` (or your configured URL)

---

## Verification Steps

### 1. Directory Structure

```bash
cd /path/to/image-hosting-app/browser-tests
ls -la
```

**Expected output:**
```
drwxr-xr-x  src/
drwxr-xr-x  tools/
drwxr-xr-x  workflows/
drwxr-xr-x  examples/
-rw-r--r--  package.json
-rw-r--r--  README.md
-rw-r--r--  VERIFY.md
```

✅ **PASS:** All directories and files exist
❌ **FAIL:** Missing directories or files

---

### 2. Core Files Present

```bash
ls -la src/ tools/ examples/
```

**Expected files:**
```
src/browser.ts
tools/gallery-test.ts
examples/smoke-test.ts
examples/comprehensive-test.ts
examples/screenshot-all.ts
workflows/auth-flow.md
workflows/gallery-flow.md
```

✅ **PASS:** All core files exist
❌ **FAIL:** Missing files

---

### 3. Bun Runtime Installed

```bash
bun --version
```

**Expected output:**
```
1.x.x (or higher)
```

✅ **PASS:** Bun is installed
❌ **FAIL:** Command not found

**If failed, install Bun:**
```bash
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc  # or ~/.zshrc
```

---

### 4. Dependencies Installed

```bash
cd /path/to/image-hosting-app/browser-tests
bun install
```

**Expected output:**
```
bun install v1.x.x
+ playwright@x.x.x
✓ installed
```

Then verify:
```bash
ls -la node_modules/playwright
```

✅ **PASS:** Playwright installed in node_modules
❌ **FAIL:** No node_modules or missing playwright

---

### 5. Playwright Browsers Installed

```bash
bunx playwright install chromium
```

**Expected output:**
```
Downloading Chromium x.x.x ...
✅ Success! Chromium downloaded
```

Verify installation:
```bash
bunx playwright --version
```

✅ **PASS:** Playwright browsers installed
❌ **FAIL:** Browser installation failed

---

### 6. TypeScript Import Works

```bash
cd /path/to/image-hosting-app/browser-tests
bun run -e "import { PlaywrightBrowser } from './src/browser'; console.log('✅ Import successful')"
```

**Expected output:**
```
✅ Import successful
```

✅ **PASS:** Can import PlaywrightBrowser
❌ **FAIL:** Import error

---

### 7. App is Running

```bash
curl -s http://localhost:8000/health
```

**Expected output:**
```json
{"status":"healthy"} (or similar)
```

✅ **PASS:** App is accessible
❌ **FAIL:** Connection refused

**If failed, start your app:**
```bash
cd /path/to/image-hosting-app/backend
uv run uvicorn app.main:app --reload
```

---

### 8. CLI Tool Test

```bash
cd /path/to/image-hosting-app/browser-tests
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

Exit code: `0`

✅ **PASS:** CLI tool executed successfully
❌ **FAIL:** Error or exit code 1

---

## Verification Summary

After completing all 8 checks:

```
✅ 1. Directory structure exists
✅ 2. Core files present
✅ 3. Bun runtime installed
✅ 4. Dependencies installed
✅ 5. Playwright browsers installed
✅ 6. TypeScript import works
✅ 7. App is running
✅ 8. CLI tool test passes
```

**All 8 checks must pass for installation to be considered complete.**

---

## Quick Verification Script

Run all checks automatically:

```bash
#!/bin/bash
cd /path/to/image-hosting-app/browser-tests

echo "1. Checking directory structure..."
[ -d "src" ] && [ -d "tools" ] && echo "✅ PASS" || echo "❌ FAIL"

echo "2. Checking core files..."
[ -f "src/browser.ts" ] && echo "✅ PASS" || echo "❌ FAIL"

echo "3. Checking Bun installation..."
bun --version > /dev/null 2>&1 && echo "✅ PASS" || echo "❌ FAIL"

echo "4. Checking dependencies..."
[ -d "node_modules/playwright" ] && echo "✅ PASS" || echo "❌ FAIL"

echo "5. Checking Playwright browsers..."
bunx playwright --version > /dev/null 2>&1 && echo "✅ PASS" || echo "❌ FAIL"

echo "6. Checking TypeScript import..."
bun run -e "import { PlaywrightBrowser } from './src/browser'" > /dev/null 2>&1 && echo "✅ PASS" || echo "❌ FAIL"

echo "7. Checking app is running..."
curl -s http://localhost:8000/health > /dev/null && echo "✅ PASS" || echo "❌ FAIL"

echo "8. Running CLI tool test..."
bun run tools/gallery-test.ts verify-home http://localhost:8000 > /dev/null 2>&1 && echo "✅ PASS" || echo "❌ FAIL"
```

---

## Troubleshooting

### Bun not found
```bash
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc
```

### Playwright browsers not installed
```bash
bunx playwright install chromium
```

### App not running
```bash
cd ../backend
uv run uvicorn app.main:app --reload
```

### Import errors
```bash
rm -rf node_modules
bun install
```

---

## Next Steps

Once all checks pass:

1. ✅ Run smoke tests: `bun run examples/smoke-test.ts`
2. ✅ Run comprehensive tests: `bun run examples/comprehensive-test.ts`
3. ✅ Generate screenshots: `bun run examples/screenshot-all.ts`
4. ✅ Integrate with CI/CD (see README.md)

---

**Installation is complete when all 8 verification points pass.**
