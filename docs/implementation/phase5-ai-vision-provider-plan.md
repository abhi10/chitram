# Phase 5: AI Vision Provider Integration - Implementation Plan

**Status:** 🚧 In Progress
**GitHub Issue:** https://github.com/abhi10/chitram/issues/53
**Started:** 2026-01-10
**Target Completion:** 2026-01-17 (1 week)

---

## Overview

Implement AI vision providers using Strategy pattern to analyze images and suggest tags automatically. Phase 5 focuses on the **provider abstraction layer only** - actual background tagging will be Phase 6.

## Goals

1. Create pluggable AI provider architecture (Strategy pattern)
2. Implement OpenAI Vision provider for production use
3. Implement Mock provider for testing (no API costs)
4. Zero database changes (reuse existing tag schema)
5. Cost control: max 10 tags per image

## Non-Goals (Deferred to Phase 6)

- ❌ Automatic background tagging on upload
- ❌ Tagging status tracking in database
- ❌ Retry logic for failed tagging
- ❌ User-facing tagging progress UI

---

## Architecture

### Strategy Pattern

```
AITaggingProvider (ABC)
├── OpenAIVisionProvider (production)
├── GoogleVisionProvider (optional alternative)
└── MockAIProvider (testing/development)

create_ai_provider(settings) → Returns correct provider
```

### Data Flow

```
Image bytes → AI Provider → List[AITag] → TagService → Database
                                ↓
                        AITag(name, confidence, category)
```

### No Database Changes Required ✅

Phase 1 already created the schema we need:
- `tags` table - stores tag definitions
- `image_tags` table - links images to tags
- `source` column - 'user' vs 'ai'
- `confidence` column - 0-100 score

---

## Implementation Batches

### Batch 1: Abstract Provider & Data Models (30 min)
**Commit:** "feat: add AI provider abstract base and data models"

**Files:**
- `backend/app/services/ai/__init__.py` (empty, marks as package)
- `backend/app/services/ai/base.py` (abstract provider + AITag)

**Code:**
```python
# app/services/ai/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class AITag:
    """AI-generated tag suggestion."""
    name: str
    confidence: int  # 0-100
    category: str | None = None

class AITaggingProvider(ABC):
    """Abstract base for AI vision providers."""

    @abstractmethod
    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        """
        Analyze image and return tag suggestions.

        Args:
            image_bytes: Raw image data (JPEG/PNG)

        Returns:
            List of AITag objects with confidence scores

        Raises:
            AIProviderError: If analysis fails
        """
        pass

class AIProviderError(Exception):
    """Raised when AI provider fails to analyze image."""
    pass
```

**Acceptance:**
- [ ] `app/services/ai/` package created
- [ ] `AITag` dataclass defined
- [ ] `AITaggingProvider` abstract base defined
- [ ] Type hints complete
- [ ] Docstrings added

---

### Batch 2: Mock Provider for Testing (20 min)
**Commit:** "feat: add mock AI provider for testing"

**Files:**
- `backend/app/services/ai/mock.py`

**Code:**
```python
# app/services/ai/mock.py
"""Mock AI provider for testing without API costs."""
from .base import AITag, AITaggingProvider

class MockAIProvider(AITaggingProvider):
    """Returns predictable fake tags for testing."""

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        """
        Return mock tags without calling any API.

        Always returns the same 3 tags for consistency in tests.
        """
        return [
            AITag(name="mock-object", confidence=95, category="object"),
            AITag(name="mock-scene", confidence=85, category="scene"),
            AITag(name="mock-color", confidence=75, category="color"),
        ]
```

**Acceptance:**
- [ ] MockAIProvider implements abstract base
- [ ] Returns predictable tags (no randomness)
- [ ] No external dependencies
- [ ] Async method signature

---

### Batch 3: Configuration & Factory (30 min)
**Commit:** "feat: add AI provider configuration and factory"

**Files:**
- `backend/app/config.py` (update)
- `backend/app/services/ai/__init__.py` (update with factory)

