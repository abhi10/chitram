# Python Coding Guidelines - Image Hosting App

Guidelines for AI assistants working on this Python project.

---

## Python Version & Tooling

### Version
- **Python 3.11+** required
- Use modern syntax: `str | None` not `Optional[str]`
- Use `match` statements where appropriate

### Package Manager: uv
Always use `uv` for package management, never raw `pip`:

```bash
# Install dependencies
uv sync

# Add a package
uv add <package>

# Add dev dependency
uv add --dev <package>

# Run commands
uv run pytest
uv run uvicorn app.main:app --reload

# NEVER use:
# pip install ...
# python -m pip ...
```

### Formatting & Linting
```bash
# Format code
uv run black .

# Lint and auto-fix
uv run ruff check --fix .

# Type checking
uv run mypy app/
```

Always resolve linter and type errors before committing.

---

## Project Structure

```
image-hosting-app/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Settings (pydantic-settings)
│   ├── database.py          # SQLAlchemy async setup
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # Route handlers
│   ├── services/            # Business logic
│   └── utils/               # Helpers
├── tests/
│   ├── unit/
│   ├── api/
│   └── integration/
├── pyproject.toml           # Project config (uv)
└── docker-compose.yml
```

---

## Import Conventions

### Order (enforced by ruff)
1. Standard library
2. Third-party packages
3. Local application imports

### Style
```python
# GOOD: Absolute imports
from app.services.image_service import ImageService
from app.schemas.image import ImageCreate, ImageResponse

# BAD: Relative imports
from ..services.image_service import ImageService
from .image import ImageCreate

# GOOD: Type imports
from collections.abc import Sequence
from typing import TypeVar, Generic

# GOOD: Path handling
from pathlib import Path
config_path = Path("config") / "settings.yaml"

# BAD: String paths
config_path = "config/settings.yaml"
```

---

## Type Annotations

### Required everywhere
```python
# GOOD: Full type hints
async def upload_image(
    file: UploadFile,
    db: AsyncSession,
) -> ImageResponse:
    ...

# BAD: Missing types
async def upload_image(file, db):
    ...
```

### Modern syntax
```python
# GOOD: Modern union syntax (3.10+)
def get_image(image_id: str) -> Image | None:
    ...

# BAD: Old Optional syntax
def get_image(image_id: str) -> Optional[Image]:
    ...

# GOOD: Modern generic syntax
def process_items(items: list[str]) -> dict[str, int]:
    ...

# BAD: Old generic syntax
def process_items(items: List[str]) -> Dict[str, int]:
    ...
```

---

## FastAPI Conventions

### Router organization
```python
# app/api/images.py
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/api/v1/images", tags=["images"])

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(...) -> ImageResponse:
    ...
```

### Dependency injection
```python
# GOOD: Use Depends for services
@router.get("/{image_id}")
async def get_image(
    image_id: str,
    service: ImageService = Depends(get_image_service),
) -> ImageResponse:
    ...

# BAD: Instantiate in handler
@router.get("/{image_id}")
async def get_image(image_id: str) -> ImageResponse:
    service = ImageService()  # Don't do this
    ...
```

### Error responses
Use the project's structured error format:

```python
from app.schemas.error import ErrorResponse, ErrorDetail

# GOOD: Structured errors
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail=ErrorDetail(
        code="INVALID_FILE_FORMAT",
        message="Only JPEG and PNG formats are supported",
    ).model_dump(),
)

# BAD: Plain string errors
raise HTTPException(
    status_code=400,
    detail="Invalid file format",
)
```

Error codes (defined in requirements.md):
- `INVALID_FILE_FORMAT` - Not JPEG or PNG
- `FILE_TOO_LARGE` - Exceeds 5 MB
- `INVALID_REQUEST` - Malformed request
- `IMAGE_NOT_FOUND` - Image ID doesn't exist
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INTERNAL_ERROR` - Server error

---

## Pydantic Conventions

### Schema patterns
```python
from pydantic import BaseModel, Field, ConfigDict

class ImageBase(BaseModel):
    """Base schema with common fields"""
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str

class ImageCreate(ImageBase):
    """Schema for creating an image (request)"""
    pass

