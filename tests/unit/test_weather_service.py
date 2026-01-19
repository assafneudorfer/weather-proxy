from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.weather import GeocodingResult, WeatherData
from app.services.weather_service import WeatherService


@pytest.fixture
def mock_cache_service():
    """Create mock cache service."""
    return MagicMock()


@pytest.fixture
def mock_open_meteo_client():
    """Create mock Open-Meteo client."""
    return MagicMock()


@pytest.fixture
def weather_service(mock_open_meteo_client, mock_cache_service) -> WeatherService:
    """Create weather service with mocks."""
    return WeatherService(mock_open_meteo_client, mock_cache_service)


@pytest.mark.asyncio
async def test_get_weather_cache_hit(weather_service, mock_cache_service):
    """Test that cached data is returned when available."""
    cached_data = {
        "city": "London",
        "country": "United Kingdom",
        "latitude": 51.5,
        "longitude": -0.12,
        "temperature": 15.0,
        "humidity": 80.0,
        "weather_code": 3,
        "wind_speed": 10.0,
        "timezone": "Europe/London",
        "timestamp": "2024-01-01T12:00",
    }
    mock_cache_service.get_weather = AsyncMock(return_value=cached_data)

    result = await weather_service.get_weather_for_city("London")

    assert result.cached is True
    assert result.city == "London"
    assert result.temperature == 15.0
    mock_cache_service.get_weather.assert_called_once_with("London")


@pytest.mark.asyncio
async def test_get_weather_cache_miss(weather_service, mock_cache_service, mock_open_meteo_client):
    """Test that fresh data is fetched on cache miss."""
    mock_cache_service.get_weather = AsyncMock(return_value=None)
    mock_cache_service.set_weather = AsyncMock()

    mock_open_meteo_client.geocode_city = AsyncMock(
        return_value=GeocodingResult(
            name="London",
            latitude=51.5,
            longitude=-0.12,
            country="United Kingdom",
            timezone="Europe/London",
        )
    )
    mock_open_meteo_client.get_weather = AsyncMock(
        return_value=WeatherData(
            temperature=15.0,
            humidity=80.0,
            weather_code=3,
            wind_speed=10.0,
            timezone="Europe/London",
            timestamp="2024-01-01T12:00",
        )
    )

    result = await weather_service.get_weather_for_city("London")

    assert result.cached is False
    assert result.city == "London"
    assert result.temperature == 15.0
    assert result.country == "United Kingdom"
    mock_cache_service.set_weather.assert_called_once()


@pytest.mark.asyncio
async def test_get_weather_uses_geocoding(
    weather_service, mock_cache_service, mock_open_meteo_client
):
    """Test that geocoding is called to convert city name to coordinates."""
    mock_cache_service.get_weather = AsyncMock(return_value=None)
    mock_cache_service.set_weather = AsyncMock()

    mock_open_meteo_client.geocode_city = AsyncMock(
        return_value=GeocodingResult(
            name="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
            country="Japan",
            timezone="Asia/Tokyo",
        )
    )
    mock_open_meteo_client.get_weather = AsyncMock(
        return_value=WeatherData(
            temperature=25.0,
            humidity=60.0,
            weather_code=1,
            wind_speed=5.0,
            timezone="Asia/Tokyo",
            timestamp="2024-01-01T12:00",
        )
    )

    result = await weather_service.get_weather_for_city("Tokyo")

    mock_open_meteo_client.geocode_city.assert_called_once_with("Tokyo")
    mock_open_meteo_client.get_weather.assert_called_once_with(35.6762, 139.6503)
    assert result.latitude == 35.6762
    assert result.longitude == 139.6503
