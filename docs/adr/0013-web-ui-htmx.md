# ADR-0013: Web UI with HTMX and Jinja2

## Status

Accepted

## Date

2026-01-03

## Context

### The Problem: User Interface for Image Hosting

The Chitram API provides full functionality for image hosting (upload, download, delete, auth). However, users need a web interface to:
- Browse images in a gallery
- Upload images via drag-and-drop
- Manage their uploaded images
- Register and login

### Options Evaluated

| Option | Stack | Effort | Pros | Cons |
|--------|-------|--------|------|------|
| **A: HTMX + Jinja2** | Python (monorepo) | ~2-3 days | No JS build, fast iteration, Python-only | Limited rich interactivity |
| **B: React SPA** | TypeScript, Vite | ~1 week | Rich UX, component ecosystem | Separate toolchain, build step |
| **C: Next.js** | TypeScript, React | ~1 week | SSR, SEO, API routes | Node.js runtime, extra complexity |
| **D: FastAPI-Admin** | Python plugin | ~2 hours | Quick admin CRUD | Not user-facing, admin-only |

### Key Considerations

1. **Current Project Stage:** MVP phase, need quick iteration
2. **Team Skills:** Python-focused, TypeScript would add learning curve
3. **Deployment:** Single container deployment preferred
4. **Interactivity Needs:** Gallery, forms, modal dialogs - achievable with HTMX
5. **SEO Requirements:** Not critical for image hosting MVP

## Decision

**Use HTMX + Jinja2 + TailwindCSS** for Phase 3 Web UI (monorepo architecture).

### Why HTMX?

HTMX provides HTML-over-the-wire interactivity without JavaScript frameworks:

```html
<!-- Load more images on scroll -->
<div hx-get="/api/gallery?page=2"
     hx-trigger="revealed"
     hx-swap="afterend">
  Loading...
</div>

<!-- Delete with confirmation -->
<button hx-delete="/api/images/123"
        hx-confirm="Delete this image?"
        hx-target="closest .image-card"
        hx-swap="outerHTML">
  Delete
</button>
```

### Why Monorepo (Not Separate Repo)?

| Aspect | Monorepo | Separate Repo |
|--------|----------|---------------|
| **Deployment** | Single container | Two deployments |
| **Shared Types** | Same Python models | API spec sync needed |
| **Development** | One codebase | Context switching |
| **Testing** | Integrated E2E | Mocked API tests |

For our MVP scale, monorepo is simpler.

### Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── images.py      # Existing API routes
│   │   ├── auth.py        # Existing auth routes
│   │   └── web.py         # NEW: Template routes
│   ├── templates/         # NEW: Jinja2 templates
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── upload.html
│   │   ├── image.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── my_images.html
│   │   └── partials/
│   │       ├── gallery_item.html
│   │       ├── upload_progress.html
│   │       └── error_toast.html
│   └── static/            # NEW: Static assets
│       ├── css/styles.css
│       └── js/htmx.min.js
```

### Route Design

Template routes serve HTML, coexisting with API routes:

| Route | Method | Returns | Auth |
|-------|--------|---------|------|
| `/` | GET | HTML (gallery) | No |
| `/image/{id}` | GET | HTML (detail) | No |
| `/upload` | GET/POST | HTML (form) | No |
| `/login` | GET/POST | HTML (form) | No |
| `/register` | GET/POST | HTML (form) | No |
| `/logout` | POST | Redirect | Yes |
| `/my-images` | GET | HTML (dashboard) | Yes |
| `/api/v1/*` | * | JSON (existing) | Varies |

### Authentication Strategy

JWT tokens stored in httpOnly cookies (not localStorage):

```python
@router.post("/login")
async def login(response: Response, form: LoginForm):
    token = auth_service.create_token(user)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,  # HTTPS only
        samesite="lax",
        max_age=86400  # 24 hours
    )
    return RedirectResponse("/", status_code=303)
```

### TailwindCSS Integration

Using CDN for simplicity (production would use built CSS):

```html
<!-- base.html -->
<head>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="/static/js/htmx.min.js"></script>
</head>
```

## Consequences

### Positive

- **No JavaScript build step:** Fast iteration, no npm/webpack/vite
- **Python-only stack:** Team familiarity, single language
- **Single deployment:** One Docker container serves everything
- **Progressive enhancement:** Works without JS, enhanced with HTMX
- **Fast development:** Jinja2 templates are quick to write

### Negative

- **Limited rich interactivity:** No complex client-side state
- **Page refreshes:** Full page loads for navigation (HTMX partial updates mitigate this)
- **Template duplication:** Some HTML patterns repeated across templates

### Neutral

- **Can migrate later:** If React SPA needed, API already exists
- **Good for MVP:** Perfect for current scale, reassess at growth

## Migration Path

If richer UI needed in Phase 5+:

1. **Keep API routes** - Already RESTful, works with any frontend
2. **Add React frontend** - Separate `frontend/` directory or repo
3. **Deprecate template routes** - Phase out `/` in favor of SPA

## References

- [HTMX Documentation](https://htmx.org/docs/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [TailwindCSS Documentation](https://tailwindcss.com/docs)
- [Phase 3 Requirements](../../requirements-phase3.md)
- [ADR-0011: User Authentication](./0011-user-authentication-jwt.md)
