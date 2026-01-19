import structlog

from app.schemas.weather import WeatherResponse
from app.services.cache_service import CacheService
from app.services.open_meteo_client import OpenMeteoClient

logger = structlog.get_logger()


class WeatherService:
    """Business logic for weather operations."""

    def __init__(self, open_meteo_client: OpenMeteoClient, cache_service: CacheService):
        self.client = open_meteo_client
        self.cache = cache_service

    async def get_weather_for_city(self, city: str) -> WeatherResponse:
        """Get weather for a city, with caching."""
        # Check cache first
        cached = await self.cache.get_weather(city)
        if cached:
            logger.info("returning_cached_weather", city=city)
            return WeatherResponse(**cached, cached=True)

        # Fetch fresh data
        logger.info("fetching_fresh_weather", city=city)

        # Get coordinates
        geo = await self.client.geocode_city(city)

        # Get weather
        weather = await self.client.get_weather(geo.latitude, geo.longitude)

        # Build response
        response = WeatherResponse(
            city=geo.name,
            country=geo.country,
            latitude=geo.latitude,
            longitude=geo.longitude,
            temperature=weather.temperature,
            humidity=weather.humidity,
            weather_code=weather.weather_code,
            wind_speed=weather.wind_speed,
            timezone=weather.timezone or geo.timezone,
            timestamp=weather.timestamp,
            cached=False,
        )

        # Cache the result (exclude cached field from stored data)
        cache_data = response.model_dump()
        cache_data.pop("cached", None)
        await self.cache.set_weather(city, cache_data)

        return response
