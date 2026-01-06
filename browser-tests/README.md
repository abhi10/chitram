# Browser Test Suite - Image Hosting App

UI automation testing for the Image Hosting App using the **kai-browser-skill pattern**.

**Key Features:**
- 🎯 Code-first browser automation (not AI-generated)
- ⚡ 99% token savings vs traditional MCP approaches
- 🔧 CLI tools for quick verification
- 🤖 CI/CD ready with exit codes
- 📸 Visual regression testing capabilities

---

## Quick Start

### 1. Installation

```bash
# Navigate to browser-tests directory
cd browser-tests

# Install dependencies
bun install

# Install Playwright browsers
bunx playwright install chromium

# Verify installation (see VERIFY.md for full checklist)
bun run tools/gallery-test.ts verify-home
```

**Full installation verification:** See [VERIFY.md](./VERIFY.md)

### 2. Run Your First Test

```bash
# Make sure your app is running
# In another terminal:
cd ../backend
uv run uvicorn app.main:app --reload

# Then run a test
bun run tools/gallery-test.ts verify-home http://localhost:8000
```

---

## Architecture

### The Three-Tier Testing Strategy

```
Tier 1: CLI Tools (90% of use cases)
  ↓ Quick one-command checks
  └─ verify-home, verify-login, screenshot

Tier 2: Workflows (8% of use cases)
  ↓ Pre-written multi-step scenarios
  └─ auth-flow.md, gallery-flow.md

Tier 3: Comprehensive Tests (2% of use cases)
  ↓ Full test suites
  └─ smoke-test.ts, comprehensive-test.ts
```

### Directory Structure

```
browser-tests/
├── src/
│   └── browser.ts              # PlaywrightBrowser class (core automation)
│
├── tools/
│   └── gallery-test.ts         # CLI tool for Image Gallery testing
│
├── workflows/
│   ├── auth-flow.md            # Authentication workflow (register/login/logout)
│   └── gallery-flow.md         # Gallery browsing workflow
│
├── examples/
│   ├── smoke-test.ts           # Quick health check (all pages load)
│   ├── comprehensive-test.ts   # Full feature testing
│   └── screenshot-all.ts       # Visual regression baselines
│
├── package.json                # Dependencies (playwright, typescript)
├── VERIFY.md                   # 8-point installation checklist
└── README.md                   # This file
```

---

## Usage

### CLI Tools (Tier 1)

**The fastest way to test. Zero boilerplate, instant execution.**

```bash
# Verify home page loads correctly
bun run tools/gallery-test.ts verify-home

# Verify login page
bun run tools/gallery-test.ts verify-login

# Verify upload page (should redirect to login)
bun run tools/gallery-test.ts verify-upload

# Verify register page
bun run tools/gallery-test.ts verify-register

# Take a screenshot
bun run tools/gallery-test.ts screenshot http://localhost:8000 output.png

# Test against different environment
bun run tools/gallery-test.ts verify-home https://staging.myapp.com
```

**Exit Codes:**
- `0` = All checks passed ✅
- `1` = Test failed ❌

Perfect for **CI/CD pipelines** and **quick manual checks**.

---

### Test Suites (Tier 3)

**Comprehensive testing for deployments and CI/CD.**

#### Smoke Tests (2-5 seconds)

Quick health check of all major pages:

```bash
bun run examples/smoke-test.ts

# Against staging
bun run examples/smoke-test.ts https://staging.myapp.com
```

**Tests:**
- ✅ All pages load (home, login, register, upload redirect)
- ✅ Required elements present
- ✅ No console errors
- ✅ Health check endpoint responds
- ✅ API docs accessible

#### Comprehensive Tests (30-60 seconds)

Full feature and regression testing:

```bash
bun run examples/comprehensive-test.ts

# Against staging
bun run examples/comprehensive-test.ts https://staging.myapp.com
```

**Test Categories:**
1. Page Load & Navigation
2. UI Elements & Layout
3. Authentication Forms
4. Protected Routes
5. API Endpoints
6. Console & Network
7. Screenshots & Visual Regression
8. Responsive Design (mobile/tablet/desktop)
9. Performance

