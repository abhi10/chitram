# Python Image Hosting MVP - Learning Distributed Systems

## Overview

This document outlines a phased approach to building an Image Hosting Application using a Python stack. Each phase intentionally introduces distributed systems concepts from the AOSA "Scalable Web Architecture" paper, allowing you to learn by building.

**Learning Goal:** Understand distributed systems building blocks through hands-on implementation.

---

## Core Distributed Systems Principles (from AOSA Paper)

Before diving into phases, these are the six foundational principles we'll address:

| Principle | Description | How We'll Learn It |
|-----------|-------------|-------------------|
| **Availability** | System uptime, graceful degradation | Redundancy, health checks |
| **Performance** | Fast responses, low latency | Caching, CDN, async processing |
| **Reliability** | Data consistency, persistence | Database transactions, replication |
| **Scalability** | Handle increased load | Horizontal scaling, partitioning |
| **Manageability** | Easy operations, debugging | Logging, monitoring, containerization |
| **Cost** | Total cost of ownership | Right-sizing, efficient architecture |

---

## Architectural Building Blocks We'll Implement

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DISTRIBUTED SYSTEMS BUILDING BLOCKS              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Phase 1 Lean (Current)       Phase 2: Performance     Phase 3: Scale   │
│  ┌─────────────────┐         ┌─────────────────┐      ┌──────────────┐ │
│  │ Monolith API    │         │ MinIO Storage   │      │ Load Balancer│ │
│  │ Local FS Only   │         │ Caching Layer   │      │ Read/Write   │ │
│  │ PostgreSQL      │         │ Async Queues    │      │   Separation │ │
│  │ 7 DB Columns    │         │ Proxies         │      │ Sharding     │ │
│  │ Manual Magic    │         │ Indexes         │      │ Replication  │ │
│  └─────────────────┘         └─────────────────┘      └──────────────┘ │
│                                                                         │
│  Phase 1.5: Add dimensions (Pillow) + Alembic migrations               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Monolithic Foundation (Learn: Basic Architecture)

### Learning Objectives
- Understand request/response lifecycle
- Implement basic CRUD operations for images
- Learn about file storage patterns
- Database design for metadata

### Phase 1 Lean Approach

> **Note:** This implementation follows a **Phase 1 Lean** strategy (see ADR-0008) to minimize complexity before validation.
> We defer non-essential features to later phases and start with the simplest working system:
> - **Local storage only** (MinIO deferred to Phase 2)
> - **Manual magic bytes validation** (python-magic deferred to Phase 2)
> - **No image dimensions** (Pillow deferred to Phase 1.5)
> - **7 essential database columns** (down from 12 in original Phase 1)
> - **9 dependencies** (down from 12 in original Phase 1)
>
> This allows us to validate core functionality before adding complexity. Once validated, we can incrementally restore features in Phase 1.5 and Phase 2.

### Tech Stack - Phase 1 Lean

```
┌──────────────────────────────────────────────────────┐
│                      Client                          │
│               (Browser / Mobile App)                 │
└────────────────────────┬─────────────────────────────┘
                         │
                         ▼
               ┌─────────────────┐
               │   FastAPI App   │
               │   (Monolith)    │
               │                 │
               │  - Upload API   │
               │  - Download API │
               │  - Metadata API │
               └────────┬────────┘
                        │
                ┌───────┴───────┐
                ▼               ▼
         ┌───────────┐   ┌───────────┐
         │PostgreSQL │   │  Local    │
         │(Metadata) │   │Filesystem │
         │           │   │           │
         │7 Columns  │   │(Phase 1)  │
         └───────────┘   └───────────┘

Note: MinIO deferred to Phase 2 (ADR-0008)
      Image dimensions deferred to Phase 1.5
```

### Core Components

#### Backend Framework
- **FastAPI** - Async Python web framework
  - Built-in file upload handling
  - Automatic API documentation
  - Native async/await support for I/O operations

#### Database
- **PostgreSQL** - Image metadata storage
  - File paths, sizes, content types
  - User associations
  - Upload timestamps
  - Access statistics

#### Storage (Development)
- **Local Filesystem** - Simple file storage for development
- **MinIO** - S3-compatible object storage for local testing

### Project Structure - Phase 1

```
image-hosting-mvp/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry
│   │   ├── config.py               # Settings management
│   │   ├── database.py             # SQLAlchemy setup
│   │   │
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── image.py            # Image metadata model
│   │   │   └── user.py             # User model
│   │   │
│   │   ├── schemas/                # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── image.py            # Image request/response
│   │   │   └── user.py
│   │   │
│   │   ├── api/                    # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── upload.py           # Image upload endpoints
│   │   │   ├── download.py         # Image retrieval endpoints
│   │   │   └── metadata.py         # Image metadata endpoints
│   │   │
│   │   ├── services/               # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── storage_service.py  # File storage abstraction
│   │   │   └── image_service.py    # Image processing logic
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── file_utils.py       # File handling helpers
│   │
│   ├── alembic/                    # Database migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml              # Local development stack
└── .env.example
```

### Database Schema - Phase 1 Lean

```
images (7 essential columns)
├── id (UUID, PK)
├── filename (original filename, sanitized)
├── storage_key (unique path/key in storage)
├── content_type (MIME type: image/jpeg or image/png)
├── file_size (bytes)
├── upload_ip (for rate limiting)
└── created_at (UTC timestamp)

Deferred to Phase 1.5:
├── width (pixels, nullable) - requires Pillow
└── height (pixels, nullable) - requires Pillow

Deferred to Phase 2:
├── checksum (SHA256 hash for deduplication)
├── user_id (FK, nullable - for authentication)
├── is_public (boolean - for access control)
└── updated_at (timestamp)

users (placeholder for future)
├── id (UUID, PK)
├── email
├── api_key (for programmatic access)
├── storage_quota (bytes)
├── storage_used (bytes)
├── created_at
└── updated_at
```

### Key Implementation Patterns

#### Storage Abstraction (Strategy Pattern)
```python
# app/services/storage_service.py
from abc import ABC, abstractmethod

class StorageBackend(ABC):
    @abstractmethod
    async def save(self, key: str, data: bytes) -> str:
        """Save file and return storage URL/path"""
        pass

    @abstractmethod
    async def get(self, key: str) -> bytes:
        """Retrieve file by key"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete file by key"""
        pass

class LocalStorageBackend(StorageBackend):
    """Development: Local filesystem storage"""
    pass

class S3StorageBackend(StorageBackend):
    """Production: S3-compatible storage"""
    pass
```

**Distributed Systems Lesson:** Abstraction allows swapping implementations without changing business logic - essential for evolving distributed systems.

### Phase 1 Lean Dependencies (9 packages)

```txt
# Core Framework
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.12

# Database
sqlalchemy==2.0.35
asyncpg==0.30.0

# Validation
pydantic==2.10.0
pydantic-settings==2.6.0

# Utilities
python-dotenv==1.0.1
httpx==0.28.0
aiofiles==24.1.0

# Deferred to Phase 1.5:
# alembic==1.14.0         # Database migrations
# pillow==11.0.0          # Image dimension extraction

# Deferred to Phase 2:
# python-magic==0.4.27    # Advanced file type validation
# minio>=7.2.0            # S3-compatible object storage

# Development
pytest==8.3.0
pytest-asyncio==0.24.0
```

### Phase 1 API Endpoints