**Code:**
```python
# app/config.py additions
class Settings(BaseSettings):
    # ... existing settings ...

    # AI Tagging Configuration
    ai_provider: str = "mock"  # 'openai', 'google', 'mock'
    ai_confidence_threshold: int = 70  # Filter tags below this
    ai_max_tags_per_image: int = 10  # Cost control

    # OpenAI Vision settings
    openai_api_key: str | None = None
    openai_vision_model: str = "gpt-4o-mini"  # Cheaper alternative
    openai_vision_prompt: str = "Generate 10 descriptive tags for this image. Return only tag names separated by commas, no explanations."

    # Google Cloud Vision settings (optional)
    google_vision_api_key: str | None = None

# app/services/ai/__init__.py
"""AI provider factory and exports."""
from app.config import Settings
from .base import AITag, AITaggingProvider, AIProviderError
from .mock import MockAIProvider

def create_ai_provider(settings: Settings) -> AITaggingProvider:
    """
    Create AI provider based on configuration.

    Args:
        settings: Application settings

    Returns:
        Configured AI provider instance

    Raises:
        ValueError: If provider type is unknown
        AIProviderError: If provider initialization fails
    """
    if settings.ai_provider == "mock":
        return MockAIProvider()

    if settings.ai_provider == "openai":
        if not settings.openai_api_key:
            raise AIProviderError("OpenAI API key not configured")
        from .openai_vision import OpenAIVisionProvider
        return OpenAIVisionProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_vision_model,
            prompt=settings.openai_vision_prompt,
            max_tags=settings.ai_max_tags_per_image,
        )

    if settings.ai_provider == "google":
        if not settings.google_vision_api_key:
            raise AIProviderError("Google Vision API key not configured")
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
```

**Acceptance:**
- [ ] Settings added to config.py
- [ ] Factory function implemented
- [ ] Raises clear errors for missing config
- [ ] Exports all public interfaces
- [ ] AI_MAX_TAGS_PER_IMAGE defaults to 10

---

### Batch 4: Unit Tests for Mock Provider (30 min)
**Commit:** "test: add unit tests for mock AI provider"

**Files:**
- `backend/tests/unit/test_ai_providers.py`

**Code:**
```python
# tests/unit/test_ai_providers.py
"""Unit tests for AI providers."""
import pytest
from app.services.ai import (
    AITag,
    AITaggingProvider,
    AIProviderError,
    MockAIProvider,
    create_ai_provider,
)
from app.config import Settings

class TestAITag:
    """Tests for AITag dataclass."""

    def test_aitag_creation(self):
        """AITag can be created with required fields."""
        tag = AITag(name="test", confidence=95)
        assert tag.name == "test"
        assert tag.confidence == 95
        assert tag.category is None

    def test_aitag_with_category(self):
        """AITag can include optional category."""
        tag = AITag(name="test", confidence=85, category="object")
        assert tag.category == "object"

class TestMockAIProvider:
    """Tests for MockAIProvider."""

    @pytest.mark.asyncio
    async def test_returns_predictable_tags(self):
        """Mock provider returns same tags every time."""
        provider = MockAIProvider()

        tags1 = await provider.analyze_image(b"fake-bytes-1")
        tags2 = await provider.analyze_image(b"fake-bytes-2")

        assert len(tags1) == 3
        assert len(tags2) == 3
        assert tags1[0].name == tags2[0].name
        assert tags1[0].confidence == tags2[0].confidence

    @pytest.mark.asyncio
    async def test_returns_aitag_objects(self):
        """Mock provider returns valid AITag objects."""
        provider = MockAIProvider()
        tags = await provider.analyze_image(b"fake")

        assert all(isinstance(tag, AITag) for tag in tags)
        assert all(0 <= tag.confidence <= 100 for tag in tags)
        assert all(isinstance(tag.name, str) for tag in tags)

    @pytest.mark.asyncio
    async def test_implements_abstract_base(self):
        """MockAIProvider implements AITaggingProvider."""
        provider = MockAIProvider()
        assert isinstance(provider, AITaggingProvider)

class TestAIProviderFactory:
    """Tests for create_ai_provider factory function."""

    def test_creates_mock_provider(self):
        """Factory creates mock provider when configured."""
        settings = Settings(ai_provider="mock")
        provider = create_ai_provider(settings)

        assert isinstance(provider, MockAIProvider)

    def test_raises_for_unknown_provider(self):
        """Factory raises ValueError for unknown provider."""
        settings = Settings(ai_provider="unknown")

        with pytest.raises(ValueError, match="Unknown AI provider"):
            create_ai_provider(settings)

    def test_raises_for_missing_openai_key(self):
        """Factory raises error if OpenAI key not configured."""
        settings = Settings(ai_provider="openai", openai_api_key=None)

        with pytest.raises(AIProviderError, match="OpenAI API key"):
            create_ai_provider(settings)

    def test_raises_for_missing_google_key(self):
        """Factory raises error if Google key not configured."""
        settings = Settings(ai_provider="google", google_vision_api_key=None)

        with pytest.raises(AIProviderError, match="Google Vision API key"):
            create_ai_provider(settings)
```

**Acceptance:**
- [ ] All mock provider tests pass
- [ ] Factory function tests pass
- [ ] Error handling tested
- [ ] Test coverage > 90%

---

### Batch 5: OpenAI Vision Provider (45 min)
**Commit:** "feat: add OpenAI Vision provider for production use"

**Files:**
- `backend/app/services/ai/openai_vision.py`
- `backend/pyproject.toml` (add openai dependency)

