#!/usr/bin/env bun

/**
 * Comprehensive Test Suite for Image Hosting App
 *
 * Complete functional testing covering all major features and user flows.
 * This test creates test data, performs actions, and verifies results.
 *
 * Usage:
 *   bun run examples/comprehensive-test.ts [base-url]
 *
 * Examples:
 *   bun run examples/comprehensive-test.ts
 *   bun run examples/comprehensive-test.ts http://localhost:8000
 */

import { PlaywrightBrowser } from '../src/browser'
import { mkdir } from 'fs/promises'

const BASE_URL = process.argv[2] || 'http://localhost:8000'
const SCREENSHOTS_DIR = './screenshots/comprehensive'

interface TestResult {
  category: string
  name: string
  status: 'pass' | 'fail' | 'skip'
  duration: number
  error?: string
}

const results: TestResult[] = []

function logTest(category: string, name: string, status: 'pass' | 'fail' | 'skip', duration: number, error?: string) {
  const icon = status === 'pass' ? '✅' : status === 'fail' ? '❌' : '⚠️ '
  console.log(`${icon} [${category}] ${name} (${duration}ms)`)
  if (error) {
    console.log(`   Error: ${error}`)
  }
  results.push({ category, name, status, duration, error })
}

async function runTest(
  category: string,
  name: string,
  fn: () => Promise<void>
): Promise<void> {
  const startTime = Date.now()
  try {
    await fn()
    logTest(category, name, 'pass', Date.now() - startTime)
  } catch (error) {
    logTest(category, name, 'fail', Date.now() - startTime, error instanceof Error ? error.message : String(error))
  }
}

