"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://app:localdev@localhost:5432/imagehost"

    # Storage Backend
    storage_backend: str = "local"  # "local" or "minio"

    # Local Storage
    local_storage_path: str = "./uploads"

    # MinIO Configuration (Phase 2)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "images"
    minio_secure: bool = False  # True for HTTPS

    # Application
    app_env: str = "development"
    debug: bool = True

    # Rate Limiting
    rate_limit_per_minute: int = 10

    # File Upload
    max_file_size_mb: int = 5
    allowed_content_types: str = "image/jpeg,image/png"

    @property
    def max_file_size_bytes(self) -> int:
        """Max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def allowed_content_types_list(self) -> list[str]:
        """List of allowed content types."""
        return [ct.strip() for ct in self.allowed_content_types.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
