# Phase 3 UI - Local Development Runbook

Quick guide to run and test the Chitram Web UI locally.

## Prerequisites

- Python 3.11+
- uv package manager
- (Optional) Docker for PostgreSQL/Redis

## Quick Start

### 1. Navigate to Backend

```bash
cd backend
```

### 2. Install Dependencies

```bash
uv sync --all-extras
```

### 3. Start the Server

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open in Browser

| Page | URL | Description |
|------|-----|-------------|
| **Home/Gallery** | http://localhost:8000/ | Browse all images |
| **Upload** | http://localhost:8000/upload | Upload new image |
| **Login** | http://localhost:8000/login | User login |
| **Register** | http://localhost:8000/register | Create account |
| **My Images** | http://localhost:8000/my-images | User dashboard (requires login) |
| **API Docs** | http://localhost:8000/docs | Swagger UI |

## Testing the UI Flow

### Anonymous User Flow

1. Go to http://localhost:8000/
2. Click "Upload" in nav
3. Drag & drop or select a JPEG/PNG image
4. Click "Upload Image"
5. Note the **delete token** shown (save it!)
6. View your image on the detail page
7. Click "Chitram" logo to return to gallery

### Registered User Flow

1. Go to http://localhost:8000/register
2. Create account with email/password
3. Upload an image (no delete token needed)
4. Go to "My Images" to see your uploads
5. Click delete button to remove images
6. Logout via nav menu

## Environment Variables

Create `.env` file in `backend/` directory:

```bash
# Database (defaults to SQLite for dev)
DATABASE_URL=sqlite+aiosqlite:///./chitram.db

# Storage (defaults to local filesystem)
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./uploads

# Optional: Enable Redis caching
CACHE_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379

# Optional: Rate limiting
RATE_LIMIT_ENABLED=false

# Debug mode
DEBUG=true
```

## With Docker Services (Optional)

If you want PostgreSQL + Redis:

```bash
# Start services
docker-compose up -d

# Update .env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/chitram
CACHE_ENABLED=true
REDIS_HOST=localhost

# Run migrations
uv run alembic upgrade head

# Start server
uv run uvicorn app.main:app --reload
```

## Troubleshooting

### "Template not found" Error

Ensure you're running from the `backend/` directory:
```bash
cd backend
uv run uvicorn app.main:app --reload
```

### Images Not Showing

1. Check `uploads/` directory exists
2. Verify storage backend is configured:
   ```bash
   ls -la uploads/
   ```

### Auth Not Working

1. Clear browser cookies for localhost
2. Check JWT secret is set (uses default in dev)

### Database Errors

Reset the database:
```bash
rm chitram.db
uv run alembic upgrade head
```

## Development Tips

### Hot Reload

The `--reload` flag watches for file changes. Template changes are picked up automatically.

### Browser Dev Tools

- **Network tab**: Watch HTMX requests
- **Application tab**: View cookies (`chitram_auth`)
- **Responsive mode**: Test mobile layouts

### Tailwind Classes

We use TailwindCSS CDN. Custom colors available:
- `terracotta-400/500/600` - Primary accent
- `cream-100/200` - Background colors

### HTMX Debugging

Add to any page:
```html
<script>
  htmx.logAll();
</script>
```

## Page Status

| Page | Status | Notes |
|------|--------|-------|
| Home (Gallery) | ✅ Working | Masonry grid, load more |
| Image Detail | ✅ Working | Dark mode, glassmorphism |
| Upload | ✅ Working | Drag-drop, preview |
| Login | ✅ Working | Cookie-based auth |
| Register | ✅ Working | Auto-login after register |
| My Images | ✅ Working | Delete with confirmation |
| 404 | ✅ Working | Custom error page |

## Next Steps (Phase 3B-D)

See [TODO.md](../TODO.md) for remaining Phase 3 tasks:
- CSRF protection
- httpOnly cookies (security hardening)
- More HTMX interactions
- Responsive polish
- Accessibility improvements
