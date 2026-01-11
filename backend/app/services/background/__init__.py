"""Background task service for async job processing."""

from app.config import Settings
from app.services.background.base import BackgroundTaskService, TaskStatus
from app.services.background.celery_service import CeleryTaskService
from app.services.background.mock_service import MockTaskService

__all__ = [
    "BackgroundTaskService",
    "TaskStatus",
    "CeleryTaskService",
    "MockTaskService",
    "create_task_service",
]


def create_task_service(settings: Settings) -> BackgroundTaskService:
    """
    Factory function to create the appropriate task service implementation.

    Args:
        settings: Application settings

    Returns:
        BackgroundTaskService implementation based on configuration

    Examples:
        >>> settings = Settings(background_task_provider="celery")
        >>> service = create_task_service(settings)
        >>> isinstance(service, CeleryTaskService)
        True

        >>> settings = Settings(background_task_provider="mock")
        >>> service = create_task_service(settings)
        >>> isinstance(service, MockTaskService)
        True
    """
    if not settings.background_task_enabled:
        # If disabled, use mock service (runs synchronously)
        return MockTaskService()

    provider = settings.background_task_provider.lower()

    if provider == "celery":
        return CeleryTaskService()
    if provider == "mock":
        return MockTaskService()
    raise ValueError(
        f"Unknown background task provider: {provider}. Valid options: 'celery', 'mock'"
    )
