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
  responseTime: number // Actual request latency (last attempt)
  totalResolutionTime: number // Total time including retries
  error?: string
  errorType?: 'timeout' | 'network' | 'http' | 'unknown'
  critical: boolean // If false, failure doesn't trigger critical alert
  timestamp: Date
}

export interface HealthCheckOptions {
  timeout?: number
  retries?: number
  retryDelay?: number
}

export interface EndpointConfig {
  name: string
  path: string
  critical?: boolean // Default: true. Set false for non-critical checks
}

const DEFAULT_OPTIONS: Required<HealthCheckOptions> = {
  timeout: 10000,
  retries: 1,
  retryDelay: 1000,
}

/**
 * Check a single endpoint with retry logic and improved error specificity
 *
 * Latency Measurement Strategy:
 * - responseTime: Actual network latency of the successful/last attempt
 * - totalResolutionTime: Total time including all retries
 *
 * This allows debugging of both transient failures and slow servers.
 */
async function checkEndpoint(
  name: string,
  url: string,
  options: Required<HealthCheckOptions>,
  critical: boolean = true
): Promise<HealthCheckResult> {
  const overallStart = Date.now() // Track total time including retries
  let lastError: string | undefined
  let lastErrorType: 'timeout' | 'network' | 'http' | 'unknown' = 'unknown'
  let lastResponseTime: number = 0

  for (let attempt = 1; attempt <= options.retries; attempt++) {
    const requestStart = Date.now() // Moved inside to measure actual request latency
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), options.timeout)

    try {
      const response = await fetch(url, {
        signal: controller.signal,
        redirect: 'follow',
      })

      clearTimeout(timeout)

      const responseTime = Date.now() - requestStart
      const success = response.ok

      return {
        name,
        url,
        status: success ? 'pass' : 'fail',
        statusCode: response.status,
        responseTime, // Actual request latency
        totalResolutionTime: Date.now() - overallStart,
        timestamp: new Date(),
        critical,
        error: success ? undefined : `HTTP ${response.status} ${response.statusText}`,
        errorType: success ? undefined : 'http',
      }
    } catch (error: any) {
      clearTimeout(timeout)
      lastResponseTime = Date.now() - requestStart

      // Distinguish between different error types
      if (error.name === 'AbortError') {
        lastError = `Timeout after ${options.timeout}ms`
        lastErrorType = 'timeout'
      } else if (
        error.message?.includes('ECONNREFUSED') ||
        error.message?.includes('ENOTFOUND') ||
        error.message?.includes('network')
      ) {
        lastError = `Network error: ${error.message}`
        lastErrorType = 'network'
      } else {
        lastError = error.message || String(error)
        lastErrorType = 'unknown'
      }

      // If we have more retries, wait and try again
      if (attempt < options.retries) {
        await new Promise(resolve => setTimeout(resolve, options.retryDelay))
      }
    }
  }

  // All retries failed
  const totalResolutionTime = Date.now() - overallStart
  return {
    name,
    url,
    status: 'fail',
    responseTime: lastResponseTime,
    totalResolutionTime,
    critical,
    error: lastError,
    errorType: lastErrorType,
    timestamp: new Date(),
  }
}

/**
 * Run health checks for multiple endpoints
 *
 * Concurrency: Uses Promise.all() - fine for small endpoint counts (< 10).
 * For larger sets, consider implementing a concurrency limiter.
 *
 * @example
 * const results = await checkHealth('https://chitram.io', {
 *   endpoints: [
 *     { name: 'Health Endpoint', path: '/health', critical: true },
 *     { name: 'Landing Page', path: '/', critical: true },
 *     { name: 'Status Page', path: '/status', critical: false } // Non-critical
 *   ]
 * })
 *
 * // Check if critical endpoints passed
 * const criticalPassed = results
 *   .filter(r => r.critical)
 *   .every(r => r.status === 'pass')
 */
