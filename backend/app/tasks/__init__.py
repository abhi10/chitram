"""Celery tasks for background job processing."""

from app.tasks.ai_tagging import tag_image_task, tag_image_task_sync

__all__ = [
    "tag_image_task",
    "tag_image_task_sync",
]
