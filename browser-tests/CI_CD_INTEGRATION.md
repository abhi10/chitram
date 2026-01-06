# CI/CD Integration Guide

Complete guide for integrating browser tests into your CI/CD pipeline using GitHub Actions.

---

## Overview

Your browser test suite is now integrated with GitHub Actions and provides:

- ✅ **Automated testing** on every push and pull request
- ✅ **Production verification** after deployments
- ✅ **Visual regression testing** on demand
- ✅ **Screenshot artifacts** for debugging
- ✅ **Fast feedback** (smoke tests in ~2s, comprehensive in ~12s)

---

## GitHub Actions Workflows

### 1. UI Tests (`ui-tests.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual trigger via GitHub UI (workflow_dispatch)

**What it does:**

#### Job 1: Test Against Localhost
Runs on all branches, for all PRs:
- Sets up Python, uv, and Bun
- Installs dependencies
- Starts backend server (SQLite, local storage)
- Runs smoke tests (6 tests, ~1-2s)
- Runs comprehensive tests (26 tests, ~10-12s)
- Uploads screenshots as artifacts (7 days retention)

#### Job 2: Test Against Production
Runs on `main` branch or manual trigger:
- Tests against https://chitram.io
- Verifies production deployment
- Uploads screenshots (30 days retention)

#### Job 3: Visual Regression
Manual trigger only:
- Generates ~36 screenshots across all viewports
- Creates baseline for visual regression
- Uploads with 90 days retention

**Example usage:**

```bash
# Automatic: Just push or create a PR
git push origin feature/new-feature

# Manual: Via GitHub UI
# Go to Actions → UI Tests → Run workflow
# Optional: Specify custom test URL
```

---

### 2. Post-Deployment Tests (`post-deployment-tests.yml`)

**Triggers:**
- After successful deployment workflows complete
- Manual trigger with custom deployment URL

**What it does:**
- Waits for deployment to be ready (up to 5 minutes)
- Runs critical smoke tests
- Runs comprehensive tests
- Creates deployment verification summary
- Optionally runs visual regression tests
- Notifies on failure

**Example usage:**

```bash
# Automatic: Triggered after your deployment workflow succeeds

# Manual: Via GitHub UI
# Go to Actions → Post-Deployment Tests → Run workflow
# Enter deployment URL (e.g., https://staging.chitram.io)
# Check "Run visual regression" if needed
```

---

## Configuration

### Environment Variables

The workflows use these environment variables (configured in workflow files):

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./test.db` | Test database |
| `SECRET_KEY` | Auto-generated | JWT secret for tests |
| `STORAGE_TYPE` | `local` | Storage backend for tests |
| `LOCAL_STORAGE_PATH` | `./test_uploads` | Upload directory |

### Secrets (Optional)

For advanced features, you can add these GitHub Secrets:

| Secret | Purpose |
|--------|---------|
| `SLACK_WEBHOOK_URL` | Notify team on test failures |
| `DISCORD_WEBHOOK_URL` | Send test results to Discord |
| `PRODUCTION_URL` | Override default production URL |

**To add secrets:**
1. Go to your repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add name and value

---

## Workflow Examples

### Daily Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/add-gallery-filters

# 2. Make changes to backend or frontend
# ...edit files...

# 3. Push changes
git push origin feature/add-gallery-filters

# 4. GitHub Actions automatically:
#    - Runs smoke tests (~2s)
#    - Runs comprehensive tests (~12s)
#    - Uploads screenshots
#    - Reports status on commit

# 5. Create PR
gh pr create --title "Add gallery filters" --body "Adds filtering by date and size"

# 6. CI runs again on PR
#    - Same tests as push
#    - Status appears on PR
```

### Deployment Workflow

```bash
# 1. Merge to main
git checkout main
git merge feature/add-gallery-filters
git push origin main

# 2. Your deployment workflow runs
#    - Builds Docker image
#    - Deploys to production
#    - Completes successfully

# 3. Post-deployment tests automatically run
#    - Waits for deployment to be ready
#    - Runs smoke tests against https://chitram.io
#    - Runs comprehensive tests
#    - Creates verification summary

# 4. Review results
#    - Check Actions tab
#    - Download screenshots if needed
#    - Verify deployment was successful
```

### Manual Testing Against Staging

