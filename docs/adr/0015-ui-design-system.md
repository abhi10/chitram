# ADR-0015: UI Design System - Warm Minimal Theme

## Status
Accepted

## Date
2026-01-03

## Context

Phase 3 introduces a web UI for Chitram. We analyzed 9 mockup designs and need to establish a consistent design system before implementation.

### Design Options Evaluated

| Theme | Mockups | Characteristics |
|-------|---------|-----------------|
| **Warm Minimal** | 4, 6, 8, 9 | Cream background, terracotta accents, serif logo, clean grid |
| **Dark Glassmorphism** | 3, 5, 7 | Blurred backgrounds, frosted glass cards, moody atmosphere |
| **Cool Blue** | 1 | Dark navy header, filters sidebar, color wheel |
| **Warm Editorial** | 2 | Polaroid-style stacked cards, muted earth tones |

### Key Questions

1. What visual style best represents "Chitram" (image/picture)?
2. How do we balance aesthetics with implementation simplicity?
3. What's the right level of visual complexity for MVP?

## Decision

Adopt **Warm Minimal** as the primary theme with **Dark Glassmorphism** reserved for image detail view only.

### Design System Specification

#### Color Palette

```
PRIMARY (Terracotta)
- Light:  #D4A574 (terracotta-400)
- Base:   #C4956A (terracotta-500) - Primary actions
- Dark:   #B4855A (terracotta-600) - Hover states

NEUTRALS
- Bg Light:   #FAF8F5 (cream-100) - Page background
- Bg Warm:    #F5F2ED (cream-200) - Card backgrounds
- Text Sec:   #6B6B6B - Secondary text
- Text Pri:   #2D2D2D - Primary text

DETAIL VIEW (Dark Mode)
- Bg Dark:    #1A1A1A - Dark background
- Glass:      rgba(255,255,255,0.1) - Glassmorphism effect
```

#### Typography

| Element | Font | Weight | Desktop | Mobile |
|---------|------|--------|---------|--------|
| Logo | Playfair Display | 600 | 28px | 24px |
| Page Title | Playfair Display | 600 | 32px | 24px |
| Nav Links | Source Sans 3 | 500 | 15px | 14px |
| Body | Source Sans 3 | 400 | 16px | 15px |
| Image Title | Playfair Display | 500 | 24px | 20px |
| Metadata | Source Sans 3 | 400 | 14px | 13px |

#### Component Patterns

**Buttons:**
- Primary: `bg-terracotta-500 text-white rounded-lg hover:bg-terracotta-600`
- Secondary: `border border-terracotta-500 text-terracotta-500 rounded-lg`
- Ghost: `text-gray-600 hover:underline`

**Cards:**
- Gallery: No border, subtle shadow on hover, `rounded-lg`
- Glass (Detail): `backdrop-blur-xl bg-white/10 border-white/20 rounded-2xl`

#### Responsive Breakpoints

| Viewport | Columns | Gap |
|----------|---------|-----|
| Mobile (< 640px) | 1 | 16px |
| Tablet (640-1024px) | 2 | 20px |
| Desktop (> 1024px) | 3-4 | 24px |

### MVP Scope Decisions

| Feature | Decision | Rationale |
|---------|----------|-----------|
| Image titles | Use filename | Already in API, no new field needed |
| EXIF data | Defer to Part 2 | Requires Pillow EXIF parsing |
| Color palette extraction | Defer to Part 2 | Additional backend work |
| Tags/hashtags | Defer to Part 2 | Requires new DB tables |
| Anonymous on gallery | Show publicly | Matches current API behavior |
| Filters sidebar | Omit for MVP | Keep simple, add in Part 2 |
| Infinite scroll | "Load More" button | HTMX-friendly, simpler |

### Implementation Approach

**TailwindCSS via CDN** (no build step for MVP):
```html
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          terracotta: { 400: '#D4A574', 500: '#C4956A', 600: '#B4855A' },
          cream: { 100: '#FAF8F5', 200: '#F5F2ED' }
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

## Consequences

### Positive
- **Warm, inviting aesthetic** - Differentiates from cold, corporate image hosts
- **Simple implementation** - Tailwind CDN, no build step
- **Clear hierarchy** - Serif for headings, sans-serif for body
- **Accessible contrast** - Dark text on light backgrounds
- **Scalable design system** - Easy to extend in Part 2

### Negative
- **CDN dependency** - Tailwind loaded from CDN (acceptable for MVP)
- **Limited dark mode** - Only detail view uses dark theme
- **No custom icons** - Using emoji/text for MVP

### Risks Mitigated
- **Masonry CSS** - Using CSS columns (no JS dependency)
- **Font loading** - Google Fonts with `display=swap`
- **Mobile-first** - Tailwind's responsive utilities

## Part 2 Deferred Features

| Feature | Complexity | Dependencies |
|---------|------------|--------------|
| Semantic Search | High | pgvector, embeddings |
| Color Palette Filter | Medium | Color extraction service |
| Collections | Medium | New DB tables |
| Tags/Hashtags | Medium | Tagging system |
| Infinite Scroll | Low | HTMX intersect extension |
| EXIF Display | Low | Pillow EXIF parsing |

## References

- [UI Design Document](../architecture/ui-design-doc.md) - Full mockup analysis
- [Phase 3 Requirements](../requirements/phase3.md) - Functional requirements
- [ADR-0013: Web UI with HTMX](./0013-web-ui-htmx.md) - Technology choice
- [TailwindCSS Documentation](https://tailwindcss.com/docs)
- [HTMX Documentation](https://htmx.org/docs/)
