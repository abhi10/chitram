# ADR-0007: Use GitHub Codespaces for Development

## Status

Accepted

## Date

2025-12-13

## Context

Development machine has limited resources (8GB RAM). Docker containers for PostgreSQL and MinIO consume significant memory and storage. Need a development environment that:
- Doesn't strain local resources
- Provides consistent setup
- Is free or low-cost for learning

## Options Considered

### Option 1: GitHub Codespaces
- **Pros:**
  - Zero local resource usage (runs in cloud)
  - Free tier: 60 hours/month (Core: 2-core, 8GB RAM)
  - DevContainer config already works
  - Full VS Code experience
  - Pre-configured with all dependencies
- **Cons:**
  - Requires internet connection
  - Limited free hours
  - Slight latency vs local

### Option 2: Gitpod
- **Pros:**
  - Similar to Codespaces
  - Free tier: 50 hours/month
  - Works with any Git provider
- **Cons:**
  - Less GitHub integration
  - Fewer free hours than Codespaces

### Option 3: Local Lightweight (SQLite + Filesystem)
- **Pros:**
  - No Docker needed
  - Works offline
  - Minimal resource usage
- **Cons:**
  - Different from production setup
  - Need to maintain two configurations
  - SQLite has different behavior than PostgreSQL

### Option 4: Optimized Local Docker
- **Pros:**
  - Same as production
  - Works offline
- **Cons:**
  - Still uses significant RAM (2-4GB)
  - Storage overhead for images

## Decision

Use **GitHub Codespaces** as primary development environment.

## Rationale

1. **Resource constraints** - 8GB RAM is insufficient for comfortable Docker + IDE + browser
2. **Free tier sufficient** - 60 hours/month is ~2 hours/day, adequate for learning
3. **Zero configuration** - DevContainer already set up
4. **Production parity** - Uses real PostgreSQL and MinIO, not lightweight alternatives
5. **Portability** - Can develop from any device with a browser

## Consequences

### Positive
- No local Docker needed
- Consistent environment across devices
- Fast startup (prebuild available)
- No "works on my machine" issues

### Negative
- Requires internet connection
- Must monitor free hours usage
- Cold starts take 1-2 minutes

### Neutral
- Can still run locally with Docker if needed
- DevContainer config works for both

## Usage

```bash
# Option 1: From GitHub UI
# Go to repo → Code → Codespaces → Create codespace

# Option 2: From VS Code
# Install "GitHub Codespaces" extension
# Cmd+Shift+P → "Codespaces: Create New Codespace"

# Option 3: From CLI
gh codespace create --repo YOUR_USERNAME/image-hosting-app
gh codespace code  # Opens in VS Code
```

## Free Tier Details

| Resource | Free Tier |
|----------|-----------|
| Hours/month | 60 (2-core) or 30 (4-core) |
| Storage | 15 GB/month |
| Prebuild storage | 15 GB/month |

## References

- [GitHub Codespaces Pricing](https://github.com/features/codespaces)
- [DevContainer Specification](https://containers.dev/)
