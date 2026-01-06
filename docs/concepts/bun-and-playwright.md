# Bun and Playwright - Usage Guide

**Purpose:** Understanding when, where, and how to use Bun and Playwright in this project

**Date:** 2026-01-05
**Status:** Active

---

## Quick Reference

| Tool | Purpose | Where Used | When to Use |
|------|---------|------------|-------------|
| **Bun** | Fast JavaScript/TypeScript runtime | `browser-tests/` | Running E2E tests, TypeScript scripts |
| **Playwright** | Browser automation library | `browser-tests/` | Testing web UI, user workflows |

---

## What is Bun?

**Bun** is a fast all-in-one JavaScript/TypeScript runtime and package manager.

### Key Features

- ⚡ **Fast** - 3-4x faster than Node.js
- 🦝 **All-in-one** - Runtime + package manager + test runner
- 📦 **Drop-in replacement** - Works with npm packages
- 🔧 **TypeScript native** - No transpilation needed

### Why We Use Bun (Instead of Node.js)

```
Traditional:                  Bun:
Node.js (runtime)            Bun (all-in-one)
+ npm (package manager)      ✅ Built-in
+ ts-node (TypeScript)       ✅ Built-in
+ jest (testing)             ✅ Built-in
= Slow startup               = Fast startup
```

**Benefits:**
- ✅ Faster test execution (~3x faster than Node)
- ✅ Simpler setup (one tool instead of four)
- ✅ Native TypeScript support
- ✅ npm package compatibility

---

## What is Playwright?

**Playwright** is a browser automation library for testing web applications.

### Key Features

- 🌐 **Multi-browser** - Chrome, Firefox, Safari
- 🎯 **Auto-wait** - Smart waiting for elements
- 📸 **Screenshots** - Visual debugging
- 🔄 **Cross-platform** - Windows, Mac, Linux

### Why We Use Playwright (Instead of Selenium/Puppeteer)

| Feature | Selenium | Puppeteer | Playwright |
|---------|----------|-----------|------------|
| Speed | Slow | Fast | Fast |
| Auto-wait | ❌ | Limited | ✅ |
| Multiple browsers | ✅ | Chrome only | ✅ |
| TypeScript support | ⚠️ | ✅ | ✅ |
| Modern API | ❌ | ✅ | ✅ |

**Why Playwright wins:**
- Auto-waits for elements (no manual waits)
- Better debugging (screenshots, traces)
- Modern async/await API
- Active development by Microsoft

---

## Where They Live in the Project

### Directory Structure

```
image-hosting-app/
│
├── backend/                    ← Python/uv (NO Bun/Playwright)
│   ├── app/
│   ├── tests/                  ← pytest (Python tests)
│   └── pyproject.toml
│
├── browser-tests/              ← Bun + Playwright (ONLY here)
│   ├── src/
│   │   └── browser.ts          ← Playwright wrapper class
│   ├── tools/
│   │   └── gallery-test.ts     ← CLI tools (run with Bun)
│   ├── examples/
│   │   ├── smoke-test.ts       ← Test suites (run with Bun)
│   │   └── comprehensive-test.ts
│   ├── package.json            ← Bun dependencies
│   └── bun.lock                ← Bun lockfile
│
└── .github/workflows/
    └── ui-tests.yml            ← GitHub Actions uses Bun
```

**Golden rule:** Bun and Playwright **only** in `browser-tests/`, never in `backend/`

---

## How to Use Bun

### Installation

```bash
# Install Bun (one-time)
curl -fsSL https://bun.sh/install | bash

# Verify installation
bun --version
# Output: 1.x.x
```

### Package Management

```bash
# Install dependencies (like npm install)
cd browser-tests
bun install

# Add a package (like npm install package)
bun add playwright

# Add dev dependency
bun add --dev typescript

# Remove a package
bun remove package-name
```

### Running Scripts

```bash
# Run a TypeScript file directly
bun run tools/gallery-test.ts

# Run with arguments
bun run tools/gallery-test.ts verify-home https://chitram.io

# Run script from package.json
bun run test
```

### REPL (Interactive Shell)

```bash
# Start Bun REPL
bun repl

# Try TypeScript
> const name: string = "Chitram"
> console.log(name.toUpperCase())
CHITRAM
```

---

## How to Use Playwright

### Our Wrapper Class

We created a `PlaywrightBrowser` class to simplify Playwright usage:

```typescript
// browser-tests/src/browser.ts
export class PlaywrightBrowser {
  private browser: Browser | null = null
  private page: Page | null = null

  // Navigation
  async launch(options?: LaunchOptions)
  async navigate(url: string)
  async close()

  // Interaction
  async click(selector: string)
  async fill(selector: string, value: string)
  async type(selector: string, text: string, options?)

  // Waiting
  async waitForSelector(selector: string, options?)
  async wait(ms: number)

  // Information
  async getTitle(): Promise<string>
  async getVisibleText(selector: string)

  // Screenshots
  async screenshot(options: ScreenshotOptions)
}
```

