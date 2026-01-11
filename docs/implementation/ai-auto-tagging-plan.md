# AI Auto-Tagging Implementation Plan

**Feature Branch:** `feat/ai-auto-tagging`
**PRD Reference:** [PRD-search-and-ai-tagging.md](../future/PRD-search-and-ai-tagging.md)
**Date:** 2026-01-10

---

## Overview

This document outlines the phased implementation approach for the AI Auto-Tagging feature. We build the tagging infrastructure first, then integrate AI providers.

## Implementation Phases

### Phase 1: Database Schema & Models (Foundation)
**Priority: Must Have | Estimated Effort: Small**

Create the database tables and SQLAlchemy models for tags.

#### 1.1 Alembic Migration

Create new tables:

```sql
-- Tags table (normalized, global)
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    category VARCHAR(20),  -- 'object', 'scene', 'color', 'attribute'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_tags_category ON tags(category);

-- Image-Tag junction table
CREATE TABLE image_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id UUID NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    source VARCHAR(10) NOT NULL,  -- 'ai' or 'user'
    confidence INTEGER,  -- 0-100 for AI tags, NULL for user tags
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(image_id, tag_id)
);
CREATE INDEX idx_image_tags_image ON image_tags(image_id);
CREATE INDEX idx_image_tags_tag ON image_tags(tag_id);

-- Tag feedback for AI improvement (future)
CREATE TABLE tag_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id UUID NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    feedback_type VARCHAR(10) NOT NULL,  -- 'removed', 'added'
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 1.2 SQLAlchemy Models

```python
# app/models/tag.py
class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Relationships
    image_tags: Mapped[list["ImageTag"]] = relationship(back_populates="tag")

class ImageTag(Base):
    __tablename__ = "image_tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    image_id: Mapped[str] = mapped_column(ForeignKey("images.id", ondelete="CASCADE"))
    tag_id: Mapped[str] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(10))  # 'ai' or 'user'
    confidence: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Relationships
    image: Mapped["Image"] = relationship(back_populates="image_tags")
    tag: Mapped["Tag"] = relationship(back_populates="image_tags")
```

#### 1.3 Deliverables
- [ ] Alembic migration file
- [ ] `app/models/tag.py` with Tag and ImageTag models
- [ ] Update `app/models/__init__.py` exports
- [ ] Unit tests for model relationships

---

### Phase 2: Tag Service (Business Logic)
**Priority: Must Have | Estimated Effort: Medium**

Implement core tag operations.

#### 2.1 Pydantic Schemas

```python
# app/schemas/tag.py
class TagBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    category: str | None = None

class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime

class ImageTagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    category: str | None
    source: str  # 'ai' or 'user'
    confidence: int | None

class AddTagRequest(BaseModel):
    tag: str = Field(..., min_length=2, max_length=50)
```

#### 2.2 Tag Service

```python
# app/services/tag_service.py
class TagService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_tag(self, name: str, category: str | None = None) -> Tag:
        """Get existing tag or create new one."""

    async def add_tag_to_image(
        self,
        image_id: str,
        tag_name: str,
        source: str = "user",
        confidence: int | None = None
    ) -> ImageTag:
        """Add a tag to an image."""

    async def remove_tag_from_image(self, image_id: str, tag_name: str) -> bool:
        """Remove a tag from an image."""

    async def get_image_tags(self, image_id: str) -> list[ImageTagResponse]:
        """Get all tags for an image."""

    async def get_popular_tags(self, limit: int = 20) -> list[TagWithCount]:
        """Get most used tags."""

    async def search_tags(self, query: str, limit: int = 10) -> list[Tag]:
        """Search tags by prefix for autocomplete."""
