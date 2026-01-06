#!/usr/bin/env bun

/**
 * Image Gallery CLI Testing Tool
 *
 * Code-first browser automation for Image Hosting App
 * Following kai-browser-skill pattern for 99% token savings
 *
 * Usage:
 *   bun run tools/gallery-test.ts screenshot <url> [output-path]
 *   bun run tools/gallery-test.ts verify-home [base-url]
 *   bun run tools/gallery-test.ts verify-upload [base-url]
 *   bun run tools/gallery-test.ts verify-login [base-url]
 *   bun run tools/gallery-test.ts verify-register [base-url]
 *   bun run tools/gallery-test.ts test-image-upload <base-url> <image-path>
 *
 * Examples:
 *   bun run tools/gallery-test.ts screenshot http://localhost:8000 screenshots/home.png
 *   bun run tools/gallery-test.ts verify-home http://localhost:8000
 *   bun run tools/gallery-test.ts verify-upload http://localhost:8000
 *   bun run tools/gallery-test.ts test-image-upload http://localhost:8000 test-image.jpg
 */

import { PlaywrightBrowser } from '../src/browser'

const DEFAULT_BASE_URL = 'http://localhost:8000'

async function screenshot(url: string, outputPath?: string) {
  const browser = new PlaywrightBrowser()

  try {
    console.log(`📸 Taking screenshot of ${url}`)
    await browser.launch({ headless: true })
    await browser.navigate(url)

    const path = outputPath || `screenshot-${Date.now()}.png`
    await browser.screenshot({ path, fullPage: true })

    console.log(`✅ Screenshot saved to: ${path}`)
    process.exit(0)
  } catch (error) {
    console.error(`❌ Screenshot failed:`, error instanceof Error ? error.message : error)
    process.exit(1)
  } finally {
    await browser.close()
  }
}

async function verifyHome(baseUrl: string = DEFAULT_BASE_URL) {
  const browser = new PlaywrightBrowser()

  try {
    console.log('🏠 Verifying Home Page...\n')
    await browser.launch({ headless: true })

    const startTime = Date.now()
    await browser.navigate(baseUrl)
    const loadTime = Date.now() - startTime

    console.log(`✅ Page loaded in ${loadTime}ms`)

    // Verify title
    const title = await browser.getTitle()
    console.log(`📄 Title: "${title}"`)

    // Verify key elements
    const checks = [
      { selector: 'nav', name: 'Navigation bar' },
      { selector: '.masonry-grid', name: 'Gallery grid' },
      { selector: 'a[href="/upload"]', name: 'Upload link' },
      { selector: 'footer', name: 'Footer' }
    ]

    for (const check of checks) {
      try {
        await browser.waitForSelector(check.selector, { timeout: 5000 })
        console.log(`✅ ${check.name} found`)
      } catch {
        console.log(`❌ ${check.name} NOT found`)
        process.exit(1)
      }
    }

    // Check for console errors
    const errors = browser.getConsoleLogs({ type: 'error' })
    if (errors.length > 0) {
      console.log(`\n⚠️  Console errors (${errors.length}):`)
      errors.slice(0, 3).forEach(err => console.log(`   - ${err.text.slice(0, 100)}`))
    } else {
      console.log(`\n✅ No console errors`)
    }

    console.log('\n🎉 Home page verification passed!')
    process.exit(0)
  } catch (error) {
    console.error(`❌ Verification failed:`, error instanceof Error ? error.message : error)
    process.exit(1)
  } finally {
    await browser.close()
  }
}

async function verifyUpload(baseUrl: string = DEFAULT_BASE_URL) {
  const browser = new PlaywrightBrowser()

  try {
    console.log('📤 Verifying Upload Page...\n')
    await browser.launch({ headless: true })

    await browser.navigate(`${baseUrl}/upload`)
    console.log(`✅ Navigated to upload page`)

    // Should redirect to login if not authenticated
    const currentUrl = browser.getUrl()
    if (currentUrl.includes('/login')) {
      console.log('✅ Correctly redirects to login when not authenticated')
      process.exit(0)
    }

    // If logged in, verify upload form elements
    const checks = [
      { selector: 'input[type="file"]', name: 'File input' },
      { selector: 'button[type="submit"]', name: 'Submit button' }
    ]

    for (const check of checks) {
      try {
        await browser.waitForSelector(check.selector, { timeout: 5000 })
        console.log(`✅ ${check.name} found`)
      } catch {
        console.log(`❌ ${check.name} NOT found`)
        process.exit(1)
      }
    }

    console.log('\n🎉 Upload page verification passed!')
    process.exit(0)
  } catch (error) {
    console.error(`❌ Verification failed:`, error instanceof Error ? error.message : error)
    process.exit(1)
  } finally {
    await browser.close()
  }
}

