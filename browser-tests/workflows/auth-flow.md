# Authentication Flow Test

**Purpose:** Test complete user authentication journey from registration through logout.

**Use when:** Testing auth system changes, user management features, or session handling.

---

## Workflow Steps

### 1. Registration Flow

```typescript
import { PlaywrightBrowser } from '../src/browser'

const browser = new PlaywrightBrowser()
await browser.launch({ headless: true })

// Navigate to register page
await browser.navigate('http://localhost:8000/register')

// Verify page loaded
const title = await browser.getTitle()
console.log(`Page title: ${title}`)

// Fill registration form
const testEmail = `test-${Date.now()}@example.com`
const testPassword = 'SecurePassword123!'

await browser.fill('input[type="email"]', testEmail)
await browser.fill('input[type="password"]', testPassword)
await browser.click('button[type="submit"]')

// Wait for redirect to home page
await browser.waitForNavigation()

const currentUrl = browser.getUrl()
console.log(`Redirected to: ${currentUrl}`)

// Verify logged in (should see user menu or logout button)
try {
  await browser.waitForSelector('[data-test="user-menu"]', { timeout: 5000 })
  console.log('✅ Successfully registered and logged in')
} catch {
  console.log('❌ Login verification failed')
  process.exit(1)
}
```

### 2. Login Flow

```typescript
// Navigate to login page
await browser.navigate('http://localhost:8000/login')

// Fill login form
await browser.fill('input[type="email"]', testEmail)
await browser.fill('input[type="password"]', testPassword)
await browser.click('button[type="submit"]')

// Wait for redirect
await browser.waitForNavigation()

// Verify successful login
const loggedInUrl = browser.getUrl()
if (loggedInUrl.includes('/login')) {
  console.log('❌ Still on login page - login failed')
  process.exit(1)
} else {
  console.log('✅ Successfully logged in')
}
```

### 3. Access Protected Page (Upload)

```typescript
// Try to access upload page (requires auth)
await browser.navigate('http://localhost:8000/upload')

// Should NOT redirect to login since we're authenticated
const uploadUrl = browser.getUrl()
if (uploadUrl.includes('/login')) {
  console.log('❌ Redirected to login - auth not working')
  process.exit(1)
}

// Verify upload form is visible
try {
  await browser.waitForSelector('input[type="file"]', { timeout: 5000 })
  console.log('✅ Upload page accessible when authenticated')
} catch {
  console.log('❌ Upload form not found')
  process.exit(1)
}
```

### 4. Logout Flow

```typescript
// Click logout button/link
try {
  await browser.click('a[href="/logout"]')
  await browser.wait(1000) // Wait for logout to process

  console.log('✅ Logout button clicked')
} catch {
  console.log('⚠️  Logout link not found')
}

// Try to access protected page again
await browser.navigate('http://localhost:8000/upload')

// Should redirect to login now
const finalUrl = browser.getUrl()
if (finalUrl.includes('/login')) {
  console.log('✅ Correctly redirected to login after logout')
} else {
  console.log('❌ Still can access protected page after logout')
  process.exit(1)
}

await browser.close()
console.log('\n🎉 Authentication flow test passed!')
```

---

## Success Criteria

✅ User can register with new account
✅ User can login with credentials
✅ Authenticated user can access protected pages
✅ User can logout
✅ Logged out user cannot access protected pages

---

## Error Scenarios Tested

- ❌ Cannot access `/upload` when not logged in
- ❌ Cannot stay logged in after clicking logout
- ✅ Proper redirects at each step

---

## Run This Workflow

```bash
# Create a standalone test file:
cd browser-tests
cp workflows/auth-flow.md examples/auth-flow-test.ts

# Wrap the code above in async main function and run:
bun run examples/auth-flow-test.ts
```

---

## Integration with CI/CD

```yaml
# .github/workflows/test.yml
- name: Test authentication flow
  run: |
    cd browser-tests
    bun run examples/auth-flow-test.ts || exit 1
```

---

## Notes

- Uses dynamic email (`test-${timestamp}@example.com`) to avoid duplicates
- Each test run creates a new user
- Can be extended to test password reset, email verification, etc.
- Adjust selectors based on your actual HTML structure
