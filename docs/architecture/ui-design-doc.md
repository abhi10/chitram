**Document Type:** Design Spike / UI Specification
**Version:** 1.1
**Date:** 2026-01-03
**Status:** Approved

> **Related ADR:** [ADR-0015: UI Design System](../adr/0015-ui-design-system.md)

## 1. Executive Summary

This document analyzes 9 UI mockups for Chitram and proposes a cohesive design system for the MVP. The goal is **elegant simplicity** with a warm, inviting aesthetic using terracotta as the primary accent color.

### MVP Scope (Phase 3 - Part 1)

|View|Priority|Status|
|---|---|---|
|Gallery/Explore|Must|In Scope|
|Image Detail|Must|In Scope|
|Profile Page|Must|In Scope|
|Upload Form|Must|In Scope (Phase 3 req)|
|Login/Register|Must|In Scope (Phase 3 req)|
|Collections|Deferred|Part 2|
|Semantic Search|Deferred|Part 2|
|Color Palette Filter|Deferred|Part 2|

## 2. Mockup Analysis

### 2.1 Design Themes Identified

|Theme|Mockups|Characteristics|
|---|---|---|
|**Warm Minimal**|4, 6, 8, 9|Cream background, terracotta accents, serif logo, clean grid|
|**Dark Glassmorphism**|3, 5, 7|Blurred backgrounds, frosted glass cards, moody atmosphere|
|**Cool Blue**|1|Dark navy header, filters sidebar, color wheel|
|**Warm Editorial**|2|Polaroid-style stacked cards, muted earth tones|

**Recommendation:** Adopt **Warm Minimal** as primary theme (mockups 4, 6, 8, 9) with **Dark Glassmorphism** reserved for image detail modal/page.

### 2.2 Consistent Elements Across Mockups

```
┌─────────────────────────────────────────────────────────────┐
│  NAVIGATION BAR                                             │
│  ┌─────────┐                    ┌─────────────────────────┐ │
│  │ Chitram │  (optional search) │ Explore │ Collections │ P│ │
│  │ (serif) │                    └─────────────────────────┘ │
│  └─────────┘                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONTENT AREA                                               │
│  ┌───┐ ┌─────┐ ┌───┐ ┌───────┐                             │
│  │   │ │     │ │   │ │       │  Masonry Grid               │
│  │   │ │     │ │   │ │       │  - Variable heights         │
│  └───┘ │     │ └───┘ │       │  - 3-4 columns (desktop)    │
│  ┌───┐ └─────┘ ┌───┐ └───────┘  - 2 columns (tablet)       │
│  │   │ ┌───┐   │   │            - 1 column (mobile)        │
│  │   │ │   │   └───┘                                       │
│  └───┘ └───┘                                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Individual Mockup Notes

|#|View|Key Elements|Adopt?|
|---|---|---|---|
|1|Gallery + Filters|Sidebar filters, color wheel, dark header|❌ Too complex for MVP|
|2|Collections|Stacked polaroid cards, warm beige|⏸️ Defer to Part 2|
|3|Detail (Dark)|Glassmorphism, EXIF, color palette, tags|✅ Detail view style|
|4|Gallery|Masonry, terracotta nav highlight, heart icons|✅ Gallery layout|
|5|Detail (Dark)|Similar to #3, cleaner EXIF layout|✅ Reference|
|6|Gallery|Uniform grid (3x3), centered search|⚠️ Simpler but less dynamic|
|7|Detail (Dark)|Best EXIF/tag layout, clear hierarchy|✅ Primary detail reference|
|8|Gallery|Masonry, orange search button, clean|✅ Search bar style|
|9|Profile|Stats bar, tabs, FAB for upload|✅ Profile layout|

---

## 3. Design System

### 3.1 Color Palette

```
┌────────────────────────────────────────────────────────────┐
│  CHITRAM COLOR PALETTE                                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  PRIMARY (Terracotta)                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │ #D4A574  │ │ #C4956A  │ │ #B4855A  │                   │
│  │ Light    │ │ Base     │ │ Dark     │                   │
│  └──────────┘ └──────────┘ └──────────┘                   │
│                                                            │
│  NEUTRALS                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ #FAF8F5  │ │ #F5F2ED  │ │ #6B6B6B  │ │ #2D2D2D  │      │
│  │ Bg Light │ │ Bg Warm  │ │ Text Sec │ │ Text Pri │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│                                                            │
│  DETAIL VIEW (Dark Mode)                                   │
│  ┌──────────┐ ┌──────────────────────┐                    │
│  │ #1A1A1A  │ │ rgba(255,255,255,0.1)│                    │
│  │ Bg Dark  │ │ Glass Effect         │                    │
│  └──────────┘ └──────────────────────┘                    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**TailwindCSS Custom Colors:**

