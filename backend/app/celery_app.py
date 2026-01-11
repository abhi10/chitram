"""Celery application for background tasks."""

from celery import Celery

from app.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "chitram",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.ai_tagging"],  # Task modules to import
)

# Celery configuration
celery_app.conf.update(
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task behavior
    task_acks_late=True,  # Acknowledge task after completion (safer)
    task_reject_on_worker_lost=True,  # Requeue task if worker crashes
    worker_prefetch_multiplier=1,  # One task at a time per worker (fairness)
    # Result expiration
    result_expires=3600,  # Results expire after 1 hour
    # Testing mode (run tasks synchronously if enabled)
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=settings.celery_task_eager_propagates,
)


# Optional: Task event monitoring
if settings.is_development:
    celery_app.conf.update(
        worker_send_task_events=True,
        task_send_sent_event=True,
    )
