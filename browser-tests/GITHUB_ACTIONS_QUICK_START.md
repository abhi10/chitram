# GitHub Actions Quick Start

Quick reference for using the CI/CD workflows.

---

## 🚀 First-Time Setup

### 1. Enable GitHub Actions

Your workflows are already created in `.github/workflows/`:
- ✅ `ui-tests.yml` - Main test workflow
- ✅ `post-deployment-tests.yml` - Post-deployment verification

**No additional setup needed!** Just push your code.

### 2. Add Status Badge to README

Add this to your main `README.md`:

```markdown
## CI/CD Status

![UI Tests](https://github.com/YOUR-USERNAME/image-hosting-app/actions/workflows/ui-tests.yml/badge.svg)
![Post-Deployment](https://github.com/YOUR-USERNAME/image-hosting-app/actions/workflows/post-deployment-tests.yml/badge.svg)
```

Replace `YOUR-USERNAME` with your GitHub username.

---

## 📋 Common Tasks

### Run Tests on Push

```bash
# Automatic - just push
git add .
git commit -m "feat: add new feature"
git push
```

**What happens:**
- Workflow triggers automatically
- Tests run against localhost
- Results appear in Actions tab
- Screenshots uploaded if tests fail

---

### Run Tests Against Custom URL

```bash
# Via GitHub CLI
gh workflow run ui-tests.yml -f test_url=https://staging.chitram.io

# Via GitHub UI
# 1. Go to Actions → UI Tests
# 2. Click "Run workflow"
# 3. Enter URL in "test_url" field
# 4. Click "Run workflow"
```

---

### Post-Deployment Verification

```bash
# Via GitHub CLI
gh workflow run post-deployment-tests.yml \
  -f deployment_url=https://chitram.io \
  -f run_visual_regression=false

# Via GitHub UI
# 1. Go to Actions → Post-Deployment Tests
# 2. Click "Run workflow"
# 3. Enter deployment URL
# 4. Check "Run visual regression" if needed
# 5. Click "Run workflow"
```

---

### Generate Visual Regression Baseline

```bash
# Via GitHub CLI
gh workflow run ui-tests.yml -f test_url=https://chitram.io

# This triggers the visual-regression job
# Downloads ~36 screenshots
# Stored for 90 days
```

---

## 📊 Viewing Results

### Check Workflow Status

```bash
# List recent runs
gh run list --workflow=ui-tests.yml

# View specific run
gh run view <run-id>

# Watch live run
gh run watch
```

### Download Screenshots

```bash
# List artifacts for a run
gh run view <run-id>

# Download all artifacts
gh run download <run-id>

# Download specific artifact
gh run download <run-id> -n screenshots-localhost
```

### View in Browser

1. Go to https://github.com/YOUR-USERNAME/image-hosting-app/actions
2. Click on workflow run
3. See test output in logs
4. Download artifacts at bottom

---

## 🔧 Workflow Triggers

### UI Tests Workflow

| Trigger | When | What it tests |
|---------|------|---------------|
| Push to `main`/`develop` | Every push | Localhost + Production |
| Pull Request | Every PR | Localhost only |
| Manual (workflow_dispatch) | On demand | Custom URL |

### Post-Deployment Tests

| Trigger | When | What it tests |
|---------|------|---------------|
| After deployment | Auto | Production (chitram.io) |
| Manual | On demand | Custom deployment URL |

---

## ⚡ Performance

| Test Suite | Duration | Tests |
|-------------|----------|-------|
| Smoke Tests | ~2s | 6 tests |
| Comprehensive | ~12s | 26 tests |
| Visual Regression | ~45s | 36 screenshots |

**Total CI time:** ~3-5 minutes (including setup)

---

## 🛠️ Troubleshooting

### Workflow not triggering?

**Check:**
1. File is in `.github/workflows/` ✅
2. File has `.yml` extension ✅
3. Pushed to `main` or `develop` branch
4. Changes affect `backend/app/**` or `browser-tests/**`

### Tests failing in CI but pass locally?

**Common causes:**
1. **Selector changed** - Update `.masonry-grid` if HTML changed
2. **Timeout too short** - Increase timeout in test files
3. **Database state** - Tests rely on production data
4. **Environment vars** - Missing `.env` values

**Quick fix:**
```bash
# Download screenshots to see what's wrong
gh run download <run-id> -n screenshots-localhost
open screenshots-localhost/
```

### Can't download screenshots?

**Reason:** Artifacts expire after retention period
- Localhost: 7 days
- Production: 30 days
- Visual regression: 90 days

**Solution:** Re-run workflow to generate fresh screenshots

---

## 📈 Advanced Usage

### Run Only Smoke Tests

Edit workflow to comment out comprehensive tests:

```yaml
# - name: Run comprehensive tests
#   run: bun run examples/comprehensive-test.ts
```

### Test Multiple Environments

```bash
# Test staging
gh workflow run ui-tests.yml -f test_url=https://staging.chitram.io

# Test preview
gh workflow run ui-tests.yml -f test_url=https://preview-123.chitram.io

# Test localhost (if backend is accessible)
gh workflow run ui-tests.yml -f test_url=http://localhost:8000
```

### Schedule Regular Tests

Add to `ui-tests.yml`:

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
```

---

## 🔐 Security

### Secrets

Add these if needed (Settings → Secrets):

| Secret | Purpose | Required? |
|--------|---------|-----------|
| `PRODUCTION_URL` | Override chitram.io | No |
| `SLACK_WEBHOOK_URL` | Notifications | No |
| `TEST_USER_EMAIL` | Auth tests | Future |
| `TEST_USER_PASSWORD` | Auth tests | Future |

### Branch Protection

Recommended settings:
1. Go to Settings → Branches → Branch protection rules
2. Add rule for `main`:
   - ✅ Require status checks to pass
   - ✅ Select "UI Tests / test-localhost"
   - ✅ Require branches to be up to date

---

## 📚 More Information

- **Full CI/CD Guide:** [CI_CD_INTEGRATION.md](./CI_CD_INTEGRATION.md)
- **Test Suite Docs:** [README.md](./README.md)
- **Verification:** [VERIFY.md](./VERIFY.md)
- **Session Notes:** [SESSION_NOTES.md](./SESSION_NOTES.md)

---

## 🎯 Quick Command Reference

```bash
# List workflows
gh workflow list

# Run UI tests
gh workflow run ui-tests.yml

# Run with custom URL
gh workflow run ui-tests.yml -f test_url=https://staging.chitram.io

# View recent runs
gh run list --workflow=ui-tests.yml --limit 5

# Download screenshots
gh run download <run-id>

# Cancel running workflow
gh run cancel <run-id>

# Re-run failed tests
gh run rerun <run-id> --failed
```

---

**Ready to test?** Just push your code! 🚀