```

#### 2.3 Deliverables
- [ ] `app/schemas/tag.py`
- [ ] `app/services/tag_service.py`
- [ ] Unit tests for TagService
- [ ] Tag name validation (lowercase, alphanumeric + spaces/hyphens)

---

### Phase 3: Tag API Endpoints
**Priority: Must Have | Estimated Effort: Medium**

REST API for tag management.

#### 3.1 Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/images/{id}/tags` | Get tags for an image |
| POST | `/api/v1/images/{id}/tags` | Add tag to image (owner only) |
| DELETE | `/api/v1/images/{id}/tags/{tag}` | Remove tag (owner only) |
| GET | `/api/v1/tags` | List all tags |
| GET | `/api/v1/tags/popular` | Get popular tags |
| GET | `/api/v1/tags/search?q={query}` | Search tags (autocomplete) |

#### 3.2 Router Implementation

```python
# app/api/tags.py
router = APIRouter(prefix="/api/v1", tags=["tags"])

@router.get("/images/{image_id}/tags")
async def get_image_tags(image_id: str, ...) -> list[ImageTagResponse]:
    """Get all tags for an image."""

@router.post("/images/{image_id}/tags", status_code=201)
async def add_tag(
    image_id: str,
    request: AddTagRequest,
    current_user: User = Depends(get_current_user),
    ...
) -> ImageTagResponse:
    """Add a tag to an image (owner only)."""

@router.delete("/images/{image_id}/tags/{tag_name}")
async def remove_tag(
    image_id: str,
    tag_name: str,
    current_user: User = Depends(get_current_user),
    ...
) -> dict:
    """Remove a tag from an image (owner only)."""

@router.get("/tags")
async def list_tags(limit: int = 100, ...) -> list[TagResponse]:
    """List all tags."""

@router.get("/tags/popular")
async def get_popular_tags(limit: int = 20, ...) -> list[TagWithCount]:
    """Get most popular tags by usage count."""

@router.get("/tags/search")
async def search_tags(q: str, limit: int = 10, ...) -> list[TagResponse]:
    """Search tags for autocomplete."""
```

#### 3.3 Deliverables
- [ ] `app/api/tags.py` router
- [ ] Register router in `main.py`
- [ ] API integration tests
- [ ] OpenAPI documentation verified

---

### Phase 4: UI - Tag Display & Manual Tagging
**Priority: Must Have | Estimated Effort: Medium**

Add tag UI to image detail page.

#### 4.1 Image Detail Page Updates

```html
<!-- Tags Section on image detail -->
<div class="tags-section">
    <h3>Tags</h3>

    <!-- Existing tags -->
    <div class="tag-list">
        {% for tag in image.tags %}
        <span class="tag {{ tag.source }}">
            {% if tag.source == 'ai' %}✨{% else %}👤{% endif %}
            {{ tag.name }}
            {% if tag.confidence %}({{ tag.confidence }}%){% endif %}
            {% if is_owner %}
            <button onclick="removeTag('{{ tag.name }}')" class="remove-tag">×</button>
            {% endif %}
        </span>
        {% endfor %}
    </div>

    <!-- Add tag input (owner only) -->
    {% if is_owner %}
    <div class="add-tag">
        <input type="text" id="new-tag" placeholder="Add a tag..." autocomplete="off">
        <div id="tag-suggestions" class="suggestions hidden"></div>
        <button onclick="addTag()">Add</button>
    </div>
    {% endif %}
</div>
```

#### 4.2 JavaScript for Tag Operations

```javascript
async function addTag() {
    const tagInput = document.getElementById('new-tag');
    const tagName = tagInput.value.trim().toLowerCase();

    const response = await fetch(`/api/v1/images/${imageId}/tags`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tag: tagName })
    });

    if (response.ok) {
        location.reload(); // or update DOM dynamically
    }
}

async function removeTag(tagName) {
    const response = await fetch(`/api/v1/images/${imageId}/tags/${tagName}`, {
        method: 'DELETE'
    });

    if (response.ok) {
        location.reload();
    }
}

// Autocomplete for tag suggestions
async function onTagInput(query) {
    if (query.length < 2) return;

    const response = await fetch(`/api/v1/tags/search?q=${query}`);
    const tags = await response.json();
    showSuggestions(tags);
}
```