```bash
# Via GitHub UI:
# 1. Go to Actions → UI Tests
# 2. Click "Run workflow"
# 3. Enter test URL: https://staging.chitram.io
# 4. Click "Run workflow"

# Or via GitHub CLI:
gh workflow run ui-tests.yml -f test_url=https://staging.chitram.io
```

---

## Viewing Test Results

### In GitHub Actions UI

1. Go to your repo → **Actions** tab
2. Click on the workflow run
3. Expand job to see test output
4. Scroll to bottom for **artifacts**

### Downloading Screenshots

```bash
# Via GitHub CLI
gh run download <run-id>

# Or via GitHub UI
# 1. Go to Actions → Select workflow run
# 2. Scroll to "Artifacts" section
# 3. Click "screenshots-localhost" or "screenshots-production"
# 4. Download ZIP file
```

### Understanding Test Output

**Smoke Test Output:**
```
🔥 Image Hosting App - Smoke Test Suite

Testing: https://chitram.io

✅ Home Page (589ms)
✅ Login Page (163ms)
✅ Register Page (125ms)
✅ Upload Page (Auth Redirect) (164ms)
✅ Health Check Endpoint (72ms)
✅ API Documentation (/docs) (334ms)

📊 Test Summary
Total Tests: 6
✅ Passed: 6
```

**Comprehensive Test Output:**
```
🧪 Image Hosting App - Comprehensive Test Suite

📁 Category: Page Load & Navigation
✅ [Navigation] Home page loads (497ms)
✅ [Navigation] Login page loads (205ms)
...

📊 Comprehensive Test Summary
Total Tests: 26
✅ Passed: 26
⏱️  Total Duration: 11.72s
```

---

## Troubleshooting

### Test Failures

**Symptom:** Tests fail in CI but pass locally

**Common causes:**
1. **Timing issues** - CI is slower than local
   - Solution: Increase timeout in test files

2. **Database state** - Tests depend on existing data
   - Solution: Use test fixtures, don't rely on prod data

3. **Environment differences** - Different Node/Bun versions
   - Solution: Lock versions in workflow file

**Symptom:** Screenshots show wrong content

**Causes:**
1. Selectors changed (`.masonry-grid` → something else)
2. Page layout changed
3. Authentication required but not provided

**Solution:**
- Review screenshots in artifacts
- Update selectors in test files
- Check if auth flow changed

### Backend Won't Start in CI

**Error:** `Backend failed to start`

**Checklist:**
- [ ] Check `backend/.env` is created correctly
- [ ] Verify database migrations run successfully
- [ ] Check port 8000 is not already in use
- [ ] Review backend logs in workflow output

**Debug:**
```yaml
# Add to workflow before "Start backend server"
- name: Debug backend setup
  working-directory: backend
  run: |
    cat .env
    uv run alembic current
    ls -la
```

### Playwright Browser Issues

**Error:** `Browser not installed`

**Solution:** Ensure `bunx playwright install chromium --with-deps` runs

**Error:** `Browser crashed`

**Solution:** Add `--disable-dev-shm-usage` flag:
```typescript
await browser.launch({
  headless: true,
  args: ['--disable-dev-shm-usage']
})
```

---

## Advanced Configuration

### Custom Test Matrix

Test against multiple environments:

```yaml
strategy:
  matrix:
    environment:
      - { name: 'Staging', url: 'https://staging.chitram.io' }
      - { name: 'Production', url: 'https://chitram.io' }
      - { name: 'Preview', url: 'https://preview.chitram.io' }

steps:
  - name: Test ${{ matrix.environment.name }}
    run: |
      bun run examples/smoke-test.ts ${{ matrix.environment.url }}
```

### Slack Notifications

Add to workflow:

```yaml
- name: Notify Slack on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "🚨 UI tests failed on ${{ github.ref }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*UI Tests Failed*\n\nBranch: `${{ github.ref }}`\nCommit: `${{ github.sha }}`\nAuthor: ${{ github.actor }}"
            }
          }
        ]
      }
```

### Parallel Test Execution

Split tests across multiple jobs:

```yaml
jobs:
  test-smoke:
    runs-on: ubuntu-latest
    steps:
      - name: Run smoke tests
        run: bun run examples/smoke-test.ts

  test-comprehensive:
    runs-on: ubuntu-latest
    steps:
      - name: Run comprehensive tests
        run: bun run examples/comprehensive-test.ts
```

---

