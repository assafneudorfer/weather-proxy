from fastapi import Request

from app.services.cache_service import CacheService
from app.services.open_meteo_client import OpenMeteoClient
from app.services.weather_service import WeatherService

# Singleton client for Open-Meteo API
_open_meteo_client: OpenMeteoClient | None = None


def get_open_meteo_client() -> OpenMeteoClient:
    """Get or create singleton Open-Meteo client."""
    global _open_meteo_client
    if _open_meteo_client is None:
        _open_meteo_client = OpenMeteoClient()
    return _open_meteo_client


async def get_cache_service(request: Request) -> CacheService:
    """Get cache service with Redis client from app state."""
    return CacheService(request.app.state.redis)


async def get_weather_service(request: Request) -> WeatherService:
    """Get weather service with all dependencies."""
    cache_service = CacheService(request.app.state.redis)
    open_meteo_client = get_open_meteo_client()
    return WeatherService(open_meteo_client, cache_service)
