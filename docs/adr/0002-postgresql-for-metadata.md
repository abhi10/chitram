# ADR-0002: Use PostgreSQL for Image Metadata Storage

## Status

Accepted

## Date

2025-12-13

## Context

We need a database to store image metadata (id, filename, size, dimensions, timestamps, etc.). The database should:
- Handle structured metadata reliably
- Support ACID transactions
- Be suitable for learning distributed systems concepts (replication in Phase 3)
- Work well with Python/FastAPI ecosystem

## Options Considered

### Option 1: PostgreSQL
- **Pros:**
  - Robust, mature, ACID-compliant
  - Excellent for structured data
  - Native support for UUID, JSONB, timestamps
  - Built-in replication (useful for Phase 3)
  - Great tooling and community
  - Works excellently with SQLAlchemy
- **Cons:**
  - Requires separate server process
  - More setup than SQLite
  - May be overkill for Phase 1 scale

### Option 2: SQLite
- **Pros:**
  - Zero configuration
  - File-based, easy to backup
  - Perfect for small scale
  - No separate server needed
- **Cons:**
  - Limited concurrent write support
  - No built-in replication
  - Not suitable for Phase 3 scaling goals
  - Would require migration later

### Option 3: MongoDB
- **Pros:**
  - Flexible schema
  - Good for document-style data
  - Built-in sharding
- **Cons:**
  - No ACID transactions (older versions)
  - Different query paradigm
  - Less suitable for relational metadata
  - Overkill for our structured data needs

## Decision

Use **PostgreSQL** as the metadata database.

## Rationale

1. **Future-proofing** - PostgreSQL's replication features align with Phase 3 learning goals
2. **ACID compliance** - Important for reliable metadata operations
3. **UUID support** - Native UUID type for image IDs
4. **Industry standard** - Learning PostgreSQL is valuable
5. **SQLAlchemy integration** - Excellent async support with asyncpg driver
6. **Docker-friendly** - Easy to run in Docker Compose for local development

## Consequences

### Positive
- Reliable, consistent data storage
- Learn industry-standard database
- Smooth path to Phase 3 replication
- Rich querying capabilities

### Negative
- Requires Docker or local installation
- Slightly more complex setup than SQLite
- Connection pooling needed for production

### Neutral
- Will use SQLAlchemy 2.0 as ORM
- Will use Alembic for migrations
- Will use asyncpg for async operations

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Async Support](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [image-hosting-mvp-distributed-systems.md](../../image-hosting-mvp-distributed-systems.md) - Phase 3 replication