class ImageResponse(ImageBase):
    """Schema for image response"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_size: int
    width: int | None = None
    height: int | None = None
    created_at: datetime
```

### Validation
```python
from pydantic import field_validator

class ImageCreate(BaseModel):
    content_type: str

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        allowed = {"image/jpeg", "image/png"}
        if v not in allowed:
            raise ValueError(f"Content type must be one of: {allowed}")
        return v
```

---

## SQLAlchemy Conventions

### Async patterns
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# GOOD: Async query
async def get_image(db: AsyncSession, image_id: str) -> Image | None:
    result = await db.execute(
        select(Image).where(Image.id == image_id)
    )
    return result.scalar_one_or_none()

# GOOD: Async insert
async def create_image(db: AsyncSession, image: ImageCreate) -> Image:
    db_image = Image(**image.model_dump())
    db.add(db_image)
    await db.commit()
    await db.refresh(db_image)
    return db_image
```

### Model definitions
```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime
from datetime import datetime
import uuid

class Image(Base):
    __tablename__ = "images"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    filename: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
```

---

## Testing Conventions

### Approach: Mixed TDD
- **TDD (test first)**: Complex logic, validation, business rules
- **Test after**: Simple CRUD, straightforward endpoints

### File organization
```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Fast, isolated tests
│   └── test_*.py
├── api/                 # HTTP endpoint tests
│   └── test_*.py
└── integration/         # Tests with real DB/Redis
    └── test_*.py
```

### Fixtures
```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_image_bytes():
    from PIL import Image
    import io
    img = Image.new("RGB", (100, 100), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.read()
```

### Test style
```python
# GOOD: Descriptive test names
async def test_upload_rejects_file_larger_than_5mb(client):
    ...

# GOOD: Arrange-Act-Assert pattern
async def test_get_image_returns_metadata(client, sample_image_bytes):
    # Arrange
    upload_response = await client.post(
        "/api/v1/images/upload",
        files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
    )
    image_id = upload_response.json()["id"]

    # Act
    response = await client.get(f"/api/v1/images/{image_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["filename"] == "test.jpg"
```

---

## Documentation

### Docstrings
```python
# GOOD: Explain WHY, not WHAT
async def deduplicate_image(checksum: str) -> Image | None:
    """
    Find existing image by checksum to avoid storing duplicates.
    Returns None if no duplicate exists.
    """
    ...

# BAD: Repeats the obvious
async def get_image(image_id: str) -> Image | None:
    """Gets an image by ID and returns it or None."""  # Obvious from signature
    ...
```

### Comments
```python
# GOOD: Explain non-obvious logic
# Rate limit window resets at the start of each minute, not rolling
window_start = now.replace(second=0, microsecond=0)

# BAD: Obvious comments
# Get the image from the database
image = await db.get(Image, image_id)
```

---

## Common Commands

```bash
# Development
uv sync                              # Install dependencies
uv run uvicorn app.main:app --reload # Run dev server
docker-compose up -d                 # Start PostgreSQL

# Testing
uv run pytest tests/unit -v          # Unit tests
uv run pytest tests/api -v           # API tests
uv run pytest --cov=app              # With coverage

# Code quality
uv run black .                       # Format
uv run ruff check --fix .            # Lint
uv run mypy app/                     # Type check

# Database
uv run alembic upgrade head          # Run migrations
uv run alembic revision --autogenerate -m "description"  # New migration
```

---

## Project-Specific Rules

### Image validation
- Accept only: `image/jpeg`, `image/png`
- Max file size: 5 MB
- Validate magic bytes, not just Content-Type header

### Storage keys
- Use UUID for storage keys, not original filenames
- Format: `{uuid}.{extension}`

### Error handling
- Always use structured error format (see ADR-0005)
- Include appropriate HTTP status codes
- Log errors with context

### Security
- Sanitize filenames (no path traversal)
- Store files outside web root
- Validate file content matches declared type

---

## References

- [requirements.md](../../requirements.md) - Functional requirements
- [ADR-0005](../../docs/adr/0005-structured-error-format.md) - Error format
- [development-workflow.md](../../docs/development-workflow.md) - Workflow guide