css

```css
/* tailwind.config.js extension */
colors: {
  terracotta: {
    50:  '#FDF8F4',
    100: '#F9EDE3',
    200: '#F0D9C7',
    300: '#E4BFA3',
    400: '#D4A574',  /* Light */
    500: '#C4956A',  /* Base - Primary */
    600: '#B4855A',  /* Dark */
    700: '#9A7050',
    800: '#7D5B42',
    900: '#644836',
  },
  cream: {
    50:  '#FDFCFA',
    100: '#FAF8F5',  /* Bg Light */
    200: '#F5F2ED',  /* Bg Warm */
    300: '#EDE8E0',
  }
}
```

### 3.2 Typography

|Element|Font|Weight|Size (Desktop)|Size (Mobile)|
|---|---|---|---|---|
|Logo|Playfair Display|600|28px|24px|
|Page Title|Playfair Display|600|32px|24px|
|Nav Links|Source Sans 3|500|15px|14px|
|Body|Source Sans 3|400|16px|15px|
|Image Title|Playfair Display|500|24px|20px|
|Metadata|Source Sans 3|400|14px|13px|
|Tags|Source Sans 3|500|12px|12px|

**Font Loading (Google Fonts):**

html

```html
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600&family=Source+Sans+3:wght@400;500;600&display=swap" rel="stylesheet">
```

### 3.3 Spacing Scale

Using Tailwind's default scale with these common patterns:

|Use Case|Tailwind Class|Pixels|
|---|---|---|
|Card padding|`p-4` / `p-6`|16px / 24px|
|Grid gap|`gap-4` / `gap-6`|16px / 24px|
|Section margin|`my-8` / `my-12`|32px / 48px|
|Nav padding|`px-6 py-4`|24px × 16px|

### 3.4 Component Patterns

#### Buttons

```
┌─────────────────────────────────────────────────────────┐
│  PRIMARY            SECONDARY          GHOST            │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   │
│  │  Download   │   │   Cancel    │   │   Delete    │   │
│  │ bg-terracotta│   │ border only │   │ text only   │   │
│  │ text-white  │   │ text-terra  │   │ text-gray   │   │
│  │ rounded-lg  │   │ rounded-lg  │   │ hover:under │   │
│  └─────────────┘   └─────────────┘   └─────────────┘   │
└─────────────────────────────────────────────────────────┘
```

#### Cards