**Generates screenshots in:** `./screenshots/comprehensive/`

#### Visual Regression (1-2 minutes)

Generate screenshot baselines for all pages and viewports:

```bash
bun run examples/screenshot-all.ts

# Custom output directory
bun run examples/screenshot-all.ts http://localhost:8000 ./baselines
```

**Captures:**
- 6 viewports (mobile, tablet, desktop variants)
- All major pages (home, login, register, etc.)
- Full page screenshots

**Generates:** ~36 screenshots in `./screenshots/visual-regression/`

---

### Workflows (Tier 2)

**Pre-written multi-step test scenarios.** See `workflows/` directory for code.

#### Authentication Flow

Tests complete auth journey:

```typescript
// workflows/auth-flow.md
Register → Login → Access Protected Page → Logout
```

#### Gallery Flow

Tests image browsing and viewing:

```typescript
// workflows/gallery-flow.md
Home → Scroll (infinite scroll) → Click Image → View Details → Back
```

**To run workflows:** Copy code from `.md` files into a new `.ts` file and execute with Bun.

---

## CI/CD Integration

**✅ Fully integrated with GitHub Actions!**

Your project now has complete CI/CD integration with two automated workflows:

### 1. UI Tests Workflow

**Runs on:** Every push, PR, and manual trigger

**What it does:**
- ✅ Tests against localhost (all branches)
- ✅ Tests against production (main branch only)
- ✅ Visual regression on demand
- ✅ Uploads screenshots as artifacts

**Status Badge:**
```markdown
![UI Tests](https://github.com/USERNAME/REPO/actions/workflows/ui-tests.yml/badge.svg)
```

### 2. Post-Deployment Tests

**Runs on:** After successful deployments

**What it does:**
- ✅ Waits for deployment to be ready
- ✅ Runs critical smoke tests
- ✅ Verifies production deployment
- ✅ Creates deployment summary

### Quick Start

```bash
# 1. Workflows are already set up in .github/workflows/

# 2. Just push your code
git add .
git commit -m "Add feature"
git push

# 3. GitHub Actions automatically runs tests

# 4. View results
# Go to GitHub → Actions tab
```

### Manual Triggers

```bash
# Test against custom URL
gh workflow run ui-tests.yml -f test_url=https://staging.myapp.com

# Run visual regression
gh workflow run ui-tests.yml -f test_url=https://chitram.io

# Post-deployment verification
gh workflow run post-deployment-tests.yml \
  -f deployment_url=https://chitram.io \
  -f run_visual_regression=true
```

### Complete Documentation

📚 **See [CI_CD_INTEGRATION.md](./CI_CD_INTEGRATION.md) for:**
- Detailed workflow documentation
- Troubleshooting guide
- Advanced configuration
- Best practices
- Migration from other CI systems

---

## Development Workflow

### Daily Development

After making UI changes:

```bash
# Quick verification
bun run tools/gallery-test.ts verify-home

# Visual check
bun run tools/gallery-test.ts screenshot http://localhost:8000 after-changes.png
```

### Before Committing

```bash
# Run smoke tests
bun run examples/smoke-test.ts
```

### Before Deployment

```bash
# Run comprehensive tests
bun run examples/comprehensive-test.ts

# Generate visual baselines
bun run examples/screenshot-all.ts
```

---

## Cost Savings

**kai-browser-skill pattern** vs **traditional Playwright MCP**:

| Frequency | Traditional MCP | kai-browser CLI | Savings |
|-----------|-----------------|-----------------|---------|
| 10 tests/day × 30 days | ~4.2M tokens ($60-90) | 0 tokens ($0) | $60-90/month |
| 100 tests/day (CI/CD) | ~42M tokens ($600-900) | 0 tokens ($0) | $600-900/month |

**How?**
- MCP loads 13,700 tokens at startup
- Each test generates 200+ tokens of code
- CLI executes pre-written code → 0 tokens

