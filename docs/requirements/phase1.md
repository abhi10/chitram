# Image Hosting App - Phase 1 Requirements

## Overview

This document defines the functional and non-functional requirements for Phase 1 (Foundation) of the Image Hosting Application. Phase 1 focuses on core upload/download functionality with a simple, anonymous-access model.

---

## Functional Requirements

### FR-1: Image Upload

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | System shall accept image uploads via REST API (POST endpoint) | Must |
| FR-1.2 | System shall support JPEG and PNG formats only | Must |
| FR-1.3 | System shall reject files exceeding 5 MB | Must |
| FR-1.4 | System shall reject non-image files with appropriate error message | Must |
| FR-1.5 | System shall generate a unique identifier (UUID) for each upload | Must |
| FR-1.6 | System shall return image metadata (id, URL, size, dimensions) on successful upload | Must |
| FR-1.7 | System shall allow duplicate uploads (no deduplication) | Must |
| FR-1.8 | System shall accept uploads from anonymous users (no authentication required) | Must |

### FR-2: Image Retrieval

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | System shall serve images via direct URL (GET endpoint) | Must |
| FR-2.2 | System shall return appropriate Content-Type header (image/jpeg, image/png) | Must |
| FR-2.3 | System shall return 404 for non-existent image IDs | Must |
| FR-2.4 | Images shall be "unlisted" - accessible only via direct link, not discoverable | Must |
| FR-2.5 | System shall provide an endpoint to retrieve image metadata without downloading the file | Should |

### FR-3: Image Deletion

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | System shall allow deletion of images via REST API (DELETE endpoint) | Must |
| FR-3.2 | Anyone with the image ID can delete (no delete token in Phase 1) | Must |
| FR-3.3 | System shall return 404 when deleting non-existent images | Must |
| FR-3.4 | System shall remove both metadata and stored file on deletion | Must |

> **Note:** Delete token authentication deferred to Phase 2. Phase 1 uses security through obscurity (UUID is hard to guess).

### FR-4: Image Listing (Limited)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | System shall NOT provide a public listing of all images (unlisted model) | Must |
| FR-4.2 | System may provide admin-only listing for debugging (optional) | Could |

### FR-5: Image Retention

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | Images shall be retained indefinitely (no auto-expiration) | Must |
| FR-5.2 | Images shall only be removed via explicit deletion | Must |

### FR-6: API Documentation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-6.1 | System shall expose OpenAPI/Swagger documentation at /docs | Must |
| FR-6.2 | All endpoints shall return JSON responses (except image file downloads) | Must |
| FR-6.3 | Error responses shall use structured format (see below) | Must |

### FR-7: Error Response Format

All error responses shall follow this structure:

```json
{
  "error": {
    "code": "INVALID_FILE_FORMAT",
    "message": "Only JPEG and PNG formats are supported",
    "details": {}
  }
}
```