**Dependencies:**
```toml
# pyproject.toml additions
[project]
dependencies = [
    # ... existing ...
    "openai>=1.50.0",  # Async support
]
```

**Code:**
```python
# app/services/ai/openai_vision.py
"""OpenAI Vision API provider for image tagging."""
import base64
import logging
from openai import AsyncOpenAI, OpenAIError

from .base import AITag, AITaggingProvider, AIProviderError

logger = logging.getLogger(__name__)

class OpenAIVisionProvider(AITaggingProvider):
    """
    OpenAI Vision API provider.

    Uses gpt-4o-mini by default for cost efficiency (~$0.004/image).
    Cost control: limits to max_tags per image.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        prompt: str = "Generate 10 descriptive tags for this image. Return only tag names separated by commas.",
        max_tags: int = 10,
    ):
        """
        Initialize OpenAI Vision provider.

        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-4o-mini recommended for cost)
            prompt: System prompt for tag generation
            max_tags: Maximum tags to return (cost control)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.prompt = prompt
        self.max_tags = max_tags

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        """
        Analyze image using OpenAI Vision API.

        Args:
            image_bytes: Raw image data (JPEG/PNG)

        Returns:
            List of AITag objects with confidence scores

        Raises:
            AIProviderError: If API call fails
        """
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

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
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=150,  # Limit response length
            )

            # Parse response
            tags_text = response.choices[0].message.content
            if not tags_text:
                logger.warning("OpenAI returned empty response")
                return []

            # Split by comma and clean
            tag_names = [
                tag.strip().lower()
                for tag in tags_text.split(",")
                if tag.strip()
            ]

            # Convert to AITag objects
            # Note: OpenAI doesn't provide confidence scores, so we use 90
            tags = [
                AITag(name=name, confidence=90, category=None)
                for name in tag_names[: self.max_tags]
            ]

            logger.info(f"OpenAI Vision returned {len(tags)} tags")
            return tags

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise AIProviderError(f"OpenAI Vision failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI provider: {e}")
            raise AIProviderError(f"Failed to analyze image: {e}") from e
```

**Acceptance:**
- [ ] OpenAI dependency added to pyproject.toml
- [ ] Provider implements abstract base
- [ ] Image encoded to base64
- [ ] API response parsed correctly
- [ ] Max tags enforced (cost control)
- [ ] Errors handled and logged
- [ ] Async implementation

---

### Batch 6: Integration Tests (Manual) (30 min)
**Commit:** "test: add integration tests for AI providers"

**Files:**
- `backend/tests/integration/test_ai_vision.py`

**Code:**
```python
# tests/integration/test_ai_vision.py
"""Integration tests for AI vision providers.

These tests call real APIs and cost money!
Only run with: pytest -m manual
"""
import os
import pytest
from app.services.ai import create_ai_provider, AIProviderError
from app.config import Settings

pytestmark = pytest.mark.manual  # Skip by default

class TestOpenAIVisionIntegration:
    """Integration tests for OpenAI Vision provider."""

    @pytest.mark.asyncio
    async def test_openai_analyzes_real_image(self, sample_jpeg_bytes):
        """
        Test OpenAI Vision with real API call.

        IMPORTANT: This test costs ~$0.004 per run!
        Requires OPENAI_API_KEY environment variable.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        settings = Settings(
            ai_provider="openai",
            openai_api_key=api_key,
            ai_max_tags_per_image=10,
        )

        provider = create_ai_provider(settings)
        tags = await provider.analyze_image(sample_jpeg_bytes)

        # Assertions
        assert len(tags) > 0, "Should return at least one tag"
        assert len(tags) <= 10, "Should respect max_tags limit"
        assert all(0 <= tag.confidence <= 100 for tag in tags)
        assert all(isinstance(tag.name, str) for tag in tags)
        assert all(tag.name == tag.name.lower() for tag in tags), "Tags should be lowercase"

        # Print tags for manual verification
        print(f"\nOpenAI returned {len(tags)} tags:")
        for tag in tags:
            print(f"  - {tag.name} ({tag.confidence}%)")

    @pytest.mark.asyncio
    async def test_openai_handles_invalid_api_key(self, sample_jpeg_bytes):
        """OpenAI provider raises error for invalid API key."""
        settings = Settings(
            ai_provider="openai",
            openai_api_key="invalid-key-12345",
        )

        provider = create_ai_provider(settings)

        with pytest.raises(AIProviderError):
            await provider.analyze_image(sample_jpeg_bytes)

# Run with: uv run pytest tests/integration/test_ai_vision.py -m manual -v
```

**Acceptance:**
- [ ] Integration test written
- [ ] Marked with `@pytest.mark.manual`
- [ ] Requires environment variable
- [ ] Tests real API behavior
- [ ] Prints results for verification
- [ ] Tests error handling

