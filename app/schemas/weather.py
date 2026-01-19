from pydantic import BaseModel, Field


class GeocodingResult(BaseModel):
    """Result from geocoding API."""

    name: str
    latitude: float
    longitude: float
    country: str | None = None
    timezone: str | None = None


class WeatherData(BaseModel):
    """Weather data from Open-Meteo API."""

    temperature: float
    humidity: float
    weather_code: int
    wind_speed: float
    timezone: str | None = None
    timestamp: str | None = None


class WeatherResponse(BaseModel):
    """Weather response returned to clients."""

    city: str = Field(..., description="City name")
    country: str | None = Field(None, description="Country name")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Relative humidity percentage")
    weather_code: int = Field(..., description="WMO weather code")
    wind_speed: float = Field(..., description="Wind speed in km/h")
    timezone: str | None = Field(None, description="Timezone")
    timestamp: str | None = Field(None, description="Data timestamp")
    cached: bool = Field(..., description="Whether response was from cache")


class WeatherErrorResponse(BaseModel):
    """Error response for weather endpoint."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Error details")
