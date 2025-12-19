# ADR-0004: Skip Delete Token for Phase 1

## Status

Accepted

## Date

2025-12-13

## Context

With anonymous access (ADR-0003), we need to decide how to handle image deletion. Without user accounts, we can't verify ownership. Options include:
- Delete tokens returned at upload time
- Anyone with UUID can delete
- No deletion in Phase 1

## Options Considered

### Option 1: Delete Token
- **Pros:**
  - Only uploader can delete (if they save the token)
  - Security mechanism without full auth
  - Industry practice (e.g., Imgur)
- **Cons:**
  - Additional complexity (token generation, storage, validation)
  - Users must save the token
  - Lost token = can't delete
  - More API parameters to handle

### Option 2: Anyone with UUID Can Delete
- **Pros:**
  - Simplest implementation
  - No additional tokens to manage
  - UUID is hard to guess (128-bit)
  - Sufficient for development/learning
- **Cons:**
  - If UUID is leaked, anyone can delete
  - No true ownership verification
  - Not suitable for production

### Option 3: No Deletion in Phase 1
- **Pros:**
  - Simplest of all
  - No accidental deletions
- **Cons:**
  - Can't clean up test data
  - Incomplete API
  - Storage fills up during development

## Decision

Use **Option 2: Anyone with UUID can delete** for Phase 1.

## Rationale

1. **Simplicity** - Aligns with Phase 1 "keep it simple" goal
2. **UUID security** - UUIDs are 128-bit, practically impossible to guess
3. **Development needs** - Need deletion for cleanup during development
4. **Defer to Phase 2** - Delete tokens will be added with user auth
5. **Risk is low** - Phase 1 is for learning, not production data

## Consequences

### Positive
- Simple DELETE endpoint implementation
- No token storage/validation logic
- Easy to test

### Negative
- Shared UUID = anyone can delete
- No audit trail of who deleted
- Must implement delete token in Phase 2

### Neutral
- Images are unlisted (UUID discovery is unlikely)
- Can add delete token later without breaking existing uploads

## References

- [requirements.md](../../requirements.md) - FR-3.2 (deletion without token)
- [ADR-0003](./0003-anonymous-access-phase1.md) - Anonymous access decision
