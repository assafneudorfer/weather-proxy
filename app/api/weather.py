from fastapi import APIRouter, Depends, Query

from app.dependencies import get_weather_service
from app.schemas.weather import WeatherErrorResponse, WeatherResponse
from app.services.weather_service import WeatherService

router = APIRouter()


@router.get(
    "/weather",
    response_model=WeatherResponse,
    responses={
        404: {"model": WeatherErrorResponse, "description": "City not found"},
        503: {"model": WeatherErrorResponse, "description": "Service unavailable"},
    },
    summary="Get current weather for a city",
    description="Returns current weather data for the specified city. "
    "Results are cached for 5 minutes to reduce external API calls.",
)
async def get_weather(
    city: str = Query(
        ...,
        min_length=1,
        max_length=100,
        description="City name to get weather for",
        examples=["London", "New York", "Tokyo"],
    ),
    weather_service: WeatherService = Depends(get_weather_service),
) -> WeatherResponse:
    """Get current weather for a city."""
    return await weather_service.get_weather_for_city(city)
