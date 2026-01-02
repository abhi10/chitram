# Image Hosting App - Phase 2 Requirements

## Overview

This document defines the functional and non-functional requirements for Phase 2 (Full Features) of the Image Hosting Application using the **EARS (Easy Approach to Requirements Specification)** format for unambiguous requirement statements.

**Phase 2 Goal:** Add production-ready features including object storage, caching, authentication, rate limiting, and background processing.

**Prerequisites:** Phase 1 Lean + Phase 1.5 complete

---

## EARS Patterns Reference

| Pattern | Template | Use Case |
|---------|----------|----------|
| **Ubiquitous** | The [system] shall [action] | Always-on behavior |
| **Event-driven** | When [trigger], the [system] shall [action] | Response to events |
| **State-driven** | While [state], the [system] shall [action] | Behavior during states |
| **Optional** | Where [feature enabled], the [system] shall [action] | Configurable features |
| **Unwanted** | If [condition], then the [system] shall [action] | Error/edge cases |

---

## Functional Requirements

### FR-2.1: MinIO Object Storage

#### FR-2.1.1: Storage Backend Selection
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.1.1a | **Where** `STORAGE_BACKEND=minio` is configured, the system shall store image files in MinIO object storage | Must | ✅ Done |
| FR-2.1.1b | **Where** `STORAGE_BACKEND=local` is configured, the system shall store image files on local filesystem | Must | ✅ Done |
| FR-2.1.1c | The system shall use the Strategy Pattern to switch between storage backends without code changes | Must | ✅ Done |

#### FR-2.1.2: MinIO Operations
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.1.2a | **When** an image is uploaded, the system shall store the file in the configured MinIO bucket with a UUID-based key | Must | ✅ Done |
| FR-2.1.2b | **When** an image file is requested, the system shall retrieve it from MinIO and stream it to the client | Must | ✅ Done |
| FR-2.1.2c | **When** an image is deleted, the system shall remove the file from MinIO storage | Must | ✅ Done |
| FR-2.1.2d | **If** MinIO is unavailable during upload, the system shall return 503 SERVICE_UNAVAILABLE | Must | ✅ Done |
| FR-2.1.2e | **If** MinIO is unavailable during deletion, the system shall still delete the database record (graceful degradation) | Should | ✅ Done |

#### FR-2.1.3: MinIO Configuration
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.1.3a | The system shall read MinIO connection settings from environment variables (endpoint, access_key, secret_key, bucket) | Must | ✅ Done |
| FR-2.1.3b | **When** the application starts with `STORAGE_BACKEND=minio`, the system shall verify MinIO connectivity | Should | ✅ Done |
| FR-2.1.3c | **If** the configured bucket does not exist, the system shall create it automatically | Should | ✅ Done |

---

### FR-2.2: Redis Caching

#### FR-2.2.1: Cache Infrastructure
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.2.1a | **Where** Redis is configured, the system shall cache image metadata to reduce database queries | Must | ⏳ Pending |
| FR-2.2.1b | The system shall connect to Redis using connection pooling | Should | ⏳ Pending |
| FR-2.2.1c | **If** Redis is unavailable, the system shall fall back to database queries (graceful degradation) | Must | ⏳ Pending |

#### FR-2.2.2: Cache Operations
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.2.2a | **When** image metadata is requested, the system shall first check the Redis cache | Must | ⏳ Pending |
| FR-2.2.2b | **If** a cache miss occurs, the system shall query the database and populate the cache | Must | ⏳ Pending |
| FR-2.2.2c | **When** an image is uploaded, the system shall cache its metadata with TTL of 1 hour | Should | ⏳ Pending |
| FR-2.2.2d | **When** an image is deleted, the system shall invalidate its cache entry | Must | ⏳ Pending |
| FR-2.2.2e | **When** an image is updated, the system shall invalidate its cache entry | Must | ⏳ Pending |

#### FR-2.2.3: Cache Configuration
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.2.3a | The system shall read Redis connection settings from environment variables (host, port, password, db) | Must | ⏳ Pending |
| FR-2.2.3b | The system shall use a configurable cache TTL (default: 3600 seconds) | Should | ⏳ Pending |
| FR-2.2.3c | The system shall use a key prefix to namespace cache entries (e.g., `chitram:image:{id}`) | Should | ⏳ Pending |

