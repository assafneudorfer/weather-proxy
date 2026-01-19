import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.open_meteo_client import CityNotFoundError, OpenMeteoClientError

logger = structlog.get_logger()


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""

    @app.exception_handler(CityNotFoundError)
    async def city_not_found_handler(request: Request, exc: CityNotFoundError) -> JSONResponse:
        logger.warning("city_not_found", error=str(exc))
        return JSONResponse(
            status_code=404,
            content={"error": "City not found", "detail": str(exc)},
        )

    @app.exception_handler(OpenMeteoClientError)
    async def open_meteo_error_handler(request: Request, exc: OpenMeteoClientError) -> JSONResponse:
        logger.error("external_api_error", error=str(exc))
        return JSONResponse(
            status_code=503,
            content={
                "error": "Weather service unavailable",
                "detail": "Unable to fetch weather data from external provider",
            },
        )
