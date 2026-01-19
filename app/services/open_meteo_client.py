from datetime import timedelta

import httpx
import structlog
from aiobreaker import CircuitBreaker
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import Settings, get_settings
from app.schemas.weather import GeocodingResult, WeatherData

logger = structlog.get_logger()


class OpenMeteoClientError(Exception):
    """Base exception for Open-Meteo client errors."""

    pass


class CityNotFoundError(OpenMeteoClientError):
    """Raised when a city cannot be found."""

    pass


class OpenMeteoClient:
    """Async HTTP client for Open-Meteo API with circuit breaker and retry logic."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None

        # Circuit breaker for external API calls
        self.circuit_breaker = CircuitBreaker(
            fail_max=self.settings.circuit_breaker_fail_max,
            timeout_duration=timedelta(seconds=self.settings.circuit_breaker_reset_timeout),
        )

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.settings.http_timeout_seconds),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _make_request_inner(self, url: str, params: dict) -> dict:
        """Inner request method called by circuit breaker."""
        client = await self.get_client()

        logger.debug("making_external_request", url=url, params=params)
        response = await client.get(url, params=params)

        logger.info(
            "external_api_response",
            url=url,
            status_code=response.status_code,
        )

        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    async def _make_request(self, url: str, params: dict) -> dict:
        """Make HTTP request with retry logic and circuit breaker."""
        return await self.circuit_breaker.call_async(self._make_request_inner, url, params)

    async def geocode_city(self, city_name: str) -> GeocodingResult:
        """Convert city name to coordinates using Open-Meteo Geocoding API."""
        url = f"{self.settings.geocoding_base_url}/search"
        params = {"name": city_name, "count": 1, "language": "en", "format": "json"}

        try:
            data = await self._make_request(url, params)

            if not data.get("results"):
                raise CityNotFoundError(f"City not found: {city_name}")

            result = data["results"][0]
            return GeocodingResult(
                name=result["name"],
                latitude=result["latitude"],
                longitude=result["longitude"],
                country=result.get("country"),
                timezone=result.get("timezone"),
            )
        except httpx.HTTPStatusError as e:
            logger.error("geocoding_api_error", status_code=e.response.status_code)
            raise OpenMeteoClientError(f"Geocoding API error: {e.response.status_code}") from e

    async def get_weather(self, latitude: float, longitude: float) -> WeatherData:
        """Get current weather for coordinates."""
        url = f"{self.settings.open_meteo_base_url}/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "timezone": "auto",
        }

        try:
            data = await self._make_request(url, params)
            current = data["current"]

            return WeatherData(
                temperature=current["temperature_2m"],
                humidity=current["relative_humidity_2m"],
                weather_code=current["weather_code"],
                wind_speed=current["wind_speed_10m"],
                timezone=data.get("timezone"),
                timestamp=current.get("time"),
            )
        except httpx.HTTPStatusError as e:
            logger.error("weather_api_error", status_code=e.response.status_code)
            raise OpenMeteoClientError(f"Weather API error: {e.response.status_code}") from e
