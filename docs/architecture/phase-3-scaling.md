# Phase 3: Horizontal Scaling

**Status:** ⏸️ Not Started
**Prerequisites:** Phase 2 complete
**Branch:** `feature/phase-3` (to be created)

---

## Learning Objectives

- Understand read/write service separation
- Implement load balancing strategies
- Learn data partitioning (sharding)
- Set up database replication
- Design for redundancy and failover

---

## Architecture

```
                              ┌──────────────┐
                              │     CDN      │ ← Edge caching
                              │ (CloudFlare) │
                              └──────┬───────┘
                                     │
                              ┌──────▼───────┐
                              │    Nginx     │
                              │Load Balancer │ ← Round-robin, health checks
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
     └────────┬────────┘                         └────────┬────────┘
              │                                           │
              │ Read Replicas                             │ Primary
              ▼                                           ▼
     ┌─────────────────┐                         ┌─────────────────┐
     │   PostgreSQL    │◄─── Replication ───────►│   PostgreSQL    │
     │    Replicas     │                         │     Primary     │
     └─────────────────┘                         └─────────────────┘

                    ┌─────────────────────────────────────┐
                    │         STORAGE SHARDS              │
                    │  ┌─────────┐ ┌─────────┐ ┌───────┐ │
                    │  │ Shard 1 │ │ Shard 2 │ │Shard N│ │
                    │  │ (a-f)   │ │ (g-m)   │ │(n-z)  │ │
                    │  └─────────┘ └─────────┘ └───────┘ │
                    └─────────────────────────────────────┘
```

---

## Key Patterns

### 1. Read/Write Service Separation (CQRS-lite)

```python
# Read service - optimized for throughput
class ImageReadService:
    def __init__(self, read_replica_pool, cache):
        self.db = read_replica_pool  # Connect to replicas
        self.cache = cache

# Write service - optimized for consistency
class ImageWriteService:
    def __init__(self, primary_db, cache, event_bus):
        self.db = primary_db  # Only primary
```

**Why:** Reads and writes have different characteristics. Reads can tolerate staleness, writes need consistency.

### 2. Load Balancing Strategies

```nginx
# Round Robin (default)
upstream read_services {
    server read-1:8000;
    server read-2:8000;
    server read-3:8000;
}

# Least Connections
upstream read_services_leastconn {
    least_conn;
    server read-1:8000;
    server read-2:8000;
}

# With health checks
upstream read_services {
    server read-1:8000 max_fails=3 fail_timeout=30s;
    server read-2:8000 max_fails=3 fail_timeout=30s;
    server read-3:8000 backup;
}
```

### 3. Storage Sharding (Consistent Hashing)

```python
class ShardRouter:
    def get_shard(self, image_id: str) -> StorageBackend:
        hash_value = int(hashlib.md5(image_id.encode()).hexdigest(), 16)
        shard_index = hash_value % self.num_shards
        return self.shards[shard_index]
```

| Strategy | Use Case | Pros | Cons |
|----------|----------|------|------|
| Hash-based | Even distribution | Balanced load | Difficult range queries |
| Range-based | Time-series | Easy range scans | Hot spots possible |
| Geographic | Regional data | Low latency | Uneven distribution |

### 4. Database Replication

```python
class DatabasePool:
    def get_write_connection(self):
        return self.primary  # Always primary for writes

    def get_read_connection(self):
        # Round-robin across replicas
        replica = self.replicas[self._replica_index]
        self._replica_index = (self._replica_index + 1) % len(self.replicas)
        return replica
```

---

## Scaling Targets

| Component | Scaling Strategy | Implementation |
|-----------|-----------------|----------------|
| Read Service | Horizontal (N instances) | Docker Swarm / K8s |
| Write Service | Vertical + Queue | Single instance + workers |
| Database | Read replicas | PostgreSQL streaming |
| Storage | Sharding | Consistent hash ring |
| Cache | Distributed | Redis Cluster |

---

## Deliverables

- [ ] Separate read/write services
- [ ] Load balancer with health checks
- [ ] Database replication (1 primary + 2 replicas)
- [ ] Storage sharding implementation
- [ ] Redundant storage with failover
- [ ] CDN integration

---

**Document Version:** 1.0
**Last Updated:** 2025-12-24
