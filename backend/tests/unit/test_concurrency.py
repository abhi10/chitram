"""Unit tests for upload concurrency control (ADR-0010)."""

import asyncio

import pytest

from app.services.concurrency import (
    UploadSemaphore,
    get_global_upload_semaphore,
    set_upload_semaphore,
)


class TestUploadSemaphore:
    """Tests for UploadSemaphore class."""

    def test_initialization_with_defaults(self):
        """Test semaphore initializes with correct limit."""
        semaphore = UploadSemaphore(limit=10, timeout=30.0)

        assert semaphore.limit == 10
        assert semaphore.timeout == 30.0
        assert semaphore.active_uploads == 0
        assert semaphore.available_slots == 10

    def test_available_slots_decreases_after_acquire(self):
        """Test available slots decreases when upload starts."""
        semaphore = UploadSemaphore(limit=5, timeout=1.0)

        # Simulate starting an upload
        semaphore._active_count = 2

        assert semaphore.active_uploads == 2
        assert semaphore.available_slots == 3

    @pytest.mark.asyncio
    async def test_acquire_succeeds_within_limit(self):
        """Test acquire succeeds when within concurrency limit."""
        semaphore = UploadSemaphore(limit=2, timeout=1.0)

        # First acquire should succeed
        result = await semaphore.acquire_with_timeout()
        assert result is True
        assert semaphore.active_uploads == 1

        # Second acquire should also succeed
        result = await semaphore.acquire_with_timeout()
        assert result is True
        assert semaphore.active_uploads == 2

    @pytest.mark.asyncio
    async def test_acquire_times_out_when_limit_exceeded(self):
        """Test acquire times out when concurrency limit is reached."""
        semaphore = UploadSemaphore(limit=1, timeout=0.1)

        # First acquire succeeds
        result = await semaphore.acquire_with_timeout()
        assert result is True

        # Second acquire should timeout (limit=1, already acquired)
        result = await semaphore.acquire_with_timeout()
        assert result is False

    @pytest.mark.asyncio
    async def test_release_allows_new_acquire(self):
        """Test release frees up slot for new acquire."""
        semaphore = UploadSemaphore(limit=1, timeout=0.5)

        # Acquire the only slot
        await semaphore.acquire_with_timeout()
        assert semaphore.active_uploads == 1

        # Release it
        semaphore.release()
        assert semaphore.active_uploads == 0

        # Now acquire should succeed again
        result = await semaphore.acquire_with_timeout()
        assert result is True

    @pytest.mark.asyncio
    async def test_release_does_not_go_negative(self):
        """Test release doesn't make active_count negative."""
        semaphore = UploadSemaphore(limit=5, timeout=1.0)

        # Release without acquire
        semaphore.release()
        assert semaphore.active_uploads == 0

    @pytest.mark.asyncio
    async def test_concurrent_acquires_respect_limit(self):
        """Test concurrent acquire attempts respect the limit."""
        semaphore = UploadSemaphore(limit=3, timeout=0.2)

        async def try_acquire():
            return await semaphore.acquire_with_timeout()

        # Try to acquire 5 slots concurrently (only 3 should succeed)
        results = await asyncio.gather(*[try_acquire() for _ in range(5)])

        successful = sum(1 for r in results if r)
        failed = sum(1 for r in results if not r)

        assert successful == 3
        assert failed == 2


class TestGlobalSemaphore:
    """Tests for global semaphore getter/setter."""

    def test_set_and_get_global_semaphore(self):
        """Test setting and getting global semaphore."""
        semaphore = UploadSemaphore(limit=10, timeout=30.0)

        set_upload_semaphore(semaphore)
        result = get_global_upload_semaphore()

        assert result is semaphore

    def test_set_global_semaphore_to_none(self):
        """Test clearing global semaphore."""
        semaphore = UploadSemaphore(limit=10, timeout=30.0)
        set_upload_semaphore(semaphore)

        set_upload_semaphore(None)
        result = get_global_upload_semaphore()

        assert result is None


class TestSemaphoreEdgeCases:
    """Edge case tests for semaphore behavior."""

    @pytest.mark.asyncio
    async def test_zero_timeout_immediately_fails(self):
        """Test that zero timeout fails immediately when limit reached."""
        semaphore = UploadSemaphore(limit=1, timeout=0.0)

        # First acquire succeeds
        await semaphore.acquire_with_timeout()

        # Second should fail immediately
        result = await semaphore.acquire_with_timeout()
        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_release_sequence(self):
        """Test correct acquire/release sequence tracking."""
        semaphore = UploadSemaphore(limit=2, timeout=1.0)

        # Acquire both slots
        await semaphore.acquire_with_timeout()
        await semaphore.acquire_with_timeout()
        assert semaphore.active_uploads == 2

        # Release one
        semaphore.release()
        assert semaphore.active_uploads == 1

        # Release another
        semaphore.release()
        assert semaphore.active_uploads == 0

    @pytest.mark.asyncio
    async def test_semaphore_with_large_limit(self):
        """Test semaphore works with large concurrency limit."""
        semaphore = UploadSemaphore(limit=100, timeout=1.0)

        # Acquire 50 slots
        for _ in range(50):
            result = await semaphore.acquire_with_timeout()
            assert result is True

        assert semaphore.active_uploads == 50
        assert semaphore.available_slots == 50
