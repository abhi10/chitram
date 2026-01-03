# ADR-0005: Use Structured Error Response Format

## Status

Accepted

## Date

2025-12-13

## Context

We need to define a consistent error response format for the API. Good error responses help:
- API consumers handle errors programmatically
- Debugging during development
- Consistent user experience

## Options Considered

### Option 1: FastAPI Default
```json
{
  "detail": "Error message here"
}
```
- **Pros:**
  - Zero implementation effort
  - FastAPI handles automatically
  - Simple structure
- **Cons:**
  - No error codes for programmatic handling
  - Inconsistent with validation errors
  - Hard to distinguish error types

### Option 2: Structured Errors with Codes
```json
{
  "error": {
    "code": "INVALID_FILE_FORMAT",
    "message": "Only JPEG and PNG formats are supported",
    "details": {}
  }
}
```
- **Pros:**
  - Error codes enable programmatic handling
  - Consistent structure
  - Room for additional details
  - Industry best practice
- **Cons:**
  - Requires custom exception handlers
  - More implementation work
  - Must maintain error code list

### Option 3: Problem Details (RFC 7807)
```json
{
  "type": "https://api.example.com/errors/invalid-format",
  "title": "Invalid File Format",
  "status": 400,
  "detail": "Only JPEG and PNG formats are supported"
}
```
- **Pros:**
  - Industry standard (RFC 7807)
  - Self-documenting with type URLs
  - Rich error information
- **Cons:**
  - More complex structure
  - Requires maintaining type URLs
  - Overkill for Phase 1

## Decision

Use **Option 2: Structured Errors with Codes**.

## Rationale

1. **Programmatic handling** - Error codes allow clients to handle specific errors
2. **Simplicity** - Simpler than RFC 7807, but better than default
3. **Extensible** - `details` object allows adding context when needed
4. **Clear contract** - Defined error codes in requirements document
5. **Balance** - Good middle ground between too simple and over-engineered

## Consequences

### Positive
- Consistent error handling across all endpoints
- Clients can switch on error codes
- Easy to add new error types
- Better developer experience

### Negative
- Need custom exception handlers in FastAPI
- Must document all error codes
- Slightly more implementation work

### Neutral
- Will create custom exception classes
- Will maintain error code enum
- HTTP status codes still indicate error category

## Error Codes Defined

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_FILE_FORMAT` | 400 | Not JPEG or PNG |
| `FILE_TOO_LARGE` | 400 | Exceeds 5 MB |
| `INVALID_REQUEST` | 400 | Malformed request |
| `IMAGE_NOT_FOUND` | 404 | Image ID doesn't exist |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

## References

- [../requirements/phase1.md](../.../requirements/phase1.md) - FR-7 (Error Response Format)
- [RFC 7807 - Problem Details](https://datatracker.ietf.org/doc/html/rfc7807) - Considered alternative
