# ADR-0003: Anonymous Access for Phase 1

## Status

Accepted

## Date

2025-12-13

## Context

We need to decide on the access model for Phase 1. Options range from fully open (anonymous) to requiring authentication. The decision impacts:
- Implementation complexity
- Security posture
- User experience
- Learning focus

## Options Considered

### Option 1: Anonymous Access (No Authentication)
- **Pros:**
  - Simplest to implement
  - No user management overhead
  - Focus on core functionality
  - Quick to test and iterate
- **Cons:**
  - No user accountability
  - Harder to implement quotas per user
  - Anyone can upload (potential abuse)
  - No ownership model for images

### Option 2: API Key Authentication
- **Pros:**
  - Simple authentication mechanism
  - Can track usage per key
  - Some accountability
- **Cons:**
  - Need key generation/management
  - Still no true user accounts
  - Additional complexity for Phase 1

### Option 3: Full User Registration
- **Pros:**
  - User accountability
  - Per-user quotas and tracking
  - Ownership model for images
  - Foundation for future features
- **Cons:**
  - Significant implementation overhead
  - Need password hashing, sessions/JWT
  - Email verification considerations
  - Distracts from Phase 1 learning goals

## Decision

Use **Anonymous Access** for Phase 1.

## Rationale

1. **Simplicity** - Focus on core upload/download functionality first
2. **Learning goals** - Phase 1 is about basic architecture, not auth
3. **Faster iteration** - No auth means quicker testing cycles
4. **Security through obscurity** - UUIDs are hard to guess (sufficient for Phase 1)
5. **Defer complexity** - User auth is planned for Phase 2

## Consequences

### Positive
- Faster Phase 1 development
- Simpler API (no auth headers/tokens)
- Easy to test with curl/Swagger
- Focus on distributed systems concepts

### Negative
- No user accountability
- Rate limiting only by IP address
- No per-user quotas (only global limits)
- Anyone can delete if they know the UUID

### Neutral
- Will add rate limiting per IP to prevent abuse
- Will implement API key auth in Phase 2
- Images are "unlisted" (not discoverable)

## References

- [../requirements/phase1.md](../.../requirements/phase1.md) - FR-1.8 (anonymous uploads)
- [ADR-0004](./0004-skip-delete-token-phase1.md) - Related deletion decision