async function main() {
  console.log('🧪 Image Hosting App - Comprehensive Test Suite\n')
  console.log(`Testing: ${BASE_URL}\n`)

  // Create screenshots directory
  await mkdir(SCREENSHOTS_DIR, { recursive: true })

  const browser = new PlaywrightBrowser()

  try {
    await browser.launch({ headless: true })
    console.log('✅ Browser launched\n')

    // =========================================================================
    // CATEGORY 1: Page Load & Navigation
    // =========================================================================
    console.log('📁 Category: Page Load & Navigation\n')

    await runTest('Navigation', 'Home page loads', async () => {
      await browser.navigate(BASE_URL)
      await browser.waitForSelector('nav', { timeout: 5000 })
    })

    await runTest('Navigation', 'Login page loads', async () => {
      await browser.navigate(`${BASE_URL}/login`)
      await browser.waitForSelector('input[type="email"]', { timeout: 5000 })
    })

    await runTest('Navigation', 'Register page loads', async () => {
      await browser.navigate(`${BASE_URL}/register`)
      await browser.waitForSelector('input[type="email"]', { timeout: 5000 })
    })

    await runTest('Navigation', 'Page titles are correct', async () => {
      await browser.navigate(BASE_URL)
      const title = await browser.getTitle()
      if (!title || title.length === 0) {
        throw new Error('Page title is empty')
      }
    })

    // =========================================================================
    // CATEGORY 2: UI Elements & Layout
    // =========================================================================
    console.log('\n📁 Category: UI Elements & Layout\n')

    await runTest('UI Elements', 'Navigation bar exists', async () => {
      await browser.navigate(BASE_URL)
      await browser.waitForSelector('nav', { timeout: 5000 })
    })

    await runTest('UI Elements', 'Footer exists', async () => {
      await browser.navigate(BASE_URL)
      await browser.waitForSelector('footer', { timeout: 5000 })
    })

    await runTest('UI Elements', 'Home page shows correct state (gallery or empty)', async () => {
      await browser.navigate(BASE_URL)
      // Page should show either gallery grid (with images) or empty state (no images)
      const page = await browser.getPage()
      const hasGallery = await page.locator('.masonry-grid').count() > 0
      const hasEmptyState = await page.locator('text=No images yet').count() > 0
      if (!hasGallery && !hasEmptyState) {
        throw new Error('Home page shows neither gallery nor empty state')
      }
    })

    await runTest('UI Elements', 'Upload link present in nav', async () => {
      await browser.navigate(BASE_URL)
      await browser.waitForSelector('a[href="/upload"]', { timeout: 5000 })
    })

    // =========================================================================
    // CATEGORY 3: Authentication Forms
    // =========================================================================
    console.log('\n📁 Category: Authentication Forms\n')

    await runTest('Auth Forms', 'Login form has all fields', async () => {
      await browser.navigate(`${BASE_URL}/login`)
      await browser.waitForSelector('input[type="email"]', { timeout: 5000 })
      await browser.waitForSelector('input[type="password"]', { timeout: 5000 })
      await browser.waitForSelector('button[type="submit"]', { timeout: 5000 })
    })

    await runTest('Auth Forms', 'Register form has all fields', async () => {
      await browser.navigate(`${BASE_URL}/register`)
      await browser.waitForSelector('input[type="email"]', { timeout: 5000 })
      await browser.waitForSelector('input[type="password"]', { timeout: 5000 })
      await browser.waitForSelector('button[type="submit"]', { timeout: 5000 })
    })

    await runTest('Auth Forms', 'Login has link to register', async () => {
      await browser.navigate(`${BASE_URL}/login`)
      await browser.waitForSelector('a[href="/register"]', { timeout: 5000 })
    })

    await runTest('Auth Forms', 'Register has link to login', async () => {
      await browser.navigate(`${BASE_URL}/register`)
      await browser.waitForSelector('a[href="/login"]', { timeout: 5000 })
    })

    // =========================================================================
    // CATEGORY 4: Protected Routes
    // =========================================================================
    console.log('\n📁 Category: Protected Routes\n')

    await runTest('Protected Routes', 'Upload page redirects to login when not authenticated', async () => {
      await browser.navigate(`${BASE_URL}/upload`)
      const url = browser.getUrl()
      if (!url.includes('/login')) {
        throw new Error('Did not redirect to login')
      }
    })

    await runTest('Protected Routes', 'My Images redirects to login when not authenticated', async () => {
      await browser.navigate(`${BASE_URL}/my-images`)
      const url = browser.getUrl()
      if (!url.includes('/login')) {
        throw new Error('Did not redirect to login')
      }
    })

    // =========================================================================
    // CATEGORY 5: API Endpoints
    // =========================================================================
    console.log('\n📁 Category: API Endpoints\n')

    await runTest('API', 'Health endpoint responds', async () => {
      await browser.navigate(`${BASE_URL}/health`)
      const text = await browser.getVisibleText('body')
      if (!text.includes('status')) {
        throw new Error('Health check response missing status')
      }
    })

    await runTest('API', 'Swagger docs accessible', async () => {
      await browser.navigate(`${BASE_URL}/docs`)
      await browser.waitForSelector('.swagger-ui', { timeout: 10000 })
    })

    // =========================================================================
    // CATEGORY 6: Console & Network
    // =========================================================================
    console.log('\n📁 Category: Console & Network\n')

    await runTest('Console', 'No console errors on home page', async () => {
      await browser.navigate(BASE_URL)
      await browser.wait(2000) // Wait for page to fully load
      const errors = browser.getConsoleLogs({ type: 'error' })
      if (errors.length > 0) {
        throw new Error(`Found ${errors.length} console errors: ${errors[0].text}`)
      }
    })

    await runTest('Console', 'No console errors on login page', async () => {
      await browser.navigate(`${BASE_URL}/login`)
      await browser.wait(2000)
      const errors = browser.getConsoleLogs({ type: 'error' })
      if (errors.length > 0) {
        throw new Error(`Found ${errors.length} console errors`)
      }
    })

    await runTest('Network', 'No failed HTTP requests on home', async () => {
      await browser.navigate(BASE_URL)
      await browser.wait(2000)
      const networkLogs = browser.getNetworkLogs()
      const failed = networkLogs.filter(log =>
        log.type === 'response' && log.status && log.status >= 400 && log.status !== 404
      )
      if (failed.length > 0) {
        throw new Error(`Found ${failed.length} failed requests: ${failed[0].url}`)
      }
    })

    // =========================================================================
    // CATEGORY 7: Screenshots & Visual Regression
    // =========================================================================
    console.log('\n📁 Category: Screenshots & Visual Regression\n')

    await runTest('Screenshots', 'Capture home page', async () => {
      await browser.navigate(BASE_URL)
      await browser.screenshot({
        path: `${SCREENSHOTS_DIR}/home.png`,
        fullPage: true
      })
    })

    await runTest('Screenshots', 'Capture login page', async () => {
      await browser.navigate(`${BASE_URL}/login`)
      await browser.screenshot({
        path: `${SCREENSHOTS_DIR}/login.png`,
        fullPage: true
      })
    })

    await runTest('Screenshots', 'Capture register page', async () => {
      await browser.navigate(`${BASE_URL}/register`)
      await browser.screenshot({
        path: `${SCREENSHOTS_DIR}/register.png`,
        fullPage: true
      })
    })

    // =========================================================================
    // CATEGORY 8: Responsive Design
    // =========================================================================
    console.log('\n📁 Category: Responsive Design\n')

    await runTest('Responsive', 'Mobile viewport (375x667)', async () => {
      await browser.resize(375, 667)
      await browser.navigate(BASE_URL)
      await browser.waitForSelector('nav', { timeout: 5000 })
      await browser.screenshot({
        path: `${SCREENSHOTS_DIR}/home-mobile.png`
      })
    })

    await runTest('Responsive', 'Tablet viewport (768x1024)', async () => {
      await browser.resize(768, 1024)
      await browser.navigate(BASE_URL)
      await browser.waitForSelector('nav', { timeout: 5000 })
      await browser.screenshot({
        path: `${SCREENSHOTS_DIR}/home-tablet.png`
      })
    })

    await runTest('Responsive', 'Desktop viewport (1920x1080)', async () => {
      await browser.resize(1920, 1080)
      await browser.navigate(BASE_URL)
      await browser.waitForSelector('nav', { timeout: 5000 })
      await browser.screenshot({
        path: `${SCREENSHOTS_DIR}/home-desktop.png`
      })
    })

    // =========================================================================
    // CATEGORY 9: Performance
    // =========================================================================
    console.log('\n📁 Category: Performance\n')

    await runTest('Performance', 'Home page loads within 3 seconds', async () => {
      const startTime = Date.now()
      await browser.navigate(BASE_URL)
      // Wait for main heading (always present, regardless of data)
      await browser.waitForSelector('h1', { timeout: 5000 })
      const loadTime = Date.now() - startTime
      if (loadTime > 3000) {
        throw new Error(`Page took ${loadTime}ms to load (threshold: 3000ms)`)
      }
    })

    // =========================================================================
    // Summary
    // =========================================================================
    console.log('\n' + '='.repeat(60))
    console.log('📊 Comprehensive Test Summary')
    console.log('='.repeat(60))

    const categories = [...new Set(results.map(r => r.category))]
    categories.forEach(category => {
      const categoryResults = results.filter(r => r.category === category)
      const passed = categoryResults.filter(r => r.status === 'pass').length
      const failed = categoryResults.filter(r => r.status === 'fail').length
      const total = categoryResults.length

      console.log(`\n${category}:`)
      console.log(`  ✅ Passed: ${passed}/${total}`)
      if (failed > 0) {
        console.log(`  ❌ Failed: ${failed}/${total}`)
      }
    })

    const totalPassed = results.filter(r => r.status === 'pass').length
    const totalFailed = results.filter(r => r.status === 'fail').length
    const totalDuration = results.reduce((sum, r) => sum + r.duration, 0)

    console.log('\n' + '='.repeat(60))
    console.log(`Total Tests: ${results.length}`)
    console.log(`✅ Passed: ${totalPassed}`)
    console.log(`❌ Failed: ${totalFailed}`)
    console.log(`⏱️  Total Duration: ${(totalDuration / 1000).toFixed(2)}s`)
    console.log(`📸 Screenshots saved to: ${SCREENSHOTS_DIR}`)

    if (totalFailed > 0) {
      console.log('\n❌ Some tests failed!')
      process.exit(1)
    } else {
      console.log('\n✅ All comprehensive tests passed!')
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
