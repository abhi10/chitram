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
    db_pool_size: int = 5  # Number of persistent connections
    db_max_overflow: int = 10  # Additional connections allowed beyond pool_size
    db_pool_recycle: int = 3600  # Recycle connections after 1 hour (seconds)

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
    minio_startup_timeout: float = 10.0  # Timeout for bucket check at startup (seconds)

    # Redis Configuration (Phase 2)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_db: int = 0
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour default
    cache_key_prefix: str = "chitram"
    cache_debug: bool = False  # Log cache operations when True

    # Application
    app_env: str = "development"
    debug: bool = True

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 10
    rate_limit_window_seconds: int = 60  # 1 minute window

    # Concurrency Control (ADR-0010)
    upload_concurrency_limit: int = 10  # Max simultaneous uploads
    upload_concurrency_timeout: float = 30.0  # Seconds to wait for semaphore

    # File Upload
    max_file_size_mb: int = 5
    allowed_content_types: str = "image/jpeg,image/png"

    # JWT Authentication (Phase 2A)
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"  # Required in production
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # Auth Provider (Phase 3.5)
    auth_provider: str = "local"  # "local" or "supabase"

    # Supabase Configuration (only used when auth_provider = "supabase")
    supabase_url: str | None = None
    supabase_anon_key: str | None = None

    # AI Tagging Configuration (Phase 5)
    ai_provider: str = "mock"  # "openai", "google", "mock"
    ai_confidence_threshold: int = 70  # Filter tags below this confidence
    ai_max_tags_per_image: int = 10  # Cost control: limit tags per image

    # OpenAI Vision settings (used when ai_provider = "openai")
    openai_api_key: str | None = None
    openai_vision_model: str = "gpt-4o-mini"  # Cost-efficient model (~$0.004/image)
    openai_vision_prompt: str = (
        "Generate 10 descriptive tags for this image. "
        "Return only tag names separated by commas, no explanations."
    )

    # Google Cloud Vision settings (used when ai_provider = "google")
    google_vision_api_key: str | None = None

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
