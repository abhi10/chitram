# Database Error Handling Implementation

**Date:** 2025-12-19
**Status:** ✅ Implemented
**Location:** `backend/app/main.py`

---

## Summary

Added specific exception handler for database connection and timeout errors to improve observability and user experience.

---

## What Changed

### 1. Added Imports (main.py:14, 17-18)

```python
from app.schemas.error import ErrorResponse, ErrorDetail, ErrorCodes  # Added ErrorCodes

# SQLAlchemy exceptions for database error handling
from sqlalchemy.exc import OperationalError, TimeoutError as SQLAlchemyTimeoutError
```

### 2. Added Database Exception Handler (main.py:68-88)

```python
# Database exception handler (more specific, comes before global handler)
@app.exception_handler(OperationalError)
@app.exception_handler(SQLAlchemyTimeoutError)
async def database_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle database connection and timeout errors.

    Returns 503 Service Unavailable for database issues to distinguish
    from application errors (500 Internal Server Error).
    """
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCodes.SERVICE_UNAVAILABLE,
            message="Database temporarily unavailable. Please try again later.",
            details={"error": str(exc)} if settings.debug else {},
        )
    )
    return JSONResponse(
        status_code=503,  # Service Unavailable
        content=error_response.model_dump(),
    )
```

---

## Behavior Comparison

### Before (All Database Errors)

**HTTP Response:**
```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred",
    "details": {}
  }
}
```

**Problem:**
- ❌ Can't distinguish database issues from application bugs
- ❌ Returns 500 (server error) for infrastructure issues
- ❌ `SERVICE_UNAVAILABLE` error code was unused

---

### After (Database Connection Errors)

**HTTP Response:**
```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Database temporarily unavailable. Please try again later.",
    "details": {
      "error": "connection timeout"  // Only in debug mode
    }
  }
}
```

**Improvements:**
- ✅ Clear distinction between database and application errors
- ✅ Correct HTTP status (503 vs 500)
- ✅ Uses existing `SERVICE_UNAVAILABLE` error code (no schema changes)
- ✅ Better observability for debugging
- ✅ Helpful in Codespaces (database startup delays)

---

## Database Errors Caught

### 1. OperationalError
**Triggers when:**
- Database connection refused (PostgreSQL not running)
- Network timeout connecting to database
- Database host unreachable
- Connection pool exhausted
- SSL/TLS connection errors

**Example scenarios:**
```python
# PostgreSQL not running
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
could not connect to server: Connection refused

# Database host unreachable
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
could not translate host name "postgres" to address
```

### 2. TimeoutError
**Triggers when:**
- Query execution exceeds timeout
- Connection acquisition from pool times out
- Statement execution timeout

**Example scenarios:**
```python
# Query timeout
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10
reached, connection timed out, timeout 30
```

---

## Exception Handler Priority

**FastAPI processes exception handlers from specific to general:**

```
1. @app.exception_handler(OperationalError)      ← Most specific (database connection)
2. @app.exception_handler(SQLAlchemyTimeoutError) ← Specific (database timeout)
3. @app.exception_handler(Exception)             ← Catch-all (everything else)
```

**This ensures:**
- Database errors → 503 (Service Unavailable)
- Application errors → 500 (Internal Server Error)

---

## Testing

### Manual Test: Database Connection Error

**Simulate database unavailable:**
```bash
# Stop PostgreSQL
docker-compose stop postgres

# Try to access any endpoint
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Database temporarily unavailable. Please try again later."
  }
}
```

**HTTP Status:** `503 Service Unavailable`

---

### Manual Test: Application Error

**Trigger application error:**
```python
# Add intentional bug to any endpoint
@router.get("/test")
async def test():
    raise ValueError("Test error")
```

**Expected response:**
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred"
  }
}
```

**HTTP Status:** `500 Internal Server Error`

---

## Benefits for Each Phase

### Phase 1 (Current)
- ✅ Better debugging in Codespaces (database startup delays)
- ✅ Clear error messages for users
- ✅ Distinguishes infrastructure from code issues

### Phase 2 (Future)
- ✅ Monitoring systems can distinguish 503 from 500
- ✅ Circuit breakers can trigger on 503s
- ✅ Load balancers can remove unhealthy instances
- ✅ Retry logic can handle 503 differently than 500

### Phase 4 (Production)
- ✅ Prometheus metrics can separate DB errors from app errors
- ✅ Alerting rules can be more specific
- ✅ On-call engineers know exactly what to investigate

---

## Why This Aligns with Phase 1 Lean

**✅ Uses existing error code** - No schema changes (SERVICE_UNAVAILABLE already existed)
**✅ Small change** - Only 22 lines added to main.py
**✅ No new dependencies** - Uses built-in SQLAlchemy exceptions
**✅ Immediate value** - Better debugging in Codespaces
**✅ Future-ready** - Positioned perfectly for Phase 2 monitoring

---

## Error Code Usage Summary

| Error Code | HTTP Status | Used By | Notes |
|------------|-------------|---------|-------|
| `INVALID_FILE_FORMAT` | 400 | validation.py | File not JPEG/PNG |
| `FILE_TOO_LARGE` | 400 | validation.py | Exceeds 5MB |
| `INVALID_REQUEST` | 400 | validation.py | Empty file |
| `IMAGE_NOT_FOUND` | 404 | api/images.py | ID doesn't exist |
| `RATE_LIMIT_EXCEEDED` | 429 | - | Not implemented (Phase 2) |
| `INTERNAL_ERROR` | 500 | main.py | Application errors |
| `SERVICE_UNAVAILABLE` | 503 | **main.py** | **✅ Now used for DB errors** |

---

## Files Modified

1. **`backend/app/main.py`**
   - Added imports (2 lines)
   - Added `database_exception_handler()` function (20 lines)
   - Total: 22 lines added

2. **`docs/code-review-phase1-lean.md`**
   - Updated main.py section to reflect new handler
   - Updated error handling section
   - Updated cross-cutting concerns

3. **`docs/changelog.md`**
   - Documented the change in Phase 1 Lean section

---

## Related Documentation

- **Error Schema:** `backend/app/schemas/error.py`
- **Database Setup:** `backend/app/database.py`
- **Code Review:** `docs/code-review-phase1-lean.md`
- **Changelog:** `docs/changelog.md`

---

## Decision Rationale

This implementation was chosen because:

1. **Small investment, high return** - 22 lines for better observability
2. **No schema changes** - Reuses existing `SERVICE_UNAVAILABLE` code
3. **Follows HTTP standards** - 503 is correct for service unavailable
4. **Improves debugging** - Especially useful in Codespaces environment
5. **Positions for Phase 2** - Monitoring/alerting can use this immediately
6. **Still "Lean"** - Focused improvement, not over-engineered

**Alternative considered:** Add granular error codes (DATABASE_CONNECTION_TIMEOUT, etc.)
**Rejected because:** Overkill for Phase 1, defer to Phase 2 with circuit breakers

---

**Implemented:** 2025-12-19
**Status:** ✅ Ready for commit
