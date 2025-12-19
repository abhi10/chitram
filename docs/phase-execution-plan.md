# Phase Execution Plan - Image Hosting App

**Purpose:** Incremental implementation strategy from lean MVP to distributed system
**Philosophy:** Start simple, validate, add complexity incrementally
**Status:** Phase 1 Lean in progress

---

## Overview

This document provides a tactical execution plan for implementing the Image Hosting App across 5 phases. Each phase builds on the previous, allowing for validation before adding complexity.

**Key Principle:** Every phase must be **validated and working** before proceeding to the next.

---

## Phase Comparison

| Aspect | Phase 1 Lean | Phase 1.5 | Phase 2 | Phase 3 | Phase 4 |
|--------|--------------|-----------|---------|---------|---------|
| **Goal** | Validate core | Image info | Optimize | Scale | Observe |
| **Duration** | 2-3 days | 1 day | 1-2 weeks | 2-3 weeks | 1 week |
| **Storage** | Local FS | Local FS | MinIO/S3 | Sharded S3 | Same |
| **Database** | Single PG | Single PG | Single PG | Replicated | Same |
| **Caching** | None | None | Redis | Redis | Same |
| **Services** | 1 | 1 | 1 | Multiple | Same |
| **Complexity** | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Phase 1: Lean Foundation (Current)

### Objective
Validate the absolute minimum working system: upload, store, retrieve, delete images.

### Scope

**Infrastructure:**
- FastAPI monolith
- PostgreSQL (single instance)
- Local filesystem storage
- DevContainer (Postgres only)

**Features:**
- ✅ Upload JPEG/PNG (max 5MB)
- ✅ Get image metadata
- ✅ Download image file
- ✅ Delete image
- ✅ Health check
- ✅ Structured error responses

**Model Fields:**
```python
id, filename, storage_key, content_type,
file_size, upload_ip, created_at
```

**Dependencies:** (9 total)
- fastapi, uvicorn, python-multipart
- sqlalchemy, asyncpg, alembic
- aiofiles, pydantic, pydantic-settings

### What's NOT Included
- ❌ MinIO/S3 storage
- ❌ Image dimensions
- ❌ Advanced validation (python-magic)
- ❌ User authentication
- ❌ Rate limiting (deferred)
- ❌ Background jobs
- ❌ Caching

### Success Criteria
- [ ] Git initialized, code committed
- [ ] Alembic migrations working
- [ ] Application starts (Postgres only)
- [ ] All CRUD operations work via API
- [ ] Tests pass (API tests)
- [ ] Swagger UI functional
- [ ] Can upload/download/delete images
- [ ] Documented in session log

### Deliverables
1. Working API with 4 endpoints
2. Database schema (7 columns)
3. API tests (test_images.py)
4. Alembic migration (initial schema)
5. Git repository with clean history
6. Validation report

**Estimated Duration:** 2-3 days (including validation)

### Exit Criteria
Ready for Phase 1.5 when:
1. All acceptance tests pass
2. No critical bugs
3. Documentation up to date
4. Deployed to Codespaces successfully

---

## Phase 1.5: Image Information

### Objective
Add image dimension extraction without changing architecture.

### Changes from Phase 1

**Add Dependency:**
```toml
"pillow>=11.0.0"
```

**Add Model Fields:**
```python
width: int | None
height: int | None
```

**Add to Service:**
```python
@staticmethod
def get_image_dimensions(data: bytes) -> tuple[int | None, int | None]:
    try:
        with PILImage.open(BytesIO(data)) as img:
            return img.width, img.height
    except Exception:
        return None, None
```

**Update API Response:**
```json
{
  "id": "...",
  "filename": "...",
  "content_type": "...",
  "file_size": 102400,
  "width": 1920,       // NEW
  "height": 1080,      // NEW
  "url": "...",
  "created_at": "..."
}
```

### Implementation Steps
1. Add Pillow to pyproject.toml
2. Run `uv sync`
3. Create Alembic migration: `alembic revision -m "Add width and height"`
4. Add columns to schema
5. Restore `get_image_dimensions()` method
6. Update model fields
7. Update schemas (ImageMetadata, ImageUploadResponse)
8. Update API response construction
9. Update tests (add width/height assertions)
10. Test migration on fresh DB
11. Validate all endpoints still work

### Testing
- [ ] Upload returns width/height for JPEG
- [ ] Upload returns width/height for PNG
- [ ] Existing images (no dimensions) still work
- [ ] Invalid images return None for dimensions
- [ ] Migration runs cleanly

**Estimated Duration:** 4-6 hours

### Exit Criteria
- All Phase 1 functionality still works
- Dimensions returned for valid images
- Migration tested on fresh + existing DB
- Tests updated and passing

---

## Phase 2: Optimization & Features

### Objective
Add production-ready features: caching, background jobs, MinIO storage, authentication.

### Architecture Changes

**New Services:**
- Redis (caching + job queue)
- MinIO (S3-compatible storage)
- Celery workers (background jobs)