```
┌─────────────────────────────────────────────────────────┐
│  IMAGE CARD (Gallery)                                   │
│  ┌─────────────────────────┐                           │
│  │                         │  - No border              │
│  │        IMAGE            │  - Subtle shadow on hover │
│  │                         │  - rounded-lg (8px)       │
│  │                         │  - Cursor pointer         │
│  └─────────────────────────┘                           │
│                                                         │
│  GLASS CARD (Detail View)                              │
│  ┌─────────────────────────┐                           │
│  │ ░░░░░░░░░░░░░░░░░░░░░░ │  - backdrop-blur-xl       │
│  │ ░░░  Frosted Glass  ░░░ │  - bg-white/10           │
│  │ ░░░░░░░░░░░░░░░░░░░░░░ │  - border border-white/20│
│  └─────────────────────────┘  - rounded-2xl            │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Page Specifications

### 4.1 Gallery / Explore Page

**Layout:** Masonry grid (CSS columns or Masonry.js)

```
┌─────────────────────────────────────────────────────────────┐
│ ┌──────────┐                      ┌───────────────────────┐ │
│ │ Chitram  │                      │ Explore │ Profile │ + │ │
│ └──────────┘                      └───────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│        ┌───────────────────────────────────────┐            │
│        │ 🔍 Search for inspiration...  [Search]│            │
│        └───────────────────────────────────────┘            │
│                                                             │
│  ┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐       │
│  │         │ │             │ │         │ │         │       │
│  │  IMG 1  │ │   IMG 2     │ │  IMG 3  │ │  IMG 4  │       │
│  │         │ │             │ │         │ │         │       │
│  └─────────┘ │             │ └─────────┘ └─────────┘       │
│  ┌─────────┐ └─────────────┘ ┌─────────────┐               │
│  │         │ ┌─────────┐     │             │               │
│  │  IMG 5  │ │  IMG 6  │     │   IMG 7     │               │
│  │         │ └─────────┘     │             │               │
│  │         │                 │             │               │
│  └─────────┘                 └─────────────┘               │
│                                                             │
│              [ Load More ] or infinite scroll               │
└─────────────────────────────────────────────────────────────┘
```

**Key Decisions:**

|Decision|Choice|Rationale|
|---|---|---|
|Grid type|CSS Columns (masonry)|No JS dependency, works with HTMX|
|Search bar|Centered, prominent|Prepares for Phase 3 Part 2 (semantic)|
|Filters sidebar|❌ Omit for MVP|Keep simple, add in Part 2|
|Hover effect|Scale + shadow|Subtle, performant|
|Pagination|"Load More" button|HTMX-friendly, simpler than infinite scroll|

**Responsive Breakpoints:**

|Viewport|Columns|Gap|
|---|---|---|
|Mobile (< 640px)|1|16px|
|Tablet (640-1024px)|2|20px|
|Desktop (> 1024px)|3-4|24px|

### 4.2 Image Detail Page

**Layout:** Full-screen dark background with glassmorphism card

```
┌─────────────────────────────────────────────────────────────┐
│                     [X] Close                               │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│  ░░┌──────────────────────────┬─────────────────────┐░░░░ │
│  ░░│                          │                     │░░░░ │
│  ░░│                          │  Whispers of the    │░░░░ │
│  ░░│                          │  Mist               │░░░░ │
│  ░░│        FULL IMAGE        │                     │░░░░ │
│  ░░│                          │  👤 Rajesh Kumar    │░░░░ │
│  ░░│                          │                     │░░░░ │
│  ░░│                          │  ─────────────────  │░░░░ │
│  ░░│                          │  EXIF Data          │░░░░ │
│  ░░│                          │  Sony A7IV          │░░░░ │
│  ░░│                          │  f/2.8 · 1/520s     │░░░░ │
│  ░░│                          │  ISO 400            │░░░░ │
│  ░░│                          │                     │░░░░ │
│  ░░│                          │  ○ ○ ○ ○ ○ (colors)│░░░░ │
│  ░░│                          │                     │░░░░ │
│  ░░│                          │  #Nature #Moody     │░░░░ │
│  ░░│                          │  #Mountains #Fog    │░░░░ │
│  ░░│                          │                     │░░░░ │
│  ░░│                          │  ┌───────────────┐  │░░░░ │
│  ░░│                          │  │   Download    │  │░░░░ │
│  ░░│                          │  └───────────────┘  │░░░░ │
│  ░░└──────────────────────────┴─────────────────────┘░░░░ │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
└─────────────────────────────────────────────────────────────┘
```

**Metadata Panel Components:**

|Component|MVP|Part 2|
|---|---|---|
|Image title|✅|-|
|Uploader name/avatar|✅|-|
|EXIF data|✅|Enhanced|
|Extracted color palette|⏸️|✅|
|Tags/hashtags|⏸️|✅|
|Download button|✅|-|
|Delete button (owner)|✅|-|
|Copy link|✅|-|

**MVP Metadata (Phase 3 Req):**

- Filename
- File size
- Dimensions
- Upload date
- Copy link button
- Delete button (if owner)

### 4.3 Profile Page

**Layout:** Header with stats, tabbed content area

```
┌─────────────────────────────────────────────────────────────┐
│ ┌──────────┐                      ┌───────────────────────┐ │
│ │ Chitram  │                      │ Explore │ Profile │ + │ │
│ └──────────┘                      └───────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│         ┌─────┐                                             │
│         │ 👤  │   Arjun V.                                 │
│         │     │   Landscape & Street Photographer          │
│         └─────┘                                             │
│                                                             │
│     5.2K VIEWS  │  1.1K DOWNLOADS  │  850 LIKES            │
│                                                             │
│  ═══════════════════════════════════════════════════════   │
│  [ UPLOADS ]    LIKED    PRIVATE                           │
│  ───────────────────────────────────────────────────────   │
│                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │         │ │         │ │         │ │         │          │
│  │  IMG 1  │ │  IMG 2  │ │  IMG 3  │ │  IMG 4  │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│                                                             │
│                                           ┌───┐            │
│                                           │ + │ FAB        │
│                                           └───┘            │
└─────────────────────────────────────────────────────────────┘
```

**MVP Simplification:**

|Full Mockup|MVP Version|
|---|---|
|Views, Downloads, Likes stats|Image count only|
|UPLOADS, LIKED, PRIVATE tabs|Single list (My Images)|
|FAB upload button|Nav upload link|
|Bio text|Email (from auth)|

---

## 5. Implementation Approach

### 5.1 TailwindCSS Setup

bash

```bash
# Install via CDN for MVP (no build step)
# In base.html:
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          terracotta: {
            400: '#D4A574',
            500: '#C4956A',
            600: '#B4855A',
          },
          cream: {
            100: '#FAF8F5',
            200: '#F5F2ED',
          }
        },
        fontFamily: {
          display: ['Playfair Display', 'serif'],
          sans: ['Source Sans 3', 'sans-serif'],
        }
      }
    }
  }
