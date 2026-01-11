"""OpenAI Vision API provider for image tagging.

Uses OpenAI's GPT-4 Vision models to analyze images and generate tags.
Optimized for cost with gpt-4o-mini model (~$0.004 per image).
"""

import base64
import logging

from openai import AsyncOpenAI, OpenAIError

from .base import AIProviderError, AITag, AITaggingProvider

logger = logging.getLogger(__name__)


class OpenAIVisionProvider(AITaggingProvider):
    """OpenAI Vision API provider for production use.

    Cost Analysis (gpt-4o-mini):
    - ~$0.004 per image
    - 1,000 images/month = $4
    - 5,000 images/month = $20

    Rate Limits:
    - 500 requests/minute (Tier 1)
    - 10,000 requests/day

    Attributes:
        client: Async OpenAI client
        model: Model ID (default: gpt-4o-mini)
        prompt: Custom prompt for tag generation
        max_tags: Maximum tags to return (cost control)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        prompt: str = "Generate 5 descriptive tags for this image. Return only tag names separated by commas.",
        max_tags: int = 5,
    ):
        """Initialize OpenAI Vision provider.

        Args:
            api_key: OpenAI API key (sk-proj-...)
            model: Model to use (gpt-4o-mini recommended for cost)
            prompt: System prompt for tag generation
            max_tags: Maximum tags to return (5 for cost control)

        Raises:
            AIProviderError: If API key is invalid format
        """
        if not api_key or not api_key.startswith("sk-"):
            raise AIProviderError(f"Invalid OpenAI API key format: {api_key[:10]}...")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.prompt = prompt
        self.max_tags = max_tags

        logger.info(f"OpenAI Vision provider initialized (model={model}, max_tags={max_tags})")

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        """Analyze image using OpenAI Vision API.

        Args:
            image_bytes: Raw image data (JPEG/PNG, max 5MB from app config)

        Returns:
            List of AITag objects with 90% confidence (OpenAI doesn't provide scores)

        Raises:
            AIProviderError: If API call fails (rate limit, network, invalid key, etc.)

        Example:
            >>> provider = OpenAIVisionProvider(api_key="sk-...")
            >>> tags = await provider.analyze_image(image_bytes)
            >>> [tag.name for tag in tags]
            ['landscape', 'sky', 'clouds', 'nature', 'outdoors']
        """
        try:
            # Encode image to base64 (required by OpenAI API)
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            logger.debug(
                f"Calling OpenAI Vision API (model={self.model}, "
                f"image_size={len(image_bytes)} bytes)"
            )

            # Call OpenAI Vision API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "low",  # Cost optimization
                                },
                            },
                        ],
                    }
                ],
                max_tokens=150,  # Limit response length for cost control
            )

            # Parse response
            tags_text = response.choices[0].message.content
            if not tags_text:
                logger.warning("OpenAI returned empty response")
                return []

            # Split by comma and clean
            # Example response: "landscape, sky, clouds, nature, outdoors"
            tag_names = [tag.strip().lower() for tag in tags_text.split(",") if tag.strip()]

            # Convert to AITag objects
            # Note: OpenAI doesn't provide confidence scores, so we use 90
            # as a reasonable "AI-generated" confidence level
            tags = [
                AITag(name=name, confidence=90, category=None)
                for name in tag_names[: self.max_tags]
            ]

            logger.info(f"OpenAI Vision returned {len(tags)} tags: {[tag.name for tag in tags]}")

            return tags

        except OpenAIError as e:
            # Handle OpenAI-specific errors (rate limit, auth, etc.)
            error_msg = str(e)

            # Check for common error scenarios
            if "rate_limit" in error_msg.lower():
                logger.error(f"OpenAI rate limit exceeded: {e}")
                raise AIProviderError("OpenAI rate limit exceeded. Please try again later.") from e

            if "invalid" in error_msg.lower() and "api" in error_msg.lower():
                logger.error(f"Invalid OpenAI API key: {e}")
                raise AIProviderError("Invalid OpenAI API key") from e

            logger.error(f"OpenAI API error: {e}")
            raise AIProviderError(f"OpenAI Vision API failed: {error_msg}") from e

        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error in OpenAI provider: {e}", exc_info=True)
            raise AIProviderError(f"Failed to analyze image: {e}") from e
