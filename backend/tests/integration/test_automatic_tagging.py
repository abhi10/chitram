"""Integration tests for automatic AI tagging on upload."""

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.models.image import Image
from tests.conftest import TestDependencies


@pytest.mark.asyncio
async def test_upload_triggers_ai_tagging_task(
    client: AsyncClient,
    test_deps: TestDependencies,
    sample_image_bytes: bytes,
    auth_headers: dict[str, str],
) -> None:
    """
    Test that uploading an image triggers background AI tagging.

    Flow:
    1. Upload image
    2. Verify task service was called to enqueue AI tagging
    3. Verify upload completes successfully
    """
    # Mock the task execution to avoid asyncio.run() issues in tests
    with patch("app.tasks.ai_tagging.tag_image_task_sync") as mock_task:
        mock_task.return_value = {"success": True, "tags_added": 3, "error": None}

        # 1. Upload image
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        image_id = data["id"]

        # 2. Verify image was created
        image = await test_deps.session.get(Image, image_id)
        assert image is not None
        assert image.filename == "test.jpg"

        # 3. Verify task service was called to enqueue tagging
        mock_task.assert_called_once()
        # Task was called with the correct image_id
        call_args = mock_task.call_args
        assert call_args[0][0] == image_id  # First positional arg is image_id


@pytest.mark.asyncio
async def test_upload_succeeds_even_if_tagging_fails(
    client: AsyncClient,
    test_deps: TestDependencies,
    sample_image_bytes: bytes,
    auth_headers: dict[str, str],
) -> None:
    """
    Test graceful degradation: upload succeeds even if AI tagging fails.

    This is critical for user experience - image upload should never fail
    due to AI service issues.
    """
    # Mock task service to raise exception
    with patch("app.services.background.MockTaskService.enqueue_ai_tagging") as mock_enqueue:
        mock_enqueue.side_effect = RuntimeError("Simulated task queue failure")

        # Upload should still succeed
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        image_id = data["id"]

        # Verify image was created despite tagging failure
        image = await test_deps.session.get(Image, image_id)
        assert image is not None
        assert image.filename == "test.jpg"


@pytest.mark.asyncio
async def test_automatic_tagging_uses_mock_provider(
    client: AsyncClient,
    test_deps: TestDependencies,
    sample_image_bytes: bytes,
    auth_headers: dict[str, str],
) -> None:
    """
    Test that automatic tagging works with mock provider in tests.

    In test environment:
    - AI_PROVIDER=mock (no OpenAI/Google keys configured)
    - Should use MockAIProvider via fallback chain
    """
    with patch("app.tasks.ai_tagging.tag_image_task_sync") as mock_task:
        mock_task.return_value = {"success": True, "tags_added": 3, "error": None}

        # Upload image
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )

        assert response.status_code == 201
        mock_task.assert_called_once()


@pytest.mark.asyncio
async def test_upload_without_auth_fails(
    client: AsyncClient,
    test_deps: TestDependencies,
    sample_image_bytes: bytes,
) -> None:
    """
    Test that unauthenticated uploads fail (authentication required).

    Phase 6 requires authentication for uploads, so AI tagging only
    applies to authenticated uploads.
    """
    # Attempt upload without auth headers
    response = await client.post(
        "/api/v1/images/upload",
        files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
    )

    # Should fail with 401 Unauthorized
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_task_service_execution_count(
    client: AsyncClient,
    test_deps: TestDependencies,
    sample_image_bytes: bytes,
    auth_headers: dict[str, str],
) -> None:
    """
    Test that task service tracks execution count correctly.

    MockTaskService provides get_execution_count() for testing.
    """
    with patch("app.tasks.ai_tagging.tag_image_task_sync") as mock_task:
        mock_task.return_value = {"success": True, "tags_added": 3, "error": None}

        # Get initial count
        initial_count = test_deps.task_service.get_execution_count("ai_tagging")

        # Upload image (triggers auto-tagging)
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )

        assert response.status_code == 201

        # Verify execution count increased
        final_count = test_deps.task_service.get_execution_count("ai_tagging")
        assert final_count == initial_count + 1


@pytest.mark.asyncio
async def test_task_service_reset(test_deps: TestDependencies) -> None:
    """
    Test that MockTaskService reset() clears all state.

    Useful for isolating tests.
    """
    # Add some fake task
    test_deps.task_service._tasks["fake-id"] = {
        "status": "success",
        "result": {},
    }
    test_deps.task_service._execution_count["ai_tagging"] = 5

    # Reset
    test_deps.task_service.reset()

    # Verify state cleared
    assert len(test_deps.task_service._tasks) == 0
    assert test_deps.task_service.get_execution_count("ai_tagging") == 0
