"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db, close_db
from app.api.images import router as images_router
from app.api.health import router as health_router
from app.schemas.error import ErrorResponse, ErrorDetail, ErrorCodes
from app.services.storage_service import StorageService, LocalStorageBackend

# SQLAlchemy exceptions for database error handling
from sqlalchemy.exc import OperationalError, TimeoutError as SQLAlchemyTimeoutError

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    # Startup
    print("🚀 Starting Image Hosting API...")

    # Initialize database
    await init_db()
    print("✅ Database initialized")

    # Initialize storage backend (local filesystem only in Phase 1)
    storage_backend = LocalStorageBackend(base_path=settings.local_storage_path)
    app.state.storage = StorageService(backend=storage_backend)
    print("✅ Storage initialized (local filesystem)")

    print("✅ Image Hosting API ready!")

    yield

    # Shutdown
    print("👋 Shutting down...")
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


# Include routers
app.include_router(health_router)
app.include_router(images_router, prefix="/api/v1")
