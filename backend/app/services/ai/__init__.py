"""AI provider factory and exports."""

import logging

from app.config import Settings

from .base import AIProviderError, AITag, AITaggingProvider
from .fallback_provider import FallbackAIProvider
from .mock import MockAIProvider

logger = logging.getLogger(__name__)


def create_ai_provider(settings: Settings, use_fallback: bool = True) -> AITaggingProvider:
    """Create AI provider based on configuration.

    When use_fallback=True (default for production):
    - Tries providers in order: OpenAI → Google → Mock
    - Provides resilience against provider outages

    When use_fallback=False (for explicit provider selection):
    - Returns only the requested provider
    - Raises errors if provider fails to initialize

    Args:
        settings: Application settings
        use_fallback: Enable fallback chain (default: True)

    Returns:
        Configured AI provider instance

    Raises:
        ValueError: If provider type is unknown
        AIProviderError: If provider initialization fails (when use_fallback=False)

    Examples:
        >>> settings = Settings(ai_provider="mock")
        >>> provider = create_ai_provider(settings)
        >>> isinstance(provider, MockAIProvider)
        True
    """
    # Strict mode: Return only the explicitly requested provider
    if not use_fallback:
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
                raise AIProviderError(
                    "Google Vision API key not configured (GOOGLE_VISION_API_KEY)"
                )
            from .google_vision import GoogleVisionProvider

            return GoogleVisionProvider(
                api_key=settings.google_vision_api_key,
                max_tags=settings.ai_max_tags_per_image,
            )

        raise ValueError(f"Unknown AI provider: {settings.ai_provider}")

    # Fallback mode: Build resilient provider chain
    # If explicitly set to mock, return mock directly (no fallback needed)
    if settings.ai_provider == "mock":
        logger.info("Using mock AI provider (no fallback)")
        return MockAIProvider()

    # Build list of available providers for fallback chain
    providers: list[AITaggingProvider] = []

    # Try OpenAI first (if configured)
    if settings.openai_api_key:
        try:
            from .openai_vision import OpenAIVisionProvider

            providers.append(
                OpenAIVisionProvider(
                    api_key=settings.openai_api_key,
                    model=settings.openai_vision_model,
                    prompt=settings.openai_vision_prompt,
                    max_tags=settings.ai_max_tags_per_image,
                )
            )
            logger.info("Added OpenAI to fallback chain")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI provider: {e}")

    # Try Google Vision second (if configured)
    if settings.google_vision_api_key:
        try:
            from .google_vision import GoogleVisionProvider

            providers.append(
                GoogleVisionProvider(
                    api_key=settings.google_vision_api_key,
                    max_tags=settings.ai_max_tags_per_image,
                )
            )
            logger.info("Added Google Vision to fallback chain")
        except Exception as e:
            logger.warning(f"Failed to initialize Google Vision provider: {e}")

    # Always add mock as last resort
    providers.append(MockAIProvider())
    logger.info("Added Mock provider to fallback chain (last resort)")

    # If only one provider, return it directly (no fallback overhead)
    if len(providers) == 1:
        logger.info(f"Using single provider: {providers[0].__class__.__name__}")
        return providers[0]

    # Multiple providers - wrap in fallback
    logger.info(
        f"Using fallback provider chain: {' → '.join(p.__class__.__name__ for p in providers)}"
    )
    return FallbackAIProvider(providers)


__all__ = [
    "AITag",
    "AITaggingProvider",
    "AIProviderError",
    "FallbackAIProvider",
    "MockAIProvider",
    "create_ai_provider",
]
