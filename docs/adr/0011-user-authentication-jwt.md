# ADR-0011: User Authentication with JWT

## Status

Proposed

## Date

2026-01-02

## Context

Phase 1 uses anonymous access (ADR-0003). Anyone with an image UUID can delete it. Phase 2 needs:
- Image ownership (who uploaded what)
- Secure deletion (only owner can delete)
- Backward compatibility (anonymous uploads still work)

## Decision

**JWT (JSON Web Tokens)** for authentication.

### Why JWT over alternatives?

| Option | Verdict | Reason |
|--------|---------|--------|
| **JWT** | ✅ Chosen | Stateless, scales horizontally, FastAPI native support |
| Session-based | ❌ | Requires session storage, harder to scale |
| API Keys | ❌ | No expiration, often leaked in code |
| OAuth 2.0 | ❌ | Overkill for MVP |

## Implementation

### Authentication Flow

```
Register: POST /auth/register {email, password} → {user, access_token}
Login:    POST /auth/login {email, password} → {access_token}
Use:      GET /images Authorization: Bearer <token> → {images}
```

### Delete Token for Anonymous Uploads

```python
# Anonymous upload → returns delete token
{"id": "image-uuid", "delete_token": "dt_abc123..."}

# Authenticated upload → owner can delete without token
{"id": "image-uuid", "user_id": "user-uuid"}
```

### Database Changes

```sql
-- New table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add to images
ALTER TABLE images ADD COLUMN user_id UUID REFERENCES users(id);
ALTER TABLE images ADD COLUMN delete_token_hash VARCHAR(255);
```

### Configuration

```bash
JWT_SECRET_KEY=<random-256-bit>  # Required
JWT_EXPIRE_MINUTES=1440          # 24 hours
```

### Dependencies

```toml
python-jose = "^3.3.0"   # JWT
passlib = "^1.7.4"       # Password hashing (bcrypt)
```

## Consequences

| Type | Impact |
|------|--------|
| ✅ Positive | Users own images, secure deletion, horizontal scaling |
| ❌ Negative | Must secure JWT secret, token revocation complex |
| ➡️ Neutral | ~200 lines code, new DB table |

## Security

- Passwords: bcrypt (work factor 12)
- Tokens: 24h expiry, HTTPS required
- Delete tokens: 32 bytes, URL-safe, stored as hash

## Security Testing Requirements

### Password Security
- [ ] Passwords hashed with bcrypt (verify `$2b$` prefix)
- [ ] Work factor ≥ 12 (timing check: hash takes 200-400ms)
- [ ] No plaintext passwords in logs or responses
- [ ] Password verification works correctly

### JWT Security
- [ ] Tokens contain required claims (sub, exp, iat)
- [ ] Expired tokens rejected (401)
- [ ] Invalid signatures rejected (401)
- [ ] Algorithm confusion prevented (only HS256 accepted)
- [ ] Token not logged or exposed in responses

### API Security
- [ ] No user enumeration (same response for "user exists" vs "wrong password")
- [ ] Rate limiting on auth endpoints (prevent brute force)
- [ ] Failed attempts don't reveal timing differences
- [ ] HTTPS enforced in production

### Delete Token Security
- [ ] Tokens are cryptographically random (32 bytes)
- [ ] Only hash stored in database (not plaintext)
- [ ] Tokens invalidated after successful deletion
- [ ] Timing-safe comparison used

### OWASP Alignment
- [ ] A01: Access control on protected routes
- [ ] A02: Bcrypt for password hashing
- [ ] A07: No credentials in logs or error messages

## References

- [ADR-0003: Anonymous Access](./0003-anonymous-access-phase1.md)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
