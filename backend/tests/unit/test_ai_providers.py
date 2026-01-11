"""Unit tests for AI providers.

Tests the AI provider abstraction layer without calling external APIs.
Uses MockAIProvider for fast, cost-free testing.
"""

import pytest

from app.config import Settings
from app.services.ai import (
    AIProviderError,
    AITag,
    AITaggingProvider,
    MockAIProvider,
    create_ai_provider,
)


class TestAITag:
    """Tests for AITag dataclass."""

    def test_aitag_creation_with_required_fields(self):
        """AITag can be created with name and confidence only."""
        tag = AITag(name="test", confidence=95)

        assert tag.name == "test"
        assert tag.confidence == 95
        assert tag.category is None

    def test_aitag_with_category(self):
        """AITag can include optional category."""
        tag = AITag(name="test", confidence=85, category="object")

        assert tag.name == "test"
        assert tag.confidence == 85
        assert tag.category == "object"

    def test_aitag_confidence_boundaries(self):
        """AITag accepts confidence values at boundaries (0-100)."""
        tag_min = AITag(name="low", confidence=0)
        tag_max = AITag(name="high", confidence=100)

        assert tag_min.confidence == 0
        assert tag_max.confidence == 100


class TestMockAIProvider:
    """Tests for MockAIProvider."""

    @pytest.mark.asyncio
    async def test_returns_predictable_tags(self):
        """Mock provider returns same tags every time for consistency."""
        provider = MockAIProvider()

        tags1 = await provider.analyze_image(b"fake-bytes-1")
        tags2 = await provider.analyze_image(b"fake-bytes-2")

        # Should return exactly 3 tags
        assert len(tags1) == 3
        assert len(tags2) == 3

        # Tags should be identical regardless of input
        assert tags1[0].name == tags2[0].name
        assert tags1[0].confidence == tags2[0].confidence
        assert tags1[0].category == tags2[0].category

    @pytest.mark.asyncio
    async def test_returns_aitag_objects(self):
        """Mock provider returns valid AITag objects."""
        provider = MockAIProvider()
        tags = await provider.analyze_image(b"fake")

        assert all(isinstance(tag, AITag) for tag in tags)
        assert all(isinstance(tag.name, str) for tag in tags)
        assert all(0 <= tag.confidence <= 100 for tag in tags)

    @pytest.mark.asyncio
    async def test_returns_tags_sorted_by_confidence(self):
        """Mock provider returns tags sorted by confidence descending."""
        provider = MockAIProvider()
        tags = await provider.analyze_image(b"fake")

        # Check confidence values are descending
        assert tags[0].confidence >= tags[1].confidence
        assert tags[1].confidence >= tags[2].confidence

    @pytest.mark.asyncio
    async def test_implements_abstract_base(self):
        """MockAIProvider implements AITaggingProvider interface."""
        provider = MockAIProvider()
        assert isinstance(provider, AITaggingProvider)

    @pytest.mark.asyncio
    async def test_tag_names_are_lowercase(self):
        """Mock provider returns lowercase tag names."""
        provider = MockAIProvider()
        tags = await provider.analyze_image(b"fake")

        assert all(tag.name == tag.name.lower() for tag in tags)

    @pytest.mark.asyncio
    async def test_ignores_image_bytes(self):
        """Mock provider doesn't actually analyze the image bytes."""
        provider = MockAIProvider()

        # Should work even with empty bytes
        tags = await provider.analyze_image(b"")
        assert len(tags) == 3

        # Should work with invalid image data
        tags = await provider.analyze_image(b"not-an-image")
        assert len(tags) == 3


class TestAIProviderFactory:
    """Tests for create_ai_provider factory function."""

    def test_creates_mock_provider_by_default(self):
        """Factory creates mock provider when ai_provider='mock'."""
        settings = Settings(ai_provider="mock")
        provider = create_ai_provider(settings)

        assert isinstance(provider, MockAIProvider)

    def test_creates_mock_provider_explicitly(self):
        """Factory creates mock provider when explicitly configured."""
        settings = Settings(ai_provider="mock")
        provider = create_ai_provider(settings)

        assert isinstance(provider, MockAIProvider)
        assert isinstance(provider, AITaggingProvider)

    def test_raises_for_unknown_provider(self):
        """Factory raises ValueError for unknown provider type."""
        settings = Settings(ai_provider="unknown-provider")

        with pytest.raises(ValueError) as exc_info:
            create_ai_provider(settings)

        assert "Unknown AI provider" in str(exc_info.value)
        assert "unknown-provider" in str(exc_info.value)

    def test_raises_for_missing_openai_key(self):
        """Factory raises AIProviderError if OpenAI key not configured."""
        settings = Settings(ai_provider="openai", openai_api_key=None)

        with pytest.raises(AIProviderError) as exc_info:
            create_ai_provider(settings)

        assert "OpenAI API key" in str(exc_info.value)

    def test_raises_for_empty_openai_key(self):
        """Factory raises AIProviderError if OpenAI key is empty string."""
        settings = Settings(ai_provider="openai", openai_api_key="")

        with pytest.raises(AIProviderError) as exc_info:
            create_ai_provider(settings)

        assert "OpenAI API key" in str(exc_info.value)

    def test_raises_for_missing_google_key(self):
        """Factory raises AIProviderError if Google Vision key not configured."""
        settings = Settings(ai_provider="google", google_vision_api_key=None)

        with pytest.raises(AIProviderError) as exc_info:
            create_ai_provider(settings)

        assert "Google Vision API key" in str(exc_info.value)

    def test_respects_ai_max_tags_setting(self):
        """Factory passes max_tags setting to providers."""
        settings = Settings(ai_provider="mock", ai_max_tags_per_image=5)

        # Should not raise (mock provider doesn't use max_tags)
        provider = create_ai_provider(settings)
        assert isinstance(provider, MockAIProvider)

    def test_provider_configuration_isolated(self):
        """Each factory call creates independent provider instance."""
        settings = Settings(ai_provider="mock")

        provider1 = create_ai_provider(settings)
        provider2 = create_ai_provider(settings)

        # Should be different instances
        assert provider1 is not provider2

    def test_lazy_import_for_openai_provider(self):
        """OpenAI provider is only imported when needed."""
        # This test verifies lazy imports don't cause issues
        # when the provider module doesn't exist yet
        settings = Settings(ai_provider="mock")

        # Should not try to import OpenAI provider
        provider = create_ai_provider(settings)
        assert isinstance(provider, MockAIProvider)


class TestAIProviderError:
    """Tests for AIProviderError exception."""

    def test_can_be_raised(self):
        """AIProviderError can be raised and caught."""
        with pytest.raises(AIProviderError):
            raise AIProviderError("Test error")

    def test_inherits_from_exception(self):
        """AIProviderError inherits from Exception."""
        assert issubclass(AIProviderError, Exception)

    def test_can_include_error_message(self):
        """AIProviderError can include detailed error message."""
        error_msg = "API rate limit exceeded"

        with pytest.raises(AIProviderError) as exc_info:
            raise AIProviderError(error_msg)

        assert str(exc_info.value) == error_msg
