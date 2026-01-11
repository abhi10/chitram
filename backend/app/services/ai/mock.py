"""Mock AI provider for testing without API costs.

This provider returns predictable fake tags for use in tests and development.
No external API calls are made.
"""

from .base import AITag, AITaggingProvider


class MockAIProvider(AITaggingProvider):
    """Returns predictable fake tags for testing.

    This provider is useful for:
    - Unit tests (no API costs)
    - Development (no API keys needed)
    - Integration tests (predictable results)
    """

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        """Return mock tags without calling any API.

        Always returns the same 3 tags for consistency in tests.

        Args:
            image_bytes: Raw image data (ignored, not analyzed)

        Returns:
            List of 3 predictable AITag objects
        """
        return [
            AITag(name="mock-object", confidence=95, category="object"),
            AITag(name="mock-scene", confidence=85, category="scene"),
            AITag(name="mock-color", confidence=75, category="color"),
        ]
