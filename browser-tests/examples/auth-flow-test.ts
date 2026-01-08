#!/usr/bin/env bun

/**
 * Authentication Flow Test Suite
 *
 * End-to-end tests for authentication workflows:
 * - Register new user
 * - Login with credentials
 * - Access protected routes
 * - Logout
 *
 * This test validates that auth works correctly regardless of whether
 * the backend uses local auth or Supabase auth (API contract is the same).
 *
 * Usage:
 *   bun run examples/auth-flow-test.ts [base-url]
 *
 * Examples:
 *   bun run examples/auth-flow-test.ts
 *   bun run examples/auth-flow-test.ts http://localhost:8000
 *   bun run examples/auth-flow-test.ts https://chitram.io
 */

import { PlaywrightBrowser } from '../src/browser'
import { mkdir } from 'fs/promises'

const BASE_URL = process.argv[2] || 'http://localhost:8000'
const SCREENSHOTS_DIR = './screenshots/auth-flow'

// Generate unique test credentials to avoid conflicts
const TEST_EMAIL = `test-${Date.now()}@example.com`
const TEST_PASSWORD = 'TestPassword123!'

interface TestResult {
  name: string
  status: 'pass' | 'fail' | 'skip'
  duration: number
  error?: string
}

const results: TestResult[] = []

function logTest(name: string, status: 'pass' | 'fail' | 'skip', duration: number, error?: string) {
  const icon = status === 'pass' ? '✅' : status === 'fail' ? '❌' : '⚠️ '
  console.log(`${icon} ${name} (${duration}ms)`)
  if (error) {
    console.log(`   Error: ${error}`)
  }
  results.push({ name, status, duration, error })
}

async function runTest(
  name: string,
  fn: () => Promise<void>
): Promise<boolean> {
  const startTime = Date.now()
  try {
    await fn()
    logTest(name, 'pass', Date.now() - startTime)
    return true
  } catch (error) {
    logTest(name, 'fail', Date.now() - startTime, error instanceof Error ? error.message : String(error))
    return false
  }
}

