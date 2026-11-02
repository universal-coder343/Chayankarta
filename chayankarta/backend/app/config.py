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
    database_name: str = "chayankarta"

    # CORS
    cors_origins: str = '["http://localhost:5173"]'

    # Railway / deployment
    railway_public_domain: str = ""

    # Logging
    log_level: str = "INFO"

    # File uploads
    upload_dir: str = "./uploads"

    # ------------------------------------------------------------------ #
    # Milestone 4 — Semantic Ranking
    # ------------------------------------------------------------------ #

    # Sentence-Transformers model name
    embedding_model: str = "all-MiniLM-L6-v2"

    # Hybrid scoring weights (must sum to 1.0)
    weight_semantic: float = 0.40
    weight_skill: float = 0.35
    weight_experience: float = 0.15
    weight_education: float = 0.10

    # ------------------------------------------------------------------ #
    # Milestone 5 — Fairness & PII Redaction
    # ------------------------------------------------------------------ #

    # Master toggle: enable PII redaction before embedding/scoring
    enable_redaction: bool = True

    # Toggle: also redact college/institution names (blind screening)
    redact_institutions: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from JSON string to list.
        Automatically includes Railway public domain if set."""
        origins = json.loads(self.cors_origins)
        if self.railway_public_domain:
            origins.append(f"https://{self.railway_public_domain}")
        return origins

    @property
    def default_weights(self) -> dict[str, float]:
        """Return the default scoring weights as a dict."""
        return {
            "semantic": self.weight_semantic,
            "skill": self.weight_skill,
            "experience": self.weight_experience,
            "education": self.weight_education,
        }


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