---

### Batch 7: Documentation (20 min)
**Commit:** "docs: add Phase 5 implementation summary"

**Files:**
- `docs/implementation/phase5-implementation-summary.md`

**Content:** Summary of implementation, design decisions, testing strategy, cost analysis

**Acceptance:**
- [ ] Implementation documented
- [ ] Cost analysis included
- [ ] Testing guide provided
- [ ] Examples added

---

## Cost Control Strategy

### API Limits
- ✅ `AI_MAX_TAGS_PER_IMAGE = 10` (hardcoded in config)
- ✅ OpenAI: ~$0.004 per image (gpt-4o-mini)
- ✅ Monthly budget: $50 = ~12,500 images

### Cost Monitoring
```bash
# Production .env
AI_PROVIDER=openai
AI_MAX_TAGS_PER_IMAGE=10
OPENAI_API_KEY=sk-proj-...
OPENAI_VISION_MODEL=gpt-4o-mini  # Cheaper than gpt-4-vision
```

### Testing Strategy (No Cost)
```bash
# Development/Testing .env
AI_PROVIDER=mock  # Free!
AI_MAX_TAGS_PER_IMAGE=10
```

---

## Testing Strategy

### Unit Tests (Free, Always Run)
```bash
# Run all unit tests (no API calls)
uv run pytest tests/unit/test_ai_providers.py -v
```

**Coverage:**
- ✅ Mock provider behavior
- ✅ Factory function logic
- ✅ Configuration validation
- ✅ Error handling

### Integration Tests (Costs Money, Manual)
```bash
# Set API key
export OPENAI_API_KEY=sk-proj-...

# Run manual tests only
uv run pytest -m manual -v

# Expected cost: ~$0.004 per test run
```

**Coverage:**
- ✅ Real OpenAI API calls
- ✅ Image encoding/decoding
- ✅ Response parsing
- ✅ Error scenarios

### Production Testing (Staged Rollout)
1. **Stage 1:** Deploy with `AI_PROVIDER=mock` (verify deployment)
2. **Stage 2:** Switch to `AI_PROVIDER=openai` (monitor costs)
3. **Stage 3:** Enable for all users (full rollout)

---

## Success Criteria

Phase 5 is complete when:

- [ ] All 7 batches committed to git
- [ ] All unit tests passing (no API keys needed)
- [ ] Integration test passes manually (verified once)
- [ ] Mock provider works for free testing
- [ ] OpenAI provider works with real API
- [ ] Factory function selects correct provider
- [ ] Configuration documented in README
- [ ] Cost control enforced (max 10 tags)
- [ ] Error handling comprehensive
- [ ] GitHub issue #53 updated with progress

---

## Rollout Plan

### Development
```bash
AI_PROVIDER=mock  # Free testing
```

### Staging/Testing
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-test-...  # Test key with low limits
AI_MAX_TAGS_PER_IMAGE=5  # Extra caution
```

### Production
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...  # Production key
AI_MAX_TAGS_PER_IMAGE=10
OPENAI_VISION_MODEL=gpt-4o-mini  # Cost efficient
```

---

## GitHub Issue Mapping

**Issue:** https://github.com/abhi10/chitram/issues/53

**Checklist Updates:**
- [ ] Batch 1-2: Abstract provider + Mock ✅
- [ ] Batch 3: Configuration + Factory ✅
- [ ] Batch 4: Unit tests ✅
- [ ] Batch 5: OpenAI provider ✅
- [ ] Batch 6: Integration tests ✅
- [ ] Batch 7: Documentation ✅

**Commit Message Pattern:**
```
<type>: <description> (#53)

- Detail 1
- Detail 2

Relates to: https://github.com/abhi10/chitram/issues/53
Part of Phase 5: AI Vision Provider Integration

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## Timeline

| Batch | Task | Est. Time | Cumulative |
|-------|------|-----------|------------|
| 1 | Abstract provider | 30 min | 30 min |
| 2 | Mock provider | 20 min | 50 min |
| 3 | Config + Factory | 30 min | 80 min |
| 4 | Unit tests | 30 min | 110 min |
| 5 | OpenAI provider | 45 min | 155 min |
| 6 | Integration tests | 30 min | 185 min |
| 7 | Documentation | 20 min | **205 min** |

**Total: ~3.5 hours of focused work**

---

## Next Steps After Phase 5

Phase 5 provides the **AI provider abstraction** but doesn't automatically tag images yet.

**Phase 6 will add:**
- Background tagging on upload (using Phase 5 providers)
- Tagging status tracking (`tagging_status` column)
- Retry logic for failures
- Integration with upload workflow

**For now, we can:**
- Manually call provider to test
- Use in admin tools
- Prepare for Phase 6 integration

---

**Ready to begin? Start with Batch 1!**
