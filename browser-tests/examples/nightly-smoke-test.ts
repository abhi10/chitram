#!/usr/bin/env bun

/**
 * Nightly Smoke Test
 *
 * Runs critical health checks against the production website.
 * Designed to catch outages like Supabase resource pauses.
 *
 * Usage:
 *   bun run examples/nightly-smoke-test.ts [base-url] [email-to]
 *
 * Examples:
 *   bun run examples/nightly-smoke-test.ts
 *   bun run examples/nightly-smoke-test.ts https://chitram.io admin@example.com
 *   bun run examples/nightly-smoke-test.ts https://staging.example.com alert@example.com
 *
 * Environment Variables:
 *   - BASE_URL: Override default base URL
 *   - ALERT_EMAIL: Email address for failure alerts
 *   - GITHUB_TOKEN: (Optional) GitHub token for creating issues
 */

import { checkHealth, isHealthy, generateHealthSummary } from '../src/modules/health-checker'
import { sendAlert, buildHealthAlertPayload, type AlertConfig } from '../src/modules/alerter'

// Configuration with sensible defaults
const config = {
  baseUrl: process.env.BASE_URL || process.argv[2] || 'https://chitram.io',
  alertEmail: process.env.ALERT_EMAIL || process.argv[3] || 'arajubuild@gmail.com',
  timeout: 10000,
  retries: 2,
  retryDelay: 1000,
}

/**
 * Main orchestration function
 * Runs health checks and sends alerts if needed
 */
async function runNightlySmoke(): Promise<void> {
  console.log('🌙 Starting Nightly Smoke Test')
  console.log(`📍 Target: ${config.baseUrl}`)
  console.log(`📧 Alert to: ${config.alertEmail}`)
  console.log('───────────────────────────────────────────────────────\n')

  try {
    // Run health checks
    const results = await checkHealth(config.baseUrl, {
      endpoints: [
        { name: 'Health Endpoint', path: '/health' },
        { name: 'Landing Page', path: '/' },
      ],
      timeout: config.timeout,
      retries: config.retries,
      retryDelay: config.retryDelay,
    })

    // Display results
    console.log(generateHealthResults(results))

    // Check if all passed
    if (isHealthy(results)) {
      console.log('✅ All checks passed! Website is healthy.\n')
      process.exit(0)
    }

    // Some checks failed - send alert
    console.log('❌ Health checks failed. Sending alert...\n')
    await sendAlertOnFailure(results)
    process.exit(1)
  } catch (error) {
    console.error('💥 Unexpected error during smoke test:')
    console.error(error)
    process.exit(2)
  }
}

/**
 * Format results for display
 */
function generateHealthResults(
  results: Array<{
    name: string
    url: string
    status: 'pass' | 'fail'
    statusCode?: number
    responseTime: number
    error?: string
    timestamp: Date
  }>
): string {
  const lines = [
    '═══════════════════════════════════════════════════════',
    '📊 Health Check Results',
    '═══════════════════════════════════════════════════════',
  ]

  for (const result of results) {
    const statusIcon = result.status === 'pass' ? '✅' : '❌'
    const error = result.error ? ` (${result.error})` : ''
    lines.push(
      `${statusIcon} ${result.name} - ${result.responseTime}ms${error}`
    )
  }

  const passCount = results.filter(r => r.status === 'pass').length
  lines.push('───────────────────────────────────────────────────────')
  lines.push(`Total: ${passCount}/${results.length} passed`)
  lines.push('═══════════════════════════════════════════════════════')

  return lines.join('\n')
}

/**
 * Send alert when health checks fail
 */
async function sendAlertOnFailure(
  results: Array<{
    name: string
    url: string
    status: 'pass' | 'fail'
    statusCode?: number
    responseTime: number
    error?: string
    timestamp: Date
  }>
): Promise<void> {
  // Build the alert message
  const failedChecks = results.filter(r => r.status === 'fail')
  const summary = `
Website Health Check FAILED
═════════════════════════════════════════════

Website: ${config.baseUrl}
Time: ${new Date().toISOString()}

Failed Checks: ${failedChecks.length}/${results.length}

${failedChecks.map(check => `❌ ${check.name}
   URL: ${check.url}
   Error: ${check.error || 'No response'}
   Response Time: ${check.responseTime}ms`).join('\n\n')}

═════════════════════════════════════════════
This is an automated alert from the nightly smoke test.
Please check the website immediately!

Common causes:
- Supabase resources paused (check dashboard)
- Database connection issues
- Storage backend (MinIO/S3) unavailable
- Network connectivity problems
`

  // Build alert configuration
  const alertConfig: AlertConfig = {
    console: true, // Always log to console
    email: {
      to: config.alertEmail,
    },
  }

  // Add GitHub credentials if available (for creating issues)
  if (process.env.GITHUB_TOKEN) {
    alertConfig.github = {
      token: process.env.GITHUB_TOKEN,
      owner: 'abhi10',
      repo: 'chitram',
    }
  }

  // Send the alert
  await sendAlert(alertConfig, {
    title: `❌ Nightly Smoke Test Failed: ${config.baseUrl}`,
    message: summary,
    severity: 'error',
    timestamp: new Date(),
    url: config.baseUrl,
    metadata: {
      failedChecks: failedChecks.length,
      totalChecks: results.length,
      failureDetails: failedChecks,
    },
  })
}

// Run the smoke test
runNightlySmoke().catch(error => {
  console.error('Fatal error:', error)
  process.exit(2)
})
