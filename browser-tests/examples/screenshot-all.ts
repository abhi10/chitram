#!/usr/bin/env bun

/**
 * Screenshot All Pages - Visual Regression Testing
 *
 * Captures screenshots of all pages across multiple viewports.
 * Use this to create visual baselines or detect visual regressions.
 *
 * Usage:
 *   bun run examples/screenshot-all.ts [base-url] [output-dir]
 *
 * Examples:
 *   bun run examples/screenshot-all.ts
 *   bun run examples/screenshot-all.ts http://localhost:8000
 *   bun run examples/screenshot-all.ts http://localhost:8000 ./baselines
 */

import { PlaywrightBrowser } from '../src/browser'
import { mkdir } from 'fs/promises'
import { join } from 'path'

const BASE_URL = process.argv[2] || 'http://localhost:8000'
const OUTPUT_DIR = process.argv[3] || './screenshots/visual-regression'

interface Page {
  name: string
  url: string
  waitFor?: string
}

interface Viewport {
  name: string
  width: number
  height: number
  description: string
}

const PAGES: Page[] = [
  { name: 'home', url: '/', waitFor: '.gallery-grid' },
  { name: 'login', url: '/login', waitFor: 'input[type="email"]' },
  { name: 'register', url: '/register', waitFor: 'input[type="email"]' },
  { name: 'upload-redirect', url: '/upload', waitFor: 'input[type="email"]' }, // Will redirect to login
  { name: 'health', url: '/health' },
  { name: 'docs', url: '/docs', waitFor: '.swagger-ui' }
]

const VIEWPORTS: Viewport[] = [
  { name: 'mobile', width: 375, height: 667, description: 'iPhone SE' },
  { name: 'mobile-large', width: 414, height: 896, description: 'iPhone 11 Pro Max' },
  { name: 'tablet', width: 768, height: 1024, description: 'iPad' },
  { name: 'tablet-landscape', width: 1024, height: 768, description: 'iPad Landscape' },
  { name: 'desktop', width: 1280, height: 720, description: 'Desktop HD' },
  { name: 'desktop-large', width: 1920, height: 1080, description: 'Desktop Full HD' }
]

async function main() {
  console.log('📸 Screenshot All Pages - Visual Regression Testing\n')
  console.log(`Target URL: ${BASE_URL}`)
  console.log(`Output Directory: ${OUTPUT_DIR}\n`)

  // Create output directory
  await mkdir(OUTPUT_DIR, { recursive: true })
  console.log(`✅ Created output directory\n`)

  const browser = new PlaywrightBrowser()
  let screenshotCount = 0
  let errorCount = 0

  try {
    await browser.launch({ headless: true })
    console.log('✅ Browser launched\n')

    // For each viewport
    for (const viewport of VIEWPORTS) {
      console.log(`📱 Viewport: ${viewport.name} (${viewport.width}x${viewport.height}) - ${viewport.description}`)
      await browser.resize(viewport.width, viewport.height)

      // Create viewport directory
      const viewportDir = join(OUTPUT_DIR, viewport.name)
      await mkdir(viewportDir, { recursive: true })

      // For each page
      for (const page of PAGES) {
        try {
          const fullUrl = `${BASE_URL}${page.url}`
          process.stdout.write(`  📄 ${page.name.padEnd(20)} `)

          // Navigate to page
          await browser.navigate(fullUrl)

          // Wait for specific element if specified
          if (page.waitFor) {
            try {
              await browser.waitForSelector(page.waitFor, { timeout: 5000 })
            } catch {
              // Element not found, but continue with screenshot
            }
          } else {
            // General wait for page to stabilize
            await browser.wait(1000)
          }

          // Take screenshot
          const filename = `${page.name}.png`
          const filepath = join(viewportDir, filename)

          await browser.screenshot({
            path: filepath,
            fullPage: true
          })

          screenshotCount++
          console.log(`✅ ${filename}`)
        } catch (error) {
          errorCount++
          console.log(`❌ Error: ${error instanceof Error ? error.message : error}`)
        }
      }

      console.log('')
    }

    // Summary
    console.log('='.repeat(60))
    console.log('📊 Screenshot Summary')
    console.log('='.repeat(60))
    console.log(`Total Screenshots: ${screenshotCount}`)
    console.log(`Errors: ${errorCount}`)
    console.log(`Output Directory: ${OUTPUT_DIR}`)
    console.log('')

    // List generated files
    console.log('📁 Generated Files:\n')
    for (const viewport of VIEWPORTS) {
      console.log(`  ${viewport.name}/`)
      for (const page of PAGES) {
        console.log(`    - ${page.name}.png`)
      }
    }

    console.log('\n💡 Next Steps:')
    console.log('  1. Review screenshots in the output directory')
    console.log('  2. Use these as baseline for visual regression testing')
    console.log('  3. Compare future screenshots with these baselines')
    console.log('  4. Tools: https://github.com/mapbox/pixelmatch or Percy.io')

    if (errorCount > 0) {
      console.log(`\n⚠️  ${errorCount} screenshots failed to capture`)
      process.exit(1)
    } else {
      console.log('\n✅ All screenshots captured successfully!')
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
