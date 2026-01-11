"""Abstract base for background task services."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"  # Task queued but not started
    RUNNING = "running"  # Task currently executing
    SUCCESS = "success"  # Task completed successfully
    FAILURE = "failure"  # Task failed (after all retries)
    RETRY = "retry"  # Task failed, will retry


@dataclass
class TaskResult:
    """Result of a background task."""

    task_id: str
    status: TaskStatus
    result: dict | None = None
    error: str | None = None


class BackgroundTaskService(ABC):
    """
    Abstract base class for background task services.

    This abstraction allows swapping task queue implementations
    (Celery, RQ, Cloud Tasks, etc.) without changing application code.

    Design Pattern: Strategy Pattern
    - BackgroundTaskService = Strategy interface
    - CeleryTaskService = Concrete strategy #1
    - MockTaskService = Concrete strategy #2 (for tests)

    Benefits:
    - Decoupled: Tests don't need Celery
    - Testable: Can mock task execution
    - Evolutionary: Easy to add new implementations
    """

    @abstractmethod
    async def enqueue_ai_tagging(self, image_id: str) -> str:
        """
        Enqueue AI tagging task for the given image.

        Args:
            image_id: UUID of the image to tag

        Returns:
            Task ID for status tracking

        Raises:
            Exception: If task cannot be enqueued
        """
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> TaskResult:
        """
        Get the current status of a task.

        Args:
            task_id: ID returned from enqueue_*

        Returns:
            TaskResult with current status

        Raises:
            Exception: If task ID is invalid
        """
        pass

    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task.

        Args:
            task_id: ID of the task to cancel

        Returns:
            True if task was cancelled, False if already complete

        Raises:
            Exception: If task ID is invalid
        """
        pass
