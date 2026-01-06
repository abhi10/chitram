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

## Next Steps

- Read [README.md](./README.md) for full usage guide
- See [VERIFY.md](./VERIFY.md) for complete verification checklist
- Explore `examples/` directory for test examples
- Check `workflows/` for pre-written test scenarios

---

**Installation complete! 🎉**
