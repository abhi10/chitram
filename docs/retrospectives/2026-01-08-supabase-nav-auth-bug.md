# Incident: Supabase Auth - Nav Bar Shows Logged Out State

**Date:** 2026-01-08
**Severity:** P2 (Major) - Core UX broken, but auth actually worked
**Duration:** ~12 hours (from PR #34 deployment to PR #36 fix)
**Author:** Chitram Team

---

## Summary

After deploying Supabase authentication (PR #31-34), users who successfully logged in via Supabase saw the navigation bar displaying "Login" and "Register" links instead of their email and "Logout" button. The actual authentication worked correctly (cookies were set, API calls succeeded), but the web UI didn't recognize the logged-in state. This created a confusing UX where users appeared logged out despite being authenticated.

---

## Timeline

| Time (UTC) | Event |
|------------|-------|
| Jan 7, 07:09 | PR #34 deployed - Supabase auth fully operational |
| Jan 7, ~08:00 | Users began logging in via Supabase |
| Jan 8, 18:00 | Bug reported - "Login is not working, breaks UX" |
| Jan 8, 18:15 | Investigation started - browser testing revealed login worked |
| Jan 8, 18:25 | Root cause identified - `web.py` using wrong auth service |
| Jan 8, 18:34 | PR #36 merged and auto-deployed |
| Jan 8, 18:37 | Verified resolved - nav shows email + Logout |

---

## Impact

**Users Affected:** All users logging in via Supabase (~12 hour window)
**Functionality Impacted:**
- Nav bar showed "Login/Register" instead of logged-in state
- "My Images" link not visible (though URL still worked)
- Confusing UX - users unsure if login succeeded

**Business Impact:**
- Poor first impression for new users
- Confusion about auth state
- Support burden (user reported issue)

---

## Root Cause

The web UI cookie authentication in `web.py` was using `AuthService.verify_token()` which only verifies **local JWTs** signed with `JWT_SECRET_KEY`.

When Supabase auth was enabled, the cookie contained a **Supabase JWT** signed with Supabase's secret. The `AuthService` couldn't verify it (wrong secret), so it returned `None`, making the UI think the user was logged out.

**The disconnect:**
- API routes (`auth.py`) correctly used `create_auth_provider()` - pluggable, works with both
- Web routes (`web.py`) used `AuthService` directly - only works with local JWT

```python
# BEFORE (broken) - web.py
auth_service = AuthService(db)
user_id = auth_service.verify_token(token)  # Uses JWT_SECRET_KEY only

# AFTER (fixed) - web.py
provider = create_auth_provider(db=db, settings=settings)
result = await provider.verify_token(token)  # Uses correct provider
```

---

## Detection Gap

**How was it detected?** User report after ~12 hours

**Why wasn't it caught earlier?**
- [x] **Test environment differs from production** - Tests use `AUTH_PROVIDER=local`, so `AuthService` worked fine in tests
- [x] **Missing test coverage** - No E2E test for "login via Supabase, verify nav bar shows logged-in state"
- [ ] No monitoring/alerting for this scenario
- [x] **Manual QA missed it** - Post-deploy verification checked API login, not web UI nav state
- [x] **Code review gap** - `web.py` wasn't updated when pluggable auth was added

**Key insight:** The pluggable auth pattern was correctly implemented for API routes but `web.py` was overlooked because it used a different authentication path (cookie-based vs header-based).

---

## Resolution

**Immediate Fix:** Updated `get_current_user_from_cookie()` in `web.py` to use `create_auth_provider()` instead of `AuthService`

**PR:** [#36 - fix(auth): use pluggable auth provider for web cookie verification](https://github.com/abhi10/chitram/pull/36)

**Changes:**
1. Import `create_auth_provider` instead of `AuthService`
2. Use provider's `verify_token()` method
3. Updated unit tests to mock pluggable provider pattern
4. Added test for Supabase provider verification

---

## Lessons Learned

### What Went Well
- CD pipeline deployed fix automatically within 3 minutes of merge
- Root cause was identified quickly once bug was reported
- Fix was straightforward - no database changes needed
- Tests were easy to update with new mocking pattern

### What Went Wrong
- 12 hours of broken UX before detection
- Assumed all auth paths used the same provider (API did, web didn't)
- Post-deploy verification was incomplete (checked login API, not nav state)
- `web.py` wasn't included in PR #31's scope when adding pluggable auth

### Where We Got Lucky
- The actual authentication worked - users could still upload/view images
- Cookie was set correctly, so a page refresh after fix immediately worked
- No data loss or security issues

---

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add E2E test: login → verify nav shows logged-in state | Team | P1 | 2026-01-15 | [ ] |
| Add post-deploy checklist item for web UI auth state | Team | P2 | 2026-01-10 | [ ] |
| Audit for other places using AuthService directly | Team | P2 | 2026-01-12 | [ ] |
| Document "auth provider pattern" in CLAUDE.md | Team | P3 | 2026-01-15 | [ ] |

---

## Prevention

**How do we prevent this class of issue?**

- [x] Add automated test for this scenario → E2E test for nav auth state
- [ ] Add monitoring/alerting → Consider auth state mismatch alerting
- [x] Update deployment checklist → Add web UI verification step
- [x] Improve code review process → When changing auth, grep for all auth usage
- [x] Add integration test → Browser test for full login flow

**Pattern to follow:**
When implementing a cross-cutting concern (like auth), search the entire codebase for related usages:
```bash
grep -r "AuthService\|verify_token\|get_current_user" --include="*.py"
```

---

## References

- Fix PR: [#36](https://github.com/abhi10/chitram/pull/36)
- Supabase Auth PRs: [#31](https://github.com/abhi10/chitram/pull/31), [#32](https://github.com/abhi10/chitram/pull/32), [#33](https://github.com/abhi10/chitram/pull/33), [#34](https://github.com/abhi10/chitram/pull/34)
- Related: [docs/learning/supabase-integration-learnings.md](../learning/supabase-integration-learnings.md)