#### 4.3 Deliverables
- [ ] Update `image_detail.html` template
- [ ] Tag display styling (CSS)
- [ ] Add/remove tag JavaScript
- [ ] Autocomplete functionality
- [ ] E2E test for manual tagging

---

### Phase 5: AI Provider Integration
**Priority: Must Have | Estimated Effort: Large**

Choose and integrate an AI vision provider.

#### 5.0 Provider Options Comparison

| Provider | Type | Cost | Hardware Req | Accuracy | Latency |
|----------|------|------|--------------|----------|---------|
| **Moondream2** | Local | Free | 4GB RAM, CPU | Good | ~2-5s |
| **SmolVLM2** | Local | Free | 2GB RAM, CPU | Good | ~1-3s |
| **Qwen2.5-VL (7B)** | Local | Free | 8GB+ VRAM | Excellent | ~3-8s |
| **LLaVA (7B)** | Local | Free | 8GB+ VRAM | Excellent | ~3-8s |
| **Google Cloud Vision** | Cloud | $1.50/1K | None | Excellent | ~500ms |
| **LandingLens** | Cloud | Contact | None | Excellent | ~500ms |

##### Local Models (Recommended for Portfolio/Learning)

**Moondream2** - Best for CPU-only deployment
- 1.86B parameters, runs on CPU
- Good for: captions, object detection, OCR
- GitHub: [vikhyat/moondream](https://github.com/vikhyat/moondream)
- HuggingFace: [vikhyatk/moondream2](https://huggingface.co/vikhyatk/moondream2)

**SmolVLM2** - Smallest model
- 256M-2.2B parameters
- Ideal for edge/mobile deployment
- Best if you want minimal resource usage

**Qwen2.5-VL / LLaVA** - Best accuracy
- Requires GPU (8GB+ VRAM)
- Superior document understanding
- Best for production quality

##### Cloud APIs

**Google Cloud Vision** - Most mature
- $1.50 per 1,000 images (label detection)
- First 1,000 units/month FREE
- $300 free credits for new accounts
- [Pricing](https://cloud.google.com/vision/pricing)

**LandingLens** - Enterprise focused
- Custom model training
- Contact for pricing
- [SDK Docs](https://docs.landing.ai/landinglens/sdk)

##### Recommendation

For this project (portfolio + learning):
1. **Start with Moondream2** - Free, runs locally, good enough for tagging
2. **Add Google Vision as fallback** - Use free tier for comparison/backup
3. **Strategy pattern** allows switching providers easily

#### 5.1 Provider Abstraction (Strategy Pattern)

```python
# app/services/ai/base.py
class AITaggingProvider(ABC):
    @abstractmethod
    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        """Analyze image and return tags with confidence scores."""

@dataclass
class AITag:
    name: str
    category: str  # 'object', 'scene', 'color', 'attribute'
    confidence: int  # 0-100

# app/services/ai/moondream_provider.py
class MoondreamProvider(AITaggingProvider):
    """Local Vision LLM - runs on CPU, no API costs."""

    def __init__(self, model_path: str | None = None):
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_id = model_path or "vikhyatk/moondream2"
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, trust_remote_code=True
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        from PIL import Image
        import io

        image = Image.open(io.BytesIO(image_bytes))

        # Prompt for tagging
        prompt = "List the main objects, scenes, and colors in this image as comma-separated tags."

        enc_image = self.model.encode_image(image)
        response = self.model.answer_question(enc_image, prompt, self.tokenizer)

        # Parse response into tags
        tags = self._parse_tags(response)
        return tags

    def _parse_tags(self, response: str) -> list[AITag]:
        """Convert model response to structured tags."""
        raw_tags = [t.strip().lower() for t in response.split(",")]
        return [
            AITag(name=tag, category=self._categorize(tag), confidence=80)
            for tag in raw_tags if len(tag) >= 2
        ]

# app/services/ai/google_vision.py
class GoogleVisionProvider(AITaggingProvider):
    """Google Cloud Vision API - fast, accurate, pay-per-use."""

    def __init__(self, api_key: str):
        from google.cloud import vision
        self.client = vision.ImageAnnotatorClient()

    async def analyze_image(self, image_bytes: bytes) -> list[AITag]:
        from google.cloud import vision

        image = vision.Image(content=image_bytes)
        response = self.client.label_detection(image=image)

        return [
            AITag(
                name=label.description.lower(),
                category="object",  # Google doesn't categorize
                confidence=int(label.score * 100)
            )
            for label in response.label_annotations
        ]

# app/services/ai/__init__.py
def create_ai_provider(settings: Settings) -> AITaggingProvider:
    if settings.ai_provider == "moondream":
        return MoondreamProvider()
    elif settings.ai_provider == "google":
        return GoogleVisionProvider(settings.google_vision_api_key)
    elif settings.ai_provider == "mock":
        return MockAIProvider()  # For testing
    raise ValueError(f"Unknown AI provider: {settings.ai_provider}")
```

#### 5.2 Configuration

```python
# app/config.py additions
class Settings(BaseSettings):
    # AI Tagging
    ai_provider: str = "mock"  # 'moondream', 'google', 'mock'
    ai_confidence_threshold: int = 70
    ai_max_tags_per_image: int = 10
    ai_rate_limit_per_minute: int = 60

    # Moondream (local) settings
    moondream_model_path: str | None = None  # Uses HuggingFace default if None

    # Google Cloud Vision settings
    google_vision_api_key: str | None = None
    google_application_credentials: str | None = None  # Path to service account JSON
```

#### 5.3 Dependencies

```toml
# pyproject.toml additions for AI providers

# For Moondream (local)
"transformers>=4.40.0",
"torch>=2.0.0",
"einops>=0.8.0",

# For Google Cloud Vision
"google-cloud-vision>=3.7.0",
```

**Note:** Moondream requires ~4GB disk space for model weights (downloaded on first use).

#### 5.4 Deliverables
- [ ] `app/services/ai/base.py` - Abstract provider + AITag dataclass
- [ ] `app/services/ai/moondream_provider.py` - Local VLM implementation
- [ ] `app/services/ai/google_vision.py` - Google implementation
- [ ] `app/services/ai/mock.py` - Mock for testing
- [ ] `app/services/ai/__init__.py` - Factory function
- [ ] Configuration in `config.py`
- [ ] Unit tests with mock provider
- [ ] Integration test with Moondream (local)
- [ ] Integration test with Google Vision (manual, uses free tier)

---

### Phase 6: Background Tagging on Upload
**Priority: Must Have | Estimated Effort: Medium**

Auto-tag images after upload.

#### 6.1 Tagging Service

```python
# app/services/ai_tagging_service.py
class AITaggingService:
    def __init__(
        self,
        db: AsyncSession,
        storage: StorageService,
        ai_provider: AITaggingProvider,
        tag_service: TagService
    ):
        self.db = db
        self.storage = storage
        self.ai_provider = ai_provider
        self.tag_service = tag_service

    async def tag_image(self, image_id: str) -> list[ImageTag]:
        """Fetch image, analyze with AI, save tags."""
        # 1. Get image from storage
        # 2. Call AI provider
        # 3. Filter by confidence threshold
        # 4. Save tags via TagService
        # 5. Update image.tagging_status
```

#### 6.2 Integration with Upload Flow

```python
# In image upload endpoint or service
async def upload_image(...):
    # ... existing upload logic ...

    # Trigger background tagging
    background_tasks.add_task(
        ai_tagging_service.tag_image,
        image.id
    )

    return image
```

#### 6.3 Image Model Updates

```python
# Add to Image model
class Image(Base):
    # ... existing fields ...
    tagging_status: Mapped[str] = mapped_column(
        String(20),
        default="pending"
    )  # 'pending', 'processing', 'completed', 'failed'
```

#### 6.4 Deliverables
- [ ] `app/services/ai_tagging_service.py`
- [ ] Migration for `tagging_status` column
- [ ] Background task integration
- [ ] Status endpoint for tagging progress
- [ ] Error handling and retry logic

---

### Phase 7: Search Implementation
**Priority: Should Have | Estimated Effort: Large**

PostgreSQL full-text search.

#### 7.1 Search Vector Migration

```sql
-- Add search vector to images table
ALTER TABLE images ADD COLUMN search_vector tsvector;
CREATE INDEX idx_images_search ON images USING GIN(search_vector);

-- Function to update search vector
CREATE OR REPLACE FUNCTION update_image_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.filename, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(
            (SELECT string_agg(t.name, ' ')
             FROM image_tags it
             JOIN tags t ON t.id = it.tag_id
             WHERE it.image_id = NEW.id), '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

#### 7.2 Search Service

```python
# app/services/search_service.py
class SearchService:
    async def search_images(
        self,
        query: str,
        user_id: str | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResults:
        """Full-text search across filenames and tags."""
```

#### 7.3 Search API

```python
@router.get("/api/v1/images/search")
async def search_images(
    q: str,
    tags: str | None = None,  # comma-separated
    limit: int = 20,
    offset: int = 0,
    ...
) -> SearchResults:
    """Search images by text query and/or tags."""
```

#### 7.4 Deliverables
- [ ] Search vector migration
- [ ] `app/services/search_service.py`
- [ ] Search API endpoint
- [ ] Search bar UI component
- [ ] Autocomplete suggestions
- [ ] Search results page

---

## Implementation Order

```
Phase 1 (Database) ──► Phase 2 (Service) ──► Phase 3 (API)
                                                  │
                                                  ▼
Phase 4 (UI) ◄────────────────────────────────────┘
     │
     ▼
Phase 5 (AI Provider) ──► Phase 6 (Background Tagging)
                                   │
                                   ▼
                          Phase 7 (Search)
```

## Dependencies

| Phase | Dependencies |
|-------|--------------|
| 1 | None |
| 2 | Phase 1 |
| 3 | Phase 2 |
| 4 | Phase 3 |
| 5 | None (parallel with 1-4) |
| 6 | Phases 2, 5 |
| 7 | Phase 6 |

## Testing Strategy

| Phase | Test Type | Coverage Target |
|-------|-----------|-----------------|
| 1 | Unit | Model relationships |
| 2 | Unit | TagService methods |
| 3 | API Integration | All endpoints |
| 4 | E2E (Browser) | Manual tagging flow |
| 5 | Unit + Integration | Mock + real API |
| 6 | Integration | Upload → tags flow |
| 7 | Integration | Search accuracy |

## Configuration Checklist

Before Phase 5 deployment:
- [ ] Google Cloud Vision API enabled
- [ ] API key created and stored securely
- [ ] Budget alerts configured ($50/month)
- [ ] Rate limiting configured
- [ ] Feature flag `enable_ai_tagging` ready

## Rollback Plan

Each phase can be rolled back independently:
- **Database**: Revert Alembic migration
- **Code**: Revert Git commits
- **Feature**: Disable via feature flag

---

## Getting Started

### Phase 1 First Steps

1. Create feature branch (done): `feat/ai-auto-tagging`
2. Generate Alembic migration:
   ```bash
   cd backend
   uv run alembic revision --autogenerate -m "add tags and image_tags tables"
   ```
3. Create `app/models/tag.py`
4. Update `app/models/__init__.py`
5. Run migration and tests

---

*Last Updated: 2026-01-10*
