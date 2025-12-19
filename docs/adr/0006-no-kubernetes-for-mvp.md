# ADR-0006: No Kubernetes for MVP Phases

## Status

Accepted

## Date

2025-12-13

## Context

We need to decide on the container orchestration and deployment strategy for the Image Hosting App. Kubernetes is the industry standard for container orchestration at scale, but introduces significant complexity.

Key considerations:
- Project is primarily for learning distributed systems concepts
- Phase 1 targets 10-50 concurrent users
- Single-region deployment
- Small number of services (API, database, cache, workers)
- Solo developer / small team

## Options Considered

### Option 1: Kubernetes (EKS/GKE/self-hosted)
- **Pros:**
  - Industry standard for container orchestration
  - Built-in load balancing, auto-scaling, self-healing
  - Service discovery and networking
  - Declarative infrastructure
  - Valuable skill to learn
- **Cons:**
  - Significant operational complexity
  - Steep learning curve (separate from distributed systems)
  - Overkill for 1-5 services at low scale
  - Expensive (managed K8s or operational overhead)
  - Distracts from core learning goals
  - Debugging is more complex

### Option 2: Docker Compose → Docker Swarm
- **Pros:**
  - Simple to start (Compose for dev)
  - Smooth upgrade path to Swarm for multi-node
  - Same docker-compose.yml works in both
  - Low operational overhead
  - Teaches same orchestration concepts
  - Fast iteration during development
- **Cons:**
  - Less feature-rich than K8s
  - Smaller community than K8s
  - May need to migrate later at large scale

### Option 3: Managed Container Services (ECS Fargate, Cloud Run)
- **Pros:**
  - No cluster management
  - Pay-per-use pricing
  - Auto-scaling built-in
  - Simpler than K8s
- **Cons:**
  - Vendor lock-in
  - Less learning about orchestration internals
  - Cost can grow with scale

## Decision

Use **Docker Compose for Phases 1-3**, with optional upgrade to **Docker Swarm or managed cloud services** for Phase 4.

**Explicitly NOT using Kubernetes** for this project.

## Rationale

1. **Complexity mismatch** - K8s operational complexity exceeds our app complexity
   ```
   App: 3-5 services, 10-50 users
   K8s: Control plane, CNI, ingress controllers, RBAC, operators, etc.
   ```

2. **Learning focus** - Goal is distributed systems concepts, not K8s operations
   - Caching strategies
   - Message queues
   - Database replication
   - Load balancing concepts

   These concepts transfer to K8s later, but K8s isn't required to learn them.

3. **Iteration speed** - Docker Compose allows faster development cycles
   ```bash
   # Compose: instant feedback
   docker-compose up

   # K8s: build → push → deploy → wait
   docker build && docker push && kubectl apply && kubectl rollout status
   ```

4. **Right-sizing** - Match tooling to actual scale
   | Scale | Right Tool |
   |-------|------------|
   | 10-50 users | Docker Compose |
   | 100-500 users | Docker Swarm / ECS |
   | 1000+ users | Consider K8s |

5. **Separate learning track** - K8s is worth learning, but as a dedicated project, not layered on top of distributed systems learning.

## Deployment Strategy by Phase

| Phase | Tool | Why |
|-------|------|-----|
| Phase 1 | Docker Compose | Simple, fast, local dev |
| Phase 2 | Docker Compose | Same, add Redis/workers |
| Phase 3 | Docker Compose + Nginx | Multi-replica with `--scale` |
| Phase 4 | Evaluate: Swarm / ECS / Cloud Run | Based on actual needs |

## Concepts That Transfer to K8s

Learning with simpler tools first:

| Concept | Learn With | K8s Equivalent |
|---------|------------|----------------|
| Container networking | Docker networks | K8s Services, CNI |
| Load balancing | Nginx | K8s Ingress, Services |
| Health checks | Docker HEALTHCHECK | K8s liveness/readiness probes |
| Scaling replicas | `docker-compose --scale` | K8s Deployments, ReplicaSets |
| Config management | Environment variables | K8s ConfigMaps, Secrets |
| Service discovery | Docker DNS | K8s DNS, Services |

## Consequences

### Positive
- Faster development iteration
- Lower operational complexity
- Focus on distributed systems concepts
- Easier debugging
- Lower cost (no managed K8s fees)

### Negative
- May need migration at very large scale
- Not learning K8s directly
- Docker Swarm has smaller community

### Neutral
- K8s remains a valid future option
- Concepts learned will transfer
- Can add K8s as separate learning project later

## When to Reconsider

Revisit this decision if:
- Scale exceeds 1000+ concurrent users
- Need multi-region deployment
- Team grows significantly
- K8s becomes an explicit learning goal

## References

- [image-hosting-mvp-distributed-systems.md](../../image-hosting-mvp-distributed-systems.md) - Phase definitions
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Swarm Documentation](https://docs.docker.com/engine/swarm/)
- [You don't need Kubernetes](https://benhouston3d.com/blog/why-you-dont-need-kubernetes) - Industry perspective
