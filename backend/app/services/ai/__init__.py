"""AI provider factory and exports."""

from app.config import Settings

from .base import AIProviderError, AITag, AITaggingProvider
from .mock import MockAIProvider


def create_ai_provider(settings: Settings) -> AITaggingProvider:
    """Create AI provider based on configuration.

    Args:
        settings: Application settings

    Returns:
        Configured AI provider instance

    Raises:
        ValueError: If provider type is unknown
        AIProviderError: If provider initialization fails (missing API key, etc.)

    Examples:
        >>> settings = Settings(ai_provider="mock")
        >>> provider = create_ai_provider(settings)
        >>> isinstance(provider, MockAIProvider)
        True
    """
    if settings.ai_provider == "mock":
        return MockAIProvider()

    if settings.ai_provider == "openai":
        if not settings.openai_api_key:
            raise AIProviderError("OpenAI API key not configured (OPENAI_API_KEY)")
        from .openai_vision import OpenAIVisionProvider

        return OpenAIVisionProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_vision_model,
            prompt=settings.openai_vision_prompt,
            max_tags=settings.ai_max_tags_per_image,
        )

    if settings.ai_provider == "google":
        if not settings.google_vision_api_key:
            raise AIProviderError("Google Vision API key not configured (GOOGLE_VISION_API_KEY)")
        from .google_vision import GoogleVisionProvider

        return GoogleVisionProvider(
            api_key=settings.google_vision_api_key,
            max_tags=settings.ai_max_tags_per_image,
        )

    raise ValueError(f"Unknown AI provider: {settings.ai_provider}")


__all__ = [
    "AITag",
    "AITaggingProvider",
    "AIProviderError",
    "MockAIProvider",
    "create_ai_provider",
]
