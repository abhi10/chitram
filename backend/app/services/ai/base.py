"""Abstract base for AI vision providers.

This module defines the interface that all AI vision providers must implement,
following the Strategy pattern for pluggable AI services.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AITag:
    """AI-generated tag suggestion.

    Attributes:
        name: Tag name (lowercase, normalized)
        confidence: Confidence score 0-100
        category: Optional tag category (e.g., 'object', 'scene', 'color')
    """

    name: str
    confidence: int  # 0-100
    category: str | None = None


class AITaggingProvider(ABC):
    """Abstract base for AI vision providers.

    All AI providers (OpenAI, Google, Mock) must implement this interface.
    """

    @abstractmethod
    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        """Analyze image and return tag suggestions.

        Args:
            image_bytes: Raw image data (JPEG/PNG)

        Returns:
            List of AITag objects with confidence scores, sorted by confidence descending

        Raises:
            AIProviderError: If analysis fails (network, API error, etc.)
        """
        pass


class AIProviderError(Exception):
    """Raised when AI provider fails to analyze image."""

    pass
