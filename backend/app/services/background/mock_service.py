"""Mock background task service for testing."""

import logging
import uuid
from collections import defaultdict

from app.services.background.base import BackgroundTaskService, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


class MockTaskService(BackgroundTaskService):
    """
    Mock implementation that runs tasks synchronously.

    Used for:
    - Fast unit tests (no Celery overhead)
    - Development without Celery setup
    - CI/CD environments

    Behavior:
    - Tasks execute immediately (synchronous)
    - No Redis required
    - No background workers needed

    Trade-offs:
    - Blocks API responses (but fast in tests)
    - No retry logic (assumes success)
    - No task persistence
    """

    def __init__(self) -> None:
        """Initialize with in-memory task storage."""
        # Store task results by ID
        self._tasks: dict[str, TaskResult] = {}

        # Track execution count for testing
        self._execution_count: defaultdict[str, int] = defaultdict(int)

    async def enqueue_ai_tagging(self, image_id: str) -> str:
        """
        Execute AI tagging synchronously (mock behavior).

        Args:
            image_id: UUID of the image to tag

        Returns:
            Mock task ID

        Note: In mock mode, task executes immediately.
        """
        task_id = str(uuid.uuid4())

        logger.info(f"Mock AI tagging task: task_id={task_id}, image_id={image_id}")

        # Track execution
        self._execution_count["ai_tagging"] += 1

        try:
            # Import task function
            from app.tasks.ai_tagging import tag_image_task_sync

            # Execute synchronously
            result = tag_image_task_sync(image_id)

            # Store result
            self._tasks[task_id] = TaskResult(
                task_id=task_id,
                status=TaskStatus.SUCCESS,
                result=result,
                error=None,
            )

            logger.info(f"Mock AI tagging complete: task_id={task_id}")

        except Exception as e:
            # Store error
            self._tasks[task_id] = TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILURE,
                result=None,
                error=str(e),
            )

            logger.error(f"Mock AI tagging failed: task_id={task_id}, error={e}")

        return task_id

    async def get_task_status(self, task_id: str) -> TaskResult:
        """
        Get task result from in-memory storage.

        Args:
            task_id: Mock task ID

        Returns:
            TaskResult with status and result/error

        Raises:
            KeyError: If task ID not found
        """
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id} not found")

        return self._tasks[task_id]

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task (no-op in mock - tasks already complete).

        Args:
            task_id: Mock task ID

        Returns:
            False (tasks complete immediately in mock)

        Raises:
            KeyError: If task ID not found
        """
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id} not found")

        # In mock mode, tasks complete immediately
        logger.info(f"Mock cancel (no-op): task_id={task_id}")
        return False

    def get_execution_count(self, task_type: str) -> int:
        """
        Get number of times a task type was executed.

        Useful for testing.

        Args:
            task_type: Task type (e.g., "ai_tagging")

        Returns:
            Number of executions
        """
        return self._execution_count[task_type]

    def reset(self) -> None:
        """Reset mock state (for testing)."""
        self._tasks.clear()
        self._execution_count.clear()
        logger.debug("Mock task service reset")
