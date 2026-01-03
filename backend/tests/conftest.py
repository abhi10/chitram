"""Shared test fixtures.

This module uses an explicit TestDependencies container that mirrors
the production app.state pattern. This ensures test fixtures have the
same dependency structure as production code.

Pattern: Production uses app.state as container, tests use TestDependencies.
Both are explicit, visible, and testable.
"""

import io
import os
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image as PILImage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.services.cache_service import CacheService, set_cache
from app.services.concurrency import UploadSemaphore, set_upload_semaphore
from app.services.rate_limiter import RateLimiter, set_rate_limiter
from app.services.storage_service import LocalStorageBackend, StorageService
from app.services.thumbnail_service import ThumbnailService


@dataclass
class TestDependencies:
    """
    Explicit container for test dependencies.

    Mirrors app.state in production - all dependencies are visible
    and can be easily overridden or inspected in tests.

    This pattern prevents hidden coupling issues where services
    create their own connections that tests can't control.
    """

    engine: object  # AsyncEngine
    session_maker: async_sessionmaker
    session: AsyncSession
    storage: StorageService
    thumbnail_service: ThumbnailService
    cache: CacheService | None = None
    rate_limiter: RateLimiter | None = None
    upload_semaphore: UploadSemaphore | None = None


# ============================================================================
# Image Data Fixtures
# ============================================================================


@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    """Create a valid JPEG test image."""
    img = PILImage.new("RGB", (100, 100), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def sample_png_bytes() -> bytes:
    """Create a valid PNG test image."""
    img = PILImage.new("RGBA", (100, 100), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def large_image_bytes() -> bytes:
    """Create an image larger than 5MB limit."""
    img = PILImage.new("RGB", (2000, 2000), color="green")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def invalid_file_bytes() -> bytes:
    """Create invalid (non-image) file content."""
    return b"This is not an image file"


# ============================================================================
# Core Infrastructure Fixtures
# ============================================================================


@pytest.fixture
def test_storage(tmp_path) -> StorageService:
    """Create test storage service with temporary directory."""
    backend = LocalStorageBackend(base_path=str(tmp_path / "uploads"))
    return StorageService(backend=backend)


@pytest.fixture
async def test_deps(test_storage: StorageService) -> AsyncGenerator[TestDependencies, None]:
    """
    Create all test dependencies in a single, explicit container.

    This fixture mirrors the production lifespan() function in main.py,
    ensuring tests use the same dependency structure as production.

    Key insight: By creating all dependencies here with shared references,
    we avoid the hidden coupling problem where ThumbnailService creates
    its own database sessions that tests can't control.
    """
    # Use file-based SQLite to allow multiple connections to share state
    # In-memory databases are isolated per connection
    engine = create_async_engine(
        "sqlite+aiosqlite:///test.db",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create session for request-scoped operations
    session = session_maker()

    # Initialize services with SHARED dependencies
    # This is the key - ThumbnailService uses the same session_maker
    # that we control, not a hidden global one
    thumbnail_service = ThumbnailService(
        storage=test_storage,
        session_factory=session_maker,
    )

    # Build the container with all dependencies
    deps = TestDependencies(
        engine=engine,
        session_maker=session_maker,
        session=session,
        storage=test_storage,
        thumbnail_service=thumbnail_service,
        cache=None,  # Disabled for most tests
        rate_limiter=None,  # Disabled for most tests
        upload_semaphore=None,  # Disabled for most tests
    )

    yield deps

    # Cleanup
    await session.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

    # Clean up test database file
    if os.path.exists("test.db"):
        os.remove("test.db")


# ============================================================================
# Backward Compatibility: Individual Fixtures
# ============================================================================


@pytest.fixture
async def test_db(test_deps: TestDependencies) -> AsyncSession:
    """
    Provide database session from the shared container.

    This maintains backward compatibility with existing tests
    that use test_db directly.
    """
    return test_deps.session


@pytest.fixture
async def client(test_deps: TestDependencies) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async test client with all dependencies from container.

    This fixture wires up the test container to app.state,
    mirroring how production lifespan() sets up dependencies.
    """

    # Override database dependency to use our shared session
    async def override_get_db():
        yield test_deps.session

    app.dependency_overrides[get_db] = override_get_db

    # Wire up app.state from our container (mirrors main.py lifespan)
    app.state.storage = test_deps.storage
    app.state.thumbnail_service = test_deps.thumbnail_service
    app.state.cache = test_deps.cache
    app.state.rate_limiter = test_deps.rate_limiter
    app.state.upload_semaphore = test_deps.upload_semaphore

    # Also set the module-level globals for dependencies that use them
    set_cache(test_deps.cache)
    set_rate_limiter(test_deps.rate_limiter)
    set_upload_semaphore(test_deps.upload_semaphore)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup: Reset all state
    app.dependency_overrides.clear()
    app.state.storage = None
    app.state.thumbnail_service = None
    app.state.cache = None
    app.state.rate_limiter = None
    app.state.upload_semaphore = None
    set_cache(None)
    set_rate_limiter(None)
    set_upload_semaphore(None)