## Performance Optimization

### Caching Dependencies

Add to workflow to speed up runs:

```yaml
- name: Cache Bun dependencies
  uses: actions/cache@v3
  with:
    path: ~/.bun/install/cache
    key: ${{ runner.os }}-bun-${{ hashFiles('browser-tests/bun.lock') }}
    restore-keys: |
      ${{ runner.os }}-bun-

- name: Cache Playwright browsers
  uses: actions/cache@v3
  with:
    path: ~/.cache/ms-playwright
    key: ${{ runner.os }}-playwright-${{ hashFiles('browser-tests/package.json') }}
```

### Skip Tests for Docs Changes

```yaml
on:
  push:
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

---

## Monitoring & Metrics

### Test Duration Trends

Track test performance over time:

```yaml
- name: Report test duration
  run: |
    echo "test_duration_seconds $(grep 'Total Duration' output.log | awk '{print $3}')" >> metrics.txt
```

### Success Rate

Track CI success rate in README badge:

```markdown
![UI Tests](https://github.com/username/repo/actions/workflows/ui-tests.yml/badge.svg)
```

---

## Migration from Other CI Systems

### GitLab CI

Convert workflow to `.gitlab-ci.yml`:

```yaml
ui-tests:
  image: oven/bun:latest
  stage: test
  before_script:
    - bun install
    - bunx playwright install chromium --with-deps
  script:
    - bun run examples/smoke-test.ts $CI_ENVIRONMENT_URL
  artifacts:
    when: always
    paths:
      - browser-tests/screenshots/
    expire_in: 1 week
```

### CircleCI

Convert to `.circleci/config.yml`:

```yaml
version: 2.1
jobs:
  ui-tests:
    docker:
      - image: oven/bun:latest
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: cd browser-tests && bun install
      - run:
          name: Install Playwright
          command: cd browser-tests && bunx playwright install chromium
      - run:
          name: Run tests
          command: cd browser-tests && bun run examples/smoke-test.ts
      - store_artifacts:
          path: browser-tests/screenshots
```

---

## Best Practices

### 1. Fast Feedback Loop

- ✅ Run smoke tests on every commit (fast, catches critical issues)
- ✅ Run comprehensive tests on PRs (thorough, before merge)
- ✅ Run visual regression on main branch only (slow, for baselines)

### 2. Artifact Management

- Keep smoke test screenshots for 7 days (debugging recent failures)
- Keep production screenshots for 30 days (deployment history)
- Keep visual regression baselines for 90 days (long-term comparison)

### 3. Fail Fast

```yaml
# Stop all jobs if smoke tests fail
jobs:
  smoke-tests:
    # ...

  comprehensive-tests:
    needs: smoke-tests  # Only run if smoke tests pass
    # ...
```

### 4. Idempotent Tests

- Don't rely on production data
- Clean up after tests
- Use test-specific accounts/images

### 5. Clear Error Messages

```typescript
// Good
await browser.waitForSelector('.masonry-grid', {
  timeout: 5000,
  errorMessage: 'Gallery grid not found - check if .masonry-grid class exists in HTML'
})

// Bad
await browser.waitForSelector('.masonry-grid')
```

---

## Next Steps

### Immediate

1. ✅ Commit and push the workflow files
2. ✅ Verify workflows appear in Actions tab
3. ✅ Create a test PR to trigger workflows
4. ✅ Review first workflow run

### Short Term

1. Add Slack/Discord notifications
2. Set up visual regression comparison
3. Create custom test scenarios for critical flows
4. Add performance budgets

### Long Term

1. Integrate with external monitoring (Datadog, New Relic)
2. Set up automated rollback on test failures
3. Create dashboard for test metrics
4. Add A/B testing verification

---

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Playwright Documentation](https://playwright.dev/)
- [Bun Documentation](https://bun.sh/docs)
- [Browser Tests README](./README.md)
- [Verification Checklist](./VERIFY.md)

---

## Support

**Issues with CI/CD integration?**

1. Check workflow logs in Actions tab
2. Review this guide's Troubleshooting section
3. Open an issue with:
   - Workflow run link
   - Error message
   - Screenshots (if available)

**Questions?**

- Review `browser-tests/README.md` for test suite documentation
- Check `browser-tests/SESSION_NOTES.md` for setup context
- Consult `browser-tests/VERIFY.md` for validation steps