---

### FR-2.3: Rate Limiting

#### FR-2.3.1: Rate Limit Enforcement
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.3.1a | The system shall limit API requests per IP address using a sliding window algorithm | Must | ⏳ Pending |
| FR-2.3.1b | **If** an IP exceeds 10 requests per minute, the system shall return 429 TOO_MANY_REQUESTS | Must | ⏳ Pending |
| FR-2.3.1c | **When** rate limit is exceeded, the response shall include `Retry-After` header with seconds until reset | Must | ⏳ Pending |
| FR-2.3.1d | **While** an IP is rate limited, the system shall reject requests immediately without processing | Should | ⏳ Pending |

#### FR-2.3.2: Rate Limit Storage
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.3.2a | **Where** Redis is available, the system shall store rate limit counters in Redis | Must | ⏳ Pending |
| FR-2.3.2b | **If** Redis is unavailable, the system shall allow requests through (fail-open for availability) | Should | ⏳ Pending |
| FR-2.3.2c | Rate limit counters shall expire automatically after the window period | Must | ⏳ Pending |

#### FR-2.3.3: Rate Limit Configuration
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.3.3a | The system shall allow configurable rate limits via environment variables | Should | ⏳ Pending |
| FR-2.3.3b | The system shall support different limits for different endpoints (upload vs read) | Could | ⏳ Pending |
| FR-2.3.3c | The system shall support IP whitelist for unlimited access (admin/monitoring) | Could | ⏳ Pending |

---

### FR-2.4: User Authentication

#### FR-2.4.1: User Registration
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.4.1a | **When** a user registers, the system shall create a user account with email and hashed password | Must | ⏳ Pending |
| FR-2.4.1b | **If** the email is already registered, the system shall return 409 CONFLICT | Must | ⏳ Pending |
| FR-2.4.1c | The system shall hash passwords using bcrypt with appropriate work factor | Must | ⏳ Pending |
| FR-2.4.1d | **When** registration succeeds, the system shall return a JWT access token | Should | ⏳ Pending |

#### FR-2.4.2: User Login
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.4.2a | **When** valid credentials are provided, the system shall return a JWT access token | Must | ⏳ Pending |
| FR-2.4.2b | **If** credentials are invalid, the system shall return 401 UNAUTHORIZED | Must | ⏳ Pending |
| FR-2.4.2c | JWT tokens shall expire after a configurable period (default: 24 hours) | Must | ⏳ Pending |
| FR-2.4.2d | JWT tokens shall contain user ID and expiration claims | Must | ⏳ Pending |

#### FR-2.4.3: Protected Routes
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.4.3a | **When** a valid JWT is provided, the system shall identify the authenticated user | Must | ⏳ Pending |
| FR-2.4.3b | **If** JWT is missing or invalid, protected routes shall return 401 UNAUTHORIZED | Must | ⏳ Pending |
| FR-2.4.3c | **If** JWT is expired, the system shall return 401 with code TOKEN_EXPIRED | Must | ⏳ Pending |
| FR-2.4.3d | Upload endpoint shall associate images with the authenticated user | Must | ⏳ Pending |
| FR-2.4.3e | Delete endpoint shall only allow deletion by image owner or admin | Must | ⏳ Pending |

#### FR-2.4.4: Anonymous Access (Backward Compatibility)
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.4.4a | **Where** authentication is optional, the system shall allow anonymous uploads | Should | ⏳ Pending |
| FR-2.4.4b | Anonymous images shall have `user_id = NULL` in the database | Should | ⏳ Pending |
| FR-2.4.4c | Image retrieval (GET) shall remain public (no auth required) | Must | ⏳ Pending |

---

### FR-2.5: Delete Tokens

#### FR-2.5.1: Token Generation
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.5.1a | **When** an anonymous image is uploaded, the system shall generate a secure delete token | Must | ⏳ Pending |
| FR-2.5.1b | Delete tokens shall be cryptographically random (minimum 32 bytes, URL-safe) | Must | ⏳ Pending |
| FR-2.5.1c | Delete tokens shall be returned in the upload response | Must | ⏳ Pending |
| FR-2.5.1d | Delete tokens shall be stored as hashed values (not plaintext) | Should | ⏳ Pending |

