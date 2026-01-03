"""Concurrency control for upload processing (ADR-0010)."""

import asyncio
from dataclasses import dataclass

# Global reference for dependency injection in tests
_upload_semaphore: "UploadSemaphore | None" = None


def set_upload_semaphore(semaphore: "UploadSemaphore | None") -> None:
    """Set global upload semaphore (used in tests)."""
    global _upload_semaphore
    _upload_semaphore = semaphore


def get_global_upload_semaphore() -> "UploadSemaphore | None":
    """Get global upload semaphore."""
    return _upload_semaphore


@dataclass
class UploadSemaphore:
    """
    Wrapper around asyncio.Semaphore for upload concurrency control.

    Limits concurrent upload processing to protect server resources.
    Acquire before file.read() to optimize memory usage.
    """

    limit: int
    timeout: float
    _semaphore: asyncio.Semaphore | None = None
    _active_count: int = 0

    def __post_init__(self) -> None:
        """Initialize the underlying semaphore."""
        self._semaphore = asyncio.Semaphore(self.limit)
        self._active_count = 0

    @property
    def active_uploads(self) -> int:
        """Number of uploads currently being processed."""
        return self._active_count

    @property
    def available_slots(self) -> int:
        """Number of available upload slots."""
        return self.limit - self._active_count

    async def acquire_with_timeout(self) -> bool:
        """
        Acquire semaphore with timeout.

        Returns True if acquired, False if timeout exceeded.
        """
        if self._semaphore is None:
            return True

        try:
            async with asyncio.timeout(self.timeout):
                await self._semaphore.acquire()
                self._active_count += 1
                return True
        except TimeoutError:
            return False

    def release(self) -> None:
        """Release semaphore after upload processing."""
        if self._semaphore is not None:
            self._semaphore.release()
            self._active_count = max(0, self._active_count - 1)
