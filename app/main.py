from contextlib import asynccontextmanager

import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from redis import asyncio as aioredis
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.router import api_router
from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import LoggingMiddleware
from app.dependencies import get_open_meteo_client

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    # Startup
    configure_logging()
    settings = get_settings()

    logger.info("starting_application", app_name=settings.app_name)

    # Initialize Redis connection
    app.state.redis = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )

    logger.info("redis_connected", url=settings.redis_url)

    yield

    # Shutdown
    logger.info("shutting_down_application")

    # Close Redis connection
    await app.state.redis.close()

    # Close Open-Meteo client
    client = get_open_meteo_client()
    await client.close()

    logger.info("application_shutdown_complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Weather Proxy API",
        description="A production-ready weather proxy service that provides "
        "current weather data with caching, structured logging, and resilience patterns.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add middleware (order matters - last added runs first)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        CorrelationIdMiddleware,
        header_name="X-Request-ID",
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Include API routes
    app.include_router(api_router)

    # Instrument Prometheus metrics
    Instrumentator().instrument(app).expose(app)

    return app


# Create application instance
app = create_app()
