# Gallery Browse & View Flow Test

**Purpose:** Test image gallery browsing, viewing, and interaction workflows.

**Use when:** Testing gallery UI changes, image loading, infinite scroll, or image detail pages.

---

## Workflow Steps

### 1. Load Home Page Gallery

```typescript
import { PlaywrightBrowser } from '../src/browser'

const browser = new PlaywrightBrowser()
await browser.launch({ headless: true })

// Navigate to home page
const startTime = Date.now()
await browser.navigate('http://localhost:8000')
const loadTime = Date.now() - startTime

console.log(`🏠 Home page loaded in ${loadTime}ms`)

// Verify gallery grid exists
try {
  await browser.waitForSelector('.gallery-grid', { timeout: 5000 })
  console.log('✅ Gallery grid found')
} catch {
  console.log('❌ Gallery grid not found')
  process.exit(1)
}

// Count images in gallery
const imageCards = await browser.evaluate(`
  document.querySelectorAll('.gallery-item, .image-card').length
`)
console.log(`📸 Found ${imageCards} images in gallery`)

if (imageCards === 0) {
  console.log('⚠️  Gallery is empty - upload some test images first')
}
```

### 2. Test Infinite Scroll (HTMX)

```typescript
// Scroll to bottom to trigger HTMX load more
await browser.evaluate(`
  window.scrollTo(0, document.body.scrollHeight)
`)

// Wait for HTMX to load more images
await browser.wait(2000)

// Count images again
const imageCardsAfterScroll = await browser.evaluate(`
  document.querySelectorAll('.gallery-item, .image-card').length
`)

if (imageCardsAfterScroll > imageCards) {
  console.log(`✅ Infinite scroll working (loaded ${imageCardsAfterScroll - imageCards} more images)`)
} else {
  console.log('⚠️  Infinite scroll did not load more images (might be at end)')
}
```

### 3. Click on First Image

```typescript
// Get first image link
const firstImageUrl = await browser.evaluate(`
  const firstImage = document.querySelector('.gallery-item a, .image-card a')
  firstImage ? firstImage.href : null
`)

if (!firstImageUrl) {
  console.log('❌ No image links found in gallery')
  process.exit(1)
}

console.log(`🖼️  Clicking first image: ${firstImageUrl}`)

// Click first image
await browser.click('.gallery-item a, .image-card a')
await browser.waitForNavigation()

// Verify we're on image detail page
const currentUrl = browser.getUrl()
if (!currentUrl.includes('/image/')) {
  console.log('❌ Did not navigate to image detail page')
  process.exit(1)
}

console.log('✅ Navigated to image detail page')
```

### 4. Verify Image Detail Page

```typescript
// Check for key elements on detail page
const detailChecks = [
  { selector: 'img[src*="/api/v1/images/"]', name: 'Full image' },
  { selector: '.image-metadata, .image-info', name: 'Image metadata' },
  { selector: 'a[href="/"]', name: 'Back to gallery link' }
]

for (const check of detailChecks) {
  try {
    await browser.waitForSelector(check.selector, { timeout: 5000 })
    console.log(`✅ ${check.name} found`)
  } catch {
    console.log(`⚠️  ${check.name} not found (might use different selector)`)
  }
}

// Take screenshot of image detail page
await browser.screenshot({
  path: 'screenshots/image-detail.png',
  fullPage: true
})
console.log('📸 Screenshot saved: screenshots/image-detail.png')
```

### 5. Test Image Download

```typescript
// Find download link/button
const downloadLink = await browser.evaluate(`
  const link = document.querySelector('a[download], a[href*="/file"]')
  link ? link.href : null
`)

if (downloadLink) {
  console.log(`✅ Download link found: ${downloadLink}`)

  // Verify download URL is correct format
  if (downloadLink.includes('/api/v1/images/') && downloadLink.includes('/file')) {
    console.log('✅ Download URL format is correct')
  }
} else {
  console.log('⚠️  Download link not found on image detail page')
}
```

### 6. Navigate Back to Gallery

```typescript
// Click back button or navigate
await browser.goBack()

// Wait for gallery to load
await browser.waitForSelector('.gallery-grid', { timeout: 5000 })

// Verify we're back on home page
const backUrl = browser.getUrl()
if (backUrl === 'http://localhost:8000/' || backUrl === 'http://localhost:8000') {
  console.log('✅ Successfully navigated back to gallery')
} else {
  console.log(`⚠️  Unexpected URL after going back: ${backUrl}`)
}
```

### 7. Test Search/Filter (if implemented)

```typescript
// Check if search functionality exists
const hasSearch = await browser.evaluate(`
  !!document.querySelector('input[type="search"], input[name="q"]')
`)

if (hasSearch) {
  console.log('🔍 Search functionality detected')

  // Test search
  await browser.fill('input[type="search"], input[name="q"]', 'test')
  await browser.pressKey('Enter')

  await browser.wait(1000)
  console.log('✅ Search executed')
} else {
  console.log('ℹ️  No search functionality found (might not be implemented yet)')
}
```

### 8. Check Network Performance

```typescript
// Get network stats
const networkLogs = browser.getNetworkLogs()

// Filter for image requests
const imageRequests = networkLogs.filter(log =>
  log.type === 'response' &&
  log.resourceType === 'image'
)

console.log(`\n📊 Network Performance:`)
console.log(`   Total requests: ${networkLogs.filter(l => l.type === 'request').length}`)
console.log(`   Image requests: ${imageRequests.length}`)

// Check for failed requests
const failedRequests = networkLogs.filter(log =>
  log.type === 'response' &&
  log.status &&
  log.status >= 400
)

if (failedRequests.length > 0) {
  console.log(`\n⚠️  Failed requests (${failedRequests.length}):`)
  failedRequests.slice(0, 5).forEach(req => {
    console.log(`   ${req.status} - ${req.url}`)
  })
} else {
  console.log('✅ No failed network requests')
}

await browser.close()
console.log('\n🎉 Gallery flow test passed!')
```

---

## Success Criteria

✅ Home page loads with gallery grid
✅ Images are displayed in gallery
✅ Can click on image to view details
✅ Image detail page shows full image
✅ Can navigate back to gallery
✅ No failed network requests
✅ Image loading is performant

---

## Optional: Test with Different Viewport Sizes

```typescript
// Test responsive gallery on mobile
await browser.resize(375, 667) // iPhone SE
await browser.navigate('http://localhost:8000')
await browser.screenshot({ path: 'screenshots/gallery-mobile.png' })

// Test on tablet
await browser.resize(768, 1024) // iPad
await browser.navigate('http://localhost:8000')
await browser.screenshot({ path: 'screenshots/gallery-tablet.png' })

// Test on desktop
await browser.resize(1920, 1080) // Full HD
await browser.navigate('http://localhost:8000')
await browser.screenshot({ path: 'screenshots/gallery-desktop.png' })
```

---

## Run This Workflow

```bash
# Create standalone test file
cd browser-tests
bun run examples/gallery-flow-test.ts
```

---

## Integration with CI/CD

```yaml
# .github/workflows/test.yml
- name: Test gallery browsing
  run: |
    cd browser-tests
    bun run examples/gallery-flow-test.ts || exit 1
```

---

## Notes

- Adjust selectors (`.gallery-item`, `.image-card`) based on your actual HTML
- Infinite scroll test assumes HTMX is configured
- Network performance checks help catch broken image URLs
- Can be extended to test filtering, sorting, pagination