</script>
```

### 5.2 Base Template Structure

html

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Chitram{% endblock %}</title>
    
    <!-- Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600&family=Source+Sans+3:wght@400;500;600&display=swap" rel="stylesheet">
    
    <!-- Tailwind CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>/* tailwind config */</script>
    
    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
</head>
<body class="bg-cream-100 font-sans text-gray-800">
    {% include 'partials/nav.html' %}
    
    <main class="container mx-auto px-4 py-8">
        {% block content %}{% endblock %}
    </main>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

### 5.3 Template File Map

```
templates/
├── base.html              # Layout, nav, Tailwind config
├── home.html              # Gallery grid
├── image.html             # Detail view (dark mode)
├── upload.html            # Upload form
├── login.html             # Login form
├── register.html          # Registration form
├── my_images.html         # Profile / My Images
└── partials/
    ├── nav.html           # Navigation bar
    ├── gallery_item.html  # Single image card (HTMX)
    ├── image_grid.html    # Grid of images (HTMX)
    └── toast.html         # Error/success messages
```

---

## 6. Deferred Features (Part 2)

|Feature|Complexity|Dependencies|
|---|---|---|
|Semantic Search|High|pgvector, embeddings|
|Color Palette Filter|Medium|Color extraction|
|Collections|Medium|New DB tables|
|Tags/Hashtags|Medium|Tagging system|
|Extracted Color Display|Low|Color extraction|
|Infinite Scroll|Low|HTMX intersect|

---

## 7. Open Questions - RESOLVED

| Question | Decision | Rationale |
|----------|----------|-----------|
| **Image titles** | Use filename for MVP | Already in API response, no new field needed |
| **EXIF extraction** | Defer to Part 2 | Requires Pillow EXIF parsing, not in current backend |
| **Color palette extraction** | Defer to Part 2 | Requires new backend service |
| **Anonymous uploads** | Show on public gallery | Matches current API behavior, simpler UX |

> **Note:** All decisions documented in [ADR-0015: UI Design System](../adr/0015-ui-design-system.md)

---

## 8. Next Steps

1. [x] Review and approve design spec
2. [x] Create ADR for design decisions → [ADR-0015](../adr/0015-ui-design-system.md)
3. [ ] Set up Tailwind config in project (Phase 3A)
4. [ ] Implement base.html with nav (Phase 3A)
5. [ ] Implement gallery page (home.html) (Phase 3B)
6. [ ] Implement detail page (image.html) (Phase 3B)
7. [ ] Implement profile page (my_images.html) (Phase 3C)

> **Implementation Plan:** See [TODO.md](../../TODO.md#phase-3a-foundation-days-1-2) for detailed phased approach