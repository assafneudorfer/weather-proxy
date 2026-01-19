from fastapi import APIRouter, Depends

from app.dependencies import get_cache_service
from app.schemas.health import HealthResponse
from app.services.cache_service import CacheService

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    description="Returns the health status of the service including Redis connectivity.",
)
async def health_check(
    cache_service: CacheService = Depends(get_cache_service),
) -> HealthResponse:
    """Check service health status."""
    redis_healthy = await cache_service.health_check()

    return HealthResponse(
        status="healthy" if redis_healthy else "degraded",
        redis_connected=redis_healthy,
    )
