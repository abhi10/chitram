# Phase 3 Web UI Architecture

This document describes the architecture and data flow for the Chitram web UI component.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────────┐          ┌──────────────────┐                       │
│   │   Web Browser    │          │   API Client     │                       │
│   │  (HTMX + HTML)   │          │  (Swagger/curl)  │                       │
│   └────────┬─────────┘          └────────┬─────────┘                       │
│            │                             │                                  │
│            │ HTML/Fragments              │ JSON                            │
│            ▼                             ▼                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────────────────┐     ┌──────────────────────────┐            │
│   │      web.py              │     │      images.py           │            │
│   │   (Web UI Routes)        │     │    (REST API Routes)     │            │
│   │                          │     │                          │            │
│   │  GET /                   │     │  POST /api/v1/images     │            │
│   │  GET /image/{id}         │     │  GET  /api/v1/images/{id}│            │
│   │  GET /upload             │     │  DELETE /api/v1/images   │            │
│   │  GET /login              │     │                          │            │
│   │  GET /register           │     ├──────────────────────────┤            │
│   │  POST /logout            │     │      auth.py             │            │
│   │  GET /my-images          │     │   (Auth API Routes)      │            │
│   │  GET /partials/gallery   │     │                          │            │
│   └───────────┬──────────────┘     │  POST /api/v1/auth/login │            │
│               │                     │  POST /api/v1/auth/register          │
│               │                     └───────────┬──────────────┘            │
│               │                                 │                           │
│               ▼                                 ▼                           │
│   ┌──────────────────────────────────────────────────────────┐             │
│   │                    app.state                              │             │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │             │
│   │  │  templates  │  │   storage   │  │    cache    │       │             │
│   │  │ (Jinja2)    │  │ (Service)   │  │  (Redis)    │       │             │
│   │  └─────────────┘  └─────────────┘  └─────────────┘       │             │
│   └──────────────────────────────────────────────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SERVICE LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌────────────────────┐  ┌────────────────────┐  ┌──────────────────┐     │
│   │   ImageService     │  │    AuthService     │  │ ThumbnailService │     │
│   │                    │  │                    │  │                  │     │
│   │  - list_recent()   │  │  - verify_token()  │  │  - generate()    │     │
│   │  - list_by_user()  │  │  - get_user_by_id()│  │  - get()         │     │
│   │  - get_by_id()     │  │  - create_user()   │  │                  │     │
│   │  - upload()        │  │  - authenticate()  │  │                  │     │
│   │  - delete()        │  │  - hash_password() │  │                  │     │
│   └─────────┬──────────┘  └─────────┬──────────┘  └────────┬─────────┘     │
│             │                       │                      │               │
│             └───────────────────────┼──────────────────────┘               │
│                                     │                                       │
│                                     ▼                                       │
│   ┌──────────────────────────────────────────────────────────┐             │
│   │                   StorageService                          │             │
│   │  - save()   - get()   - delete()   - exists()            │             │
│   │                                                           │             │
│   │  ┌─────────────────────┐  ┌─────────────────────┐        │             │
│   │  │ LocalStorageBackend │  │  MinioStorageBackend│        │             │
│   │  │   (Development)     │  │    (Production)     │        │             │
│   │  └─────────────────────┘  └─────────────────────┘        │             │
│   └──────────────────────────────────────────────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             DATA LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌────────────────────┐  ┌────────────────────┐  ┌──────────────────┐     │
│   │     PostgreSQL     │  │       Redis        │  │  Local/MinIO     │     │
│   │    (Metadata)      │  │     (Cache)        │  │   (Files)        │     │
│   │                    │  │                    │  │                  │     │
│   │  - images table    │  │  - image metadata  │  │  - originals     │     │
│   │  - users table     │  │  - rate limits     │  │  - thumbnails    │     │
│   └────────────────────┘  └────────────────────┘  └──────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Web Request Data Flow

