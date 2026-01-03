"""Shared FastAPI dependencies for API endpoints."""

from fastapi import Request

from app.services.cache_service import CacheService
from app.services.concurrency import UploadSemaphore
from app.services.rate_limiter import RateLimiter


def get_cache(request: Request) -> CacheService | None:
    """Dependency to get cache service from app state."""
    return getattr(request.app.state, "cache", None)


def get_rate_limiter(request: Request) -> RateLimiter | None:
    """Dependency to get rate limiter from app state."""
    return getattr(request.app.state, "rate_limiter", None)


def get_upload_semaphore(request: Request) -> UploadSemaphore | None:
    """Dependency to get upload semaphore from app state."""
    return getattr(request.app.state, "upload_semaphore", None)
