# Image Hosting App

A simple image hosting API built with FastAPI for learning distributed systems concepts.

## Quick Start

### Using GitHub Codespaces (Recommended)

**Zero local setup required!**

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new)

1. Push this repo to GitHub
2. Go to your repo → Click **Code** → **Codespaces** → **Create codespace**
3. Wait 2-3 minutes for setup
4. Start the API:
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload --host 0.0.0.0
   ```
5. Click the popup to open port 8000 → Access Swagger at `/docs`

**Free tier:** 60 hours/month (plenty for learning!)

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
5. Open http://localhost:8000/docs

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

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/images/upload` | Upload an image |
| GET | `/api/v1/images/{id}` | Get image metadata |
| GET | `/api/v1/images/{id}/file` | Download image file |
| DELETE | `/api/v1/images/{id}` | Delete an image |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

## Usage Examples

### Upload an image

```bash
curl -X POST http://localhost:8000/api/v1/images/upload \
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

### Delete image

```bash
curl -X DELETE http://localhost:8000/api/v1/images/{image_id}
```

## Development

### Run Tests

```bash
cd backend

# All tests
uv run pytest

# With coverage
uv run pytest --cov=app

# Specific test file
uv run pytest tests/api/test_images.py -v
```

### Code Quality

```bash
# Format
uv run black .

# Lint
uv run ruff check --fix .

# Type check
uv run mypy app/
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
image-hosting-app/
├── backend/
│   ├── app/
│   │   ├── api/           # Route handlers
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── utils/         # Helpers
│   │   ├── main.py        # FastAPI app
│   │   ├── config.py      # Settings
│   │   └── database.py    # DB setup
│   ├── tests/
│   ├── pyproject.toml
│   └── .env.example
├── docs/
│   ├── adr/               # Architecture decisions
│   └── ...
└── .devcontainer/         # Dev environment
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `STORAGE_BACKEND` | `local` or `minio` | `minio` |
| `MAX_FILE_SIZE_MB` | Max upload size | `5` |
| `ALLOWED_CONTENT_TYPES` | Accepted MIME types | `image/jpeg,image/png` |

## Documentation

- [Requirements](docs/requirements/phase1.md) - Phase 1 requirements
- [Design Document](image-hosting-mvp-distributed-systems.md) - Architecture & distributed systems concepts
- [ADRs](docs/adr/) - Architecture decision records
- [Development Workflow](docs/development-workflow.md) - How to contribute

## License

MIT
