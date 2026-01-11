"""Celery-based background task service."""

import logging

from celery.result import AsyncResult

from app.celery_app import celery_app
from app.services.background.base import BackgroundTaskService, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


class CeleryTaskService(BackgroundTaskService):
    """
    Production implementation using Celery for background tasks.

    Uses Redis as message broker and result backend.

    Benefits:
    - Asynchronous: Doesn't block API responses
    - Reliable: Tasks are persisted in Redis
    - Scalable: Can add more workers
    - Retry logic: Built into Celery tasks
    """

    async def enqueue_ai_tagging(self, image_id: str) -> str:
        """
        Enqueue AI tagging task using Celery.

        Args:
            image_id: UUID of the image to tag

        Returns:
            Celery task ID

        Raises:
            Exception: If task cannot be enqueued
        """
        try:
            # Import task lazily to avoid circular imports
            from app.tasks.ai_tagging import tag_image_task

            # Enqueue task (returns AsyncResult)
            result = tag_image_task.delay(image_id)

            logger.info(f"AI tagging task enqueued: task_id={result.id}, image_id={image_id}")

            return result.id

        except Exception as e:
            logger.error(f"Failed to enqueue AI tagging task: {e}", exc_info=True)
            raise

    async def get_task_status(self, task_id: str) -> TaskResult:
        """
        Get task status from Celery result backend.

        Args:
            task_id: Celery task ID

        Returns:
            TaskResult with current status and result/error

        Raises:
            Exception: If task ID is invalid
        """
        try:
            result = AsyncResult(task_id, app=celery_app)

            # Map Celery states to our TaskStatus enum
            if result.state == "PENDING":
                status = TaskStatus.PENDING
            elif result.state == "STARTED":
                status = TaskStatus.RUNNING
            elif result.state == "RETRY":
                status = TaskStatus.RETRY
            elif result.state == "SUCCESS":
                status = TaskStatus.SUCCESS
            elif result.state == "FAILURE":
                status = TaskStatus.FAILURE
            else:
                # Unknown state, treat as pending
                status = TaskStatus.PENDING

            # Get result or error
            task_result = None
            error = None

            if result.successful():
                task_result = result.result
            elif result.failed():
                error = str(result.info)

            return TaskResult(
                task_id=task_id,
                status=status,
                result=task_result,
                error=error,
            )

        except Exception as e:
            logger.error(f"Failed to get task status: {e}", exc_info=True)
            raise

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a Celery task.

        Args:
            task_id: Celery task ID

        Returns:
            True if cancelled, False if already complete

        Raises:
            Exception: If task ID is invalid
        """
        try:
            result = AsyncResult(task_id, app=celery_app)

            if result.state in ["SUCCESS", "FAILURE"]:
                # Task already complete
                logger.info(f"Task {task_id} already complete, cannot cancel")
                return False

            # Revoke task (terminate if running)
            result.revoke(terminate=True)

            logger.info(f"Task {task_id} cancelled")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel task: {e}", exc_info=True)
            raise