**Standard Error Codes:**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_FILE_FORMAT` | 400 | Uploaded file is not JPEG or PNG |
| `FILE_TOO_LARGE` | 400 | File exceeds 5 MB limit |
| `INVALID_REQUEST` | 400 | Malformed request body |
| `IMAGE_NOT_FOUND` | 404 | Image ID does not exist |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests from this IP |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Non-Functional Requirements

### NFR-1: Performance

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-1.1 | Image upload response time (excluding transfer) | < 500ms | Should |
| NFR-1.2 | Image metadata retrieval response time | < 100ms | Should |
| NFR-1.3 | Image download time to first byte | < 200ms | Should |

### NFR-2: Capacity

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-2.1 | Concurrent users supported | 10-50 | Must |
| NFR-2.2 | Maximum single file size | 5 MB | Must |
| NFR-2.3 | Minimum storage capacity | 10 GB | Should |
| NFR-2.4 | Maximum uploads per minute (rate limit) | 10/IP | Should |
| NFR-2.5 | Rate limit response | 429 + Retry-After header | Should |

### NFR-3: Availability

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-3.1 | System uptime (Phase 1 - development) | Best effort | - |
| NFR-3.2 | Graceful error handling (no crashes on bad input) | 100% | Must |
| NFR-3.3 | System shall recover from restart without data loss | 100% | Must |

### NFR-4: Security

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-4.1 | System shall validate file content matches declared type (magic bytes) | Must |
| NFR-4.2 | System shall sanitize filenames to prevent path traversal | Must |
| NFR-4.3 | System shall not execute uploaded files | Must |
| NFR-4.4 | API shall implement basic rate limiting per IP | Should |
| NFR-4.5 | File storage shall be outside web-accessible directory | Must |

### NFR-5: Maintainability

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-5.1 | Code shall follow PEP 8 style guidelines | Should |
| NFR-5.2 | All API endpoints shall have unit tests | Should |
| NFR-5.3 | System shall log all uploads and errors | Must |
| NFR-5.4 | Configuration shall be via environment variables | Must |

### NFR-6: Deployment

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-6.1 | Application shall be containerized (Docker) | Must |
| NFR-6.2 | Local development shall use Docker Compose | Must |
| NFR-6.3 | System shall run on a single server instance | Must |

---

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/images/upload` | Upload a new image |
| GET | `/api/v1/images/{id}` | Get image metadata |
| GET | `/api/v1/images/{id}/file` | Download image file |
| DELETE | `/api/v1/images/{id}` | Delete an image |
| GET | `/health` | Health check endpoint |
| GET | `/docs` | Swagger UI documentation |

---

## Data Model Summary

### Image Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Unique identifier (primary key) |
| filename | string | Yes | Original filename (sanitized) |
| storage_key | string | Yes | Internal storage path/key (UUID-based) |
| content_type | string | Yes | MIME type (image/jpeg, image/png) |
| file_size | integer | Yes | Size in bytes |
| width | integer | No | Image width in pixels (null if unreadable) |
| height | integer | No | Image height in pixels (null if unreadable) |
| upload_ip | string | Yes | Uploader's IP (for rate limiting) |
| created_at | timestamp | Yes | Upload timestamp (UTC) |

> **Note:** `delete_token` deferred to Phase 2.

---

## Out of Scope (Phase 1)

The following features are explicitly **NOT** included in Phase 1:

| Feature | Planned Phase |
|---------|---------------|
| User authentication/accounts | Phase 2 |
| Image thumbnails/resizing | Phase 2 |
| Caching layer (Redis) | Phase 2 |
| Background job processing | Phase 2 |
| Public image galleries | Phase 2+ |
| Image search | Phase 2+ |
| Social features (likes, comments) | Not planned |
| Image editing/filters | Not planned |
| Geographic distribution/CDN | Phase 3 |
| High availability (multi-instance) | Phase 3 |
| Monitoring/telemetry (Prometheus) | Phase 4 |

---

## Acceptance Criteria (Phase 1 Complete)

Phase 1 is considered complete when:

- [ ] Can upload a JPEG image via API and receive metadata response
- [ ] Can upload a PNG image via API and receive metadata response
- [ ] Upload rejects files > 5 MB with appropriate error
- [ ] Upload rejects non-image files with appropriate error
- [ ] Can retrieve image metadata by ID
- [ ] Can download image file by ID
- [ ] Can delete image by ID
- [ ] 404 returned for non-existent images
- [ ] Swagger documentation accessible at /docs
- [ ] Application runs in Docker container
- [ ] Docker Compose starts app + PostgreSQL
- [ ] Basic logging in place
- [ ] Unit tests for upload/download services
- [ ] API tests for all endpoints

---

## Assumptions

1. Single-region deployment (no geographic distribution)
2. Single server instance (no horizontal scaling)
3. PostgreSQL for metadata storage
4. Local filesystem or MinIO for image storage
5. No CDN or caching layer in Phase 1
6. Development/learning environment (not production-grade)

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-13 | Initial Phase 1 requirements |
| 1.1 | 2025-12-13 | Clarified: delete token (deferred), rate limiting (429), error format (structured) |

---

## References

- [Image Hosting MVP - Distributed Systems Design](./image-hosting-mvp-distributed-systems.md)
