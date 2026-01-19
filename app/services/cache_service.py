import json

import structlog
from redis.asyncio import Redis

from app.config import Settings, get_settings

logger = structlog.get_logger()


class CacheService:
    """Redis caching service for weather data."""

    def __init__(self, redis_client: Redis, settings: Settings | None = None):
        self.redis = redis_client
        self.settings = settings or get_settings()

    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create cache key with prefix."""
        return f"weather-proxy:{prefix}:{identifier.lower()}"

    async def get_weather(self, city: str) -> dict | None:
        """Get cached weather data for city."""
        key = self._make_key("weather", city)
        try:
            data = await self.redis.get(key)
            if data:
                logger.debug("cache_hit", key=key)
                return json.loads(data)
            logger.debug("cache_miss", key=key)
            return None
        except Exception as e:
            logger.warning("cache_get_error", key=key, error=str(e))
            return None

    async def set_weather(self, city: str, data: dict) -> None:
        """Cache weather data for city."""
        key = self._make_key("weather", city)
        try:
            await self.redis.set(
                key,
                json.dumps(data),
                ex=self.settings.cache_ttl_seconds,
            )
            logger.debug("cache_set", key=key, ttl=self.settings.cache_ttl_seconds)
        except Exception as e:
            logger.warning("cache_set_error", key=key, error=str(e))

    async def health_check(self) -> bool:
        """Check Redis connectivity."""
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False
