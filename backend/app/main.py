"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# SQLAlchemy exceptions for database error handling
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.images import router as images_router
from app.api.tags import router as tags_router
from app.api.web import router as web_router
from app.config import get_settings
from app.database import async_session_maker, close_db, init_db
from app.schemas.error import ErrorCodes, ErrorDetail, ErrorResponse
from app.services.cache_service import CacheService, set_cache
from app.services.concurrency import UploadSemaphore, set_upload_semaphore
from app.services.rate_limiter import RateLimiter, set_rate_limiter
from app.services.storage_factory import create_storage_backend
from app.services.storage_service import StorageService
from app.services.thumbnail_service import ThumbnailService

settings = get_settings()

# Template and static file paths
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    # Startup
    print("🚀 Starting Image Hosting API...")

    # Initialize database
    await init_db()
    print("✅ Database initialized")

    # Initialize storage using shared factory (DRY principle)
    storage_backend = await create_storage_backend(settings)
    app.state.storage = StorageService(backend=storage_backend)
    backend_name = "MinIO" if settings.storage_backend == "minio" else "local filesystem"
    print(f"✅ Storage initialized ({backend_name})")

    # Initialize Redis cache (Phase 2)
    cache_service: CacheService | None = None
    if settings.cache_enabled:
        cache_service = CacheService(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            key_prefix=settings.cache_key_prefix,
            default_ttl=settings.cache_ttl_seconds,
        )
        connected = await cache_service.connect()
        if connected:
            print("✅ Redis cache connected")
        else:
            print("⚠️ Redis cache unavailable - running without cache")
            cache_service = None
    else:
        print("ℹ️ Cache disabled by configuration")

    # Store cache service in app state and global
    app.state.cache = cache_service
    set_cache(cache_service)

    # Initialize rate limiter (uses same Redis connection as cache)
    rate_limiter: RateLimiter | None = None
    if settings.rate_limit_enabled:
        # Rate limiter uses the cache service's Redis client if available
        redis_client = cache_service._client if cache_service else None
        rate_limiter = RateLimiter(
            redis_client=redis_client,
            key_prefix=settings.cache_key_prefix,
            limit=settings.rate_limit_per_minute,
            window_seconds=settings.rate_limit_window_seconds,
            enabled=settings.rate_limit_enabled,
        )
        if redis_client:
            print("✅ Rate limiter enabled (Redis-backed)")
        else:
            print("⚠️ Rate limiter enabled but no Redis - running in fail-open mode")
    else:
        print("ℹ️ Rate limiting disabled by configuration")

    # Store rate limiter in app state and global
    app.state.rate_limiter = rate_limiter
    set_rate_limiter(rate_limiter)

    # Initialize upload concurrency limiter (ADR-0010)
    upload_semaphore = UploadSemaphore(
        limit=settings.upload_concurrency_limit,
        timeout=settings.upload_concurrency_timeout,
    )
    app.state.upload_semaphore = upload_semaphore
    set_upload_semaphore(upload_semaphore)
    print(f"✅ Upload concurrency limit: {settings.upload_concurrency_limit}")

    # Initialize thumbnail service (Phase 2B)
    thumbnail_service: ThumbnailService | None = None
    try:
        thumbnail_service = ThumbnailService(
            storage=app.state.storage,
            session_factory=async_session_maker,
            cache=cache_service,
        )
        print("✅ Thumbnail service initialized")
    except Exception as e:
        print(f"⚠️ Thumbnail service initialization failed: {e}")
        print("   App will continue without thumbnail generation")
        thumbnail_service = None

    app.state.thumbnail_service = thumbnail_service

    # Initialize background task service (Phase 6)
    from app.services.background import create_task_service

    task_service = create_task_service(settings)
    app.state.task_service = task_service
    print("✅ Background task service initialized")

    # Store templates in app.state for web routes (single source of truth)
    app.state.templates = templates

    print("✅ Image Hosting API ready!")

    yield

    # Shutdown
    print("👋 Shutting down...")

    # Close cache connection
    if cache_service:
        await cache_service.close()
        print("✅ Redis connection closed")

    await close_db()
    print("✅ Database connections closed")


app = FastAPI(
    title="Image Hosting API",
    description="A simple image hosting service for learning distributed systems",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware (development)
if settings.is_development:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


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


# Global exception handler for structured errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with structured error response."""
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details={"exception": str(exc)} if settings.debug else {},
        )
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
    )


# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(images_router, prefix="/api/v1")
app.include_router(tags_router, prefix="/api/v1")
app.include_router(web_router)  # Web UI routes (no prefix, serves at /)
