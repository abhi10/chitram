/**
 * Alerter Module
 *
 * Reusable module for sending notifications about health check failures.
 * Supports multiple notification channels: email, GitHub issues, console.
 *
 * DRY principles:
 * - Single responsibility: Only handles notifications
 * - Configurable: Can send to multiple channels
 * - Extensible: Easy to add new notification types
 * - Reusable: Can be imported by multiple scripts
 */

export interface AlertConfig {
  email?: {
    to: string
    from?: string
    subject?: string
  }
  github?: {
    token: string
    owner: string
    repo: string
  }
  slack?: {
    webhookUrl: string
  }
  console?: boolean
}

export interface AlertPayload {
  title: string
  message: string
  severity: 'info' | 'warning' | 'error'
  timestamp: Date
  url?: string
  metadata?: Record<string, any>
}

/**
 * Send alert via console (always available, useful for local testing)
 */
function alertViaConsole(payload: AlertPayload): void {
  const icon = payload.severity === 'error' ? '❌' : '⚠️'
  console.error(`
${icon} ${payload.title}
${payload.message}
Time: ${payload.timestamp.toISOString()}
${payload.url ? `URL: ${payload.url}` : ''}
  `)
}

/**
 * Send alert via email using GitHub Actions or external service
 *
 * For production use with GitHub Actions:
 * 1. Store SMTP credentials as GitHub Secrets
 * 2. Use environment variables: SMTP_USER, SMTP_PASSWORD, SMTP_HOST
 * 3. GitHub Actions will pass these as secrets
 */
async function alertViaEmail(
  payload: AlertPayload,
  config: AlertConfig['email']
): Promise<void> {
  if (!config) return

  // In GitHub Actions environment
  if (process.env.GITHUB_ACTIONS === 'true') {
    // For now, we'll use a simple approach: write to a file that GH Actions can read
    // Or we can use a GH Actions step to send email
    console.log('📧 Email alert would be sent to:', config.to)
    console.log('   Title:', payload.title)
    console.log('   Message:', payload.message)

    // In a real implementation, you would:
    // 1. Call SendGrid API
    // 2. Call AWS SES
    // 3. Call a webhook that sends email
    // 4. Use node-mailer with SMTP credentials

    return
  }

  // Local development: just log it
  console.log('📧 Email notification (local):', config.to)
  console.log(payload.message)
}

/**
 * Send alert via GitHub Issue
 *
 * Useful because:
 * - No additional credentials needed
 * - Creates a record/history of incidents
 * - Integrates with GitHub workflow
 * - Can be assigned, labeled, etc.
 *
 * Security: Uses spawnSync with argument array to avoid shell injection.
 * Arguments are passed directly to 'gh' CLI without shell interpolation.
 */
async function alertViaGitHubIssue(
  payload: AlertPayload,
  config: AlertConfig['github']
): Promise<void> {
  if (!config) return

  // Build the issue body
  const body = `## ${payload.title}

${payload.message}

**Severity:** ${payload.severity}
**Timestamp:** ${payload.timestamp.toISOString()}
${payload.url ? `**URL:** ${payload.url}` : ''}

${payload.metadata ? `**Metadata:**\n\`\`\`json\n${JSON.stringify(payload.metadata, null, 2)}\n\`\`\`` : ''}

---
*Automated health check alert*`

  // Use GitHub CLI if available
  try {
    // Use spawnSync with argument array instead of execSync with string
    // This avoids shell injection vulnerabilities and brittle escaping
    const { spawnSync } = await import('child_process')

    const result = spawnSync('gh', ['issue', 'create', '--title', payload.title, '--body', body, '--label', 'incident'], {
      cwd: process.cwd(),
      encoding: 'utf8',
    })

    // Handle errors from spawnSync
    if (result.error) {
      throw result.error
    }

    if (result.status !== 0) {
      throw new Error(`gh exited with code ${result.status}: ${result.stderr}`)
    }

    console.log('📋 GitHub issue created:', result.stdout)
  } catch (error) {
    console.warn('Failed to create GitHub issue:', error)
  }
}

/**
 * Send alert via Slack
 */
async function alertViaSlack(
  payload: AlertPayload,
  config: AlertConfig['slack']
): Promise<void> {
  if (!config) return

  const color =
    payload.severity === 'error' ? 'danger' : payload.severity === 'warning' ? 'warning' : 'good'

  const slackMessage = {
    attachments: [
      {
        color,
        title: payload.title,
        text: payload.message,
        ts: Math.floor(payload.timestamp.getTime() / 1000),
        fields: payload.url
          ? [
              {
                title: 'URL',
                value: payload.url,
                short: false,
              },
            ]
          : [],
      },
    ],
  }

  try {
    const response = await fetch(config.webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(slackMessage),
    })

    if (!response.ok) {
      throw new Error(`Slack API error: ${response.status}`)
    }

    console.log('💬 Slack notification sent')
  } catch (error) {
    console.warn('Failed to send Slack notification:', error)
  }
}

/**
 * Send alert via configured channels
 *
 * @example
 * await sendAlert({
 *   email: { to: 'admin@example.com' },
 *   console: true
 * }, {
 *   title: 'Website Down',
 *   message: 'Health check failed',
 *   severity: 'error',
 *   timestamp: new Date(),
 *   url: 'https://example.com'
 * })
 */
export async function sendAlert(config: AlertConfig, payload: AlertPayload): Promise<void> {
  // Always log to console if explicitly enabled or no other channels
  if (config.console === true || (!config.email && !config.github && !config.slack)) {
    alertViaConsole(payload)
  }

  // Send to configured channels
  const promises: Promise<void>[] = []

  if (config.email) {
    promises.push(alertViaEmail(payload, config.email))
  }

  if (config.github) {
    promises.push(alertViaGitHubIssue(payload, config.github))
  }

  if (config.slack) {
    promises.push(alertViaSlack(payload, config.slack))
  }

  // Wait for all notifications to complete (don't fail if one fails)
  await Promise.allSettled(promises)
}

/**
 * Build email-friendly alert payload
 */
export function buildHealthAlertPayload(
  baseUrl: string,
  healthSummary: string
): AlertPayload {
  return {
    title: `❌ Website Health Check Failed: ${baseUrl}`,
    message: healthSummary,
    severity: 'error',
    timestamp: new Date(),
    url: baseUrl,
  }
}
