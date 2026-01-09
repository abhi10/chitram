# Product Requirements Document: Search & AI Tagging

**Feature:** Image Search Bar & AI Auto-Tagging System
**Version:** 1.0
**Author:** Product Management
**Date:** 2026-01-06
**Status:** Draft

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Problem Statement](#problem-statement)
- [Goals & Success Metrics](#goals--success-metrics)
- [User Personas](#user-personas)
- [Feature Overview](#feature-overview)
- [User Stories](#user-stories)
- [Functional Requirements](#functional-requirements)
- [Non-Functional Requirements](#non-functional-requirements)
- [Tag Taxonomy & Standardization](#tag-taxonomy--standardization)
- [AI Tagging Specifications](#ai-tagging-specifications)
- [Search Specifications](#search-specifications)
- [UI/UX Requirements](#uiux-requirements)
- [API Design](#api-design)
- [Data Model Changes](#data-model-changes)
- [Privacy & Security Considerations](#privacy--security-considerations)
- [Acceptance Criteria](#acceptance-criteria)
- [Out of Scope](#out-of-scope)
- [Dependencies & Risks](#dependencies--risks)
- [Rollout Strategy](#rollout-strategy)
- [References](#references)

---

## Executive Summary

This PRD defines requirements for two interconnected features for Chitram:

1. **Search Bar**: Enable users to find images by text query across filenames, tags, and metadata
2. **AI Auto-Tagging**: Automatically generate descriptive tags for images using machine learning

These features transform Chitram from a simple upload-and-share service into a searchable, organized image gallery that scales with user collections.

### Business Value

| Metric | Current State | Target State |
|--------|---------------|--------------|
| Image Discovery | Browse only (20 recent) | Search + Browse + Filter |
| Time to Find Image | Minutes (manual scroll) | Seconds (search query) |
| Image Organization | None | Automatic categorization |
| User Engagement | Upload → Share → Leave | Upload → Organize → Return |

---

## Problem Statement

### Current Pain Points

1. **No Discovery Mechanism**: Users can only browse recent images chronologically. With growing collections, finding a specific image becomes increasingly difficult.

2. **No Organization System**: Images have no categorization, tags, or labels. Users cannot group or filter their uploads.

3. **Wasted Metadata**: Image filenames often contain useful information ("beach_vacation_2025.jpg") that is not searchable.

4. **Manual Effort Required**: Users who want organization must rename files before upload or maintain external records.

### User Feedback (Hypothetical)

> "I uploaded 50 photos last month but can't find the sunset one without scrolling through everything."

> "I wish I could tag my photos so I can find all my food pictures later."

> "Other photo services auto-detect what's in my photos. Why can't Chitram?"

---

## Goals & Success Metrics

### Primary Goals

1. **Enable Image Discovery**: Users can find any image in under 10 seconds using search
2. **Automate Organization**: 80%+ of images receive accurate AI-generated tags
3. **Improve Retention**: Users return to manage and browse their organized galleries

### Success Metrics (KPIs)

| Metric | Definition | Target |
|--------|------------|--------|
| Search Usage Rate | % of sessions with at least one search | > 30% |
| Search Success Rate | Searches resulting in image click | > 60% |
| AI Tag Accuracy | Human-verified correct tags / total tags | > 85% |
| Tag Interaction Rate | % of users who view/edit tags | > 20% |
| Return Visit Rate | Users visiting gallery 2+ times/week | +25% increase |
| Time to First Image | Seconds from search to clicking result | < 5 seconds |

---

## User Personas

### Persona 1: Casual Uploader (Primary)

**Name:** Sarah, 28
**Usage:** Uploads 5-20 images/month for sharing
**Goals:**
- Quickly share images with friends via links
- Find past uploads when needed
- Minimal effort for organization

**Pain Points:**
- Forgets where specific images are
- Doesn't want to manually tag everything

**Feature Needs:**
- Simple search by filename or content
- Automatic tags that "just work"

---

### Persona 2: Power User (Secondary)

**Name:** Marcus, 35
**Usage:** Uploads 50-100 images/month, photography hobbyist
**Goals:**
- Maintain organized portfolio
- Find images by subject, location, or style
- Efficient bulk operations

**Pain Points:**
- Current tools don't scale with collection size
- Needs precise control over categorization

**Feature Needs:**
- Advanced search with filters
- Ability to edit and add custom tags
- Bulk tagging operations
- Tag hierarchies (e.g., Animals > Dogs > Golden Retriever)

---

### Persona 3: Anonymous Visitor (Tertiary)

**Name:** Anyone with a shared link
**Usage:** Views images shared by others
**Goals:**
- View the shared image
- Possibly browse public gallery

**Pain Points:**
- Cannot search public images

**Feature Needs:**
- Search within public gallery (if enabled)

---

## Feature Overview

### Feature 1: Search Bar

A persistent search input allowing text-based queries across:
- Image filenames
- AI-generated tags
- User-added tags
- Image dimensions (e.g., "landscape", "portrait")

### Feature 2: AI Auto-Tagging

Background service that analyzes uploaded images and generates:
- Object tags (e.g., "dog", "car", "building")
- Scene tags (e.g., "beach", "forest", "indoor")
- Color tags (e.g., "blue", "vibrant", "monochrome")
- Attribute tags (e.g., "landscape orientation", "high contrast")

### Feature 3: Manual Tagging

User interface for:
- Viewing AI-generated tags
- Adding custom tags
- Removing incorrect tags
- Bulk tag operations

---

## User Stories

### Epic 1: Image Search

#### US-1.1: Basic Search
**As a** logged-in user
**I want to** search my images by typing keywords
**So that** I can quickly find specific images without scrolling

**Acceptance Criteria:**
- Search bar is visible on gallery pages (home, my-images)
- Typing a query and pressing Enter returns matching images
- Results show images where filename OR tags match the query
- Empty results show "No images found" with suggestions
- Search is case-insensitive
- Partial matches are supported (e.g., "beach" matches "beach_sunset")

---

#### US-1.2: Search Autocomplete
**As a** user typing a search query
**I want to** see suggested completions based on existing tags
**So that** I can discover available tags and search faster

**Acceptance Criteria:**
- After typing 2+ characters, show up to 5 suggestions
- Suggestions come from: existing tags, recent searches, filenames
- Clicking a suggestion executes the search
- Keyboard navigation works (arrow keys + Enter)
- Suggestions appear within 200ms of typing

---

#### US-1.3: Search with Filters
**As a** power user
**I want to** combine search with filters
**So that** I can narrow down results precisely

**Acceptance Criteria:**
- Filter options: Date range, File type, Dimensions, Tag category
- Filters can be combined with text search
- Active filters are displayed as removable chips
- Filter state persists during session
- "Clear all filters" button available

---

#### US-1.4: Search Results Display
**As a** user viewing search results
**I want to** see results in a familiar gallery layout
**So that** the experience is consistent with browsing

**Acceptance Criteria:**
- Results use same masonry grid as main gallery
- Result count shown (e.g., "23 images found")
- Matching tags are highlighted on result cards
- "Load more" pagination works for large result sets
- Clicking result navigates to image detail page
- Back button returns to search results (preserves state)

---

#### US-1.5: Empty State & Error Handling
**As a** user whose search returns no results
**I want to** understand why and get helpful suggestions
**So that** I can refine my search or try alternatives

**Acceptance Criteria:**
- Empty state shows friendly message: "No images match '{query}'"
- Suggest similar tags if available
- Offer to clear filters if active
- Handle special characters gracefully (no errors)
- Show error message if search service is unavailable

---

### Epic 2: AI Auto-Tagging

#### US-2.1: Automatic Tagging on Upload
**As a** user uploading an image
**I want** the system to automatically generate relevant tags
**So that** my images are searchable without manual effort

**Acceptance Criteria:**
- Tags are generated asynchronously (don't block upload response)
- 3-10 tags generated per image (configurable)
- Tags appear on image detail page once generated
- Processing status shown: "Analyzing image..." → "Tags ready"
- Works for both JPEG and PNG images

---

#### US-2.2: Tag Confidence & Accuracy
**As a** user viewing AI-generated tags
**I want to** understand the confidence level of each tag
**So that** I can identify potentially incorrect tags

**Acceptance Criteria:**
- Each tag has a confidence score (0-100%)
- Tags below 70% confidence are marked as "suggested"
- High-confidence tags (>90%) shown prominently
- Low-confidence tags can be hidden by user preference
- Overall accuracy target: 85%+ for object recognition

---

#### US-2.3: Backfill Existing Images
**As a** user with existing uploaded images
**I want** AI tagging applied to my old images
**So that** my entire collection becomes searchable

**Acceptance Criteria:**
- Admin can trigger backfill job for all/selected images
- Backfill runs at low priority (doesn't impact live uploads)
- Progress tracking available (X of Y images processed)
- Images already tagged are skipped (unless forced)
- Rate limiting prevents API cost spikes

---

#### US-2.4: Tag Categories
**As a** user browsing tags
**I want** tags organized into categories
**So that** I can understand and filter by tag type

**Acceptance Criteria:**
- Standard categories: Objects, Scenes, Colors, Attributes
- Each tag belongs to one primary category
- Category shown as prefix or color coding in UI
- Filter search results by tag category

---

### Epic 3: Manual Tagging

#### US-3.1: View Tags on Image
**As a** user viewing an image detail page
**I want to** see all tags associated with the image
**So that** I understand how it's categorized

**Acceptance Criteria:**
- Tags section visible on image detail page
- Shows both AI-generated and user-added tags
- AI tags marked with icon (e.g., sparkle/robot)
- User tags marked with icon (e.g., user/pencil)
- Tags are clickable → search for that tag

---

#### US-3.2: Add Custom Tags
**As a** user viewing my image
**I want to** add my own tags
**So that** I can categorize images my way

**Acceptance Criteria:**
- "Add tag" input visible on image detail (owner only)
- Autocomplete suggests existing tags (for consistency)
- New tags are created if they don't exist
- Maximum 20 tags per image (AI + user combined)
- Tags must be 2-50 characters, alphanumeric + spaces/hyphens
- Duplicate tags prevented

---

#### US-3.3: Remove Tags
**As a** user viewing my image
**I want to** remove incorrect or unwanted tags
**So that** search results stay accurate

**Acceptance Criteria:**
- Each tag has "X" button to remove (owner only)
- Confirmation not required (undo available)
- Removed AI tags recorded for model feedback
- User can restore removed AI tags
- Cannot remove all tags (minimum 1 required? Or allow 0?)

---

#### US-3.4: Bulk Tag Operations
**As a** power user with many images
**I want to** add or remove tags from multiple images at once
**So that** I can organize efficiently

**Acceptance Criteria:**
- Multi-select mode on gallery (checkboxes)
- Bulk action menu: "Add tag", "Remove tag"
- Preview affected images before applying
- Progress indicator for bulk operations
- Maximum 50 images per bulk operation

---

#### US-3.5: Tag Feedback for AI Improvement
**As a** user correcting AI-generated tags
**I want** my corrections to improve future tagging
**So that** the system gets smarter over time

**Acceptance Criteria:**
- Removed AI tags logged as negative feedback
- Added tags to AI-tagged images logged as positive examples
- Feedback data exportable for model retraining
- Privacy-preserving: no image content in feedback, only tag corrections

---

### Epic 4: Tag Management

#### US-4.1: Browse by Tag
**As a** user exploring my gallery
**I want to** click a tag and see all images with that tag
**So that** I can browse by category

**Acceptance Criteria:**
- Tags are clickable links throughout UI
- Clicking tag navigates to `/search?tag={tag}`
- Results show all images with that tag
- Tag shown as heading: "Images tagged: {tag}"

---

#### US-4.2: Popular Tags Display
**As a** user on the gallery page
**I want to** see popular tags as filter shortcuts
**So that** I can quickly browse common categories

**Acceptance Criteria:**
- "Popular tags" section on gallery sidebar/top
- Shows top 10-20 tags by image count
- Clicking tag filters gallery to that tag
- Tags update based on user's collection (my-images) or all (home)

---

#### US-4.3: Tag Cloud/Browser
**As a** user wanting to explore tags
**I want** a dedicated tag browsing interface
**So that** I can discover how my images are categorized

**Acceptance Criteria:**
- Accessible from navigation: "Tags" or "Browse Tags"
- Shows all tags with image counts
- Sortable: alphabetical, by count, by category
- Search within tags
- Hierarchical view for nested tags (future)

---

## Functional Requirements

### FR-1: Search Functionality

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | System shall provide a search input on gallery pages | Must Have |
| FR-1.2 | Search shall query: filename, tags (AI + user), and metadata | Must Have |
| FR-1.3 | Search shall support partial matching and be case-insensitive | Must Have |
| FR-1.4 | Search shall return results within 500ms for 95% of queries | Must Have |
| FR-1.5 | Search shall support pagination (20 results per page) | Must Have |
| FR-1.6 | Search shall provide autocomplete suggestions | Should Have |
| FR-1.7 | Search shall support filter combinations (date, type, category) | Should Have |
| FR-1.8 | Search shall highlight matching terms in results | Nice to Have |
| FR-1.9 | Search shall support boolean operators (AND, OR, NOT) | Nice to Have |
| FR-1.10 | Search shall remember recent searches per user | Nice to Have |

### FR-2: AI Auto-Tagging

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | System shall automatically generate tags for new uploads | Must Have |
| FR-2.2 | Tagging shall be asynchronous (not block upload) | Must Have |
| FR-2.3 | System shall generate 3-10 tags per image | Must Have |
| FR-2.4 | Tags shall include confidence scores | Must Have |
| FR-2.5 | System shall support tagging JPEG and PNG images | Must Have |
| FR-2.6 | System shall categorize tags (objects, scenes, colors) | Should Have |
| FR-2.7 | System shall support backfilling existing images | Should Have |
| FR-2.8 | System shall use feedback to improve accuracy | Should Have |
| FR-2.9 | System shall detect and tag text in images (OCR) | Nice to Have |
| FR-2.10 | System shall detect faces (count, not identity) | Nice to Have |

### FR-3: Manual Tagging

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Users shall view tags on image detail page | Must Have |
| FR-3.2 | Image owners shall add custom tags | Must Have |
| FR-3.3 | Image owners shall remove tags | Must Have |
| FR-3.4 | System shall validate tag format (length, characters) | Must Have |
| FR-3.5 | System shall prevent duplicate tags on same image | Must Have |
| FR-3.6 | System shall distinguish AI vs user tags visually | Should Have |
| FR-3.7 | Users shall perform bulk tag operations | Should Have |
| FR-3.8 | System shall suggest existing tags during input | Should Have |
| FR-3.9 | System shall limit tags per image (max 20) | Should Have |

---

## Non-Functional Requirements

### NFR-1: Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1.1 | Search response time (p95) | < 500ms |
| NFR-1.2 | Autocomplete response time | < 200ms |
| NFR-1.3 | AI tagging completion time | < 30 seconds |
| NFR-1.4 | Tag add/remove operation | < 200ms |
| NFR-1.5 | Search index update after tag change | < 5 seconds |

### NFR-2: Scalability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-2.1 | Support concurrent search queries | 100/second |
| NFR-2.2 | Support total indexed images | 1 million |
| NFR-2.3 | Support tags per system | 100,000 unique |
| NFR-2.4 | Support AI tagging queue depth | 10,000 pending |

### NFR-3: Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-3.1 | Search availability | 99.9% |
| NFR-3.2 | AI tagging availability | 99% (graceful degradation) |
| NFR-3.3 | Tag data durability | 99.99% |
| NFR-3.4 | Search index recovery time | < 1 hour |

### NFR-4: Usability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-4.1 | Search accessible via keyboard | Full support |
| NFR-4.2 | Mobile search experience | Touch-optimized |
| NFR-4.3 | Screen reader compatibility | WCAG 2.1 AA |
| NFR-4.4 | Search input visible without scrolling | All viewports |

---

## Tag Taxonomy & Standardization

### Tag Format Rules

| Rule | Specification |
|------|---------------|
| Length | 2-50 characters |
| Characters | Letters, numbers, spaces, hyphens |
| Case | Stored lowercase, displayed Title Case |
| Language | English (v1), extensible to others |
| Uniqueness | Unique per system (not per user) |

### Standard Tag Categories

Based on industry best practices from [Cloudinary](https://cloudinary.com/guides/image-effects/simplify-your-life-with-automatic-image-tagging), [Daminion](https://daminion.net/articles/tools/image-tagging-software/), and [Adobe Lightroom](https://lightroom.adobe.com/):

#### Category 1: Objects (What's in the image)

```
Animals: dog, cat, bird, horse, fish, butterfly, bear, elephant
People: person, face, crowd, baby, man, woman, child
Vehicles: car, truck, motorcycle, bicycle, boat, airplane
Food: fruit, vegetable, meal, drink, dessert, coffee
Nature: flower, tree, mountain, ocean, river, sky, cloud
Buildings: house, skyscraper, church, bridge, monument
Objects: phone, laptop, book, furniture, clothing
```

#### Category 2: Scenes (Where/Context)

```
Locations: beach, forest, city, park, indoor, outdoor, office
Events: wedding, party, concert, sports, travel
Weather: sunny, cloudy, rainy, snowy, foggy
Time: day, night, sunset, sunrise, golden hour
```

#### Category 3: Visual Attributes

```
Colors: red, blue, green, yellow, black, white, colorful, monochrome
Composition: landscape, portrait, square, close-up, wide-angle
Quality: high contrast, soft focus, sharp, blurry
Style: minimalist, vintage, modern, artistic
```

#### Category 4: Technical

```
Orientation: landscape orientation, portrait orientation
Format: photograph, illustration, screenshot, document
```

### Tag Hierarchy (Future Enhancement)

```
Animals
├── Pets
│   ├── Dogs
│   │   ├── Golden Retriever
│   │   └── Labrador
│   └── Cats
└── Wildlife
    ├── Birds
    └── Marine
```

---

## AI Tagging Specifications

### ML Model Options

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **Cloud API (Recommended)** | High accuracy, no ML infra needed, regular updates | Per-image cost, external dependency | Start here |
| Self-hosted Model | No per-call cost, data stays local | Requires GPU, maintenance overhead | Phase 2 |
| Hybrid | Best of both | Complexity | Future |

### Recommended Cloud APIs

1. **Google Cloud Vision API**
   - Label Detection: Objects, scenes
   - Safe Search: Content moderation
   - Web Detection: Similar images
   - Pricing: ~$1.50 per 1000 images

2. **AWS Rekognition**
   - Label Detection: Objects, scenes
   - Text Detection: OCR
   - Face Detection: Count, attributes
   - Pricing: ~$1.00 per 1000 images

3. **Azure Computer Vision**
   - Tags: Objects, actions
   - Categories: Scene classification
   - Adult content detection
   - Pricing: ~$1.00 per 1000 images

4. **Cloudinary AI** (if already using for CDN)
   - Auto-tagging included
   - Integrated with media pipeline
   - Pricing: Varies by plan

### Confidence Score Thresholds

| Threshold | Action |
|-----------|--------|
| ≥ 90% | Auto-apply tag, show prominently |
| 70-89% | Auto-apply tag, show as "suggested" |
| 50-69% | Store but don't display by default |
| < 50% | Discard |

### Rate Limiting & Cost Control

| Control | Setting |
|---------|---------|
| Max AI calls per minute | 60 |
| Max AI calls per user per day | 100 |
| Backfill batch size | 100 images |
| Backfill delay between batches | 1 minute |
| Monthly budget alert | $50 |

---

## Search Specifications

### Search Index Strategy

**Option A: PostgreSQL Full-Text Search (Recommended for MVP)**
- Use `tsvector` and `tsquery` for text search
- GIN index on searchable columns
- Pros: No additional infrastructure, ACID compliance
- Cons: Limited relevance ranking, no fuzzy matching

**Option B: Elasticsearch/OpenSearch (Future)**
- Dedicated search engine
- Advanced relevance, fuzzy matching, aggregations
- Pros: Better search quality, analytics
- Cons: Additional infrastructure, sync complexity

### Search Query Processing

```
User Input: "beach sunset"

1. Tokenize: ["beach", "sunset"]
2. Normalize: lowercase, remove special chars
3. Expand: synonyms? (not v1)
4. Query:
   - Match filename ILIKE '%beach%' OR ILIKE '%sunset%'
   - Match tags WHERE tag IN ('beach', 'sunset')
   - Match tag prefixes WHERE tag LIKE 'beach%'
5. Rank: Order by match count, then recency
6. Return: Paginated results with match highlights
```

### Search Ranking Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| Exact tag match | 1.0 | Query exactly matches a tag |
| Partial tag match | 0.5 | Query is prefix of tag |
| Filename match | 0.3 | Query found in filename |
| Recency | 0.1 | Newer images ranked higher |
| Popularity | 0.1 | Images with more views (future) |

---

## UI/UX Requirements

### Search Bar Design

```
┌─────────────────────────────────────────────────────────────┐
│  🔍  Search images...                              [Filters]│
└─────────────────────────────────────────────────────────────┘
         │
         ▼ (on focus, after 2+ chars)
┌─────────────────────────────────────────────────────────────┐
│  📷 beach (15 images)                                       │
│  🏷️ beach sunset (8 images)                                │
│  🏷️ beach vacation (5 images)                              │
│  🕐 Recent: "mountains"                                     │
└─────────────────────────────────────────────────────────────┘
```

### Tag Display on Image Card

```
┌──────────────────────┐
│                      │
│    [Image Preview]   │
│                      │
├──────────────────────┤
│ beach_sunset.jpg     │
│ 🏷️ beach · sunset   │
│ 📅 Jan 5, 2026       │
└──────────────────────┘
```

### Tag Section on Image Detail

```
Tags
─────────────────────────────────────
✨ beach (95%)      ✨ sunset (92%)     ✨ ocean (88%)
✨ sky (85%)        👤 vacation         👤 2025

[+ Add tag...]

✨ = AI generated   👤 = User added
```

### Mobile Considerations

- Search bar collapses to icon on mobile, expands on tap
- Filters in bottom sheet (not sidebar)
- Tags wrap horizontally on cards
- Swipe to see more tags on detail page

---

## API Design

### New Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/images/search` | Search images |
| GET | `/api/v1/tags` | List all tags |
| GET | `/api/v1/tags/popular` | Get popular tags |
| POST | `/api/v1/images/{id}/tags` | Add tag to image |
| DELETE | `/api/v1/images/{id}/tags/{tag}` | Remove tag from image |
| POST | `/api/v1/images/bulk/tags` | Bulk add tags |
| DELETE | `/api/v1/images/bulk/tags` | Bulk remove tags |
| POST | `/api/v1/admin/backfill-tags` | Trigger AI tagging backfill |

### Search Endpoint

```
GET /api/v1/images/search?q={query}&tags={tag1,tag2}&date_from={date}&date_to={date}&limit={20}&offset={0}

Response:
{
  "total": 45,
  "limit": 20,
  "offset": 0,
  "query": "beach",
  "results": [
    {
      "id": "uuid",
      "filename": "beach_sunset.jpg",
      "thumbnail_url": "/api/v1/images/{id}/thumbnail",
      "tags": [
        {"name": "beach", "source": "ai", "confidence": 95},
        {"name": "vacation", "source": "user", "confidence": null}
      ],
      "created_at": "2026-01-05T12:00:00Z",
      "match_highlights": ["beach"]
    }
  ]
}
```

### Tag Management Endpoints

```
POST /api/v1/images/{id}/tags
Body: {"tag": "vacation"}
Response: {"success": true, "tag": {"name": "vacation", "source": "user"}}

DELETE /api/v1/images/{id}/tags/vacation
Response: {"success": true}

GET /api/v1/tags?limit=100&sort=count
Response: {
  "tags": [
    {"name": "beach", "count": 45, "category": "scene"},
    {"name": "dog", "count": 32, "category": "object"}
  ]
}
```

---

## Data Model Changes

### New Tables

```sql
-- Tags table (normalized)
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
CREATE INDEX idx_image_tags_source ON image_tags(source);

-- Tag feedback for AI improvement
CREATE TABLE tag_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id UUID NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    feedback_type VARCHAR(10) NOT NULL,  -- 'removed', 'added'
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Search Index

```sql
-- Full-text search on images
ALTER TABLE images ADD COLUMN search_vector tsvector;

CREATE INDEX idx_images_search ON images USING GIN(search_vector);

-- Trigger to update search vector
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

---

## Privacy & Security Considerations

### Data Privacy

| Concern | Mitigation |
|---------|------------|
| AI processes user images | Images sent to 3rd party API (with consent) |
| Tag data reveals image content | Tags tied to authenticated users only |
| Search queries logged | Anonymize after 30 days |
| Feedback data | No image pixels, only tag corrections |

### Security

| Concern | Mitigation |
|---------|------------|
| Search injection | Parameterized queries, input sanitization |
| Bulk API abuse | Rate limiting on tag operations |
| Unauthorized tag modification | Owner-only access enforced |
| AI cost attacks | Per-user quotas on AI tagging |

### Content Moderation

- AI services include safe-search detection
- Flag images with adult/violent content
- Do not auto-tag sensitive content
- Admin review queue for flagged images

---

## Acceptance Criteria

### Definition of Done

- [ ] All "Must Have" functional requirements implemented
- [ ] All non-functional requirements met
- [ ] Unit tests: >80% coverage for new code
- [ ] Integration tests: Search and tagging flows
- [ ] API documentation updated (OpenAPI/Swagger)
- [ ] UI responsive on mobile, tablet, desktop
- [ ] Accessibility audit passed (WCAG 2.1 AA)
- [ ] Performance benchmarks met
- [ ] Security review completed
- [ ] User documentation/help text added

### Demo Checklist

1. [ ] Upload image → AI tags appear within 30 seconds
2. [ ] Search by filename → relevant results returned
3. [ ] Search by AI tag → images with that tag shown
4. [ ] Add custom tag → tag appears, image searchable by it
5. [ ] Remove tag → tag removed, search updated
6. [ ] Click tag → navigate to search for that tag
7. [ ] Popular tags → display on gallery page
8. [ ] Bulk select → add tag to multiple images
9. [ ] Backfill → process existing images
10. [ ] Mobile → search and tag features work

---

## Out of Scope

The following are explicitly **not** included in this PRD:

| Feature | Reason | Future Phase |
|---------|--------|--------------|
| Face recognition (identity) | Privacy concerns, complexity | Phase 5+ |
| Image similarity search | Requires embeddings infrastructure | Phase 5+ |
| Natural language search ("my dog at the beach") | Requires NLP | Phase 5+ |
| Tag hierarchies | Added complexity | Phase 4.5 |
| Tag translations (i18n) | English first | Phase 5+ |
| Custom AI model training | Use off-the-shelf APIs first | Phase 5+ |
| Tag sharing/social | Focus on personal organization | Future |
| Tag-based albums/collections | Separate feature | Phase 4.5 |
| Geo-tagging from EXIF | Requires EXIF parsing | Phase 4.5 |

---

## Dependencies & Risks

### Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| Cloud Vision API account | DevOps | Required |
| PostgreSQL full-text search | Backend | Available |
| Redis for search cache | Backend | Available |
| Background task system (Celery) | Backend | Phase 4 |
| UI components (HTMX/Jinja2) | Frontend | Available |

### Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| AI API costs exceed budget | High | Medium | Per-user quotas, budget alerts |
| AI tagging accuracy below target | Medium | Medium | Confidence thresholds, user feedback |
| Search performance degrades | High | Low | Index optimization, caching |
| User adoption low | Medium | Medium | Progressive disclosure, good defaults |
| Cloud API downtime | Medium | Low | Graceful degradation, retry logic |

---

## Rollout Strategy

### Phase 1: Foundation (Week 1-2)

- Database schema changes (tags, image_tags tables)
- Tag CRUD API endpoints
- Manual tagging UI on image detail page

### Phase 2: AI Tagging (Week 3-4)

- Integrate Cloud Vision API
- Background task for tagging new uploads
- Confidence scores and categories

### Phase 3: Search (Week 5-6)

- PostgreSQL full-text search
- Search API endpoint
- Search bar UI with autocomplete

### Phase 4: Polish (Week 7-8)

- Bulk operations
- Popular tags display
- Backfill existing images
- Performance optimization

### Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `enable_search` | false | Show search bar |
| `enable_ai_tagging` | false | Run AI on uploads |
| `enable_manual_tags` | false | Allow user tagging |
| `ai_tagging_provider` | google | Which AI API to use |

### Rollout Phases

1. **Internal Testing**: All flags on for team
2. **Beta Users**: 10% of users, opt-in
3. **General Availability**: 100% rollout
4. **Backfill**: Process historical images

---

## References

### Industry Research

- [Cloudinary: Simplify Your Life with Automatic Image Tagging](https://cloudinary.com/guides/image-effects/simplify-your-life-with-automatic-image-tagging)
- [Wasabi: AI Tagging Explained](https://wasabi.com/blog/technology/what-is-ai-tagging)
- [Daminion: Image Tagging Software](https://daminion.net/articles/tools/image-tagging-software/)
- [DesignMonks: Master Search UX in 2025](https://www.designmonks.co/blog/search-ux-best-practices)
- [DesignRush: Search UX Best Practices](https://www.designrush.com/best-designs/websites/trends/search-ux-best-practices)
- [Mobbin: Gallery UI Design](https://mobbin.com/glossary/gallery)
- [Picturepark: Best Practices for DAM AI Auto-Tagging](https://picturepark.com/content-management-blog/best-practices-for-dam-ai-auto-tagging-content-management-blog)

### Technical References

- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [Google Cloud Vision API](https://cloud.google.com/vision/docs)
- [AWS Rekognition](https://docs.aws.amazon.com/rekognition/)
- [IPTC Photo Metadata Standard](https://iptc.org/standards/photo-metadata/)

### Internal Documents

- [ADR-0009: Redis Caching for Metadata](../adr/0009-redis-caching-for-metadata.md)
- [ADR-0012: Background Jobs Strategy](../adr/0012-background-jobs-celery.md)
- [Phase 4 Requirements](./phase4.md) (planned)

---

*Document Version: 1.0*
*Last Updated: 2026-01-06*
*Next Review: Before implementation kickoff*
