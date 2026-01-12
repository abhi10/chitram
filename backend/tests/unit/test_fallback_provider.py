"""Unit tests for FallbackAIProvider."""

import pytest

from app.services.ai import AIProviderError, AITag, FallbackAIProvider
from app.services.ai.base import AITaggingProvider


class MockSuccessProvider(AITaggingProvider):
    """Mock provider that always succeeds."""

    def __init__(self, tags: list[AITag] | None = None) -> None:
        self.tags = tags or [AITag(name="test", confidence=0.9, category="object")]

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        return self.tags


class MockFailProvider(AITaggingProvider):
    """Mock provider that always fails."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error or AIProviderError("Mock failure")

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        raise self.error


class TestFallbackAIProvider:
    """Test suite for FallbackAIProvider."""

    @pytest.mark.asyncio
    async def test_initialization_requires_providers(self) -> None:
        """Test that initialization fails with empty provider list."""
        with pytest.raises(ValueError, match="at least one provider"):
            FallbackAIProvider(providers=[])

    @pytest.mark.asyncio
    async def test_first_provider_succeeds(self) -> None:
        """Test that first provider is used when it succeeds."""
        expected_tags = [
            AITag(name="cat", confidence=0.95, category="animal"),
            AITag(name="kitten", confidence=0.85, category="animal"),
        ]
        provider1 = MockSuccessProvider(tags=expected_tags)
        provider2 = MockSuccessProvider(
            tags=[AITag(name="wrong", confidence=0.5, category="object")]
        )

        fallback = FallbackAIProvider(providers=[provider1, provider2])
        result = await fallback.analyze_image(b"fake_image_bytes")

        assert result == expected_tags

    @pytest.mark.asyncio
    async def test_fallback_to_second_provider(self) -> None:
        """Test fallback when first provider fails."""
        expected_tags = [AITag(name="backup", confidence=0.7, category="object")]
        provider1 = MockFailProvider()
        provider2 = MockSuccessProvider(tags=expected_tags)

        fallback = FallbackAIProvider(providers=[provider1, provider2])
        result = await fallback.analyze_image(b"fake_image_bytes")

        assert result == expected_tags

    @pytest.mark.asyncio
    async def test_fallback_chain_all_providers(self) -> None:
        """Test that all providers are tried in order."""
        expected_tags = [AITag(name="final", confidence=0.6, category="object")]
        provider1 = MockFailProvider(AIProviderError("Provider 1 failed"))
        provider2 = MockFailProvider(AIProviderError("Provider 2 failed"))
        provider3 = MockSuccessProvider(tags=expected_tags)

        fallback = FallbackAIProvider(providers=[provider1, provider2, provider3])
        result = await fallback.analyze_image(b"fake_image_bytes")

        assert result == expected_tags

    @pytest.mark.asyncio
    async def test_all_providers_fail(self) -> None:
        """Test error when all providers fail."""
        provider1 = MockFailProvider(AIProviderError("Provider 1 down"))
        provider2 = MockFailProvider(AIProviderError("Provider 2 down"))
        provider3 = MockFailProvider(AIProviderError("Provider 3 down"))

        fallback = FallbackAIProvider(providers=[provider1, provider2, provider3])

        with pytest.raises(AIProviderError, match="All AI providers failed"):
            await fallback.analyze_image(b"fake_image_bytes")

    @pytest.mark.asyncio
    async def test_unexpected_exception_handled(self) -> None:
        """Test that unexpected exceptions are caught and next provider tried."""
        provider1 = MockFailProvider(RuntimeError("Unexpected error"))
        expected_tags = [AITag(name="recovered", confidence=0.8, category="object")]
        provider2 = MockSuccessProvider(tags=expected_tags)

        fallback = FallbackAIProvider(providers=[provider1, provider2])
        result = await fallback.analyze_image(b"fake_image_bytes")

        assert result == expected_tags

    @pytest.mark.asyncio
    async def test_single_provider_works(self) -> None:
        """Test that fallback works with just one provider."""
        expected_tags = [AITag(name="solo", confidence=0.9, category="object")]
        provider = MockSuccessProvider(tags=expected_tags)

        fallback = FallbackAIProvider(providers=[provider])
        result = await fallback.analyze_image(b"fake_image_bytes")

        assert result == expected_tags

    @pytest.mark.asyncio
    async def test_empty_tags_returned_successfully(self) -> None:
        """Test that empty tag list is valid success case."""

        # Create provider with explicitly empty tags
        class EmptyTagProvider(AITaggingProvider):
            async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
                return []

        provider = EmptyTagProvider()

        fallback = FallbackAIProvider(providers=[provider])
        result = await fallback.analyze_image(b"fake_image_bytes")

        assert result == []
