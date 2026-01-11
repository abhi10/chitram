"""Integration tests for AI vision providers.

IMPORTANT: These tests call real APIs and cost money!
Only run with: pytest -m manual

Cost per run:
- OpenAI (gpt-4o-mini): ~$0.004 per image
- Running all tests: ~$0.008 (2 images)

Setup:
    export OPENAI_API_KEY=sk-proj-your-key-here
    uv run pytest tests/integration/test_ai_vision.py -m manual -v
"""

import os

import pytest

from app.config import Settings
from app.services.ai import AIProviderError, create_ai_provider

# Mark all tests in this module as manual
pytestmark = pytest.mark.manual


class TestOpenAIVisionIntegration:
    """Integration tests for OpenAI Vision provider.

    These tests cost money - only run manually with: pytest -m manual
    """

    @pytest.mark.asyncio
    async def test_openai_analyzes_real_image(self, sample_jpeg_bytes):
        """Test OpenAI Vision with real API call.

        COST: ~$0.004 per run
        Requires: OPENAI_API_KEY environment variable

        This test verifies:
        - API connection works
        - Image encoding correct
        - Response parsing correct
        - Tag format matches expectations
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set - skipping paid test")

        settings = Settings(
            ai_provider="openai",
            openai_api_key=api_key,
            ai_max_tags_per_image=5,
        )

        provider = create_ai_provider(settings)
        tags = await provider.analyze_image(sample_jpeg_bytes)

        # Assertions
        assert len(tags) > 0, "Should return at least one tag"
        assert len(tags) <= 5, "Should respect max_tags limit (5)"
        assert all(0 <= tag.confidence <= 100 for tag in tags), "Confidence should be 0-100"
        assert all(isinstance(tag.name, str) for tag in tags), "Tag names should be strings"
        assert all(tag.name == tag.name.lower() for tag in tags), "Tags should be lowercase"
        assert all(tag.confidence == 90 for tag in tags), "OpenAI tags should have 90% confidence"

        # Print tags for manual verification
        print(f"\n✓ OpenAI Vision returned {len(tags)} tags:")
        for i, tag in enumerate(tags, 1):
            print(f"  {i}. {tag.name} ({tag.confidence}%)")

    @pytest.mark.asyncio
    async def test_openai_handles_invalid_api_key(self, sample_jpeg_bytes):
        """OpenAI provider raises error for invalid API key.

        COST: FREE (fails before API call)
        """
        settings = Settings(
            ai_provider="openai",
            openai_api_key="sk-invalid-key-12345",
        )

        provider = create_ai_provider(settings)

        with pytest.raises(AIProviderError) as exc_info:
            await provider.analyze_image(sample_jpeg_bytes)

        assert "OpenAI" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_openai_respects_max_tags_limit(self, sample_jpeg_bytes):
        """OpenAI provider respects max_tags configuration.

        COST: ~$0.004 per run
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set - skipping paid test")

        settings = Settings(
            ai_provider="openai",
            openai_api_key=api_key,
            ai_max_tags_per_image=3,  # Limit to 3 tags
        )

        provider = create_ai_provider(settings)
        tags = await provider.analyze_image(sample_jpeg_bytes)

        assert len(tags) <= 3, f"Should return max 3 tags, got {len(tags)}"

        print(f"\n✓ OpenAI Vision limited to {len(tags)}/3 tags:")
        for i, tag in enumerate(tags, 1):
            print(f"  {i}. {tag.name}")

    @pytest.mark.asyncio
    async def test_openai_handles_empty_image(self):
        """OpenAI provider handles empty image bytes gracefully.

        COST: Likely FREE (should fail before API call)
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        settings = Settings(ai_provider="openai", openai_api_key=api_key)
        provider = create_ai_provider(settings)

        # Empty bytes should raise an error
        with pytest.raises(AIProviderError):
            await provider.analyze_image(b"")

    @pytest.mark.asyncio
    async def test_openai_model_selection(self, sample_jpeg_bytes):
        """Verify OpenAI provider uses correct model.

        COST: ~$0.004 per run
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        # Test with default model (gpt-4o-mini)
        settings = Settings(
            ai_provider="openai",
            openai_api_key=api_key,
            openai_vision_model="gpt-4o-mini",
        )

        provider = create_ai_provider(settings)
        assert provider.model == "gpt-4o-mini"

        tags = await provider.analyze_image(sample_jpeg_bytes)
        assert len(tags) > 0

        print(f"\n✓ Model {provider.model} returned {len(tags)} tags")


# Example: Run only OpenAI tests
# uv run pytest tests/integration/test_ai_vision.py::TestOpenAIVisionIntegration -m manual -v

# Example: Run with cost awareness
# OPENAI_API_KEY=sk-... uv run pytest tests/integration/test_ai_vision.py -m manual -v --tb=short