### 1. Home Page (Gallery) Flow

```
Browser                  web.py              ImageService           Database
   │                        │                      │                    │
   │  GET /                 │                      │                    │
   │───────────────────────>│                      │                    │
   │                        │                      │                    │
   │                        │  list_recent(20)     │                    │
   │                        │─────────────────────>│                    │
   │                        │                      │                    │
   │                        │                      │  SELECT images     │
   │                        │                      │  ORDER BY created  │
   │                        │                      │  LIMIT 20          │
   │                        │                      │───────────────────>│
   │                        │                      │                    │
   │                        │                      │  [Image, Image...] │
   │                        │                      │<───────────────────│
   │                        │                      │                    │
   │                        │  List[Image]         │                    │
   │                        │<─────────────────────│                    │
   │                        │                      │                    │
   │                        │  templates.render("home.html",           │
   │                        │                   images=images)          │
   │                        │                      │                    │
   │  <html>...</html>      │                      │                    │
   │<───────────────────────│                      │                    │
```

### 2. Cookie Authentication Flow

```
Browser                  web.py              AuthService            Database
   │                        │                      │                    │
   │  GET /my-images        │                      │                    │
   │  Cookie: chitram_auth  │                      │                    │
   │───────────────────────>│                      │                    │
   │                        │                      │                    │
   │                        │  get_current_user_from_cookie()          │
   │                        │                      │                    │
   │                        │  Extract JWT from    │                    │
   │                        │  cookie              │                    │
   │                        │                      │                    │
   │                        │  verify_token(jwt)   │                    │
   │                        │─────────────────────>│                    │
   │                        │                      │                    │
   │                        │  user_id             │                    │
   │                        │<─────────────────────│                    │
   │                        │                      │                    │
   │                        │  get_user_by_id(id)  │                    │
   │                        │─────────────────────>│                    │
   │                        │                      │  SELECT user       │
   │                        │                      │───────────────────>│
   │                        │                      │                    │
   │                        │  User                │  User              │
   │                        │<─────────────────────│<───────────────────│
   │                        │                      │                    │
   │                        │  (continue with authenticated user)      │
```

### 3. HTMX Partial Load Flow (Load More)

```
Browser (HTMX)           web.py              ImageService           Database
   │                        │                      │                    │
   │  Click "Load More"     │                      │                    │
   │                        │                      │                    │
   │  GET /partials/gallery │                      │                    │
   │  ?offset=20&limit=20   │                      │                    │
   │  HX-Request: true      │                      │                    │
   │───────────────────────>│                      │                    │
   │                        │                      │                    │
   │                        │  list_recent(20, 20) │                    │
   │                        │─────────────────────>│                    │
   │                        │                      │                    │
   │                        │                      │  SELECT images     │
   │                        │                      │  OFFSET 20 LIMIT 20│
   │                        │                      │───────────────────>│
   │                        │                      │                    │
   │                        │  List[Image]         │  [Image, ...]      │
   │                        │<─────────────────────│<───────────────────│
   │                        │                      │                    │
   │                        │  templates.render(   │                    │
   │                        │    "partials/gallery_items.html")        │
   │                        │                      │                    │
   │  <div>...</div>        │                      │                    │
   │  (HTML fragment)       │                      │                    │
   │<───────────────────────│                      │                    │
   │                        │                      │                    │
   │  HTMX swaps fragment   │                      │                    │
   │  into DOM              │                      │                    │
```

## Component Dependency Graph