### Basic Usage

```typescript
#!/usr/bin/env bun
import { PlaywrightBrowser } from '../src/browser'

async function main() {
  const browser = new PlaywrightBrowser()

  try {
    // Launch browser
    await browser.launch({ headless: true })

    // Navigate to page
    await browser.navigate('https://chitram.io')

    // Interact with elements
    await browser.click('a[href="/login"]')
    await browser.fill('input[type="email"]', 'user@example.com')
    await browser.fill('input[type="password"]', 'password123')
    await browser.click('button[type="submit"]')

    // Wait for navigation
    await browser.waitForSelector('.dashboard')

    // Take screenshot
    await browser.screenshot({ path: 'dashboard.png' })

    console.log('✅ Test passed!')
  } catch (error) {
    console.error('❌ Test failed:', error)
    process.exit(1)
  } finally {
    await browser.close()
  }
}

if (import.meta.main) {
  main()
}
```

---

## When to Use Bun

### ✅ Use Bun For:

1. **Running browser tests**
   ```bash
   bun run examples/smoke-test.ts
   ```

2. **Running CLI test tools**
   ```bash
   bun run tools/gallery-test.ts verify-home
   ```

3. **Installing test dependencies**
   ```bash
   cd browser-tests
   bun install
   ```

4. **TypeScript scripts** (no compilation needed)
   ```bash
   bun run my-script.ts
   ```

### ❌ Don't Use Bun For:

1. **Backend code** - Use Python + uv
   ```bash
   # ❌ Wrong
   cd backend
   bun run app/main.py

   # ✅ Right
   cd backend
   uv run uvicorn app.main:app
   ```

2. **Python tests** - Use pytest
   ```bash
   # ❌ Wrong
   bun run pytest

   # ✅ Right
   uv run pytest
   ```

3. **Production runtime** - Backend runs Python only
   ```dockerfile
   # ❌ Don't add Bun to Dockerfile
   # ✅ Docker runs Python app only
   ```

---

## When to Use Playwright

### ✅ Use Playwright For:

1. **Testing user workflows**
   ```typescript
   // Login → Upload → View Gallery
   await browser.navigate('/login')
   await browser.fill('input[type="email"]', email)
   await browser.click('button[type="submit"]')
   await browser.navigate('/upload')
   // ...
   ```

2. **Verifying UI elements**
   ```typescript
   // Check gallery grid exists
   await browser.waitForSelector('.masonry-grid')

   // Check navigation
   await browser.waitForSelector('nav')
   await browser.waitForSelector('a[href="/upload"]')
   ```

3. **Testing across viewports**
   ```typescript
   // Mobile
   await browser.resize(375, 667)
   await browser.screenshot({ path: 'mobile.png' })

   // Desktop
   await browser.resize(1920, 1080)
   await browser.screenshot({ path: 'desktop.png' })
   ```

4. **Production verification**
   ```bash
   # Can test live site!
   bun run examples/smoke-test.ts https://chitram.io
   ```

5. **Visual regression testing**
   ```bash
   # Generate baseline screenshots
   bun run examples/screenshot-all.ts
   ```

### ❌ Don't Use Playwright For:

1. **API testing** - Use pytest + httpx
   ```python
   # ✅ Right - Fast API test
   async def test_upload(client):
       response = await client.post("/upload", ...)
       assert response.status_code == 201
   ```

2. **Unit testing** - Use pytest
   ```python
   # ✅ Right - Fast unit test
   def test_validate_jpeg():
       result = validate_image_type(jpeg_bytes)
       assert result == "image/jpeg"
   ```

3. **Performance testing** - Use dedicated tools (locust, k6)

4. **Security testing** - Use security scanners (OWASP ZAP, etc.)

---

## Common Patterns

### Pattern 1: CLI Test Tool

```typescript
#!/usr/bin/env bun
// browser-tests/tools/gallery-test.ts

import { PlaywrightBrowser } from '../src/browser'

async function verifyHome(url: string) {
  const browser = new PlaywrightBrowser()

  try {
    await browser.launch({ headless: true })
    await browser.navigate(url)
    await browser.waitForSelector('.masonry-grid')
    console.log('✅ Home page verified')
    process.exit(0)
  } catch (error) {
    console.error('❌ Verification failed:', error)
    process.exit(1)
  } finally {
    await browser.close()
  }
}

// CLI router
const command = process.argv[2]
const arg1 = process.argv[3]

switch (command) {
  case 'verify-home':
    await verifyHome(arg1 || 'http://localhost:8000')
    break
  default:
    console.error('Unknown command')
    process.exit(1)
}
```

