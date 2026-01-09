# Chitram - Image Hosting App

A production-ready image hosting application built with FastAPI, featuring a web UI and Supabase authentication.

**Live Demo:** https://chitram.io

## Features

- **Web UI** - Upload, view, and manage images with a responsive gallery
- **Authentication** - Secure login via Supabase (email/password)
- **Private Galleries** - Each user sees only their own images
- **Thumbnails** - Auto-generated 300px thumbnails for fast loading
- **API** - Full REST API with Swagger documentation

## Tech Stack

- **Backend:** FastAPI, PostgreSQL, MinIO (S3-compatible storage)
- **Frontend:** HTMX, Jinja2, TailwindCSS
- **Auth:** Supabase (production) / Local JWT (development)
- **Infrastructure:** DigitalOcean, Docker, Caddy

## Quick Start

### Using GitHub Codespaces (Recommended)

**Zero local setup required!**

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new)

1. Go to your repo -> Click **Code** -> **Codespaces** -> **Create codespace**
2. Wait 2-3 minutes for setup
3. Start the API:
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload --host 0.0.0.0
   ```
4. Click the popup to open port 8000
5. Access the app at the forwarded URL

### Using Local DevContainer

> Requires Docker Desktop (uses 2-4GB RAM)

1. Open in VS Code
2. Click "Reopen in Container" when prompted
3. Wait for setup to complete
4. Start the API:
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload --host 0.0.0.0
   ```
5. Open http://localhost:8000

### Manual Setup

**Prerequisites:**
- Python 3.11+
- PostgreSQL 16
- MinIO (or S3-compatible storage)
- [uv](https://docs.astral.sh/uv/) package manager

**Steps:**

```bash
# Clone and navigate
cd image-hosting-app/backend

# Install dependencies
uv sync

# Copy environment config
cp .env.example .env

# Start PostgreSQL and MinIO (via Docker)
docker-compose -f ../.devcontainer/docker-compose.yml up -d postgres minio

# Run migrations
uv run alembic upgrade head

# Start the API
uv run uvicorn app.main:app --reload
```

## Web Pages

| Page | URL | Description |
|------|-----|-------------|
| Home | `/` | Your image gallery (login required) |
| Upload | `/upload` | Upload new images |
| My Images | `/my-images` | Manage your uploads |
| Login | `/login` | Sign in |
| Register | `/register` | Create account |

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/images/upload` | Upload an image | Required |
| GET | `/api/v1/images/{id}` | Get image metadata | - |
| GET | `/api/v1/images/{id}/file` | Download image file | - |
| GET | `/api/v1/images/{id}/thumbnail` | Get thumbnail | - |
| DELETE | `/api/v1/images/{id}` | Delete an image | Owner only |
| POST | `/api/v1/auth/register` | Create account | - |
| POST | `/api/v1/auth/login` | Get JWT token | - |
| GET | `/api/v1/auth/me` | Current user profile | Required |
| GET | `/health` | Health check | - |
| GET | `/docs` | Swagger UI | - |

## Usage Examples

### Upload an image (authenticated)

```bash
# Get a token first
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"yourpassword"}' | jq -r '.access_token')

# Upload with token
curl -X POST http://localhost:8000/api/v1/images/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@photo.jpg"
```

### Get image metadata

```bash
curl http://localhost:8000/api/v1/images/{image_id}
```

### Download image

```bash
curl http://localhost:8000/api/v1/images/{image_id}/file --output image.jpg
```

## Development

### Run Tests

```bash
cd backend

# All tests (255 tests)
uv run pytest

# With coverage
uv run pytest --cov=app

# Specific test file
uv run pytest tests/api/test_images.py -v
```

### Code Quality

Pre-commit hooks run automatically on every commit:

```bash
# Run manually
uv run pre-commit run --all-files

# Or individual tools
uv run ruff check --fix .  # Lint
uv run ruff format .       # Format
```

### Database Migrations

```bash
# Create migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

## Project Structure

```
chitram/
├── backend/
│   ├── app/
│   │   ├── api/           # Route handlers (images, auth, web)
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   │   └── auth/      # Pluggable auth providers
│   │   ├── templates/     # Jinja2 templates
│   │   ├── static/        # CSS, JS
│   │   ├── main.py        # FastAPI app
│   │   ├── config.py      # Settings
│   │   └── database.py    # DB setup
│   ├── tests/             # 255 tests
│   ├── alembic/           # DB migrations
│   └── pyproject.toml
├── browser-tests/         # E2E tests with Playwright
├── docs/
│   ├── adr/               # Architecture decisions (15 ADRs)
│   ├── deployment/        # Deployment guides
│   ├── retrospectives/    # Incident retrospectives
│   └── requirements/      # Phase requirements
├── scripts/               # Automation scripts
└── .devcontainer/         # Dev environment
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `STORAGE_BACKEND` | `local` or `minio` | `minio` |
| `AUTH_PROVIDER` | `local` or `supabase` | `local` |
| `SUPABASE_URL` | Supabase project URL | - |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | - |
| `MAX_FILE_SIZE_MB` | Max upload size | `5` |
| `ALLOWED_CONTENT_TYPES` | Accepted MIME types | `image/jpeg,image/png` |

## Documentation

- [TODO & Progress](TODO.md) - Current status and roadmap
- [CLAUDE.md](CLAUDE.md) - Developer guide and patterns
- [Requirements](docs/requirements/) - Phase requirements
- [ADRs](docs/adr/) - Architecture decision records
- [Deployment](docs/deployment/) - Deployment guides

## Project Status

- **Phase 3.5 Complete** - Supabase Auth + Production Deployed
- **255 tests passing**
- **Live at:** https://chitram.io

See [TODO.md](TODO.md) for detailed progress.

## License

MIT

---

**Project Name:** Chitram (చిత్రం - Image/Picture in Telugu)