export async function checkHealth(
  baseUrl: string,
  options?: {
    endpoints?: EndpointConfig[]
    timeout?: number
    retries?: number
    retryDelay?: number
  }
): Promise<HealthCheckResult[]> {
  const mergedOptions = {
    ...DEFAULT_OPTIONS,
    ...options,
  }

  // Normalize baseUrl: ensure trailing slash removed for URL constructor
  const normalizedBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl

  const defaultEndpoints: EndpointConfig[] = [
    { name: 'Health Endpoint', path: '/health', critical: true },
    { name: 'Landing Page', path: '/', critical: true },
  ]

  const endpoints = options?.endpoints || defaultEndpoints

  const results = await Promise.all(
    endpoints.map(endpoint => {
      // Safe URL construction: handle sub-paths correctly
      const fullUrl = new URL(endpoint.path, normalizedBaseUrl).toString()
      return checkEndpoint(
        endpoint.name,
        fullUrl,
        {
          timeout: mergedOptions.timeout,
          retries: mergedOptions.retries,
          retryDelay: mergedOptions.retryDelay,
        },
        endpoint.critical !== false // Default to true if not specified
      )
    })
  )

  return results
}

/**
 * Check if all critical health checks passed
 * Non-critical failures don't affect overall health status
 */
export function isHealthy(results: HealthCheckResult[]): boolean {
  const criticalChecks = results.filter(r => r.critical)
  return criticalChecks.every(result => result.status === 'pass')
}

/**
 * Check if any critical checks failed
 * Useful for alerting logic
 */
export function hasCriticalFailure(results: HealthCheckResult[]): boolean {
  return results.some(r => r.critical && r.status === 'fail')
}

/**
 * Format health check results for logging/display
 * Shows latency, total resolution time, error type, and criticality
 */
export function formatHealthResults(results: HealthCheckResult[]): string {
  const lines = [
    '═══════════════════════════════════════════════════════',
    '📊 Health Check Results',
    '═══════════════════════════════════════════════════════',
  ]

  for (const result of results) {
    const statusIcon = result.status === 'pass' ? '✅' : '❌'
    const criticalBadge = result.critical ? '🔴' : '🟡'
    const errorInfo = result.error ? ` [${result.errorType}] ${result.error}` : ''
    const latencyInfo =
      result.responseTime !== result.totalResolutionTime
        ? ` (${result.responseTime}ms + ${result.totalResolutionTime - result.responseTime}ms retry)`
        : ` (${result.responseTime}ms)`

    lines.push(
      `${statusIcon} ${criticalBadge} ${result.name}${latencyInfo}${errorInfo}`
    )
  }

  const passCount = results.filter(r => r.status === 'pass').length
  const criticalCount = results.filter(r => r.critical).length
  lines.push('───────────────────────────────────────────────────────')
  lines.push(
    `Total: ${passCount}/${results.length} passed (${criticalCount} critical)`
  )
  lines.push('═══════════════════════════════════════════════════════')

  return lines.join('\n')
}

/**
 * Generate health check summary for alerts
 * Shows error types, latency precision, and criticality
 */
export function generateHealthSummary(
  baseUrl: string,
  results: HealthCheckResult[]
): string {
  const healthy = isHealthy(results)
  const passCount = results.filter(r => r.status === 'pass').length
  const criticalFailures = results.filter(r => r.critical && r.status === 'fail')
  const timestamp = new Date().toISOString()

  let summary = `Website Health Check Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: ${healthy ? '✅ HEALTHY' : '❌ UNHEALTHY'}
Website: ${baseUrl}
Time: ${timestamp}
Passed: ${passCount}/${results.length}
Critical Failures: ${criticalFailures.length}

Details:
`

  for (const result of results) {
    const status = result.status === 'pass' ? '✅ PASS' : '❌ FAIL'
    const criticality = result.critical ? '[CRITICAL]' : '[NON-CRITICAL]'
    const errorInfo = result.error
      ? `\n  Error Type: ${result.errorType}
  Error: ${result.error}`
      : ''
    const timingInfo =
      result.responseTime !== result.totalResolutionTime
        ? `\n  Request Latency: ${result.responseTime}ms
  Total Resolution Time: ${result.totalResolutionTime}ms`
        : `\n  Latency: ${result.responseTime}ms`

    summary += `
${status} ${criticality}: ${result.name}
  URL: ${result.url}${timingInfo}${errorInfo}`
  }

  return summary
}
