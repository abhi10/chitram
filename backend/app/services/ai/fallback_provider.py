"""Fallback AI provider that tries multiple providers in sequence."""

import logging

from .base import AIProviderError, AITag, AITaggingProvider

logger = logging.getLogger(__name__)


class FallbackAIProvider(AITaggingProvider):
    """
    AI provider that tries multiple providers in order until one succeeds.

    Order: OpenAI → Google → Mock

    Benefits:
    - Resilience (if OpenAI down, use Google)
    - Graceful degradation (if all fail, use mock)
    - Same interface (transparent to caller)

    Example:
        >>> providers = [openai_provider, google_provider, mock_provider]
        >>> fallback = FallbackAIProvider(providers)
        >>> tags = await fallback.analyze_image(image_bytes)
        # Returns result from first successful provider
    """

    def __init__(self, providers: list[AITaggingProvider]) -> None:
        """
        Initialize fallback provider with list of providers to try.

        Args:
            providers: List of providers to try in order (e.g., [OpenAI, Google, Mock])

        Raises:
            ValueError: If providers list is empty
        """
        if not providers:
            raise ValueError("FallbackAIProvider requires at least one provider")
        self.providers = providers

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        """
        Analyze image using first available provider.

        Tries each provider in order until one succeeds. If all providers fail,
        raises AIProviderError with details from all attempts.

        Args:
            image_bytes: Raw image file content

        Returns:
            List of AI tags from first successful provider

        Raises:
            AIProviderError: If all providers fail
        """
        errors: list[tuple[str, Exception]] = []

        for provider in self.providers:
            provider_name = provider.__class__.__name__
            try:
                logger.debug(f"Trying AI provider: {provider_name}")
                tags = await provider.analyze_image(image_bytes)
                logger.info(f"AI provider succeeded: {provider_name} (returned {len(tags)} tags)")
                return tags

            except AIProviderError as e:
                logger.warning(f"AI provider failed: {provider_name} - {e}")
                errors.append((provider_name, e))
                continue  # Try next provider

            except Exception as e:
                # Unexpected error - still try next provider but log as error
                logger.error(
                    f"Unexpected error in AI provider {provider_name}: {e}",
                    exc_info=True,
                )
                errors.append((provider_name, e))
                continue

        # All providers failed
        error_summary = ", ".join(f"{name}: {str(err)}" for name, err in errors)
        logger.error(f"All AI providers failed: {error_summary}")
        raise AIProviderError(f"All AI providers failed: {error_summary}")
