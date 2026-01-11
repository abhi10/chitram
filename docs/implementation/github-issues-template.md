# GitHub Issues for AI Auto-Tagging

Create these issues in GitHub to track implementation progress.

**Milestone:** AI Auto-Tagging MVP
**Labels:** `enhancement`, `ai-tagging`

---

## Issue #1: Phase 1 - Database Schema & Models

**Title:** `Phase 1: Database Schema & Models for AI Auto-Tagging`

**Status:** ✅ **COMPLETED** (Close this issue immediately)

**Description:**

Create foundational database schema and SQLAlchemy models for AI auto-tagging feature.

### Objectives
- [x] Create tags table for normalized tag storage
- [x] Create image_tags junction table linking images to tags
- [x] Create tag_feedback table for future AI improvement
- [x] Add SQLAlchemy models with relationships
- [x] Write comprehensive unit tests

### Deliverables
- [x] `backend/alembic/versions/okr4l08scgm2_add_tags_image_tags_and_tag_feedback.py`
- [x] `backend/app/models/tag.py`
- [x] `backend/app/models/image.py` (updated with relationship)
- [x] `backend/tests/unit/test_tag_models.py`
- [x] Documentation: `docs/implementation/phase1-database-schema-summary.md`

### Results
- 11/11 unit tests passing
- 240/240 existing tests still passing (no regressions)
- Fully backward compatible
- Migration reversible

### Commits
- `06b416d` - feat: add Tag and ImageTag models with database schema (Phase 1)
- `9744c82` - docs: add Phase 1 implementation summary
- `e660781` - docs: add AI auto-tagging implementation plan

**Close this issue with:** "Closes #1" in next PR or commit message

---

## Issue #2: Phase 2 - Tag Service (Business Logic)

**Title:** `Phase 2: Tag Service - Business Logic Layer`

**Labels:** `enhancement`, `ai-tagging`, `in-progress`

**Description:**

Implement core tag operations and business logic.

### Objectives
- [ ] Create Pydantic schemas for tag API contracts
- [ ] Implement TagService with CRUD operations
- [ ] Add tag validation and normalization
- [ ] Write unit tests for all service methods

### Deliverables

**Code:**
- [ ] `backend/app/schemas/tag.py` - Pydantic schemas
- [ ] `backend/app/services/tag_service.py` - Business logic
- [ ] `backend/tests/unit/test_tag_service.py` - Unit tests

**Methods to Implement:**
- [ ] `get_or_create_tag(name, category)` - Idempotent tag creation
- [ ] `add_tag_to_image(image_id, tag_name, source, confidence)` - Link tag to image
- [ ] `remove_tag_from_image(image_id, tag_name)` - Unlink tag
- [ ] `get_image_tags(image_id)` - Fetch all tags for image
- [ ] `get_popular_tags(limit)` - Most used tags
- [ ] `search_tags(query, limit)` - Autocomplete search

### Acceptance Criteria
- [ ] All service methods have unit tests
- [ ] Tag names normalized (lowercase, trimmed)
- [ ] Handles duplicate tags gracefully (get_or_create pattern)
- [ ] Edge cases tested (empty strings, special characters, NULL)
- [ ] All existing tests still pass

### Implementation Notes
- Use `INSERT ... ON CONFLICT` for get_or_create pattern
- Normalize tag names: lowercase, strip whitespace
- Validation: 2-50 characters, alphanumeric + spaces/hyphens
- Category validation: 'object', 'scene', 'color', 'attribute', or NULL

### Dependencies
- Requires Phase 1 (database schema) ✅

---

## Issue #3: Phase 3 - Tag API Endpoints

**Title:** `Phase 3: REST API Endpoints for Tag Management`

**Labels:** `enhancement`, `ai-tagging`, `api`

**Description:**

Create REST API endpoints for tag operations.

### Objectives
- [ ] Create tags router with 6 endpoints
- [ ] Add authentication for owner-only operations
- [ ] Implement structured error responses
- [ ] Write API integration tests

### Deliverables

**Code:**
- [ ] `backend/app/api/tags.py` - FastAPI router
- [ ] `backend/app/main.py` (updated to register router)
- [ ] `backend/tests/api/test_tags.py` - API integration tests

**Endpoints:**
```
GET    /api/v1/images/{id}/tags           - Get tags for an image
POST   /api/v1/images/{id}/tags           - Add tag to image (owner only)
DELETE /api/v1/images/{id}/tags/{tag}     - Remove tag (owner only)
GET    /api/v1/tags                        - List all tags
GET    /api/v1/tags/popular                - Get popular tags
GET    /api/v1/tags/search?q={query}      - Search tags (autocomplete)
```

