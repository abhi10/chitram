# Building an AI Provider System: The Strategy Pattern for Vision APIs (Part 1 of 3)

**Date:** 2026-01-13
**Reading Time:** 3 minutes
**Tags:** #ai #strategy-pattern #architecture #openai #vision-api
**Repository:** https://github.com/abhi10/chitram

---

## TL;DR

Built a swappable AI provider system for automatic image tagging using the Strategy pattern. Switch between OpenAI Vision, Google Vision, or mock providers with a single environment variable - zero code changes. This 3-part series covers: (1) Provider architecture, (2) Manual→Automatic evolution, (3) Deployment debugging.

---

## The Problem: Vendor Lock-In

When adding AI vision to Chitram, I faced a critical decision:

**What if OpenAI raises prices tomorrow?**
**What if Google Vision releases a better model next month?**
**How do we test without burning money on API calls?**

Most tutorials hardcode the provider:

```python
# ❌ BAD: Locked into OpenAI
def tag_image(image_bytes: bytes) -> list[str]:
    openai_client = OpenAI(api_key=API_KEY)
    response = openai_client.vision.analyze(image_bytes)
    return response.tags

# Problem: Switching providers = rewriting this function everywhere
```

**The pain:**
- Provider code scattered across the codebase
- Changing providers requires code changes in multiple files
- Testing requires real API calls (expensive)
- No way to A/B test providers

---

## The Solution: Strategy Pattern

Abstract the "what" (analyze image → get tags) from the "how" (OpenAI vs Google vs Mock).

**Core idea:** Define a common interface, implement it multiple ways, switch via configuration.

### The Interface

```python
# app/services/ai/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class AITag:
    """AI-generated tag with confidence score."""
    name: str              # Tag name (lowercase, normalized)
    confidence: int        # Confidence 0-100
    category: str | None   # Optional category (object, scene, color)


class AITaggingProvider(ABC):
    """Abstract base for AI vision providers."""

    @abstractmethod
    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        """
        Analyze image and return tag suggestions.

        Args:
            image_bytes: Raw image data (JPEG/PNG)

        Returns:
            List of AI-generated tags with confidence scores

        Raises:
            AIProviderError: If provider fails
        """
        pass
```

**Why this works:**
- ✅ Single responsibility: Each provider implements one interface
- ✅ Open/closed: Add new providers without changing existing code
- ✅ Dependency inversion: Code depends on abstraction, not concrete providers

---

## Three Implementations

### 1. MockAIProvider (Free, Testing)

```python
# app/services/ai/mock_provider.py

class MockAIProvider(AITaggingProvider):
    """Returns predictable fake tags for testing."""

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        """Return mock tags without calling any API."""
        return [
            AITag(name="mock-object", confidence=99, category="object"),
            AITag(name="mock-scene", confidence=85, category="scene"),
            AITag(name="mock-color", confidence=75, category="color"),
        ]
```

**Use case:** Local dev, CI/CD, unit tests
**Cost:** $0
**Speed:** Instant

### 2. OpenAIVisionProvider (Production)

```python
# app/services/ai/openai_vision.py

class OpenAIVisionProvider(AITaggingProvider):
    """OpenAI Vision API provider using gpt-4o-mini."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", max_tags: int = 5):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_tags = max_tags
        self.prompt = (
            f"Analyze this image and provide {max_tags} descriptive tags. "
            "Return only tag names separated by commas, no explanations."
        )

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        """Call OpenAI Vision API."""
        # Encode to base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # Call API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": self.prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                            "detail": "low"  # Cost optimization
                        }
                    }
                ]
            }],
            max_tokens=150  # Limit response length
        )

        # Parse response
        tags_text = response.choices[0].message.content
        tag_names = [tag.strip().lower() for tag in tags_text.split(",")]

        # Convert to AITag objects
        return [
            AITag(name=name, confidence=90, category=None)
            for name in tag_names[:self.max_tags]
        ]
```

**Use case:** Production tagging
**Cost:** ~$0.004/image
**Speed:** ~2-3 seconds

### 3. GoogleVisionProvider (Future)

```python
# app/services/ai/google_vision.py

class GoogleVisionProvider(AITaggingProvider):
    """Google Cloud Vision API provider (Phase 7)."""

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        # TODO: 62% cheaper ($0.0015/image vs $0.004)
        pass
```

---

## The Factory: Configuration-Driven Switching

```python
# app/services/ai/__init__.py

def create_ai_provider(settings: Settings) -> AITaggingProvider:
    """
    Create AI provider based on configuration.

    Environment variable AI_PROVIDER controls which implementation:
    - "mock" → MockAIProvider (free, testing)
    - "openai" → OpenAIVisionProvider (production)
    - "google" → GoogleVisionProvider (future)
    """
    if settings.ai_provider == "mock":
        return MockAIProvider()

    if settings.ai_provider == "openai":
        if not settings.openai_api_key:
            raise AIProviderError("OPENAI_API_KEY not configured")

        return OpenAIVisionProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_vision_model,
            max_tags=settings.ai_max_tags_per_image,
        )

    if settings.ai_provider == "google":
        if not settings.google_vision_api_key:
            raise AIProviderError("GOOGLE_VISION_API_KEY not configured")

        return GoogleVisionProvider(
            api_key=settings.google_vision_api_key,
            max_tags=settings.ai_max_tags_per_image,
        )

    raise ValueError(f"Unknown AI provider: {settings.ai_provider}")
```

---

## Usage: One Line Everywhere

**Configuration (.env):**

```bash
# Development (free, instant)
AI_PROVIDER=mock

# Production (real tags, costs money)
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-abc123...
AI_MAX_TAGS_PER_IMAGE=5
OPENAI_VISION_MODEL=gpt-4o-mini

# Future (cost optimization)
AI_PROVIDER=google
GOOGLE_VISION_API_KEY=...
```

**Application code (same everywhere):**

```python
# Factory handles the decision
provider = create_ai_provider(settings)
tags = await provider.analyze_image(image_bytes)

# Works with mock, OpenAI, Google - zero code changes
```

**Benefits:**
- ✅ Change provider = change env var (no deploy needed)
- ✅ Test with mock provider (free, no API costs)
- ✅ Switch to cheaper provider later (easy cost optimization)
- ✅ A/B test providers (run both, compare results)

---

## Key Takeaway

**Abstract early to avoid vendor lock-in.**

The Strategy pattern costs 30 minutes upfront to design the interface, but saves hours later:
- Adding Google Vision = implement interface, update factory (20 minutes)
- Testing without API calls = use MockAIProvider (instant)
- Switching providers in production = change environment variable (2 seconds)

**Next:** [Part 2 - Manual→Automatic Evolution](04b-ai-vision-part2-manual-to-automatic.md) covers why we started with a manual `/ai-tag` endpoint (Phase 5) before going automatic with Celery (Phase 6).

---

## Related Resources

**This Series:**
- Part 2 - Manual→Automatic Evolution (next)
- Part 3 - Deployment Debugging & Storage Factory (coming soon)

**External:**
- [Strategy Pattern - Refactoring Guru](https://refactoring.guru/design-patterns/strategy)
- [OpenAI Vision API Docs](https://platform.openai.com/docs/guides/vision)

---

**Live Demo:** https://chitram.io
**Source Code:** https://github.com/abhi10/chitram

**License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