#### FR-2.5.2: Token Validation
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.5.2a | **When** deleting an anonymous image, the system shall require the delete token | Must | ⏳ Pending |
| FR-2.5.2b | **If** the delete token is incorrect, the system shall return 403 FORBIDDEN | Must | ⏳ Pending |
| FR-2.5.2c | **If** the user is authenticated and owns the image, delete token is not required | Should | ⏳ Pending |

---

### FR-2.6: Background Jobs

#### FR-2.6.1: Job Queue Infrastructure
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.6.1a | The system shall use Celery with Redis as message broker for background tasks | Must | ⏳ Pending |
| FR-2.6.1b | Background jobs shall run in separate worker processes | Must | ⏳ Pending |
| FR-2.6.1c | **If** a job fails, the system shall retry up to 3 times with exponential backoff | Should | ⏳ Pending |

#### FR-2.6.2: Thumbnail Generation
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.6.2a | **When** an image is uploaded, the system shall queue a thumbnail generation job | Should | ⏳ Pending |
| FR-2.6.2b | The system shall generate 3 thumbnail sizes: small (150px), medium (300px), large (600px) | Should | ⏳ Pending |
| FR-2.6.2c | Thumbnails shall maintain aspect ratio | Must | ⏳ Pending |
| FR-2.6.2d | Thumbnails shall be stored in the same storage backend as originals | Must | ⏳ Pending |

#### FR-2.6.3: Checksum Calculation
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.6.3a | **When** an image is uploaded, the system shall calculate and store SHA-256 checksum | Should | ⏳ Pending |
| FR-2.6.3b | Checksum calculation shall run as a background job (non-blocking) | Should | ⏳ Pending |

---

### FR-2.7: Advanced Validation

#### FR-2.7.1: File Type Detection
| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| FR-2.7.1a | The system shall validate file content using magic bytes (file signature) | Must | ✅ Done |
| FR-2.7.1b | **If** Content-Type header doesn't match file signature, the system shall reject the upload | Must | ✅ Done |
| FR-2.7.1c | **Where** python-magic is available, the system shall use it for enhanced detection | Could | ⏳ Pending |

---

## Non-Functional Requirements

### NFR-2.1: Performance

| ID | EARS Requirement | Target | Priority | Status |
|----|------------------|--------|----------|--------|
| NFR-2.1.1 | **When** metadata is cached, retrieval response time shall be < 50ms | < 50ms | Should | ⏳ Pending |
| NFR-2.1.2 | Cache hit ratio shall exceed 80% for repeated metadata requests | > 80% | Should | ⏳ Pending |
| NFR-2.1.3 | MinIO upload throughput shall support files up to 5MB in < 2 seconds | < 2s | Should | ✅ Done |
| NFR-2.1.4 | Rate limit checking shall add < 5ms overhead per request | < 5ms | Should | ⏳ Pending |

### NFR-2.2: Reliability

| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| NFR-2.2.1 | **If** Redis is unavailable, the system shall continue operating with degraded caching | Must | ⏳ Pending |
| NFR-2.2.2 | **If** MinIO is unavailable, uploads shall fail gracefully with clear error message | Must | ✅ Done |
| NFR-2.2.3 | **If** a background job fails, it shall not affect the main API response | Must | ⏳ Pending |
| NFR-2.2.4 | The system shall log all failures with sufficient context for debugging | Must | ⏳ Pending |

### NFR-2.3: Security

| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| NFR-2.3.1 | JWT secrets shall be configurable via environment variables (never hardcoded) | Must | ⏳ Pending |
| NFR-2.3.2 | Passwords shall be hashed using bcrypt with work factor >= 12 | Must | ⏳ Pending |
| NFR-2.3.3 | Delete tokens shall be cryptographically random (256 bits minimum entropy) | Must | ⏳ Pending |
| NFR-2.3.4 | MinIO credentials shall be stored as environment variables | Must | ✅ Done |
| NFR-2.3.5 | Redis connection shall support password authentication | Should | ⏳ Pending |

### NFR-2.4: Scalability

| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| NFR-2.4.1 | The system shall support 100+ concurrent users with caching enabled | Should | ⏳ Pending |
| NFR-2.4.2 | Redis and MinIO shall be external services (not in-process) for horizontal scaling | Must | ✅ Done |
| NFR-2.4.3 | Database connections shall use connection pooling | Should | ⏳ Pending |

### NFR-2.5: Observability

| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| NFR-2.5.1 | The system shall log cache hits/misses for monitoring | Should | ⏳ Pending |
| NFR-2.5.2 | The system shall log rate limit events (exceeded, near-limit) | Should | ⏳ Pending |
| NFR-2.5.3 | Health check endpoint shall report status of Redis and MinIO | Should | ⏳ Pending |

### NFR-2.6: Testing

| ID | EARS Requirement | Priority | Status |
|----|------------------|----------|--------|
| NFR-2.6.1 | All new features shall have unit tests with > 80% coverage | Must | ✅ Partial |
| NFR-2.6.2 | Integration tests shall verify Redis and MinIO connectivity | Must | ✅ Done |
| NFR-2.6.3 | CI pipeline shall run all tests before merge | Must | ✅ Done |
| NFR-2.6.4 | Dependency check shall verify all imports resolve | Must | ✅ Done |

---

## API Endpoints (Phase 2 Additions)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login and get JWT | No |
| POST | `/api/v1/auth/refresh` | Refresh JWT token | Yes |
| GET | `/api/v1/users/me` | Get current user profile | Yes |
| GET | `/api/v1/users/me/images` | List user's images | Yes |
| GET | `/api/v1/images/{id}/thumbnails` | Get thumbnail URLs | No |
| DELETE | `/api/v1/images/{id}?token={delete_token}` | Delete with token | No (token) |

---

## Data Model Changes (Phase 2)

### New Table: Users
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| email | string | Yes | Unique, indexed |
| password_hash | string | Yes | bcrypt hash |
| is_active | boolean | Yes | Account status |
| is_admin | boolean | Yes | Admin privileges |
| created_at | timestamp | Yes | Registration time |

### Modified Table: Images
| Field | Type | Change | Description |
|-------|------|--------|-------------|
| user_id | UUID | Added | FK to users (nullable for anonymous) |
| delete_token_hash | string | Added | Hashed delete token |
| checksum | string | Added | SHA-256 hash |
| thumbnail_keys | JSON | Added | Storage keys for thumbnails |

---

## Acceptance Criteria (Phase 2 Complete)

Phase 2 is considered complete when:

### Storage (MinIO) ✅
- [x] Images stored in MinIO when `STORAGE_BACKEND=minio`
- [x] Images stored locally when `STORAGE_BACKEND=local`
- [x] Storage backend switchable via environment variable
- [x] MinIO integration tests passing

### Caching (Redis) ⏳
- [ ] Metadata cached in Redis with 1-hour TTL
- [ ] Cache invalidated on delete
- [ ] System works without Redis (graceful degradation)
- [ ] Cache hit/miss logging implemented

### Rate Limiting ⏳
- [ ] 429 returned when limit exceeded
- [ ] Retry-After header included
- [ ] Rate limits stored in Redis
- [ ] Configurable limits per endpoint

### Authentication ⏳
- [ ] User registration working
- [ ] JWT login working
- [ ] Protected routes require valid JWT
- [ ] Image ownership enforced on delete

### Delete Tokens ⏳
- [ ] Token generated on anonymous upload
- [ ] Token required for anonymous delete
- [ ] Token stored as hash

### Background Jobs ⏳
- [ ] Celery worker running
- [ ] Thumbnail generation working
- [ ] Job failures don't affect API

### CI/CD ✅
- [x] GitHub Actions running on PR
- [x] All tests passing
- [x] Dependency check passing

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-01 | Initial Phase 2 requirements with EARS format |

---

## References

- [Phase 1 Requirements](./requirements.md) - Foundation requirements
- [EARS Paper](https://www.iaria.org/conferences2012/filesICCGI12/ICCGI_2012_Tutorial_Mavin.pdf) - EARS methodology
- [TODO.md](./TODO.md) - Implementation tracking
- [Phase 2 Retro](./docs/PHASE2_RETRO.md) - Lessons learned