```
                            ┌─────────────┐
                            │   main.py   │
                            │  (Lifespan) │
                            └──────┬──────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
            ┌───────────┐  ┌───────────┐  ┌───────────┐
            │  web.py   │  │ images.py │  │  auth.py  │
            │  (Routes) │  │  (Routes) │  │  (Routes) │
            └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
                  │              │              │
                  │              │              │
                  ▼              ▼              ▼
            ┌─────────────────────────────────────────┐
            │              Dependencies               │
            │  ┌─────────────────────────────────┐   │
            │  │         get_image_service()      │   │
            │  │  ┌───────────┐ ┌───────────────┐│   │
            │  │  │ get_db()  │ │ get_storage() ││   │
            │  │  └───────────┘ └───────────────┘│   │
            │  └─────────────────────────────────┘   │
            │  ┌─────────────────────────────────┐   │
            │  │  get_current_user_from_cookie() │   │
            │  │         (web.py only)           │   │
            │  └─────────────────────────────────┘   │
            │  ┌─────────────────────────────────┐   │
            │  │       get_templates()            │   │
            │  │    (from app.state.templates)   │   │
            │  └─────────────────────────────────┘   │
            └─────────────────────────────────────────┘
                              │
                              ▼
            ┌─────────────────────────────────────────┐
            │             Services Layer              │
            │                                         │
            │  ┌─────────────┐  ┌─────────────────┐  │
            │  │ImageService │  │   AuthService   │  │
            │  │             │  │                 │  │
            │  │ list_recent │  │ verify_token    │  │
            │  │ list_by_user│  │ get_user_by_id  │  │
            │  │ get_by_id   │  │ create_user     │  │
            │  │ upload      │  │ authenticate    │  │
            │  │ delete      │  │                 │  │
            │  └─────────────┘  └─────────────────┘  │
            │                                         │
            └─────────────────────────────────────────┘
```

## File Structure

```
backend/app/
├── main.py                    # App entry, lifespan, app.state setup
├── api/
│   ├── web.py                 # Web UI routes (HTML responses)
│   ├── images.py              # REST API routes (JSON responses)
│   ├── auth.py                # Auth API routes
│   └── dependencies.py        # Shared FastAPI dependencies
├── services/
│   ├── image_service.py       # Image business logic
│   ├── auth_service.py        # Auth business logic
│   ├── storage_service.py     # File storage abstraction
│   └── thumbnail_service.py   # Thumbnail generation
├── templates/
│   ├── base.html              # Base layout (TailwindCSS, HTMX)
│   ├── home.html              # Gallery page
│   ├── image.html             # Image detail (glassmorphism)
│   ├── upload.html            # Upload form (drag-drop)
│   ├── login.html             # Login form
│   ├── register.html          # Registration form
│   ├── my_images.html         # User dashboard
│   ├── 404.html               # Error page
│   └── partials/
│       ├── nav.html           # Navigation component
│       ├── gallery_item.html  # Single image card
│       └── gallery_items.html # Multiple cards (HTMX)
└── static/
    └── .gitkeep               # Placeholder for static assets
```

## Key Design Decisions

### 1. Loose Coupling via Services
- `web.py` depends only on `ImageService`, not SQLAlchemy directly
- Makes testing easier (mock service, not database)
- Same pattern as `images.py` REST API

### 2. Single Source of Truth for Templates
- Templates configured in `main.py`, stored in `app.state.templates`
- `web.py` accesses via `get_templates(request)` helper
- No duplicate Jinja2Templates instantiation

### 3. Cookie-Based Auth for Web UI
- `get_current_user_from_cookie()` extracts JWT from `chitram_auth` cookie
- Returns `None` for anonymous (doesn't raise exception)
- Allows mixed authenticated/anonymous pages

### 4. HTMX for Progressive Enhancement
- Initial page load is full HTML (SEO-friendly)
- Subsequent interactions use HTML fragments
- `/partials/*` endpoints return only the needed HTML

## Security Considerations

| Concern | Implementation |
|---------|----------------|
| XSS | Jinja2 auto-escapes by default |
| CSRF | TODO: Add CSRF tokens (Phase 3D) |
| Cookie Security | TODO: httpOnly, Secure, SameSite (Phase 3D) |
| Auth Bypass | Routes check `user` before rendering protected content |
