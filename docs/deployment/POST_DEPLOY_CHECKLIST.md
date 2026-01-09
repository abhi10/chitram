# Post-Deploy Verification Checklist

**Purpose:** Verify production deployment is working correctly after CD pipeline completes.
**Last Updated:** 2026-01-08

---

## Quick Verification (< 5 minutes)

Run these checks immediately after deployment:

### 1. Health Check
```bash
curl -s https://chitram.io/health | jq .
```
Expected:
```json
{
  "status": "healthy",
  "database": "connected",
  "storage": "connected",
  "cache": "connected"
}
```

### 2. API Authentication
```bash
# Test login endpoint responds
curl -s -X POST https://chitram.io/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"wrong"}' | jq .code
```
Expected: `"INVALID_CREDENTIALS"` (confirms auth API is responding)

### 3. Web UI Loads
- [ ] Visit https://chitram.io/login
- [ ] Page renders without errors
- [ ] Login form is visible

---

## Authentication Flow Verification

**CRITICAL:** These checks prevent the nav bar auth bug from recurring.

### 4. Web UI Auth State (FR-4.1 Compliance)

#### 4a. Anonymous User Behavior
- [ ] Visit https://chitram.io/ (home page)
- [ ] **Expected:** Redirects to `/login`
- [ ] Nav bar shows "Login" and "Register" links

#### 4b. Login Flow
- [ ] Enter valid credentials on login page
- [ ] Click "Sign In"
- [ ] **Expected:** Redirects to home page (`/`)

#### 4c. Logged-In State Verification (THE CRITICAL CHECK)
After successful login:
- [ ] **Nav bar shows user email** (e.g., "user@example.com")
- [ ] **Nav bar shows "Logout" button**
- [ ] **Nav bar shows "My Images" link**
- [ ] "Login" and "Register" links are NOT visible

> **Why this matters:** PR #36 fixed a bug where the nav showed logged-out state
> even after successful Supabase login. This check catches regressions.

#### 4d. Protected Route Access
While logged in:
- [ ] Visit https://chitram.io/upload
- [ ] **Expected:** Upload page loads (not redirect to login)
- [ ] Visit https://chitram.io/my-images
- [ ] **Expected:** My Images page loads (not redirect to login)

#### 4e. Private Gallery (FR-4.1)
- [ ] Home page shows ONLY the logged-in user's images
- [ ] Other users' images are NOT visible on home page
- [ ] Direct URL access to any image still works (unlisted model)

### 5. Logout Flow
- [ ] Click "Logout" button
- [ ] **Expected:** Redirects to home (`/`), then to `/login`
- [ ] Nav bar shows "Login" and "Register" again

---

## Functional Verification

### 6. Image Upload (Authenticated)
- [ ] Log in as test user
- [ ] Go to /upload
- [ ] Upload a test JPEG image
- [ ] **Expected:** Success, redirects to image detail page
- [ ] Image appears in "My Images" gallery

### 7. Image Access (Public by Direct URL)
- [ ] Copy the uploaded image's URL
- [ ] Log out
- [ ] Paste URL in new browser tab
- [ ] **Expected:** Image detail page loads (unlisted model allows direct access)

---

## Automated Browser Tests

Run the auth flow E2E test:

```bash
cd browser-tests
bun run examples/auth-flow-test.ts https://chitram.io
```

Expected: All tests pass, screenshots saved to `./screenshots/auth-flow/`

---

## Rollback Criteria

If any of these fail, consider rollback:

| Check | Severity | Action |
|-------|----------|--------|
| Health check fails | Critical | Rollback immediately |
| Login API errors | Critical | Rollback immediately |
| Nav shows wrong auth state | High | Rollback or hotfix |
| Protected routes accessible when logged out | Critical | Rollback immediately |
| User sees other users' images | Critical | Rollback immediately |
| Upload fails | Medium | Investigate, hotfix if needed |

---

## Checklist Template

Copy this for each deployment:

```markdown
## Deployment: [DATE] - [PR #]

### Quick Checks
- [ ] Health check passes
- [ ] API auth responds
- [ ] Web UI loads

### Auth Flow
- [ ] Anonymous → redirects to login
- [ ] Login → nav shows email + Logout
- [ ] Protected routes work when logged in
- [ ] Logout → nav shows Login/Register

### FR-4.1 Compliance
- [ ] Home shows only user's own images
- [ ] Direct URL access works for any image

### E2E Tests
- [ ] `auth-flow-test.ts` passes

**Status:** [ ] Verified OK / [ ] Issues Found
**Verified by:** _______________
**Time:** _______________
```

---

## Related Documentation

- [Incident Retrospective: Nav Auth Bug](../retrospectives/2026-01-08-supabase-nav-auth-bug.md)
- [Auth Provider Pattern](../../CLAUDE.md#auth-provider-pattern)
- [Browser Tests README](../../browser-tests/README.md)
