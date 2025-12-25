# Testing Strategy

**Project:** Chitram - Image Hosting API
**Purpose:** Define testing approach for distributed systems learning

---

## Testing Pyramid

```
                    ┌───────────────┐
                    │   E2E / Load  │  ← Few, slow, expensive
                    │    Testing    │
                    ├───────────────┤
                    │     API       │  ← Service boundaries
                    │  Integration  │
                ┌───┴───────────────┴───┐
                │      Unit Testing      │  ← Many, fast, cheap
                └───────────────────────┘
```

---

## Test Types & Tools

| Test Type | Tool | When to Run | Purpose |
|-----------|------|-------------|---------|
| **Unit** | pytest | Every change | Test functions in isolation |
| **API** | pytest + httpx | Every change | Test HTTP endpoints |
| **Integration** | pytest + testcontainers | Before merge | Test with real services |
| **Load** | locust | Before release | Validate scalability |
| **Contract** | schemathesis | API changes | Validate OpenAPI spec |

---

## Current Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── api/
│   ├── __init__.py
│   └── test_images.py       # API endpoint tests
└── unit/                    # Future: unit tests
```

---

## Test Fixtures

### Image Fixtures (conftest.py)

```python
@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    """Create a valid JPEG test image."""
    img = PILImage.new("RGB", (100, 100), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.read()

@pytest.fixture
def invalid_file_bytes() -> bytes:
    """Create invalid (non-image) file content."""
    return b"This is not an image file"
```

### Test Client Fixture

```python
@pytest.fixture
async def client(test_db, test_storage):
    """Async test client with overridden dependencies."""
    app.dependency_overrides[get_db] = lambda: test_db
    app.state.storage = test_storage

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
```

---

## Test Coverage by Endpoint

| Endpoint | Happy Path | Error Cases | Status |
|----------|------------|-------------|--------|
| `POST /upload` | ✅ JPEG, PNG | ✅ Invalid type, no file | Done |
| `GET /{id}` | ✅ Existing | ✅ Not found | Done |
| `GET /{id}/file` | ✅ Download | ✅ Not found | Done |
| `DELETE /{id}` | ✅ Existing | ✅ Not found | Done |
| `GET /health` | ✅ Status | - | Done |

---

## Running Tests

```bash
cd backend

# All tests
uv run pytest

# Verbose output
uv run pytest -v

# Specific file
uv run pytest tests/api/test_images.py

# With coverage
uv run pytest --cov=app --cov-report=term-missing

# Stop on first failure
uv run pytest -x
```

---

## Test Patterns

### Arrange-Act-Assert

```python
async def test_upload_valid_jpeg(client, sample_jpeg_bytes):
    # Arrange
    files = {"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")}

    # Act
    response = await client.post("/api/v1/images/upload", files=files)

    # Assert
    assert response.status_code == 201
    assert response.json()["content_type"] == "image/jpeg"
```

### Test Independence

Each test should:
- Create its own test data
- Not depend on other tests
- Clean up after itself (handled by fixtures)

---

## Known Issues

### Pillow Dependency

The test fixtures use Pillow to generate test images, but Pillow is listed under `[project.optional-dependencies].future`.

**Workarounds:**
1. Install with `uv sync --all-extras`
2. Or add Pillow to dev dependencies
3. Or use static fixture files instead

---

## Future Improvements

### Phase 1.5
- [ ] Add width/height assertions after Pillow integration

### Phase 2
- [ ] Integration tests with real PostgreSQL (testcontainers)
- [ ] Cache hit/miss tests
- [ ] Background job tests

### Phase 3
- [ ] Load testing with locust
- [ ] Multi-instance tests

### Phase 4
- [ ] Chaos testing (failure injection)
- [ ] Performance regression tests

---

## CI Integration (Future)

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: cd backend && uv sync --all-extras
      - name: Run tests
        run: cd backend && uv run pytest --cov=app
```

---

**Document Version:** 1.0
**Last Updated:** 2025-12-24