```
POST   /api/v1/images/upload     # Upload single image
POST   /api/v1/images/batch      # Upload multiple images
GET    /api/v1/images/{id}       # Get image metadata
GET    /api/v1/images/{id}/file  # Download actual image
DELETE /api/v1/images/{id}       # Delete image
GET    /api/v1/images            # List images (paginated)
```

### Deliverables - Phase 1
- [ ] Working upload/download API
- [ ] PostgreSQL metadata storage
- [ ] Local file storage (switchable to S3)
- [ ] Basic error handling
- [ ] Docker Compose for local dev
- [ ] Unit tests for services

---

## Phase 2: Performance Optimization (Learn: Caching, Queues, Indexes)

### Learning Objectives
- Implement caching layers (local → distributed)
- Understand cache invalidation strategies
- Learn message queue patterns for async processing
- Implement indexes for fast lookups

### Distributed Systems Concepts Introduced

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PHASE 2 ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │    Client    │
                              └──────┬───────┘
                                     │
                              ┌──────▼───────┐
                              │    Nginx     │ ←── Static file serving
                              │   (Proxy)    │     Response caching
                              └──────┬───────┘
                                     │
                              ┌──────▼───────┐
                              │   FastAPI    │
                              │     App      │
                              └──────┬───────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          ▼                          ▼                          ▼
   ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
   │   Redis     │           │ PostgreSQL  │           │   Redis     │
   │   Cache     │           │  + Indexes  │           │   Queue     │
   │             │           │             │           │ (or RabbitMQ)│
   │ - Metadata  │           │ - B-tree    │           │             │
   │ - Hot images│           │ - Hash      │           │ - Thumbnails│
   └─────────────┘           │ - GIN/GIST  │           │ - Cleanup   │
                             └─────────────┘           └─────────────┘
                                                              │
                                                              ▼
                                                       ┌─────────────┐
                                                       │   Worker    │
                                                       │  Process(es)│
                                                       │             │
                                                       │ - Resize    │
                                                       │ - Optimize  │
                                                       │ - Cleanup   │
                                                       └─────────────┘
```

### New Components

#### 1. Caching Layer (Redis)

**Learning: Cache-aside pattern**
```python
# app/services/cache_service.py
class CacheService:
    """
    Cache-aside pattern implementation:
    1. Check cache first
    2. If miss, fetch from DB
    3. Store in cache
    4. Return data
    """

    async def get_image_metadata(self, image_id: str) -> dict | None:
        # Try cache first
        cached = await self.redis.get(f"image:{image_id}")
        if cached:
            return json.loads(cached)

        # Cache miss - fetch from DB
        image = await self.db.get_image(image_id)
        if image:
            # Store in cache with TTL
            await self.redis.setex(
                f"image:{image_id}",
                ttl=3600,  # 1 hour
                value=json.dumps(image.to_dict())
            )
        return image
```

**Cache Invalidation Strategies:**
- Time-based (TTL) - Simple, eventual consistency
- Write-through - Update cache on every write
- Write-behind - Queue cache updates, batch to DB
- Event-based - Pub/sub for invalidation

#### 2. Message Queue (Async Processing)

**Learning: Producer-Consumer pattern**

```python
# app/services/queue_service.py
from celery import Celery

# Tasks that shouldn't block the upload response:
# 1. Generate thumbnails (multiple sizes)
# 2. Extract EXIF metadata
# 3. Run virus scan
# 4. Update search index
# 5. Send webhook notifications

@celery.task
def process_uploaded_image(image_id: str):
    """Background job for post-upload processing"""
    image = get_image(image_id)

    # Generate thumbnails
    generate_thumbnail(image, size=(150, 150))
    generate_thumbnail(image, size=(300, 300))
    generate_thumbnail(image, size=(800, 800))

    # Extract and store EXIF data
    extract_exif_metadata(image)

    # Update search index
    index_image(image)
```

**Queue Patterns to Learn:**
- Task queues (Celery/RQ)
- Pub/Sub (Redis Pub/Sub)
- Message brokers (RabbitMQ)

#### 3. Database Indexes

**Learning: Index types and their use cases**

```sql
-- B-tree: Equality and range queries (default)
CREATE INDEX idx_images_created_at ON images(created_at);

-- Hash: Exact match lookups (O(1))
CREATE INDEX idx_images_checksum ON images USING hash(checksum);

-- GIN: Full-text search on JSONB
CREATE INDEX idx_images_metadata ON images USING gin(metadata);

-- Partial: Index only relevant rows
CREATE INDEX idx_images_public ON images(created_at)
WHERE is_public = true;

-- Covering: Include columns to avoid table lookup
CREATE INDEX idx_images_list ON images(user_id, created_at)
INCLUDE (filename, file_size);
```

#### 4. Reverse Proxy (Nginx)

**Learning: Proxy patterns**

```nginx
# nginx.conf
upstream fastapi {
    server app:8000;
}

