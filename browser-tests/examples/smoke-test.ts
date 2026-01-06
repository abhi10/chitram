#!/usr/bin/env bun

/**
 * Smoke Test Suite for Image Hosting App
 *
 * Quick health check that verifies all major pages load correctly.
 * Run this after deployments or before releases to catch critical issues.
 *
 * Usage:
 *   bun run examples/smoke-test.ts [base-url]
 *
 * Examples:
 *   bun run examples/smoke-test.ts
 *   bun run examples/smoke-test.ts http://localhost:8000
 *   bun run examples/smoke-test.ts https://staging.myapp.com
 */

import { PlaywrightBrowser } from '../src/browser'

const BASE_URL = process.argv[2] || 'http://localhost:8000'

interface TestResult {
  name: string
  status: 'pass' | 'fail' | 'skip'
  duration: number
  error?: string
}

const results: TestResult[] = []

function logResult(result: TestResult) {
  const icon = result.status === 'pass' ? '✅' : result.status === 'fail' ? '❌' : '⚠️ '
  console.log(`${icon} ${result.name} (${result.duration}ms)`)
  if (result.error) {
    console.log(`   Error: ${result.error}`)
  }
}

async function testPage(
  browser: PlaywrightBrowser,
  name: string,
  url: string,
  requiredSelectors: string[]
): Promise<TestResult> {
  const startTime = Date.now()

  try {
    // Navigate to page
    await browser.navigate(url)

    // Check for required elements
    for (const selector of requiredSelectors) {
      await browser.waitForSelector(selector, { timeout: 5000 })
    }

    // Check for console errors
    const errors = browser.getConsoleLogs({ type: 'error' })
    if (errors.length > 0) {
      return {
        name,
        status: 'fail',
        duration: Date.now() - startTime,
        error: `Console errors: ${errors.length}`
      }
    }

    return {
      name,
      status: 'pass',
      duration: Date.now() - startTime
    }
  } catch (error) {
    return {
      name,
      status: 'fail',
      duration: Date.now() - startTime,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}

async function main() {
  console.log('🔥 Image Hosting App - Smoke Test Suite\n')
  console.log(`Testing: ${BASE_URL}\n`)

  const browser = new PlaywrightBrowser()

  try {
    // Launch browser
    console.log('Launching browser...')
    await browser.launch({ headless: true })
    console.log('✅ Browser launched\n')

    // Test 1: Home Page
    console.log('Testing pages...\n')
    const homeTest = await testPage(
      browser,
      'Home Page',
      BASE_URL,
      ['nav', 'h1']  // Check nav and heading (always present, regardless of data)
    )
    results.push(homeTest)
    logResult(homeTest)

    // Test 2: Login Page
    const loginTest = await testPage(
      browser,
      'Login Page',
      `${BASE_URL}/login`,
      ['input[type="email"]', 'input[type="password"]', 'button[type="submit"]']
    )
    results.push(loginTest)
    logResult(loginTest)

    // Test 3: Register Page
    const registerTest = await testPage(
      browser,
      'Register Page',
      `${BASE_URL}/register`,
      ['input[type="email"]', 'input[type="password"]', 'button[type="submit"]']
    )
    results.push(registerTest)
    logResult(registerTest)

    // Test 4: Upload Page (should redirect to login)
    const uploadStart = Date.now()
    try {
      await browser.navigate(`${BASE_URL}/upload`)
      const currentUrl = browser.getUrl()

      if (currentUrl.includes('/login')) {
        results.push({
          name: 'Upload Page (Auth Redirect)',
          status: 'pass',
          duration: Date.now() - uploadStart
        })
        logResult(results[results.length - 1])
      } else {
        results.push({
          name: 'Upload Page (Auth Redirect)',
          status: 'fail',
          duration: Date.now() - uploadStart,
          error: 'Did not redirect to login'
        })
        logResult(results[results.length - 1])
      }
    } catch (error) {
      results.push({
        name: 'Upload Page (Auth Redirect)',
        status: 'fail',
        duration: Date.now() - uploadStart,
        error: error instanceof Error ? error.message : String(error)
      })
      logResult(results[results.length - 1])
    }

    // Test 5: Health Check Endpoint
    const healthStart = Date.now()
    try {
      await browser.navigate(`${BASE_URL}/health`)

      // Check if health endpoint returns JSON
      const bodyText = await browser.getVisibleText('body')

      if (bodyText.includes('status') || bodyText.includes('healthy')) {
        results.push({
          name: 'Health Check Endpoint',
          status: 'pass',
          duration: Date.now() - healthStart
        })
      } else {
        results.push({
          name: 'Health Check Endpoint',
          status: 'fail',
          duration: Date.now() - healthStart,
          error: 'Unexpected health check response'
        })
      }
      logResult(results[results.length - 1])
    } catch (error) {
      results.push({
        name: 'Health Check Endpoint',
        status: 'fail',
        duration: Date.now() - healthStart,
        error: error instanceof Error ? error.message : String(error)
      })
      logResult(results[results.length - 1])
    }

    // Test 6: Check API Documentation
    const docsStart = Date.now()
    try {
      await browser.navigate(`${BASE_URL}/docs`)
      await browser.waitForSelector('.swagger-ui', { timeout: 5000 })

      results.push({
        name: 'API Documentation (/docs)',
        status: 'pass',
        duration: Date.now() - docsStart
      })
      logResult(results[results.length - 1])
    } catch (error) {
      results.push({
        name: 'API Documentation (/docs)',
        status: 'fail',
        duration: Date.now() - docsStart,
        error: error instanceof Error ? error.message : String(error)
      })
      logResult(results[results.length - 1])
    }

    // Summary
    console.log('\n' + '='.repeat(50))
    console.log('📊 Test Summary')
    console.log('='.repeat(50))

    const passed = results.filter(r => r.status === 'pass').length
    const failed = results.filter(r => r.status === 'fail').length
    const skipped = results.filter(r => r.status === 'skip').length
    const totalDuration = results.reduce((sum, r) => sum + r.duration, 0)

    console.log(`Total Tests: ${results.length}`)
    console.log(`✅ Passed: ${passed}`)
    console.log(`❌ Failed: ${failed}`)
    console.log(`⚠️  Skipped: ${skipped}`)
    console.log(`⏱️  Total Duration: ${totalDuration}ms`)

    // Exit code
    if (failed > 0) {
      console.log('\n❌ Smoke tests failed!')
      process.exit(1)
    } else {
      console.log('\n✅ All smoke tests passed!')
      process.exit(0)
    }
  } catch (error) {
    console.error('\n💥 Fatal error:', error instanceof Error ? error.message : error)
    process.exit(1)
  } finally {
    await browser.close()
  }
}

// Run tests
if (import.meta.main) {
  main()
}

export { main }
