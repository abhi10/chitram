"""Tests to verify template fetch URLs match actual API routes.

This test prevents bugs where templates call URLs that don't exist,
like calling /auth/login when the actual route is /api/v1/auth/login.
"""

import re
from pathlib import Path

import pytest

from app.main import app

# Path to templates directory
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "templates"


def get_app_routes() -> dict[str, set[str]]:
    """Get all routes from the FastAPI app, grouped by path."""
    routes: dict[str, set[str]] = {}
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            path = route.path
            for method in route.methods:
                if method != "HEAD":  # Skip auto-generated HEAD
                    if path not in routes:
                        routes[path] = set()
                    routes[path].add(method)
    return routes


def extract_fetch_urls_from_template(template_path: Path) -> list[tuple[str, str, int]]:
    """
    Extract fetch() URLs from a template file.

    Returns list of (url, method, line_number) tuples.
    """
    content = template_path.read_text()
    results = []
    lines = content.split("\n")

    # Find all fetch calls and their methods by looking at multi-line context
    # Pattern: fetch('/url', { ... method: 'POST' ... })
    for line_num, line in enumerate(lines, 1):
        # Match fetch('url' or fetch("url"
        fetch_match = re.search(r"fetch\(['\"]([^'\"]+)['\"]", line)
        if fetch_match:
            url = fetch_match.group(1)

            # Look for method in the next 5 lines (handles multi-line fetch calls)
            method = "GET"  # Default
            context_lines = lines[line_num - 1 : line_num + 5]
            context = "\n".join(context_lines)
            method_match = re.search(r"method:\s*['\"](\w+)['\"]", context)
            if method_match:
                method = method_match.group(1).upper()

            results.append((url, method, line_num))

    return results


def normalize_path_for_matching(path: str) -> str:
    """
    Normalize path for matching, replacing path parameters with regex pattern.

    e.g., /api/v1/images/{image_id} -> /api/v1/images/[^/]+
    """
    return re.sub(r"\{[^}]+\}", "[^/]+", path)


def path_matches_route(url: str, route_path: str) -> bool:
    """Check if a URL matches a route path (handling path parameters)."""
    pattern = "^" + normalize_path_for_matching(route_path) + "$"
    return bool(re.match(pattern, url))


class TestTemplateFetchUrls:
    """Test that all fetch() URLs in templates match actual API routes."""

    @pytest.fixture
    def app_routes(self) -> dict[str, set[str]]:
        """Get all routes from the app."""
        return get_app_routes()

    def test_all_template_fetch_urls_exist(self, app_routes: dict[str, set[str]]):
        """Every fetch() URL in templates should match an actual route."""
        errors = []

        for template_path in TEMPLATES_DIR.glob("**/*.html"):
            fetch_urls = extract_fetch_urls_from_template(template_path)

            for url, method, line_num in fetch_urls:
                # Skip external URLs
                if url.startswith("http://") or url.startswith("https://"):
                    continue

                # Check if URL matches any route
                found = False
                for route_path, methods in app_routes.items():
                    if path_matches_route(url, route_path):
                        if method in methods:
                            found = True
                            break
                        # Path exists but method doesn't match
                        errors.append(
                            f"{template_path.name}:{line_num}: "
                            f"fetch('{url}') uses {method} but route only accepts {methods}"
                        )
                        found = True  # Don't also report as missing
                        break

                if not found:
                    errors.append(
                        f"{template_path.name}:{line_num}: "
                        f"fetch('{url}') with {method} does not match any route"
                    )

        if errors:
            error_msg = "Template fetch URLs that don't match API routes:\n" + "\n".join(
                f"  - {e}" for e in errors
            )
            pytest.fail(error_msg)

    def test_auth_routes_use_api_prefix(self, app_routes: dict[str, set[str]]):
        """Auth-related fetch calls should use /api/v1/auth/ prefix."""
        errors = []

        for template_path in TEMPLATES_DIR.glob("**/*.html"):
            fetch_urls = extract_fetch_urls_from_template(template_path)

            for url, _method, line_num in fetch_urls:
                # Check for common mistakes: /auth/* instead of /api/v1/auth/*
                if url.startswith("/auth/"):
                    errors.append(
                        f"{template_path.name}:{line_num}: "
                        f"fetch('{url}') should use '/api/v1{url}' instead"
                    )

        if errors:
            error_msg = (
                "Templates using incorrect auth paths (should use /api/v1/auth/*):\n"
                + "\n".join(f"  - {e}" for e in errors)
            )
            pytest.fail(error_msg)

    def test_login_template_posts_to_correct_endpoint(self):
        """Login template should POST to /api/v1/auth/login."""
        login_template = TEMPLATES_DIR / "login.html"
        if not login_template.exists():
            pytest.skip("login.html not found")

        content = login_template.read_text()
        assert (
            "/api/v1/auth/login" in content
        ), "login.html should contain fetch('/api/v1/auth/login')"
        assert (
            "/auth/login" not in content or "/api/v1/auth/login" in content
        ), "login.html should not use '/auth/login' (missing /api/v1 prefix)"

    def test_register_template_posts_to_correct_endpoint(self):
        """Register template should POST to /api/v1/auth/register."""
        register_template = TEMPLATES_DIR / "register.html"
        if not register_template.exists():
            pytest.skip("register.html not found")

        content = register_template.read_text()
        assert (
            "/api/v1/auth/register" in content
        ), "register.html should contain fetch('/api/v1/auth/register')"
        assert (
            "/auth/register" not in content or "/api/v1/auth/register" in content
        ), "register.html should not use '/auth/register' (missing /api/v1 prefix)"
