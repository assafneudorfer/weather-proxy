import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "weather-proxy"
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"  # "json" for production, "console" for development

    # Redis
    redis_url: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    cache_ttl_seconds: int = 300  # 5 minutes

    # Open-Meteo API
    open_meteo_base_url: str = "https://api.open-meteo.com/v1"
    geocoding_base_url: str = "https://geocoding-api.open-meteo.com/v1"

    # Circuit Breaker
    circuit_breaker_fail_max: int = 5
    circuit_breaker_reset_timeout: int = 60

    # HTTP Client
    http_timeout_seconds: float = 10.0
    http_max_retries: int = 3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