### Acceptance Criteria
- [ ] All endpoints return proper HTTP status codes
- [ ] Owner-only endpoints enforce authentication
- [ ] Errors use structured ErrorDetail format
- [ ] OpenAPI docs updated (`/docs` shows new endpoints)
- [ ] API tests cover success and error cases
- [ ] Rate limiting applied

### Implementation Notes
- Use existing `get_current_user` dependency for auth
- Return 403 if non-owner tries to add/remove tags
- Return 404 if image doesn't exist
- Return 400 if tag name invalid

### Dependencies
- Requires Phase 2 (Tag Service) ✅

---

## Issue #4: Phase 4 - UI for Manual Tagging

**Title:** `Phase 4: Web UI for Tag Display and Manual Tagging`

**Labels:** `enhancement`, `ai-tagging`, `frontend`

**Description:**

Add UI components for viewing and managing tags on images.

### Objectives
- [ ] Display tags on image detail page
- [ ] Add tag input with autocomplete
- [ ] Allow owners to add/remove tags
- [ ] Differentiate AI vs user tags visually

### Deliverables

**Code:**
- [ ] `backend/app/templates/image_detail.html` (updated)
- [ ] `backend/app/static/js/tags.js` (new)
- [ ] `backend/app/static/css/tags.css` (new)
- [ ] E2E test for manual tagging flow

**UI Components:**
- [ ] Tag display area (badges/chips)
- [ ] Tag input with autocomplete
- [ ] Add tag button
- [ ] Remove tag button (owner only)
- [ ] Visual distinction (✨ AI, 👤 user)

### Acceptance Criteria
- [ ] Tags display correctly on image detail page
- [ ] Autocomplete suggests existing tags
- [ ] Add tag works and updates UI
- [ ] Remove tag works and updates UI
- [ ] Non-owners cannot add/remove tags
- [ ] Mobile responsive
- [ ] Keyboard accessible (Enter to submit)

### Implementation Notes
- Use HTMX for dynamic updates (optional, or vanilla JS)
- Debounce autocomplete requests (300ms)
- Show confidence percentage for AI tags
- Limit display to 10 tags initially (show more button)

### Dependencies
- Requires Phase 3 (API endpoints) ✅

### Deployment
After Phase 4 completes, ready for production deployment!

---

## Issue #5: Phase 5 - AI Provider Integration

**Title:** `Phase 5: AI Vision Provider Integration (Strategy Pattern)`

**Labels:** `enhancement`, `ai-tagging`, `ai`, `good-first-ai-issue`

**Description:**

Implement AI vision providers using Strategy pattern.

### Objectives
- [ ] Create abstract AITaggingProvider base
- [ ] Implement GoogleVisionProvider
- [ ] Implement MockProvider for testing
- [ ] (Optional) Implement MoondreamProvider
- [ ] Add provider configuration

### Deliverables

**Code:**
- [ ] `backend/app/services/ai/base.py` - Abstract provider + AITag dataclass
- [ ] `backend/app/services/ai/google_vision.py` - Google implementation
- [ ] `backend/app/services/ai/mock.py` - Mock for testing
- [ ] `backend/app/services/ai/__init__.py` - Factory function
- [ ] `backend/app/config.py` (updated with AI settings)
- [ ] Unit tests with mock provider
- [ ] Integration test with Google Vision (manual)

**Configuration:**
```python
AI_PROVIDER = "google"  # or "moondream", "mock"
AI_CONFIDENCE_THRESHOLD = 70
AI_MAX_TAGS_PER_IMAGE = 10
GOOGLE_VISION_API_KEY = "<secret>"
```

### Acceptance Criteria
- [ ] Factory function returns correct provider based on config
- [ ] GoogleVisionProvider returns valid AITag objects
- [ ] MockProvider works for testing
- [ ] Provider can be swapped via environment variable
- [ ] Errors handled gracefully (API failures)

### Implementation Notes
- Use Strategy pattern (see plan)
- Google Vision free tier: 1,000 images/month
- Return top 10 tags with highest confidence
- Filter tags below confidence threshold

### Dependencies
- Requires Phase 2 (Tag Service) ✅
- Optional: Phases 1-4 for full feature

### Infrastructure
- **Google Vision:** No droplet upgrade needed ✅
- **Moondream:** Requires 8GB RAM droplet ($48/month)

---

## Issue #6: Phase 6 - Background Tagging on Upload

**Title:** `Phase 6: Automatic Background Tagging on Image Upload`

**Labels:** `enhancement`, `ai-tagging`, `background-tasks`

**Description:**

Automatically tag images using AI when uploaded.

### Objectives
- [ ] Create AITaggingService to orchestrate tagging
- [ ] Integrate with image upload flow
- [ ] Add tagging_status to Image model
- [ ] Implement retry logic for failures