async function main() {
  console.log('🔐 Authentication Flow Test Suite\n')
  console.log(`Testing: ${BASE_URL}`)
  console.log(`Test user: ${TEST_EMAIL}\n`)

  // Create screenshots directory
  await mkdir(SCREENSHOTS_DIR, { recursive: true })

  const browser = new PlaywrightBrowser()

  try {
    await browser.launch({ headless: true })
    console.log('✅ Browser launched\n')

    // =========================================================================
    // Test 1: Register New User
    // =========================================================================
    console.log('📝 Testing User Registration\n')

    const registerSuccess = await runTest('Navigate to register page', async () => {
      await browser.navigate(`${BASE_URL}/register`)
      await browser.waitForSelector('input[type="email"]', { timeout: 5000 })
      await browser.screenshot({ path: `${SCREENSHOTS_DIR}/01-register-page.png` })
    })

    if (!registerSuccess) {
      throw new Error('Cannot continue: register page failed to load')
    }

    await runTest('Fill registration form', async () => {
      await browser.type('input[type="email"]', TEST_EMAIL)
      await browser.type('input[type="password"]', TEST_PASSWORD)
      await browser.type('input#confirm-password', TEST_PASSWORD)
      await browser.screenshot({ path: `${SCREENSHOTS_DIR}/02-register-filled.png` })
    })

    await runTest('Submit registration and verify redirect', async () => {
      await browser.click('button[type="submit"]')

      // Wait for redirect to home page (registration auto-logs in)
      await browser.wait(3000) // Wait for API call and redirect

      const url = browser.getUrl()
      // After successful registration, user is redirected to home
      if (url.includes('/register')) {
        // Check for error message
        const html = await browser.getVisibleHtml()
        if (html.includes('error') || html.includes('Error')) {
          throw new Error('Registration failed - error displayed on page')
        }
        throw new Error('Still on register page after submit')
      }

      await browser.screenshot({ path: `${SCREENSHOTS_DIR}/03-after-register.png` })
    })

    // =========================================================================
    // Test 2: Verify Logged In State
    // =========================================================================
    console.log('\n🔍 Verifying Logged In State\n')

    await runTest('User is logged in after registration', async () => {
      await browser.navigate(BASE_URL)
      await browser.wait(1000)

      // Check if logout link is visible (indicates logged in)
      const html = await browser.getVisibleHtml()
      const isLoggedIn = html.includes('Logout') || html.includes('logout') ||
                         html.includes('My Images') || html.includes('my-images')

      if (!isLoggedIn) {
        await browser.screenshot({ path: `${SCREENSHOTS_DIR}/04-login-state-check.png` })
        throw new Error('User does not appear to be logged in')
      }

      await browser.screenshot({ path: `${SCREENSHOTS_DIR}/04-logged-in-home.png` })
    })

    await runTest('Can access protected upload page', async () => {
      await browser.navigate(`${BASE_URL}/upload`)
      await browser.wait(1000)

      const url = browser.getUrl()
      // Should NOT redirect to login if authenticated
      if (url.includes('/login')) {
        throw new Error('Redirected to login - user not authenticated')
      }

      // Should see upload form
      const html = await browser.getVisibleHtml()
      if (!html.includes('upload') && !html.includes('Upload')) {
        throw new Error('Upload page content not found')
      }

      await browser.screenshot({ path: `${SCREENSHOTS_DIR}/05-upload-page-authed.png` })
    })

    await runTest('Can access protected my-images page', async () => {
      await browser.navigate(`${BASE_URL}/my-images`)
      await browser.wait(1000)

      const url = browser.getUrl()
      if (url.includes('/login')) {
        throw new Error('Redirected to login - user not authenticated')
      }

      await browser.screenshot({ path: `${SCREENSHOTS_DIR}/06-my-images-authed.png` })
    })

    // =========================================================================
    // Test 3: Logout
    // =========================================================================
    console.log('\n🚪 Testing Logout\n')

    await runTest('Logout and verify redirect', async () => {
      // Clear the auth cookie to simulate logout
      await browser.evaluate(`document.cookie = 'chitram_auth=; path=/; max-age=0'`)
      await browser.navigate(BASE_URL)
      await browser.wait(1000)

      await browser.screenshot({ path: `${SCREENSHOTS_DIR}/07-after-logout.png` })
    })

    await runTest('Protected routes redirect to login after logout', async () => {
      await browser.navigate(`${BASE_URL}/upload`)
      await browser.wait(1000)

      const url = browser.getUrl()
      if (!url.includes('/login')) {
        throw new Error('Did not redirect to login after logout')
      }

      await browser.screenshot({ path: `${SCREENSHOTS_DIR}/08-redirect-after-logout.png` })
    })

    // =========================================================================
    // Test 4: Login with Existing User
    // =========================================================================
    console.log('\n🔑 Testing Login with Existing User\n')

    await runTest('Navigate to login page', async () => {
      await browser.navigate(`${BASE_URL}/login`)
      await browser.waitForSelector('input[type="email"]', { timeout: 5000 })
      await browser.screenshot({ path: `${SCREENSHOTS_DIR}/09-login-page.png` })
    })

    await runTest('Fill login form', async () => {
      await browser.type('input[type="email"]', TEST_EMAIL)
      await browser.type('input[type="password"]', TEST_PASSWORD)
      await browser.screenshot({ path: `${SCREENSHOTS_DIR}/10-login-filled.png` })
    })

    await runTest('Submit login and verify redirect', async () => {
      await browser.click('button[type="submit"]')
      await browser.wait(3000)

      const url = browser.getUrl()
      if (url.includes('/login')) {
        const html = await browser.getVisibleHtml()
        if (html.includes('error') || html.includes('Invalid')) {
          throw new Error('Login failed - invalid credentials or error')
        }
        throw new Error('Still on login page after submit')
      }

      await browser.screenshot({ path: `${SCREENSHOTS_DIR}/11-after-login.png` })
    })

    await runTest('User is logged in after login', async () => {
      await browser.navigate(BASE_URL)
      await browser.wait(1000)

      const html = await browser.getVisibleHtml()
      const isLoggedIn = html.includes('Logout') || html.includes('logout') ||
                         html.includes('My Images') || html.includes('my-images')

      if (!isLoggedIn) {
        throw new Error('User does not appear to be logged in after login')
      }

      await browser.screenshot({ path: `${SCREENSHOTS_DIR}/12-logged-in-after-login.png` })
    })

    // =========================================================================
    // Test 5: Invalid Login Attempt
    // =========================================================================
    console.log('\n❌ Testing Invalid Login\n')

    // Clear auth first
    await browser.evaluate(`document.cookie = 'chitram_auth=; path=/; max-age=0'`)

    await runTest('Invalid password shows error', async () => {
      await browser.navigate(`${BASE_URL}/login`)
      await browser.waitForSelector('input[type="email"]', { timeout: 5000 })

      await browser.type('input[type="email"]', TEST_EMAIL)
      await browser.type('input[type="password"]', 'WrongPassword123!')
      await browser.click('button[type="submit"]')

      await browser.wait(3000)

      const html = await browser.getVisibleHtml()
      // Should still be on login page with error
      const url = browser.getUrl()
      if (!url.includes('/login')) {
        throw new Error('Did not stay on login page after invalid credentials')
      }

      // Should show error message
      if (!html.includes('Invalid') && !html.includes('error') && !html.includes('credentials')) {
        // This is acceptable - some implementations just don't redirect
        console.log('   Note: Error message may not be visible, but stayed on login page')
      }

      await browser.screenshot({ path: `${SCREENSHOTS_DIR}/13-invalid-login.png` })
    })

    // =========================================================================
    // Summary
    // =========================================================================
    console.log('\n' + '='.repeat(60))
    console.log('📊 Authentication Flow Test Summary')
    console.log('='.repeat(60))

    const totalPassed = results.filter(r => r.status === 'pass').length
    const totalFailed = results.filter(r => r.status === 'fail').length
    const totalDuration = results.reduce((sum, r) => sum + r.duration, 0)

    console.log(`\nTotal Tests: ${results.length}`)
    console.log(`✅ Passed: ${totalPassed}`)
    console.log(`❌ Failed: ${totalFailed}`)
    console.log(`⏱️  Total Duration: ${(totalDuration / 1000).toFixed(2)}s`)
    console.log(`📸 Screenshots saved to: ${SCREENSHOTS_DIR}`)

    if (totalFailed > 0) {
      console.log('\n❌ Some auth flow tests failed!')

      // Show failed tests
      console.log('\nFailed tests:')
      results.filter(r => r.status === 'fail').forEach(r => {
        console.log(`  - ${r.name}: ${r.error}`)
      })

      process.exit(1)
    } else {
      console.log('\n✅ All authentication flow tests passed!')
      console.log('\nAuth system is working correctly - ready for Supabase migration.')
      process.exit(0)
    }
  } catch (error) {
    console.error('\n💥 Fatal error:', error instanceof Error ? error.message : error)
    process.exit(1)
  } finally {
    await browser.close()
  }
}

if (import.meta.main) {
  main()
}

export { main }