server {
    listen 80;

    # Serve static files directly (bypass app server)
    location /static/ {
        alias /var/www/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Cache image responses
    location /api/v1/images/ {
        proxy_pass http://fastapi;
        proxy_cache images_cache;
        proxy_cache_valid 200 1h;
        proxy_cache_key $request_uri;

        # Collapse identical requests
        proxy_cache_lock on;
    }

    # No cache for uploads
    location /api/v1/images/upload {
        proxy_pass http://fastapi;
        client_max_body_size 50M;
    }
}
```

**Proxy Benefits:**
- Request collapsing (multiple identical requests = 1 backend call)
- Response caching
- SSL termination
- Static file serving
- Rate limiting

### Updated Project Structure

```
image-hosting-mvp/
├── backend/
│   ├── app/
│   │   ├── ...existing...
│   │   │
│   │   ├── services/
│   │   │   ├── ...existing...
│   │   │   ├── cache_service.py    # NEW: Redis caching
│   │   │   └── queue_service.py    # NEW: Task queue
│   │   │
│   │   └── workers/                # NEW: Background workers
│   │       ├── __init__.py
│   │       ├── celery_app.py       # Celery configuration
│   │       ├── thumbnail_worker.py # Image processing tasks
│   │       └── cleanup_worker.py   # Orphan file cleanup
│   │
│   └── ...
│
├── nginx/
│   ├── nginx.conf                  # NEW: Reverse proxy config
│   └── Dockerfile
│
└── docker-compose.yml              # Updated with Redis, Nginx
```

### Phase 2 Additional Dependencies

```txt
# Caching
redis==5.2.0
hiredis==3.0.0  # C parser for performance

# Task Queue
celery==5.4.0
# OR
rq==2.0.0  # Simpler alternative

# Image Processing
pillow==11.0.0
pillow-heif==0.18.0  # HEIF/HEIC support
```

### Phase 2 Metrics to Track

| Metric | Tool | Purpose |
|--------|------|---------|
| Cache hit ratio | Redis INFO | Measure cache effectiveness |
| Queue depth | Celery/Flower | Identify processing bottlenecks |
| P95 response time | Prometheus | Performance baseline |
| DB query time | pg_stat_statements | Identify slow queries |

### Deliverables - Phase 2
- [ ] Redis caching for metadata
- [ ] Background job processing (thumbnails)
- [ ] Nginx reverse proxy setup
- [ ] Database indexes optimized
- [ ] Cache invalidation strategy
- [ ] Monitoring dashboard (basic)

---

## Phase 3: Horizontal Scaling (Learn: Load Balancing, Sharding, Replication)

### Learning Objectives
- Understand read/write service separation
- Implement load balancing strategies
- Learn data partitioning (sharding)
- Set up database replication
- Design for redundancy and failover

### Distributed Systems Concepts Introduced

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PHASE 3 ARCHITECTURE                            │
│                    (Horizontally Scalable Design)                       │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │     CDN      │ ←── Edge caching
                              │ (CloudFlare) │     Geographic distribution
                              └──────┬───────┘
                                     │
                              ┌──────▼───────┐
                              │    Nginx     │
                              │Load Balancer │ ←── Round-robin, least-conn
                              └──────┬───────┘
                                     │
              ┌──────────────────────┴──────────────────────┐
              │                                             │
              ▼                                             ▼
     ┌─────────────────┐                         ┌─────────────────┐
     │  READ SERVICE   │                         │ WRITE SERVICE   │
     │   (Multiple)    │                         │   (Separate)    │
     │                 │                         │                 │
     │ - Get image     │                         │ - Upload image  │
     │ - List images   │                         │ - Delete image  │
     │ - Search        │                         │ - Update meta   │
     └────────┬────────┘                         └────────┬────────┘
              │                                           │
              │ Read Replicas                             │ Primary
              ▼                                           ▼
     ┌─────────────────┐                         ┌─────────────────┐
     │   PostgreSQL    │◄────── Replication ────►│   PostgreSQL    │
     │    Replica 1    │                         │     Primary     │
     │    Replica 2    │                         └─────────────────┘
     └─────────────────┘

                    ┌─────────────────────────────────────┐
                    │         STORAGE LAYER               │
                    │                                     │
                    │  ┌─────────┐ ┌─────────┐ ┌───────┐ │
                    │  │ Shard 1 │ │ Shard 2 │ │Shard N│ │
                    │  │ (a-f)   │ │ (g-m)   │ │(n-z)  │ │
                    │  │         │ │         │ │       │ │
                    │  │ S3/MinIO│ │ S3/MinIO│ │S3/MinIO│ │
                    │  └─────────┘ └─────────┘ └───────┘ │
                    └─────────────────────────────────────┘
```

### Key Patterns

#### 1. Read/Write Service Separation (CQRS-lite)

**Why separate?** From the AOSA paper:
> "Reads and writes have fundamentally different characteristics. Writes are serialized, require consistency. Reads can be parallelized, tolerate staleness."

```python
# Read service - optimized for throughput
# app/api/read_service.py
class ImageReadService:
    def __init__(self, read_replica_pool, cache):
        self.db = read_replica_pool  # Connect to replicas
        self.cache = cache

    async def get_image(self, image_id: str):
        # Check cache first
        if cached := await self.cache.get(image_id):
            return cached

        # Read from replica (slightly stale OK)
        image = await self.db.fetch_one(
            "SELECT * FROM images WHERE id = $1", image_id
        )
        await self.cache.set(image_id, image, ttl=300)
        return image

# Write service - optimized for consistency
# app/api/write_service.py
class ImageWriteService:
    def __init__(self, primary_db, cache, event_bus):
        self.db = primary_db  # Only primary
        self.cache = cache
        self.events = event_bus

    async def upload_image(self, file, metadata):
        async with self.db.transaction():
            image = await self.db.insert_image(metadata)
            await self.storage.save(image.storage_key, file)

        # Invalidate cache
        await self.cache.delete(f"image:{image.id}")

        # Publish event for other services
        await self.events.publish("image.created", image.id)

        return image
```

#### 2. Load Balancing Strategies

**Learning: Different algorithms for different needs**

```nginx
# nginx load balancer configuration

# Round Robin (default) - Equal distribution
upstream read_services {
    server read-1:8000;
    server read-2:8000;
    server read-3:8000;
}

# Least Connections - Route to least busy
upstream read_services_leastconn {
    least_conn;
    server read-1:8000;
    server read-2:8000;
    server read-3:8000;
}

# IP Hash - Session affinity (same user → same server)
upstream read_services_sticky {
    ip_hash;
    server read-1:8000;
    server read-2:8000;
    server read-3:8000;
}

# Weighted - Different server capacities
upstream read_services_weighted {
    server read-1:8000 weight=5;  # 50% traffic
    server read-2:8000 weight=3;  # 30% traffic
    server read-3:8000 weight=2;  # 20% traffic
}
```

**Health Checks:**
```nginx
upstream read_services {
    server read-1:8000 max_fails=3 fail_timeout=30s;
    server read-2:8000 max_fails=3 fail_timeout=30s;
    server read-3:8000 backup;  # Only used when others fail
}
```

#### 3. Data Partitioning (Sharding)

**Learning: How to distribute data across multiple storage nodes**

```python
# app/services/shard_router.py
import hashlib

class ShardRouter:
    """
    Consistent hashing for storage sharding.
    Distributes images across multiple storage backends.
    """

    def __init__(self, shards: list[StorageBackend]):
        self.shards = shards
        self.num_shards = len(shards)

    def get_shard(self, image_id: str) -> StorageBackend:
        """
        Determine which shard stores this image.
        Uses consistent hashing for even distribution.
        """
        hash_value = int(hashlib.md5(image_id.encode()).hexdigest(), 16)
        shard_index = hash_value % self.num_shards
        return self.shards[shard_index]

    async def save(self, image_id: str, data: bytes):
        shard = self.get_shard(image_id)
        return await shard.save(image_id, data)

    async def get(self, image_id: str) -> bytes:
        shard = self.get_shard(image_id)
        return await shard.get(image_id)


# More advanced: Consistent hashing ring
# Minimizes data movement when adding/removing shards
class ConsistentHashRing:
    """
    Consistent hashing minimizes redistribution when
    nodes are added/removed.
    """
    def __init__(self, nodes, virtual_nodes=150):
        self.ring = {}
        self.sorted_keys = []

        for node in nodes:
            for i in range(virtual_nodes):
                key = self._hash(f"{node}:{i}")
                self.ring[key] = node
                self.sorted_keys.append(key)

        self.sorted_keys.sort()

    def get_node(self, key: str):
        """Find the node responsible for this key"""
        hash_val = self._hash(key)

        for ring_key in self.sorted_keys:
            if hash_val <= ring_key:
                return self.ring[ring_key]

        return self.ring[self.sorted_keys[0]]
```

**Sharding Strategies:**
| Strategy | Use Case | Pros | Cons |
|----------|----------|------|------|
| Hash-based | Even distribution | Balanced load | Difficult range queries |
| Range-based | Time-series data | Easy range scans | Hot spots possible |
| Geographic | Regional data | Low latency | Uneven distribution |
| Directory-based | Flexible | Any scheme | Single point of failure |

#### 4. Database Replication

**Learning: Primary-Replica pattern**

```yaml
# docker-compose.yml - PostgreSQL replication setup
services:
  postgres-primary:
    image: postgres:16
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: imagehost
    command: |
      postgres
        -c wal_level=replica
        -c max_wal_senders=3
        -c max_replication_slots=3
    volumes:
      - postgres_primary_data:/var/lib/postgresql/data

  postgres-replica:
    image: postgres:16
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    command: |
      bash -c "
        pg_basebackup -h postgres-primary -D /var/lib/postgresql/data -U replicator -P -R
        postgres
      "
    depends_on:
      - postgres-primary
```

**Application-level routing:**
```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine

class DatabasePool:
    def __init__(self, primary_url: str, replica_urls: list[str]):
        self.primary = create_async_engine(primary_url)
        self.replicas = [create_async_engine(url) for url in replica_urls]
        self._replica_index = 0

    def get_write_connection(self):
        """Always use primary for writes"""
        return self.primary

    def get_read_connection(self):
        """Round-robin across replicas"""
        if not self.replicas:
            return self.primary

        replica = self.replicas[self._replica_index]
        self._replica_index = (self._replica_index + 1) % len(self.replicas)
        return replica
```

#### 5. Redundancy & Failover

**Learning: Eliminating single points of failure**

```python
# app/services/resilient_storage.py
class ReplicatedStorage:
    """
    Write to multiple storage backends for redundancy.
    Read from any available replica.
    """

    def __init__(self, primary: StorageBackend, replicas: list[StorageBackend]):
        self.primary = primary
        self.replicas = replicas

    async def save(self, key: str, data: bytes):
        """Write to primary and replicate async"""
        # Synchronous write to primary
        await self.primary.save(key, data)

        # Async replication (fire-and-forget or queued)
        for replica in self.replicas:
            asyncio.create_task(replica.save(key, data))

    async def get(self, key: str) -> bytes:
        """Try primary, fallback to replicas"""
        try:
            return await self.primary.get(key)
        except StorageError:
            for replica in self.replicas:
                try:
                    return await replica.get(key)
                except StorageError:
                    continue
            raise StorageError(f"All replicas failed for key: {key}")
```

### Updated Architecture Files

```
image-hosting-mvp/
├── services/
│   ├── read-service/              # Scaled read instances
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── write-service/             # Single write service
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── worker-service/            # Background processors
│       ├── app/
│       ├── Dockerfile
│       └── requirements.txt
│
├── infrastructure/
│   ├── nginx/
│   │   └── nginx.conf             # Load balancer config
│   │
│   └── postgres/
│       ├── primary.conf
│       └── replica.conf
│
├── docker-compose.yml             # Local multi-service setup
└── docker-compose.prod.yml        # Production-like setup
```

### Phase 3 Scaling Targets

| Component | Scaling Strategy | Implementation |
|-----------|-----------------|----------------|
| Read Service | Horizontal (N instances) | Docker Swarm / K8s |
| Write Service | Vertical + Queue | Single instance + workers |
| Database | Read replicas | PostgreSQL streaming |
| Storage | Sharding | Consistent hash ring |
| Cache | Distributed | Redis Cluster |

### Deliverables - Phase 3
- [ ] Separate read/write services
- [ ] Load balancer with health checks
- [ ] Database replication (1 primary + 2 replicas)
- [ ] Storage sharding implementation
- [ ] Redundant storage with failover
- [ ] Horizontal scaling configuration

---

## Phase 4: Production Readiness (Learn: Observability, Resilience)

### Learning Objectives
- Implement comprehensive monitoring
- Learn circuit breaker patterns
- Understand rate limiting
- Practice graceful degradation

### Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PHASE 4: PRODUCTION READINESS                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         OBSERVABILITY STACK                             │
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │ Prometheus  │    │   Grafana   │    │   Jaeger    │                 │
│  │  (Metrics)  │    │(Dashboards) │    │  (Tracing)  │                 │
│  └─────────────┘    └─────────────┘    └─────────────┘                 │
│         ▲                  ▲                  ▲                         │
│         │                  │                  │                         │
│         └──────────────────┼──────────────────┘                         │
│                            │                                            │
└────────────────────────────┼────────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │   Application   │
                    │    Services     │
                    └─────────────────┘
```

### 1. Rate Limiting

```python
# app/middleware/rate_limit.py
from fastapi import Request, HTTPException
import redis.asyncio as redis

class RateLimiter:
    """
    Token bucket rate limiting using Redis.
    Distributed across all service instances.
    """

    def __init__(self, redis_client, requests_per_minute: int = 60):
        self.redis = redis_client
        self.limit = requests_per_minute
        self.window = 60  # seconds

    async def is_allowed(self, key: str) -> bool:
        """Check if request is within rate limit"""
        pipe = self.redis.pipeline()
        now = time.time()
        window_start = now - self.window

        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Count requests in window
        pipe.zcard(key)
        # Set expiry
        pipe.expire(key, self.window)

        results = await pipe.execute()
        request_count = results[2]

        return request_count <= self.limit
```

### 2. Circuit Breaker

```python
# app/utils/circuit_breaker.py
from enum import Enum
from dataclasses import dataclass
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreaker:
    """
    Prevents cascading failures by failing fast
    when a dependency is unhealthy.
    """
    failure_threshold: int = 5
    recovery_timeout: float = 30.0

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0

    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

### 3. Graceful Degradation

```python
# app/services/image_service.py
class ImageService:
    """
    Implements graceful degradation when services fail.
    """

    async def get_image_with_thumbnail(self, image_id: str):
        image = await self.get_image(image_id)

        # Try to get thumbnail, fallback to placeholder
        try:
            thumbnail = await self.thumbnail_service.get(image_id)
        except (ServiceUnavailable, TimeoutError):
            # Graceful degradation: return placeholder
            thumbnail = self.get_placeholder_thumbnail()
            # Log for monitoring
            logger.warning(f"Thumbnail service unavailable for {image_id}")

        return ImageResponse(image=image, thumbnail=thumbnail)

    async def get_image_metadata(self, image_id: str):
        # Try cache first (fast path)
        try:
            if cached := await self.cache.get(image_id):
                return cached
        except redis.RedisError:
            # Cache unavailable - continue without it
            logger.warning("Cache unavailable, falling back to DB")

        # Fallback to database
        return await self.db.get_image(image_id)
```

### 4. Metrics & Monitoring

```python
# app/middleware/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10]
)

# Business metrics
UPLOADS_TOTAL = Counter('images_uploaded_total', 'Total images uploaded')
STORAGE_BYTES = Gauge('storage_bytes_used', 'Total storage used in bytes')
CACHE_HIT_RATIO = Gauge('cache_hit_ratio', 'Cache hit ratio')

# Dependency health
DB_CONNECTIONS = Gauge('db_connections_active', 'Active DB connections')
QUEUE_DEPTH = Gauge('queue_depth', 'Background job queue depth')
```

### Deliverables - Phase 4
- [ ] Prometheus metrics collection
- [ ] Grafana dashboards
- [ ] Distributed tracing (Jaeger)
- [ ] Rate limiting (per IP, per user)
- [ ] Circuit breakers for external calls
- [ ] Graceful degradation patterns
- [ ] Health check endpoints
- [ ] Alerting rules

---

## Testing Strategy

### Testing Pyramid for Distributed Systems

```
                    ┌───────────────┐
                    │   E2E / UI    │  ← Few, slow, expensive
                    │  Automation   │
                    ├───────────────┤
                    │     Load      │  ← Validate scalability
                    │   Testing     │
                ┌───┴───────────────┴───┐
                │    API / Integration  │  ← Service boundaries
                │       Testing         │
            ┌───┴───────────────────────┴───┐
            │         Unit Testing          │  ← Many, fast, cheap
            └───────────────────────────────┘
```

### Simplest Tools Recommendation

| Test Type | Tool | Why It's Simple |
|-----------|------|-----------------|
| Unit Testing | **pytest** | Python standard, minimal setup |
| API Testing | **pytest + httpx** | Built into FastAPI, async support |
| Integration | **pytest + testcontainers** | Real services in Docker, auto-cleanup |
| Load Testing | **locust** | Python-based, simple scripts |
| UI Automation | **Playwright** | Modern, auto-waits, great DX |
| Contract Testing | **schemathesis** | Auto-generates tests from OpenAPI |

---

### 1. Unit Testing (pytest)

**When:** Test individual functions and classes in isolation.

**Setup:**
```bash
pip install pytest pytest-asyncio pytest-cov
```

**Project structure:**
```
backend/
├── app/
│   └── services/
│       └── image_service.py
└── tests/
    ├── __init__.py
    ├── conftest.py              # Shared fixtures
    └── unit/
        ├── __init__.py
        └── test_image_service.py
```

**Example - Testing image service:**
```python
# tests/unit/test_image_service.py
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.image_service import ImageService

class TestImageService:
    """Unit tests - mock all dependencies"""

    @pytest.fixture
    def mock_storage(self):
        storage = AsyncMock()
        storage.save.return_value = "images/abc123.jpg"
        return storage

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_storage, mock_db):
        return ImageService(storage=mock_storage, db=mock_db)

    @pytest.mark.asyncio
    async def test_upload_generates_unique_key(self, service, mock_storage):
        """Each upload should have a unique storage key"""
        file_content = b"fake image data"

        result = await service.upload(file_content, filename="test.jpg")

        # Verify storage was called
        mock_storage.save.assert_called_once()
        # Key should be generated, not the original filename
        call_args = mock_storage.save.call_args[0]
        assert call_args[0] != "test.jpg"
        assert result.storage_key is not None

    @pytest.mark.asyncio
    async def test_upload_calculates_checksum(self, service):
        """Uploads should calculate file checksum for deduplication"""
        file_content = b"fake image data"

        result = await service.upload(file_content, filename="test.jpg")

        assert result.checksum is not None
        assert len(result.checksum) == 64  # SHA256 hex length

    @pytest.mark.asyncio
    async def test_get_nonexistent_image_returns_none(self, service, mock_db):
        """Getting a non-existent image should return None"""
        mock_db.get_image.return_value = None

        result = await service.get("nonexistent-id")

        assert result is None
```

**Run tests:**
```bash
# Run all unit tests
pytest tests/unit -v

# With coverage
pytest tests/unit --cov=app --cov-report=term-missing

# Run specific test
pytest tests/unit/test_image_service.py::TestImageService::test_upload_generates_unique_key -v
```

**Fixtures file (shared test utilities):**
```python
# tests/conftest.py
import pytest
from PIL import Image
import io

@pytest.fixture
def sample_image_bytes():
    """Create a valid test image"""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.read()

@pytest.fixture
def sample_png_bytes():
    """Create a valid PNG test image"""
    img = Image.new('RGBA', (100, 100), color='blue')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.read()
```

---

### 2. API Testing (pytest + httpx)

**When:** Test HTTP endpoints, request/response contracts, error handling.

**Setup:**
```bash
pip install httpx pytest-asyncio
```

**Example - Testing upload endpoint:**
```python
# tests/api/test_upload_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

class TestUploadAPI:
    """API tests - test HTTP layer"""

    @pytest.fixture
    async def client(self):
        """Async test client for FastAPI"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_upload_valid_image(self, client, sample_image_bytes):
        """POST /api/v1/images/upload with valid image returns 201"""
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")}
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "storage_key" in data
        assert data["content_type"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_upload_no_file_returns_422(self, client):
        """POST /api/v1/images/upload without file returns 422"""
        response = await client.post("/api/v1/images/upload")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type_returns_400(self, client):
        """POST /api/v1/images/upload with non-image returns 400"""
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.txt", b"not an image", "text/plain")}
        )

        assert response.status_code == 400
        assert "invalid file type" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_image_metadata(self, client, sample_image_bytes):
        """GET /api/v1/images/{id} returns image metadata"""
        # First upload
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")}
        )
        image_id = upload_response.json()["id"]

        # Then fetch metadata
        response = await client.get(f"/api/v1/images/{image_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == image_id
        assert data["filename"] == "test.jpg"

    @pytest.mark.asyncio
    async def test_get_nonexistent_image_returns_404(self, client):
        """GET /api/v1/images/{id} with invalid ID returns 404"""
        response = await client.get("/api/v1/images/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_image_file(self, client, sample_image_bytes):
        """GET /api/v1/images/{id}/file returns actual image bytes"""
        # Upload first
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")}
        )
        image_id = upload_response.json()["id"]

        # Download file
        response = await client.get(f"/api/v1/images/{image_id}/file")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert len(response.content) > 0
```

---

### 3. Integration Testing (pytest + testcontainers)

**When:** Test services working together with real dependencies (DB, Redis, S3).

**Why testcontainers:** Spins up real Docker containers for tests, auto-cleanup.

**Setup:**
```bash
pip install testcontainers[postgres,redis]
```

**Example - Testing with real PostgreSQL and Redis:**
```python
# tests/integration/test_image_flow.py
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.database import Base
from app.services.image_service import ImageService
from app.services.cache_service import CacheService

class TestImageFlowIntegration:
    """Integration tests with real services"""

    @pytest.fixture(scope="class")
    def postgres_container(self):
        """Start PostgreSQL container for test class"""
        with PostgresContainer("postgres:16") as postgres:
            yield postgres

    @pytest.fixture(scope="class")
    def redis_container(self):
        """Start Redis container for test class"""
        with RedisContainer("redis:7") as redis:
            yield redis

    @pytest.fixture
    async def db_session(self, postgres_container):
        """Create test database session"""
        # Build async connection string
        url = postgres_container.get_connection_url()
        async_url = url.replace("postgresql://", "postgresql+asyncpg://")

        engine = create_async_engine(async_url)

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSession(engine) as session:
            yield session

        # Cleanup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @pytest.fixture
    def redis_client(self, redis_container):
        """Create Redis client for tests"""
        import redis
        return redis.from_url(redis_container.get_connection_url())

    @pytest.mark.asyncio
    async def test_upload_persists_to_database(
        self, db_session, sample_image_bytes
    ):
        """Uploaded images should be persisted to PostgreSQL"""
        service = ImageService(db=db_session, storage=LocalStorage())

        result = await service.upload(sample_image_bytes, filename="test.jpg")

        # Verify in database
        from app.models.image import Image
        db_image = await db_session.get(Image, result.id)
        assert db_image is not None
        assert db_image.filename == "test.jpg"

    @pytest.mark.asyncio
    async def test_cache_stores_metadata(
        self, db_session, redis_client, sample_image_bytes
    ):
        """Image metadata should be cached in Redis after fetch"""
        cache = CacheService(redis_client)
        service = ImageService(db=db_session, storage=LocalStorage(), cache=cache)

        # Upload
        uploaded = await service.upload(sample_image_bytes, filename="test.jpg")

        # First fetch - should cache
        await service.get(uploaded.id)

        # Verify cached in Redis
        cached = redis_client.get(f"image:{uploaded.id}")
        assert cached is not None

    @pytest.mark.asyncio
    async def test_full_upload_download_cycle(
        self, db_session, redis_client, sample_image_bytes
    ):
        """Complete flow: upload → cache → download"""
        cache = CacheService(redis_client)
        service = ImageService(db=db_session, storage=LocalStorage(), cache=cache)

        # Upload
        uploaded = await service.upload(sample_image_bytes, filename="photo.jpg")
        assert uploaded.id is not None

        # Fetch metadata (should cache)
        metadata = await service.get(uploaded.id)
        assert metadata.filename == "photo.jpg"

        # Download file
        file_bytes = await service.download(uploaded.id)
        assert file_bytes == sample_image_bytes
```

**Run integration tests:**
```bash
# Requires Docker running
pytest tests/integration -v

# Skip if no Docker
pytest tests/integration -v --ignore-glob="**/test_*_integration.py"
```

---

### 4. Load Testing (locust)

**When:** Validate scalability, find bottlenecks, establish performance baselines.

**Why locust:** Python-based, simple to write, web UI for results.

**Setup:**
```bash
pip install locust
```

**Example - Load testing image service:**
```python
# tests/load/locustfile.py
from locust import HttpUser, task, between
import io
from PIL import Image

class ImageHostingUser(HttpUser):
    """Simulates a user uploading and viewing images"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    uploaded_image_ids = []

    def on_start(self):
        """Create a test image on user start"""
        img = Image.new('RGB', (800, 600), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        self.test_image = buffer.read()

    @task(3)  # Weight: 3x more likely than upload
    def view_image(self):
        """GET /api/v1/images/{id} - View image metadata"""
        if self.uploaded_image_ids:
            image_id = self.uploaded_image_ids[-1]
            self.client.get(
                f"/api/v1/images/{image_id}",
                name="/api/v1/images/[id]"
            )

    @task(3)
    def download_image(self):
        """GET /api/v1/images/{id}/file - Download actual image"""
        if self.uploaded_image_ids:
            image_id = self.uploaded_image_ids[-1]
            self.client.get(
                f"/api/v1/images/{image_id}/file",
                name="/api/v1/images/[id]/file"
            )

    @task(1)  # Less frequent than reads
    def upload_image(self):
        """POST /api/v1/images/upload - Upload new image"""
        response = self.client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", self.test_image, "image/jpeg")},
            name="/api/v1/images/upload"
        )
        if response.status_code == 201:
            image_id = response.json().get("id")
            if image_id:
                self.uploaded_image_ids.append(image_id)

    @task(1)
    def list_images(self):
        """GET /api/v1/images - List all images"""
        self.client.get("/api/v1/images?limit=20")


class HeavyUploadUser(HttpUser):
    """Simulates users doing bulk uploads"""

    wait_time = between(0.5, 1)

    def on_start(self):
        # Larger image for stress testing
        img = Image.new('RGB', (1920, 1080), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        self.large_image = buffer.read()

    @task
    def upload_large_image(self):
        """Upload larger images to stress test"""
        self.client.post(
            "/api/v1/images/upload",
            files={"file": ("large.jpg", self.large_image, "image/jpeg")},
            name="/api/v1/images/upload (large)"
        )
```

**Run load tests:**
```bash
# Start web UI (recommended)
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Then open http://localhost:8089 in browser
# Set: Number of users: 100, Spawn rate: 10

# Or run headless
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=100 \
    --spawn-rate=10 \
    --run-time=60s \
    --headless
```

**Key metrics to watch:**
| Metric | Target | Red Flag |
|--------|--------|----------|
| P50 response time | < 100ms | > 500ms |
| P95 response time | < 500ms | > 2s |
| Requests/sec | Baseline | Sudden drops |
| Error rate | < 1% | > 5% |

---

### 5. UI Automation (Playwright)

**When:** Test user flows in the browser, visual regression, E2E.

**Why Playwright:** Modern, auto-waits, works with all browsers, great Python support.

**Setup:**
```bash
pip install playwright pytest-playwright
playwright install  # Downloads browser binaries
```

**Example - Testing image upload UI:**
```python
# tests/e2e/test_upload_flow.py
import pytest
from playwright.sync_api import Page, expect

class TestImageUploadFlow:
    """End-to-end browser tests"""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to app before each test"""
        page.goto("http://localhost:3000")  # Frontend URL

    def test_homepage_loads(self, page: Page):
        """Homepage should display upload button"""
        expect(page.get_by_role("button", name="Upload")).to_be_visible()

    def test_upload_image_success(self, page: Page):
        """User can upload an image and see it in gallery"""
        # Click upload button
        page.get_by_role("button", name="Upload").click()

        # Upload file
        page.get_by_label("Choose file").set_input_files("tests/fixtures/sample.jpg")

        # Click submit
        page.get_by_role("button", name="Submit").click()

        # Wait for success message
        expect(page.get_by_text("Upload successful")).to_be_visible(timeout=10000)

        # Verify image appears in gallery
        expect(page.get_by_alt_text("sample.jpg")).to_be_visible()

    def test_upload_invalid_file_shows_error(self, page: Page):
        """Uploading non-image shows error message"""
        page.get_by_role("button", name="Upload").click()
        page.get_by_label("Choose file").set_input_files("tests/fixtures/document.txt")
        page.get_by_role("button", name="Submit").click()

        expect(page.get_by_text("Invalid file type")).to_be_visible()

    def test_view_image_details(self, page: Page):
        """Clicking an image shows its details"""
        # Assuming there's at least one image
        page.get_by_role("img").first.click()

        # Details panel should show
        expect(page.get_by_text("File size")).to_be_visible()
        expect(page.get_by_text("Uploaded")).to_be_visible()

    def test_delete_image(self, page: Page):
        """User can delete an uploaded image"""
        # Upload first
        page.get_by_role("button", name="Upload").click()
        page.get_by_label("Choose file").set_input_files("tests/fixtures/to_delete.jpg")
        page.get_by_role("button", name="Submit").click()
        expect(page.get_by_text("Upload successful")).to_be_visible()

        # Click image to select
        page.get_by_alt_text("to_delete.jpg").click()

        # Delete
        page.get_by_role("button", name="Delete").click()

        # Confirm dialog
        page.get_by_role("button", name="Confirm").click()

        # Image should be gone
        expect(page.get_by_alt_text("to_delete.jpg")).not_to_be_visible()
```

**Run E2E tests:**
```bash
# Run all E2E tests
pytest tests/e2e -v

# Run with browser visible (for debugging)
pytest tests/e2e -v --headed

# Run specific browser
pytest tests/e2e -v --browser=firefox

# Generate HTML report
pytest tests/e2e -v --html=report.html
```

---

### 6. Contract Testing (schemathesis)

**When:** Validate API matches OpenAPI spec, catch breaking changes.

**Why schemathesis:** Auto-generates tests from your OpenAPI/Swagger spec.

**Setup:**
```bash
pip install schemathesis
```

**Example - Auto-testing from OpenAPI:**
```bash
# FastAPI auto-generates OpenAPI at /openapi.json

# Run against live server
schemathesis run http://localhost:8000/openapi.json

# Or against specific endpoints
schemathesis run http://localhost:8000/openapi.json \
    --endpoint="/api/v1/images" \
    --method=GET

# With more thorough testing
schemathesis run http://localhost:8000/openapi.json \
    --hypothesis-max-examples=100
```

**Programmatic usage:**
```python
# tests/contract/test_api_contract.py
import schemathesis
from app.main import app

schema = schemathesis.from_asgi("/openapi.json", app)

@schema.parametrize()
def test_api_contracts(case):
    """Auto-generated tests for all endpoints"""
    response = case.call_asgi()
    case.validate_response(response)
```

---

### Testing Dependencies Summary

```txt
# tests/requirements.txt

# Core
pytest==8.3.0
pytest-asyncio==0.24.0
pytest-cov==6.0.0

# API Testing
httpx==0.28.0

# Integration Testing
testcontainers[postgres,redis]==4.8.0

# Load Testing
locust==2.32.0

# E2E / UI Automation
playwright==1.49.0
pytest-playwright==0.6.0

# Contract Testing
schemathesis==3.36.0

# Utilities
Pillow==11.0.0  # For generating test images
```

---

### Test Organization

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures (sample images, etc.)
├── requirements.txt            # Test dependencies
│
├── unit/                       # Fast, isolated tests
│   ├── __init__.py
│   ├── test_image_service.py
│   ├── test_storage_service.py
│   └── test_cache_service.py
│
├── api/                        # HTTP endpoint tests
│   ├── __init__.py
│   ├── test_upload_api.py
│   ├── test_download_api.py
│   └── test_metadata_api.py
│
├── integration/                # Tests with real services
│   ├── __init__.py
│   ├── test_db_integration.py
│   ├── test_cache_integration.py
│   └── test_full_flow.py
│
├── load/                       # Performance tests
│   └── locustfile.py
│
├── e2e/                        # Browser automation
│   ├── __init__.py
│   └── test_upload_flow.py
│
├── contract/                   # API contract tests
│   └── test_api_contract.py
│
└── fixtures/                   # Test data
    ├── sample.jpg
    ├── sample.png
    └── document.txt
```

---

### When to Run Each Test Type

| Test Type | When to Run | CI Stage |
|-----------|-------------|----------|
| Unit | Every code change | Pre-commit, PR |
| API | Every code change | PR |
| Integration | Before merge | PR (with Docker) |
| Contract | API changes | PR |
| Load | Before release | Nightly / Release |
| E2E | Before release | Nightly / Release |

**Example CI workflow:**
```yaml
# .github/workflows/test.yml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r tests/requirements.txt
      - run: pytest tests/unit tests/api -v --cov

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/integration -v

  e2e-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - run: playwright install
      - run: pytest tests/e2e -v
```

---

## Summary: Learning Path

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DISTRIBUTED SYSTEMS LEARNING PATH                    │
└─────────────────────────────────────────────────────────────────────────┘

Phase 1                Phase 2                Phase 3              Phase 4
────────               ────────               ────────             ────────
Foundations            Performance            Scalability          Resilience

• Request lifecycle    • Caching (Redis)      • Load balancing     • Monitoring
• CRUD operations      • Message queues       • Read/write split   • Circuit breakers
• Storage abstraction  • Database indexes     • Sharding           • Rate limiting
• Single DB            • Reverse proxy        • Replication        • Graceful degradation
• Error handling       • Async processing     • Failover           • Alerting

      │                      │                      │                    │
      ▼                      ▼                      ▼                    ▼
┌──────────┐          ┌──────────┐          ┌──────────┐          ┌──────────┐
│ Working  │          │  Fast    │          │ Scalable │          │Production│
│   MVP    │    →     │   MVP    │    →     │   MVP    │    →     │  Ready   │
└──────────┘          └──────────┘          └──────────┘          └──────────┘
```

---

## Quick Reference: Technologies by Phase

| Phase | Component | Technology Options |
|-------|-----------|-------------------|
| 1 | Web Framework | FastAPI |
| 1 | Database | PostgreSQL |
| 1 | Object Storage | Local FS → MinIO → S3 |
| 2 | Cache | Redis |
| 2 | Queue | Celery + Redis / RQ / RabbitMQ |
| 2 | Proxy | Nginx |
| 3 | Load Balancer | Nginx / HAProxy / Traefik |
| 3 | DB Replication | PostgreSQL Streaming |
| 4 | Metrics | Prometheus |
| 4 | Visualization | Grafana |
| 4 | Tracing | Jaeger / Zipkin |

---

## Next Steps

1. **Start Phase 1**: Set up FastAPI project with basic upload/download
2. **Local Development**: Use Docker Compose for all dependencies
3. **Learn Incrementally**: Complete each phase before moving to the next
4. **Measure Everything**: Add metrics from Phase 1, expand over time

---

## Learning Resources

### Learning Strategy Recommendation

**Primary approach: Learn by Building**

For most technologies in this stack, hands-on implementation beats courses. The concepts matter more than memorizing APIs.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LEARNING APPROACH BY TECHNOLOGY                      │
├──────────────┬─────────────┬────────────────────────────────────────────┤
│ Technology   │ Complexity  │ Recommended Approach                       │
├──────────────┼─────────────┼────────────────────────────────────────────┤
│ FastAPI      │ Low         │ Official tutorial (1-2 hours) + build      │
│ PostgreSQL   │ Low-Medium  │ You likely know this; just build           │
│ Redis        │ Low         │ 30 min CLI exploration + docs              │
│ Celery       │ Medium      │ One tutorial + build simple task           │
│ RQ           │ Low         │ Read README + build (simpler than Celery)  │
│ Nginx        │ Low         │ Copy config examples + modify              │
│ DB Replicas  │ Medium-High │ Dedicated tutorial or use managed service  │
│ Prometheus   │ Medium      │ Official getting started + Grafana basics  │
└──────────────┴─────────────┴────────────────────────────────────────────┘
```

---

### Phase 1: Foundation Resources

#### FastAPI (Web Framework)
| Resource | Type | Time | Notes |
|----------|------|------|-------|
| [FastAPI Official Tutorial](https://fastapi.tiangolo.com/tutorial/) | Docs | 2-3 hrs | **Start here.** Best-in-class docs |
| [FastAPI Full Stack Template](https://github.com/tiangolo/full-stack-fastapi-template) | Code | Reference | Real-world project structure |
| [TestDriven.io FastAPI Guide](https://testdriven.io/blog/fastapi-crud/) | Tutorial | 1 hr | CRUD patterns with async |

**Skip courses for FastAPI** - the official docs are exceptional.

#### PostgreSQL (Database)
| Resource | Type | Time | Notes |
|----------|------|------|-------|
| [PostgreSQL Tutorial](https://www.postgresqltutorial.com/) | Tutorial | As needed | Reference for specific queries |
| [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/) | Docs | 2 hrs | Focus on async patterns |
| [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) | Docs | 30 min | Database migrations |

#### Docker (Local Development)
| Resource | Type | Time | Notes |
|----------|------|------|-------|
| [Docker Getting Started](https://docs.docker.com/get-started/) | Docs | 1-2 hrs | If new to Docker |
| [Docker Compose Overview](https://docs.docker.com/compose/) | Docs | 30 min | Multi-container setup |

---

### Phase 2: Performance Resources

#### Redis (Caching)
| Resource | Type | Time | Notes |
|----------|------|------|-------|
| [Try Redis (Interactive)](https://try.redis.io/) | Interactive | 30 min | **Start here.** Hands-on in browser |
| [Redis Crash Course](https://www.youtube.com/watch?v=jgpVdJB2sKQ) | Video | 40 min | Traversy Media - practical intro |
| [Redis Official Docs](https://redis.io/docs/get-started/) | Docs | 1 hr | Getting started guide |
| [Redis Python Guide](https://redis.io/docs/clients/python/) | Docs | 30 min | redis-py library usage |

**Key commands to learn first:** `GET`, `SET`, `SETEX`, `DEL`, `EXPIRE`, `KEYS`, `TTL`

**Hands-on exercise:**
```bash
# Install and explore
brew install redis  # or docker run -p 6379:6379 redis
redis-cli

# Try these commands
SET mykey "hello"
GET mykey
SETEX tempkey 60 "expires in 60 seconds"
TTL tempkey
```

#### Message Queues (Celery vs RQ)

**Option A: RQ (Recommended for learning)**
| Resource | Type | Time | Notes |
|----------|------|------|-------|
| [RQ Documentation](https://python-rq.org/) | Docs | 30 min | **Start here.** Simple and clear |
| [RQ + FastAPI Example](https://testdriven.io/blog/fastapi-and-celery/) | Tutorial | 1 hr | Practical integration |

```python
# RQ is this simple:
from redis import Redis
from rq import Queue

q = Queue(connection=Redis())
job = q.enqueue(my_function, arg1, arg2)
```

**Option B: Celery (More features, more complexity)**
| Resource | Type | Time | Notes |
|----------|------|------|-------|
| [Celery First Steps](https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html) | Docs | 1 hr | Official getting started |
| [Real Python Celery Guide](https://realpython.com/asynchronous-tasks-with-django-and-celery/) | Tutorial | 2 hrs | Comprehensive (Django but applies) |
| [Celery + FastAPI](https://testdriven.io/blog/fastapi-and-celery/) | Tutorial | 1.5 hrs | **Best for this project** |

**When to choose which:**
- **RQ**: Learning, simple tasks, < 10k tasks/day
- **Celery**: Complex workflows, scheduling, high volume

#### Nginx (Reverse Proxy)
| Resource | Type | Time | Notes |
|----------|------|------|-------|
| [Nginx Beginner's Guide](https://nginx.org/en/docs/beginners_guide.html) | Docs | 30 min | Official basics |
| [Nginx Config Generator](https://www.digitalocean.com/community/tools/nginx) | Tool | - | Generate configs visually |
| [Nginx Full Example Config](https://github.com/h5bp/server-configs-nginx) | Code | Reference | Production-ready templates |

**Learn by copying:** Nginx is configuration-driven. Copy working configs, modify, test.

---

### Phase 3: Scalability Resources

#### Load Balancing
| Resource | Type | Time | Notes |
|----------|------|------|-------|
| [Nginx Load Balancing](https://nginx.org/en/docs/http/load_balancing.html) | Docs | 20 min | Official guide |
| [HAProxy vs Nginx](https://www.digitalocean.com/community/tutorials/an-introduction-to-haproxy-and-load-balancing-concepts) | Article | 30 min | Understand the concepts |
| [Traefik Quick Start](https://doc.traefik.io/traefik/getting-started/quick-start/) | Docs | 30 min | Modern alternative, auto-discovery |

#### Database Replication
| Resource | Type | Time | Notes |
|----------|------|------|-------|
| [PostgreSQL Replication Explained](https://www.youtube.com/watch?v=yp-MfSLBJFo) | Video | 45 min | Clear conceptual overview |
| [PostgreSQL Streaming Replication](https://www.postgresql.org/docs/current/warm-standby.html) | Docs | 1 hr | Official documentation |
| [Setting Up PostgreSQL Replication](https://www.digitalocean.com/community/tutorials/how-to-set-up-physical-streaming-replication-with-postgresql-12-on-ubuntu-20-04) | Tutorial | 1 hr | Step-by-step guide |

**Alternative:** Use managed PostgreSQL (AWS RDS, Cloud SQL) - replication is built-in.

#### Sharding & Partitioning
| Resource | Type | Time | Notes |
|----------|------|------|-------|
| [Consistent Hashing Explained](https://www.toptal.com/big-data/consistent-hashing) | Article | 20 min | Core concept for sharding |
| [Database Sharding (System Design)](https://www.youtube.com/watch?v=5faMjKuB9bc) | Video | 15 min | Visual explanation |

---

### Phase 4: Production Resources

#### Prometheus & Grafana (Monitoring)
| Resource | Type | Time | Notes |
|----------|------|------|-------|
| [Prometheus Getting Started](https://prometheus.io/docs/prometheus/latest/getting_started/) | Docs | 1 hr | Official guide |
| [Grafana Fundamentals](https://grafana.com/tutorials/grafana-fundamentals/) | Tutorial | 1 hr | Building dashboards |
| [FastAPI + Prometheus](https://github.com/trallnag/prometheus-fastapi-instrumentator) | Library | 30 min | Easy integration |

#### Resilience Patterns
| Resource | Type | Time | Notes |
|----------|------|------|-------|
| [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html) | Article | 15 min | Martin Fowler explanation |
| [Pybreaker Library](https://github.com/danielfm/pybreaker) | Library | 30 min | Python implementation |

---

### Distributed Systems Concepts (Theory)

**For deeper understanding of WHY, not just HOW:**

| Resource | Type | Time | Notes |
|----------|------|------|-------|
| [AOSA Distributed Systems](https://aosabook.org/en/v2/distsys.html) | Book Chapter | 1 hr | **Source for this MVP** |
| [Designing Data-Intensive Applications](https://dataintensive.net/) | Book | 20+ hrs | **Gold standard** - read over time |
| [System Design Primer](https://github.com/donnemartin/system-design-primer) | GitHub | Reference | Visual, comprehensive |
| [ByteByteGo YouTube](https://www.youtube.com/@ByteByteGo) | Video | Varies | Excellent system design animations |
| [High Scalability Blog](http://highscalability.com/) | Blog | Varies | Real-world architecture case studies |

---

### Simpler Alternatives (Reduce Cognitive Load)

If a technology feels too complex, use these stepping stones:

| Original | Simpler Alternative | When to Graduate |
|----------|---------------------|------------------|
| **Celery** | `FastAPI BackgroundTasks` | Need persistence, retries, scheduling |
| **Celery** | **RQ** | Need Celery's advanced features |
| **Redis** | In-memory Python dict | Need distributed cache or persistence |
| **Nginx** | **Traefik** | Need more control or custom configs |
| **PostgreSQL Replicas** | Single DB + read caching | Actually need read scaling |
| **Prometheus** | Print statements + logs | Need historical metrics, alerting |

```python
# Example: FastAPI BackgroundTasks (zero setup)
from fastapi import BackgroundTasks

@app.post("/upload")
async def upload(file: UploadFile, background_tasks: BackgroundTasks):
    image = await save_image(file)

    # Run after response is sent (no Redis/Celery needed)
    background_tasks.add_task(generate_thumbnails, image.id)

    return {"id": image.id}
```

---

### Recommended Learning Path

```
Week 1-2: Phase 1 (Foundation)
├── Day 1-2: FastAPI tutorial
├── Day 3-4: Build upload/download endpoints
├── Day 5-7: Add PostgreSQL, Docker Compose
└── Deliverable: Working monolith

Week 3-4: Phase 2 (Performance)
├── Day 1: Redis exploration (30 min CLI, then integrate)
├── Day 2-3: Add caching to GET endpoints
├── Day 4-5: Background tasks (start with FastAPI BackgroundTasks)
├── Day 6-7: Graduate to RQ or Celery if needed
└── Deliverable: Cached, async-processing MVP

Week 5-6: Phase 3 (Scaling)
├── Focus on concepts: load balancing, read replicas
├── Implement with Nginx + Docker Compose
└── Deliverable: Multi-instance setup

Week 7+: Phase 4 (Production)
├── Add Prometheus metrics
├── Build Grafana dashboard
└── Deliverable: Observable system
```

---

### Quick Reference Links

**Official Documentation:**
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Redis](https://redis.io/docs/)
- [Celery](https://docs.celeryq.dev/)
- [RQ](https://python-rq.org/)
- [Nginx](https://nginx.org/en/docs/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)

**Python Libraries:**
- [redis-py](https://redis-py.readthedocs.io/)
- [asyncpg](https://magicstack.github.io/asyncpg/)
- [aiofiles](https://github.com/Tinche/aiofiles)
- [Pillow](https://pillow.readthedocs.io/)
- [prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)

---

**Document Version:** 1.3
**Last Updated:** 2025-12-19
**Changes:** Updated for Phase 1 Lean approach (ADR-0008) - local storage only, 7 DB columns, 9 dependencies
