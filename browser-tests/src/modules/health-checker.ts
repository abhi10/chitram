/**
 * Health Checker Module
 *
 * Reusable module for checking website health and availability.
 * Tests critical endpoints and returns structured results.
 *
 * DRY principles:
 * - Single responsibility: Only handles health checks
 * - Configurable: Works with any base URL
 * - Testable: Pure functions with clear return types
 * - Reusable: Can be imported by multiple scripts
 */

export interface HealthCheckResult {
  name: string
  url: string
  status: 'pass' | 'fail'
  statusCode?: number
  responseTime: number
  error?: string
  timestamp: Date
}

export interface HealthCheckOptions {
  timeout?: number
  retries?: number
  retryDelay?: number
}

const DEFAULT_OPTIONS: Required<HealthCheckOptions> = {
  timeout: 10000,
  retries: 1,
  retryDelay: 1000,
}

/**
 * Check a single endpoint with retry logic
 */
async function checkEndpoint(
  name: string,
  url: string,
  options: Required<HealthCheckOptions>
): Promise<HealthCheckResult> {
  const startTime = Date.now()
  let lastError: string | undefined

  for (let attempt = 1; attempt <= options.retries; attempt++) {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), options.timeout)

      const response = await fetch(url, {
        signal: controller.signal,
        redirect: 'follow',
      })

      clearTimeout(timeout)

      const responseTime = Date.now() - startTime
      const success = response.ok

      return {
        name,
        url,
        status: success ? 'pass' : 'fail',
        statusCode: response.status,
        responseTime,
        timestamp: new Date(),
        error: success ? undefined : `HTTP ${response.status}`,
      }
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error)

      // If we have more retries, wait and try again
      if (attempt < options.retries) {
        await new Promise(resolve => setTimeout(resolve, options.retryDelay))
      }
    }
  }

  // All retries failed
  const responseTime = Date.now() - startTime
  return {
    name,
    url,
    status: 'fail',
    responseTime,
    error: lastError,
    timestamp: new Date(),
  }
}

/**
 * Run health checks for multiple endpoints
 *
 * @example
 * const results = await checkHealth('https://chitram.io', {
 *   endpoints: [
 *     { name: 'Health Check', path: '/health' },
 *     { name: 'Landing Page', path: '/' }
 *   ]
 * })
 */
export async function checkHealth(
  baseUrl: string,
  options?: {
    endpoints?: Array<{ name: string; path: string }>
    timeout?: number
    retries?: number
    retryDelay?: number
  }
): Promise<HealthCheckResult[]> {
  const mergedOptions = {
    ...DEFAULT_OPTIONS,
    ...options,
  }

  const defaultEndpoints = [
    { name: 'Health Endpoint', path: '/health' },
    { name: 'Landing Page', path: '/' },
  ]

  const endpoints = options?.endpoints || defaultEndpoints

  const results = await Promise.all(
    endpoints.map(endpoint => {
      const fullUrl = new URL(endpoint.path, baseUrl).toString()
      return checkEndpoint(endpoint.name, fullUrl, {
        timeout: mergedOptions.timeout,
        retries: mergedOptions.retries,
        retryDelay: mergedOptions.retryDelay,
      })
    })
  )

  return results
}

/**
 * Check if all health checks passed
 */
export function isHealthy(results: HealthCheckResult[]): boolean {
  return results.every(result => result.status === 'pass')
}

/**
 * Format health check results for logging/display
 */
export function formatHealthResults(results: HealthCheckResult[]): string {
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
 * Generate health check summary for alerts
 */
export function generateHealthSummary(
  baseUrl: string,
  results: HealthCheckResult[]
): string {
  const healthy = isHealthy(results)
  const passCount = results.filter(r => r.status === 'pass').length
  const timestamp = new Date().toISOString()

  let summary = `Website Health Check Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: ${healthy ? '✅ HEALTHY' : '❌ UNHEALTHY'}
Website: ${baseUrl}
Time: ${timestamp}
Passed: ${passCount}/${results.length}

Details:
`

  for (const result of results) {
    const status = result.status === 'pass' ? '✅ PASS' : '❌ FAIL'
    const error = result.error ? `\n  Error: ${result.error}` : ''
    summary += `
${status}: ${result.name}
  URL: ${result.url}
  Response Time: ${result.responseTime}ms${error}`
  }

  return summary
}
