"""AI tagging Celery task for background image analysis."""

import logging

from app.celery_app import celery_app
from app.config import get_settings
from app.database import async_session_maker
from app.services.ai import AIProviderError, create_ai_provider
from app.services.image_service import ImageService
from app.services.storage_factory import create_storage_backend
from app.services.storage_service import StorageService
from app.services.tag_service import TagService

logger = logging.getLogger(__name__)


@celery_app.task(
    name="ai_tagging.tag_image",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(AIProviderError,),
    retry_backoff=True,
    retry_backoff_max=240,  # 4 minutes
    retry_jitter=True,
)
def tag_image_task(self, image_id: str) -> dict:
    """
    Background task to analyze image and add AI tags.

    Retry logic:
    - Attempt 1: Immediate
    - Attempt 2: After ~1 minute
    - Attempt 3: After ~2 minutes
    - Attempt 4: After ~4 minutes

    Graceful degradation:
    - If all retries fail, log error but don't crash
    - Image remains without AI tags (can retry manually later)

    Args:
        image_id: UUID of the image to analyze

    Returns:
        dict: {"success": bool, "tags_added": int, "error": str | None}
    """
    try:
        # Use synchronous version (Celery tasks can't use async)
        return tag_image_task_sync(image_id)

    except AIProviderError as e:
        # Celery will auto-retry based on autoretry_for
        logger.warning(
            f"AI tagging failed (attempt {self.request.retries + 1}): {e}",
            extra={"image_id": image_id, "retry": self.request.retries},
        )
        raise  # Let Celery handle retry

    except Exception as e:
        # Permanent errors - log but don't retry
        logger.error(
            f"Permanent error in AI tagging: {e}",
            exc_info=True,
            extra={"image_id": image_id},
        )
        return {"success": False, "tags_added": 0, "error": str(e)}


def tag_image_task_sync(image_id: str) -> dict:
    """
    Synchronous version of AI tagging task.

    Used by:
    - Celery task (can't use async)
    - MockTaskService (synchronous execution for tests)

    Args:
        image_id: UUID of the image to analyze

    Returns:
        dict: {"success": bool, "tags_added": int, "error": str | None}

    Raises:
        AIProviderError: If AI provider fails (triggers retry in Celery)
        ValueError: If image not found (permanent error, no retry)
    """
    import asyncio

    # Run async code in event loop
    return asyncio.run(_tag_image_async(image_id))


async def _tag_image_async(image_id: str) -> dict:
    """
    Internal async implementation of AI tagging.

    Args:
        image_id: UUID of the image to analyze

    Returns:
        dict: {"success": bool, "tags_added": int, "error": str | None}

    Raises:
        AIProviderError: If AI provider fails (retryable)
        ValueError: If image not found (permanent)
    """
    settings = get_settings()

    # Create services
    async with async_session_maker() as db:
        # Initialize storage using shared factory (DRY principle)
        storage_backend = await create_storage_backend(settings)
        storage = StorageService(backend=storage_backend)

        # Initialize services
        image_service = ImageService(db=db, storage=storage, cache=None)
        tag_service = TagService(db=db)

        # 1. Fetch image metadata
        image = await image_service.get_by_id(image_id)
        if not image:
            raise ValueError(f"Image {image_id} not found")

        # 2. Fetch image bytes from storage
        image_bytes = await storage.get(image.storage_key)
        if not image_bytes:
            raise ValueError(f"Image file not found in storage: {image.storage_key}")

        # 3. Analyze image with AI provider (reuse existing abstraction - DRY)
        ai_provider = create_ai_provider(settings)
        ai_tags = await ai_provider.analyze_image(image_bytes)

        logger.info(
            f"AI provider returned {len(ai_tags)} tags for image {image_id}",
            extra={"image_id": image_id, "tags": [tag.name for tag in ai_tags]},
        )

        # 4. Add tags to image (reuse existing tag service - DRY)
        tags_added = 0
        for ai_tag in ai_tags:
            try:
                await tag_service.add_tag_to_image(
                    image_id=image_id,
                    tag_name=ai_tag.name,
                    source="ai",
                    confidence=ai_tag.confidence,
                    category=ai_tag.category,
                )
                tags_added += 1
            except ValueError as e:
                # Tag already exists or other validation error
                logger.debug(f"Skipping tag '{ai_tag.name}': {e}")
                continue

        logger.info(
            f"AI tagging complete: {tags_added} tags added to image {image_id}",
            extra={"image_id": image_id, "tags_added": tags_added},
        )

        return {"success": True, "tags_added": tags_added, "error": None}