**New Features:**
1. **MinIO/S3 Storage**
   - Restore MinioStorageBackend class
   - Add configuration
   - Update docker-compose.yml
   - Strategy pattern makes this transparent

2. **Redis Caching**
   - Cache metadata queries
   - TTL: 1 hour
   - Invalidate on delete

3. **User Authentication**
   - JWT tokens or API keys
   - User accounts table
   - Associate images with users
   - Add `user_id` to images table

4. **Delete Tokens**
   - Generate secure token on upload
   - Require token for deletion
   - Store in separate table or encrypted field

5. **Background Jobs**
   - Thumbnail generation (3 sizes)
   - Image optimization
   - Checksum calculation for deduplication

6. **Rate Limiting**
   - Redis-backed rate limiter
   - 10 requests/IP/minute
   - Return 429 with Retry-After header

7. **Advanced Validation**
   - Restore python-magic for better detection
   - Virus scanning (optional)
   - Content moderation (optional)

### Model Changes

**Add Fields:**
```python
user_id: str | None           # For auth
is_public: bool               # Public vs private
updated_at: datetime          # Track updates
checksum: str                 # For deduplication
thumbnail_path: str | None    # Generated thumbnail
```

**New Tables:**
```python
User(id, email, password_hash, created_at)
DeleteToken(image_id, token_hash, expires_at)
```

### Dependencies Added
```toml
# Storage
"minio>=7.2.0"

# Caching & Jobs
"redis>=5.0.0"
"celery>=5.3.0"

# Auth
"python-jose[cryptography]>=3.3.0"
"passlib[bcrypt]>=1.7.4"

# Validation
"python-magic>=0.4.27"
```

### Implementation Strategy

**Week 1: Storage & Caching**
1. Day 1-2: Add MinIO backend, test switching
2. Day 3: Add Redis caching layer
3. Day 4: Add rate limiting
4. Day 5: Testing & validation

**Week 2: Auth & Background Jobs**
1. Day 1-2: User authentication system
2. Day 3: Delete tokens
3. Day 4-5: Celery setup, thumbnail generation

### Success Criteria
- [ ] Can switch between local/MinIO storage
- [ ] Metadata cached in Redis
- [ ] Rate limiting works (429 responses)
- [ ] Users can register/login
- [ ] Thumbnails generated in background
- [ ] Delete requires token
- [ ] All Phase 1 functionality preserved

**Estimated Duration:** 1-2 weeks

### Exit Criteria
- Feature parity with original Phase 1 scaffolding
- Plus user auth and background jobs
- Ready for horizontal scaling

---

## Phase 3: Horizontal Scaling

### Objective
Scale to handle 1000s of concurrent users across multiple instances.

### Architecture Changes

```
                     ┌─────────────┐
                     │   Nginx LB  │
                     └──────┬──────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
    ┌────────┐         ┌────────┐        ┌────────┐
    │ API 1  │         │ API 2  │        │ API 3  │
    └────────┘         └────────┘        └────────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
    ┌────────┐         ┌────────┐        ┌────────┐
    │Redis   │         │PG Write│        │Storage │
    │Cluster │         │Replica │        │Sharded │
    └────────┘         └────────┘        └────────┘
                            │
                       ┌────┴────┐
                       ▼         ▼
                   ┌──────┐  ┌──────┐
                   │PG R1 │  │PG R2 │
                   └──────┘  └──────┘
```

### New Components

1. **Load Balancer (Nginx)**
   - Round-robin across API instances
   - Health checks
   - SSL termination

2. **Read/Write Database Split**
   - Write → Primary PostgreSQL
   - Reads → Read replicas (2-3)
   - Connection pooling (PgBouncer)

3. **Storage Sharding**
   - Shard by image ID prefix
   - Multiple S3 buckets
   - Consistent hashing

4. **Redis Cluster**
   - 3 master nodes
   - Sentinel for failover
   - Session storage

5. **CDN Integration**
   - CloudFront or Cloudflare
   - Cache image files
   - Reduce latency

### Database Replication

**Setup:**
```sql
-- Primary (write)
postgresql://primary:5432/imagehost

-- Read replicas
postgresql://read-1:5432/imagehost
postgresql://read-2:5432/imagehost
```

**Code Changes:**
```python
# Use read replica for queries
@router.get("/{image_id}")
async def get_image(image_id: str, db: AsyncSession = Depends(get_read_db)):
    # Uses read replica
    ...

# Use primary for writes
@router.post("/upload")
async def upload(file: UploadFile, db: AsyncSession = Depends(get_write_db)):
    # Uses primary
    ...
```

### Implementation Steps

**Week 1: Load Balancing**
1. Docker Compose with 3 API instances
2. Nginx configuration
3. Session handling (Redis)
4. Health check endpoint

**Week 2: Database Replication**
1. Set up PostgreSQL streaming replication
2. Add read/write connection pools
3. Update code to use read replicas
4. Test failover

**Week 3: Storage & CDN**
1. Implement storage sharding
2. Add CDN integration
3. Update image URLs
4. Test distribution