### Deliverables

**Code:**
- [ ] `backend/app/services/ai_tagging_service.py`
- [ ] `backend/app/api/images.py` (updated upload endpoint)
- [ ] `backend/alembic/versions/xxx_add_tagging_status.py` (migration)
- [ ] Integration tests for background tagging

**Image Model Update:**
```python
tagging_status: Mapped[str] = mapped_column(
    String(20), default="pending"
)  # 'pending', 'processing', 'completed', 'failed'
```

### Acceptance Criteria
- [ ] AI tagging triggers on image upload
- [ ] Tagging runs in background (non-blocking)
- [ ] Tags saved with source='ai' and confidence scores
- [ ] Tagging status tracked in database
- [ ] Upload works even if AI fails (graceful degradation)
- [ ] Error handling and logging

### Implementation Notes
- Use FastAPI BackgroundTasks (like ThumbnailService)
- Run AI inference in thread pool (CPU-bound)
- Filter tags by confidence threshold
- Limit to max_tags_per_image
- Update tagging_status on completion/failure

### Dependencies
- Requires Phase 5 (AI Provider) ✅
- Requires Phase 2 (Tag Service) ✅

---

## Issue #7: Phase 7 - Full-Text Search (Optional)

**Title:** `Phase 7: PostgreSQL Full-Text Search for Images by Tags`

**Labels:** `enhancement`, `ai-tagging`, `search`, `nice-to-have`

**Description:**

Enable searching images by tags and filenames using PostgreSQL full-text search.

### Objectives
- [ ] Add search_vector column to images table
- [ ] Create trigger to update search vector
- [ ] Implement SearchService
- [ ] Add search API endpoint
- [ ] Add search UI

### Deliverables

**Code:**
- [ ] `backend/alembic/versions/xxx_add_search_vector.py`
- [ ] `backend/app/services/search_service.py`
- [ ] `backend/app/api/search.py` (or add to images.py)
- [ ] `backend/app/templates/search.html`
- [ ] Tests for search functionality

**SQL Changes:**
```sql
ALTER TABLE images ADD COLUMN search_vector tsvector;
CREATE INDEX idx_images_search ON images USING GIN(search_vector);
CREATE TRIGGER update_search_vector ...
```

### Acceptance Criteria
- [ ] Can search by tag names
- [ ] Can search by filename
- [ ] Results ranked by relevance
- [ ] Search works with partial matches
- [ ] Search UI has autocomplete suggestions

### Dependencies
- Requires Phase 6 (background tagging) for best experience
- Can work with manual tags only (Phase 4)

---

## Creating These Issues

### Quick Setup

1. **Create Milestone:**
   - Name: "AI Auto-Tagging MVP"
   - Description: "Implement AI-powered automatic image tagging with manual override"
   - Due date: (your choice)

2. **Create Labels:**
   - `ai-tagging` (color: purple)
   - `enhancement` (default)
   - `api` (color: green)
   - `frontend` (color: blue)
   - `background-tasks` (color: orange)
   - `good-first-ai-issue` (color: yellow)

3. **Create Issues:**
   - Copy each issue section above
   - Create as separate GitHub issues
   - Assign to milestone
   - Add appropriate labels
   - Close Issue #1 immediately (already done)

### Issue Workflow

```bash
# When starting a phase
git checkout feat/ai-auto-tagging
# Work on phase...

# When committing
git commit -m "feat: implement tag service (Phase 2)

- Add TagService with CRUD operations
- Implement tag validation and normalization
- Add comprehensive unit tests

Relates to #2"

# When phase is complete
git commit -m "feat: complete tag service (Phase 2)

- All service methods implemented
- 15/15 unit tests passing
- Tag normalization working

Closes #2"
```

### GitHub CLI (Optional)

```bash
# Create issues via CLI
gh issue create --title "Phase 2: Tag Service" --body-file issue-2.md --label enhancement,ai-tagging --milestone "AI Auto-Tagging MVP"

# Link commit to issue
git commit -m "feat: add tag service

Relates to #2"

# Close issue
git commit -m "feat: complete Phase 2

Closes #2"
```

---

## Benefits of This Approach

1. **Visibility:** Track progress at a glance
2. **Traceability:** Every commit linked to an issue
3. **Documentation:** Issue discussions preserve decisions
4. **Portfolio:** Shows professional process
5. **Milestones:** See overall project progress
6. **Labels:** Filter by type (api, frontend, etc.)
7. **Automation:** GitHub auto-closes on merge

---

## Current Status

- Issue #1: ✅ Completed (close immediately)
- Issue #2: 🚧 In progress (Phase 2)
- Issue #3-7: 📋 Planned

**Next Action:** Create Issue #2 and begin Phase 2 implementation!
