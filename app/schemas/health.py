from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status (healthy/degraded)")
    redis_connected: bool = Field(..., description="Redis connectivity status")