async function verifyLogin(baseUrl: string = DEFAULT_BASE_URL) {
  const browser = new PlaywrightBrowser()

  try {
    console.log('🔐 Verifying Login Page...\n')
    await browser.launch({ headless: true })

    await browser.navigate(`${baseUrl}/login`)
    console.log(`✅ Navigated to login page`)

    const title = await browser.getTitle()
    console.log(`📄 Title: "${title}"`)

    // Verify login form elements
    const checks = [
      { selector: 'input[type="email"]', name: 'Email input' },
      { selector: 'input[type="password"]', name: 'Password input' },
      { selector: 'button[type="submit"]', name: 'Submit button' },
      { selector: 'a[href="/register"]', name: 'Register link' }
    ]

    for (const check of checks) {
      try {
        await browser.waitForSelector(check.selector, { timeout: 5000 })
        console.log(`✅ ${check.name} found`)
      } catch {
        console.log(`❌ ${check.name} NOT found`)
        process.exit(1)
      }
    }

    console.log('\n🎉 Login page verification passed!')
    process.exit(0)
  } catch (error) {
    console.error(`❌ Verification failed:`, error instanceof Error ? error.message : error)
    process.exit(1)
  } finally {
    await browser.close()
  }
}

async function verifyRegister(baseUrl: string = DEFAULT_BASE_URL) {
  const browser = new PlaywrightBrowser()

  try {
    console.log('📝 Verifying Register Page...\n')
    await browser.launch({ headless: true })

    await browser.navigate(`${baseUrl}/register`)
    console.log(`✅ Navigated to register page`)

    const title = await browser.getTitle()
    console.log(`📄 Title: "${title}"`)

    // Verify registration form elements
    const checks = [
      { selector: 'input[type="email"]', name: 'Email input' },
      { selector: 'input[type="password"]', name: 'Password input' },
      { selector: 'button[type="submit"]', name: 'Submit button' },
      { selector: 'a[href="/login"]', name: 'Login link' }
    ]

    for (const check of checks) {
      try {
        await browser.waitForSelector(check.selector, { timeout: 5000 })
        console.log(`✅ ${check.name} found`)
      } catch {
        console.log(`❌ ${check.name} NOT found`)
        process.exit(1)
      }
    }

    console.log('\n🎉 Register page verification passed!')
    process.exit(0)
  } catch (error) {
    console.error(`❌ Verification failed:`, error instanceof Error ? error.message : error)
    process.exit(1)
  } finally {
    await browser.close()
  }
}

// Main CLI router
const command = process.argv[2]
const arg1 = process.argv[3]
const arg2 = process.argv[4]

if (!command) {
  console.error(`
Usage:
  bun run tools/gallery-test.ts screenshot <url> [output-path]
  bun run tools/gallery-test.ts verify-home [base-url]
  bun run tools/gallery-test.ts verify-upload [base-url]
  bun run tools/gallery-test.ts verify-login [base-url]
  bun run tools/gallery-test.ts verify-register [base-url]

Examples:
  bun run tools/gallery-test.ts screenshot http://localhost:8000 screenshots/home.png
  bun run tools/gallery-test.ts verify-home http://localhost:8000
  bun run tools/gallery-test.ts verify-login
  `)
  process.exit(1)
}

switch (command) {
  case 'screenshot':
    if (!arg1) {
      console.error('Error: URL required for screenshot command')
      process.exit(1)
    }
    await screenshot(arg1, arg2)
    break

  case 'verify-home':
    await verifyHome(arg1)
    break

  case 'verify-upload':
    await verifyUpload(arg1)
    break

  case 'verify-login':
    await verifyLogin(arg1)
    break

  case 'verify-register':
    await verifyRegister(arg1)
    break

  default:
    console.error(`Unknown command: ${command}`)
    process.exit(1)
}