**Usage:**
```bash
bun run tools/gallery-test.ts verify-home
bun run tools/gallery-test.ts verify-home https://chitram.io
```

---

### Pattern 2: Test Suite

```typescript
#!/usr/bin/env bun
// browser-tests/examples/smoke-test.ts

import { PlaywrightBrowser } from '../src/browser'

interface TestResult {
  name: string
  status: 'pass' | 'fail'
  duration: number
  error?: string
}

const results: TestResult[] = []

async function runTest(name: string, testFn: () => Promise<void>) {
  const start = Date.now()
  try {
    await testFn()
    results.push({ name, status: 'pass', duration: Date.now() - start })
  } catch (error) {
    results.push({
      name,
      status: 'fail',
      duration: Date.now() - start,
      error: error instanceof Error ? error.message : String(error)
    })
  }
}

async function main() {
  const browser = new PlaywrightBrowser()
  await browser.launch({ headless: true })

  // Run tests
  await runTest('Home page loads', async () => {
    await browser.navigate('https://chitram.io')
    await browser.waitForSelector('.masonry-grid')
  })

  await runTest('Login page loads', async () => {
    await browser.navigate('https://chitram.io/login')
    await browser.waitForSelector('input[type="email"]')
  })

  await browser.close()

  // Print results
  const passed = results.filter(r => r.status === 'pass').length
  const failed = results.filter(r => r.status === 'fail').length

  console.log(`\n✅ Passed: ${passed}`)
  console.log(`❌ Failed: ${failed}`)

  process.exit(failed > 0 ? 1 : 0)
}

if (import.meta.main) {
  main()
}
```

---

### Pattern 3: Screenshot Utility

```typescript
#!/usr/bin/env bun
// browser-tests/tools/screenshot-utility.ts

import { PlaywrightBrowser } from '../src/browser'

async function captureScreenshots(url: string, outputDir: string) {
  const browser = new PlaywrightBrowser()
  await browser.launch({ headless: true })

  const viewports = [
    { name: 'mobile', width: 375, height: 667 },
    { name: 'tablet', width: 768, height: 1024 },
    { name: 'desktop', width: 1920, height: 1080 }
  ]

  for (const viewport of viewports) {
    await browser.resize(viewport.width, viewport.height)
    await browser.navigate(url)
    await browser.screenshot({
      path: `${outputDir}/home-${viewport.name}.png`,
      fullPage: true
    })
    console.log(`✅ ${viewport.name} screenshot saved`)
  }

  await browser.close()
}

// Usage
const url = process.argv[2] || 'http://localhost:8000'
const outputDir = process.argv[3] || './screenshots'

await captureScreenshots(url, outputDir)
```

---

## CI/CD Usage

### GitHub Actions Setup

```yaml
# .github/workflows/ui-tests.yml

- name: Setup Bun
  uses: oven-sh/setup-bun@v1
  with:
    bun-version: latest

- name: Install dependencies
  working-directory: browser-tests
  run: bun install

- name: Install Playwright browsers
  working-directory: browser-tests
  run: bunx playwright install chromium --with-deps

- name: Run smoke tests
  working-directory: browser-tests
  run: bun run examples/smoke-test.ts http://localhost:8000

- name: Run comprehensive tests
  working-directory: browser-tests
  run: bun run examples/comprehensive-test.ts http://localhost:8000
```

**Note:** `bunx` is like `npx` - runs packages without installing globally

---

## Best Practices

### 1. Always Use Headless Mode in CI

```typescript
// ✅ Good - Fast, works in CI
await browser.launch({ headless: true })

// ❌ Bad - Requires display server
await browser.launch({ headless: false })
```

### 2. Use Proper Error Handling

```typescript
// ✅ Good
try {
  await browser.waitForSelector('.element', { timeout: 5000 })
} catch (error) {
  console.error('Element not found:', error)
  await browser.screenshot({ path: 'error.png' })
  throw error
}

// ❌ Bad - No error context
await browser.waitForSelector('.element')
```

### 3. Clean Up Resources

```typescript
// ✅ Good - Always close browser
async function test() {
  const browser = new PlaywrightBrowser()
  try {
    await browser.launch()
    // Test code
  } finally {
    await browser.close()  // Always runs
  }
}

// ❌ Bad - Browser may stay open
async function test() {
  const browser = new PlaywrightBrowser()
  await browser.launch()
  // Test code
  await browser.close()  // Skipped if error occurs
}
```

### 4. Use Exit Codes for CI

