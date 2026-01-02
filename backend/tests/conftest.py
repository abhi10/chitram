"""Shared test fixtures."""

import io
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image as PILImage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.services.cache_service import set_cache
from app.services.storage_service import LocalStorageBackend, StorageService

# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


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
    # Create a large image (approximately 6MB)
    img = PILImage.new("RGB", (2000, 2000), color="green")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def invalid_file_bytes() -> bytes:
    """Create invalid (non-image) file content."""
    return b"This is not an image file"


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def test_storage(tmp_path) -> StorageService:
    """Create test storage service with temporary directory."""
    backend = LocalStorageBackend(base_path=str(tmp_path / "uploads"))
    return StorageService(backend=backend)


@pytest.fixture
async def client(
    test_db: AsyncSession, test_storage: StorageService
) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with overridden dependencies."""

    # Override database dependency
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    # Override storage in app state
    app.state.storage = test_storage

    # Disable cache for API tests (cache tested separately)
    app.state.cache = None
    set_cache(None)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clear overrides
    app.dependency_overrides.clear()
    app.state.cache = None
    set_cache(None)
