"""Health check endpoints."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.services.cache_service import CacheService

router = APIRouter(tags=["health"])
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    environment: str
    database: str
    storage: str
    cache: str


def get_cache(request: Request) -> CacheService | None:
    """Dependency to get cache service from app state."""
    return getattr(request.app.state, "cache", None)


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    cache: CacheService | None = Depends(get_cache),
) -> HealthResponse:
    """
    Health check endpoint.

    Returns service status and configuration info.
    """
    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    # Check Redis connectivity
    if cache:
        cache_status = "connected" if await cache.is_connected() else "disconnected"
    else:
        cache_status = "disabled" if not settings.cache_enabled else "disconnected"

    # Overall status: healthy if DB connected, degraded if cache is down
    if db_status != "connected":
        overall_status = "unhealthy"
    elif cache_status not in ("connected", "disabled"):
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        environment=settings.app_env,
        database=db_status,
        storage=settings.storage_backend,
        cache=cache_status,
    )
