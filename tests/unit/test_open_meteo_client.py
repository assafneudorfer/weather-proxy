import pytest
import respx
from httpx import Response

from app.config import Settings
from app.services.open_meteo_client import (
    CityNotFoundError,
    OpenMeteoClient,
    OpenMeteoClientError,
)


@pytest.fixture
def client_settings() -> Settings:
    """Provide settings for Open-Meteo client."""
    return Settings(
        open_meteo_base_url="https://api.open-meteo.com/v1",
        geocoding_base_url="https://geocoding-api.open-meteo.com/v1",
        http_timeout_seconds=5.0,
        circuit_breaker_fail_max=5,
        circuit_breaker_reset_timeout=60,
    )


@pytest.fixture
def open_meteo_client(client_settings) -> OpenMeteoClient:
    """Create Open-Meteo client for testing."""
    return OpenMeteoClient(client_settings)


@pytest.mark.asyncio
@respx.mock
async def test_geocode_city_success(open_meteo_client):
    """Test successful geocoding."""
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=Response(
            200,
            json={
                "results": [
                    {
                        "name": "London",
                        "latitude": 51.5074,
                        "longitude": -0.1278,
                        "country": "United Kingdom",
                        "timezone": "Europe/London",
                    }
                ]
            },
        )
    )

    result = await open_meteo_client.geocode_city("London")

    assert result.name == "London"
    assert result.latitude == 51.5074
    assert result.longitude == -0.1278
    assert result.country == "United Kingdom"

    await open_meteo_client.close()


@pytest.mark.asyncio
@respx.mock
async def test_geocode_city_not_found(open_meteo_client):
    """Test city not found error."""
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=Response(200, json={"results": []})
    )

    with pytest.raises(CityNotFoundError):
        await open_meteo_client.geocode_city("NonexistentCity12345")

    await open_meteo_client.close()


@pytest.mark.asyncio
@respx.mock
async def test_geocode_city_no_results_key(open_meteo_client):
    """Test city not found when results key is missing."""
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=Response(200, json={})
    )

    with pytest.raises(CityNotFoundError):
        await open_meteo_client.geocode_city("SomeCity")

    await open_meteo_client.close()


@pytest.mark.asyncio
@respx.mock
async def test_get_weather_success(open_meteo_client):
    """Test successful weather fetch."""
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=Response(
            200,
            json={
                "current": {
                    "temperature_2m": 15.5,
                    "relative_humidity_2m": 75,
                    "weather_code": 2,
                    "wind_speed_10m": 12.3,
                    "time": "2024-01-15T14:00",
                },
                "timezone": "Europe/London",
            },
        )
    )

    result = await open_meteo_client.get_weather(51.5074, -0.1278)

    assert result.temperature == 15.5
    assert result.humidity == 75
    assert result.weather_code == 2
    assert result.wind_speed == 12.3
    assert result.timezone == "Europe/London"

    await open_meteo_client.close()


@pytest.mark.asyncio
@respx.mock
async def test_get_weather_api_error(open_meteo_client):
    """Test weather API error handling."""
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=Response(500, json={"error": "Internal Server Error"})
    )

    with pytest.raises(OpenMeteoClientError):
        await open_meteo_client.get_weather(51.5074, -0.1278)

    await open_meteo_client.close()