---

## Customization

### Adding New CLI Commands

Edit `tools/gallery-test.ts`:

```typescript
async function verifyMyFeature(baseUrl: string = DEFAULT_BASE_URL) {
  const browser = new PlaywrightBrowser()
  try {
    await browser.launch({ headless: true })
    await browser.navigate(`${baseUrl}/my-feature`)

    // Your test logic
    await browser.waitForSelector('.my-element')
    console.log('✅ Feature verified!')
    process.exit(0)
  } catch (error) {
    console.error('❌ Test failed:', error)
    process.exit(1)
  } finally {
    await browser.close()
  }
}

// Add to switch statement
case 'verify-my-feature':
  await verifyMyFeature(arg1)
  break
```

### Adding New Test Suites

Create `examples/my-test.ts`:

```typescript
#!/usr/bin/env bun
import { PlaywrightBrowser } from '../src/browser'

async function main() {
  const browser = new PlaywrightBrowser()
  await browser.launch({ headless: true })

  // Your test logic here

  await browser.close()
}

if (import.meta.main) {
  main()
}
```

---

## Troubleshooting

### Browser not installed

```bash
bunx playwright install chromium
```

### App not accessible

```bash
# Make sure backend is running
cd ../backend
uv run uvicorn app.main:app --reload

# Check it's accessible
curl http://localhost:8000/health
```

### TypeScript errors

```bash
# Reinstall dependencies
rm -rf node_modules
bun install
```

### Selectors not found

Your HTML might use different CSS classes. Update selectors in:
- `tools/gallery-test.ts`
- `examples/*.ts`
- `workflows/*.md`

Common selectors to check:
- `.gallery-grid` → Your gallery container
- `.gallery-item` or `.image-card` → Individual images
- `input[type="email"]` → Email inputs
- `button[type="submit"]` → Submit buttons

---

## API Reference

### PlaywrightBrowser Class

Located in `src/browser.ts`

**Navigation:**
```typescript
await browser.launch({ headless: true })
await browser.navigate('http://localhost:8000')
await browser.goBack()
await browser.reload()
await browser.close()
```

**Interaction:**
```typescript
await browser.click('.button')
await browser.fill('input[type="email"]', 'test@example.com')
await browser.type('.search', 'query', { delay: 100 })
await browser.pressKey('Enter')
```

**Waiting:**
```typescript
await browser.waitForSelector('.element', { timeout: 5000 })
await browser.waitForNavigation()
await browser.wait(1000)
```

**Capture:**
```typescript
await browser.screenshot({ path: 'output.png', fullPage: true })
const text = await browser.getVisibleText('.element')
const title = await browser.getTitle()
```

**Monitoring:**
```typescript
const errors = browser.getConsoleLogs({ type: 'error' })
const networkLogs = browser.getNetworkLogs()
```

**Viewport:**
```typescript
await browser.resize(375, 667) // Mobile
await browser.setDevice('iPhone 11')
```

---

## Resources

- [VERIFY.md](./VERIFY.md) - Installation verification checklist
- [kai-browser-skill](https://github.com/your-repo/kai-browser-skill) - Original pattern
- [Playwright Documentation](https://playwright.dev/)
- [Bun Documentation](https://bun.sh/docs)

---

## Philosophy

This test suite follows the **kai-browser-skill pattern**:

1. **Code-First, Not Code-Generated**
   - Pre-written tools vs AI-generated scripts
   - 99% token savings

2. **CLI for Simple Tasks**
   - One command = one action
   - Zero boilerplate

3. **Exit Codes for Automation**
   - 0 = success, 1 = failure
   - Perfect for CI/CD

4. **Deterministic Testing**
   - Same input → same output
   - No AI variability

---

## Contributing

When adding new tests:

1. ✅ Use CLI tools for simple checks
2. ✅ Add comprehensive tests for complex scenarios
3. ✅ Update VERIFY.md if adding dependencies
4. ✅ Document in this README

---

## License

Same as parent project (MIT)
