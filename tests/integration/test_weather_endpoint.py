import pytest
import respx
from httpx import AsyncClient, Response


@pytest.mark.asyncio
@respx.mock
async def test_get_weather_success(client: AsyncClient):
    """Test successful weather fetch."""
    # Mock geocoding API
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

    # Mock weather API
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=Response(
            200,
            json={
                "current": {
                    "temperature_2m": 15.0,
                    "relative_humidity_2m": 80.0,
                    "weather_code": 3,
                    "wind_speed_10m": 10.0,
                    "time": "2024-01-01T12:00",
                },
                "timezone": "Europe/London",
            },
        )
    )

    response = await client.get("/weather", params={"city": "London"})

    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "London"
    assert data["temperature"] == 15.0
    assert data["country"] == "United Kingdom"
    assert data["cached"] is False


@pytest.mark.asyncio
@respx.mock
async def test_get_weather_cached(client: AsyncClient):
    """Test that second request returns cached data."""
    # Mock geocoding API
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=Response(
            200,
            json={
                "results": [
                    {
                        "name": "Paris",
                        "latitude": 48.8566,
                        "longitude": 2.3522,
                        "country": "France",
                        "timezone": "Europe/Paris",
                    }
                ]
            },
        )
    )

    # Mock weather API
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=Response(
            200,
            json={
                "current": {
                    "temperature_2m": 20.0,
                    "relative_humidity_2m": 65.0,
                    "weather_code": 1,
                    "wind_speed_10m": 5.0,
                    "time": "2024-01-01T12:00",
                },
                "timezone": "Europe/Paris",
            },
        )
    )

    # First request - should fetch fresh
    response1 = await client.get("/weather", params={"city": "Paris"})
    assert response1.status_code == 200
    assert response1.json()["cached"] is False

    # Second request - should be cached
    response2 = await client.get("/weather", params={"city": "Paris"})
    assert response2.status_code == 200
    assert response2.json()["cached"] is True


@pytest.mark.asyncio
async def test_get_weather_missing_city(client: AsyncClient):
    """Test validation error for missing city parameter."""
    response = await client.get("/weather")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_weather_empty_city(client: AsyncClient):
    """Test validation error for empty city parameter."""
    response = await client.get("/weather", params={"city": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
@respx.mock
async def test_get_weather_city_not_found(client: AsyncClient):
    """Test city not found error."""
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=Response(200, json={"results": []})
    )

    response = await client.get("/weather", params={"city": "NonexistentCity12345"})
    assert response.status_code == 404
    assert "not found" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_get_weather_has_request_id(client: AsyncClient):
    """Test that response includes correlation ID header."""
    # Mock APIs to avoid actual calls
    with respx.mock:
        respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=Response(
                200,
                json={
                    "results": [
                        {
                            "name": "Berlin",
                            "latitude": 52.52,
                            "longitude": 13.405,
                            "country": "Germany",
                            "timezone": "Europe/Berlin",
                        }
                    ]
                },
            )
        )
        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=Response(
                200,
                json={
                    "current": {
                        "temperature_2m": 10.0,
                        "relative_humidity_2m": 70.0,
                        "weather_code": 2,
                        "wind_speed_10m": 15.0,
                        "time": "2024-01-01T12:00",
                    },
                    "timezone": "Europe/Berlin",
                },
            )
        )

        response = await client.get("/weather", params={"city": "Berlin"})
        assert response.status_code == 200
        # Correlation ID middleware adds this header
        assert "x-request-id" in response.headers
