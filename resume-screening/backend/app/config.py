"""
Application configuration using pydantic-settings.
Reads from environment variables and .env file.
"""

import json
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "resume_screening"

    # CORS
    cors_origins: str = '["http://localhost:5173"]'

    # Logging
    log_level: str = "INFO"

    # File uploads
    upload_dir: str = "./uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from JSON string to list."""
        return json.loads(self.cors_origins)


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
