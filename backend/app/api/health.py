"""Health check endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings

router = APIRouter(tags=["health"])
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    environment: str
    database: str
    storage: str


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
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

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version="0.1.0",
        environment=settings.app_env,
        database=db_status,
        storage=settings.storage_backend,
    )
