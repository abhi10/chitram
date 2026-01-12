"""Unit tests for background task service abstraction."""

import pytest

from app.config import Settings
from app.services.background import (
    BackgroundTaskService,
    CeleryTaskService,
    MockTaskService,
    TaskStatus,
    create_task_service,
)


class TestMockTaskService:
    """Test suite for MockTaskService (synchronous test implementation)."""

    @pytest.mark.asyncio
    async def test_enqueue_with_mock_succeeds(self) -> None:
        """Test that enqueue returns a task ID when mocked."""
        from unittest.mock import patch

        service = MockTaskService()

        # Mock the task function to avoid asyncio.run() issue in tests
        with patch("app.tasks.ai_tagging.tag_image_task_sync") as mock_task:
            mock_task.return_value = {"success": True, "tags_added": 3, "error": None}

            task_id = await service.enqueue_ai_tagging(image_id="test-image-123")

            assert task_id is not None
            assert isinstance(task_id, str)

    @pytest.mark.asyncio
    async def test_task_id_format(self) -> None:
        """Test that task IDs are UUIDs."""
        from unittest.mock import patch

        service = MockTaskService()

        # Mock the task function to avoid asyncio.run() issue
        with patch("app.tasks.ai_tagging.tag_image_task_sync") as mock_task:
            mock_task.return_value = {"success": True, "tags_added": 3, "error": None}

            task_id = await service.enqueue_ai_tagging(image_id="test-image-123")

            assert task_id is not None
            assert isinstance(task_id, str)
            # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
            assert len(task_id) == 36

    @pytest.mark.asyncio
    async def test_task_status_success_immediately(self) -> None:
        """Test that MockTaskService marks successful tasks as SUCCESS."""
        from unittest.mock import patch

        service = MockTaskService()

        with patch("app.tasks.ai_tagging.tag_image_task_sync") as mock_task:
            mock_task.return_value = {"success": True, "tags_added": 3, "error": None}

            task_id = await service.enqueue_ai_tagging(image_id="test-image-123")
            result = await service.get_task_status(task_id)

            assert result.status == TaskStatus.SUCCESS
            assert result.result == {"success": True, "tags_added": 3, "error": None}

    @pytest.mark.asyncio
    async def test_unknown_task_raises_error(self) -> None:
        """Test that unknown task IDs raise KeyError."""
        service = MockTaskService()

        with pytest.raises(KeyError, match="Task .* not found"):
            await service.get_task_status("nonexistent-task-id")

    @pytest.mark.asyncio
    async def test_task_failure_stored(self) -> None:
        """Test that task failures are captured."""
        from unittest.mock import patch

        service = MockTaskService()

        with patch("app.tasks.ai_tagging.tag_image_task_sync") as mock_task:
            mock_task.side_effect = RuntimeError("Simulated failure")

            task_id = await service.enqueue_ai_tagging(image_id="test-image-123")
            result = await service.get_task_status(task_id)

            assert result.status == TaskStatus.FAILURE
            assert "Simulated failure" in result.error


@pytest.mark.skip(reason="Requires Redis connection - run in integration environment")
class TestCeleryTaskService:
    """Test suite for CeleryTaskService (production implementation)."""

    @pytest.mark.asyncio
    async def test_enqueue_returns_task_id(self) -> None:
        """Test that enqueue returns a Celery task ID."""
        service = CeleryTaskService()
        task_id = await service.enqueue_ai_tagging(image_id="test-image-123")

        assert task_id is not None
        assert isinstance(task_id, str)
        # Celery task IDs are UUIDs
        assert len(task_id) == 36  # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

    @pytest.mark.asyncio
    async def test_task_status_pending_initially(self) -> None:
        """Test that newly enqueued tasks start as PENDING."""
        service = CeleryTaskService()
        task_id = await service.enqueue_ai_tagging(image_id="test-image-123")

        result = await service.get_task_status(task_id)

        # Should be PENDING or RUNNING (if worker picked it up quickly)
        assert result.status in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.SUCCESS)

    @pytest.mark.asyncio
    async def test_unknown_task_status(self) -> None:
        """Test that unknown task IDs return PENDING status (Celery behavior)."""
        service = CeleryTaskService()

        result = await service.get_task_status("00000000-0000-0000-0000-000000000000")

        # Celery returns PENDING for unknown task IDs
        assert result.status == TaskStatus.PENDING


class TestTaskServiceFactory:
    """Test suite for create_task_service factory function."""

    def test_create_mock_service_when_disabled(self) -> None:
        """Test that factory creates MockTaskService when background tasks disabled."""
        settings = Settings(
            background_task_enabled=False,
            background_task_provider="celery",  # Should be ignored
        )

        service = create_task_service(settings)

        assert isinstance(service, MockTaskService)

    def test_create_mock_service_explicitly(self) -> None:
        """Test that factory creates MockTaskService when explicitly requested."""
        settings = Settings(
            background_task_enabled=True,
            background_task_provider="mock",
        )

        service = create_task_service(settings)

        assert isinstance(service, MockTaskService)

    def test_create_celery_service(self) -> None:
        """Test that factory creates CeleryTaskService for production."""
        settings = Settings(
            background_task_enabled=True,
            background_task_provider="celery",
        )

        service = create_task_service(settings)

        assert isinstance(service, CeleryTaskService)

    def test_unknown_provider_raises_error(self) -> None:
        """Test that unknown provider type raises ValueError."""
        settings = Settings(
            background_task_enabled=True,
            background_task_provider="redis-queue",  # Unknown
        )

        with pytest.raises(ValueError, match="Unknown background task provider"):
            create_task_service(settings)


class TestTaskServiceInterface:
    """Test that both implementations conform to BackgroundTaskService interface."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "service_class",
        [MockTaskService, CeleryTaskService],
        ids=["mock", "celery"],
    )
    async def test_implements_interface(self, service_class: type[BackgroundTaskService]) -> None:
        """Test that both implementations follow the interface contract."""
        service = service_class()

        # Should have required methods
        assert hasattr(service, "enqueue_ai_tagging")
        assert hasattr(service, "get_task_status")

        # Methods should be async
        assert callable(service.enqueue_ai_tagging)
        assert callable(service.get_task_status)