### Success Criteria
- [ ] 3+ API instances behind load balancer
- [ ] Database replication working
- [ ] Read queries use replicas
- [ ] Write queries use primary
- [ ] Storage sharded across buckets
- [ ] CDN serving images
- [ ] Load test: 1000 concurrent users

**Estimated Duration:** 2-3 weeks

### Exit Criteria
- System handles 10x Phase 2 load
- No single point of failure
- Automatic failover working
- Ready for observability

---

## Phase 4: Observability & Reliability

### Objective
Add monitoring, alerting, and resilience patterns.

### New Components

1. **Metrics (Prometheus)**
   - Request rates
   - Error rates
   - Latency percentiles (p50, p95, p99)
   - Storage usage
   - Database connection pool

2. **Dashboards (Grafana)**
   - System overview
   - API performance
   - Database health
   - Storage metrics
   - Alert status

3. **Logging (ELK or Loki)**
   - Structured logging
   - Request tracing
   - Error aggregation
   - Search interface

4. **Tracing (Jaeger)**
   - Distributed traces
   - Request flow visualization
   - Performance bottlenecks

5. **Alerting**
   - PagerDuty integration
   - Slack notifications
   - Alert rules:
     - Error rate > 1%
     - p95 latency > 500ms
     - Disk usage > 80%
     - Service down

6. **Circuit Breakers**
   - Protect external services
   - Graceful degradation
   - Retry with exponential backoff

7. **Health Checks**
   - Liveness probe
   - Readiness probe
   - Dependency checks

### Implementation

**Week 1: Metrics & Dashboards**
1. Add Prometheus instrumentation
2. Deploy Prometheus server
3. Create Grafana dashboards
4. Set up alerts

**Week 2: Logging & Tracing**
1. Structured logging setup
2. Deploy Loki/ELK
3. Add Jaeger tracing
4. Create runbooks

**Week 3: Resilience**
1. Add circuit breakers
2. Implement retry logic
3. Chaos engineering tests
4. Performance tuning

### Success Criteria
- [ ] All metrics collected
- [ ] Dashboards showing real-time data
- [ ] Alerts firing correctly
- [ ] Traces showing request flow
- [ ] Circuit breakers prevent cascading failures
- [ ] 99.9% uptime achieved

**Estimated Duration:** 1 week

### Exit Criteria
- Full observability
- On-call runbooks complete
- Incident response tested
- Production-ready system

---

## Phase Timeline & Dependencies

```
Phase 1 Lean (Week 1-2)
    │
    ├─ Validate core functionality
    │
    └─> Phase 1.5 (Week 2)
            │
            ├─ Add image dimensions
            │
            └─> Phase 2 (Week 3-4)
                    │
                    ├─ MinIO, Redis, Auth
                    │
                    └─> Phase 3 (Week 5-7)
                            │
                            ├─ Horizontal scaling
                            │
                            └─> Phase 4 (Week 8)
                                    │
                                    └─ Observability
```

**Total Timeline:** 8 weeks (2 months)

---

## Migration Checklist

When moving between phases:

### Pre-Migration
- [ ] All tests passing in current phase
- [ ] Documentation updated
- [ ] Git commit with phase tag
- [ ] Backup database
- [ ] Session log written

### During Migration
- [ ] Follow phase-specific guide
- [ ] Run tests after each step
- [ ] Verify no regressions
- [ ] Update docker-compose.yml

### Post-Migration
- [ ] All new tests passing
- [ ] Performance benchmarks run
- [ ] Documentation updated
- [ ] ADR created (if needed)
- [ ] Changelog updated

---

## Rollback Strategy

Each phase should be rollback-safe:

**Phase 1.5 → Phase 1:**
- Drop width/height columns
- Remove Pillow dependency
- Revert schemas

**Phase 2 → Phase 1.5:**
- Remove Redis, MinIO services
- Drop new tables (users, tokens)
- Switch to local storage

**Phase 3 → Phase 2:**
- Remove load balancer
- Stop read replicas
- Single API instance

**Phase 4 → Phase 3:**
- Remove monitoring services
- Keep core functionality

---

## Resource Requirements

| Phase | CPU | RAM | Storage | Services |
|-------|-----|-----|---------|----------|
| 1 Lean | 1 core | 2 GB | 10 GB | 2 (app, pg) |
| 1.5 | 1 core | 2 GB | 10 GB | 2 |
| 2 | 2 cores | 4 GB | 20 GB | 5 (app, pg, redis, minio, celery) |
| 3 | 6 cores | 12 GB | 50 GB | 10+ (LB, 3x app, pg cluster, redis cluster, minio) |
| 4 | 8 cores | 16 GB | 100 GB | 15+ (add prometheus, grafana, jaeger, loki) |

---

## Current Status

**Phase:** 1 Lean (In Progress)
**Next Milestone:** Complete validation checklist
**Blockers:** None
**Last Updated:** 2025-12-19

---

## References

- **Design Document:** `image-hosting-mvp-distributed-systems.md`
- **Requirements:** `requirements.md`
- **ADR-0008:** Phase 1 Lean decision
- **Removal Guide:** `phase1-lean-removals-summary.md`
- **Validation:** `validation-checklist.md`