```typescript
// ✅ Good - CI knows if test passed
try {
  await runTests()
  process.exit(0)  // Success
} catch (error) {
  console.error(error)
  process.exit(1)  // Failure
}

// ❌ Bad - CI thinks test passed even if it failed
try {
  await runTests()
} catch (error) {
  console.error(error)
}
// No exit code = defaults to 0 (success)
```

### 5. Use Meaningful Selectors

```typescript
// ✅ Good - Semantic selectors
await browser.click('button[type="submit"]')
await browser.fill('input[type="email"]')
await browser.waitForSelector('[data-testid="gallery-grid"]')

// ⚠️ Okay - Class/ID selectors
await browser.click('.submit-button')
await browser.fill('#email-input')

// ❌ Bad - Fragile selectors
await browser.click('body > div:nth-child(3) > button')
```

---

## Troubleshooting

### Issue: "bun: command not found"

**Solution:**
```bash
# Install Bun
curl -fsSL https://bun.sh/install | bash

# Add to PATH
echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify
bun --version
```

---

### Issue: "Playwright browser not found"

**Solution:**
```bash
cd browser-tests
bunx playwright install chromium --with-deps
```

---

### Issue: "Error: connect ECONNREFUSED localhost:8000"

**Cause:** Backend not running

**Solution:**
```bash
# Start backend first
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 &

# Wait for it to start
sleep 5

# Then run tests
cd ../browser-tests
bun run examples/smoke-test.ts
```

---

### Issue: "Timeout waiting for selector"

**Cause:** Element not found or slow to load

**Solution:**
```typescript
// Increase timeout
await browser.waitForSelector('.element', { timeout: 10000 })

// Or check the selector
await browser.screenshot({ path: 'debug.png' })
// Look at screenshot to see actual HTML
```

---

## Performance Tips

### 1. Reuse Browser Instances

```typescript
// ✅ Good - One browser for multiple tests
const browser = new PlaywrightBrowser()
await browser.launch()

for (const test of tests) {
  await runTest(browser, test)
}

await browser.close()

// ❌ Bad - New browser per test
for (const test of tests) {
  const browser = new PlaywrightBrowser()
  await browser.launch()
  await runTest(browser, test)
  await browser.close()
}
```

### 2. Parallel Test Execution (Future)

```typescript
// Run independent tests in parallel
const results = await Promise.all([
  testHomePage(),
  testLoginPage(),
  testRegisterPage()
])
```

### 3. Skip Waiting When Not Needed

```typescript
// ✅ Good - Wait only when necessary
await browser.navigate('/login')
await browser.fill('input[type="email"]', email)
// No wait needed, Playwright auto-waits

// ❌ Bad - Unnecessary explicit waits
await browser.navigate('/login')
await browser.wait(1000)  // Unnecessary
await browser.fill('input[type="email"]', email)
await browser.wait(500)   // Unnecessary
```

---

## Quick Command Reference

```bash
# Bun
bun --version                    # Check version
bun install                      # Install dependencies
bun add package                  # Add package
bun run script.ts                # Run TypeScript file
bunx playwright install          # Install Playwright browsers

# Our CLI Tools
bun run tools/gallery-test.ts verify-home
bun run tools/gallery-test.ts verify-login
bun run tools/gallery-test.ts verify-upload
bun run tools/gallery-test.ts screenshot <url> <output>

# Test Suites
bun run examples/smoke-test.ts [url]
bun run examples/comprehensive-test.ts [url]
bun run examples/screenshot-all.ts [url]
```

---

## Summary

### Use Bun When:
- ✅ Running browser tests
- ✅ Executing TypeScript scripts
- ✅ Managing test dependencies
- ✅ Need fast JavaScript runtime

### Use Playwright When:
- ✅ Testing user workflows
- ✅ Verifying UI elements
- ✅ Taking screenshots
- ✅ Testing production deployments
- ✅ Cross-browser testing

### Don't Use Bun/Playwright When:
- ❌ Testing backend code (use pytest)
- ❌ Testing APIs (use httpx)
- ❌ In production Dockerfile
- ❌ For backend runtime

---

## Related Documentation

- **Overview:** [`docs/learning/browser-test-overview.md`](../learning/browser-test-overview.md)
- **Architecture:** [`browser-tests/ARCHITECTURE_DECISION.md`](../../browser-tests/ARCHITECTURE_DECISION.md)
- **CI/CD:** [`browser-tests/CI_CD_INTEGRATION.md`](../../browser-tests/CI_CD_INTEGRATION.md)
- **Bun docs:** https://bun.sh/docs
- **Playwright docs:** https://playwright.dev/

---

**Remember:** Bun and Playwright are tools for **end-to-end testing**, complementing (not replacing) your Python backend tests. Use the right tool for the right job! 🎯
