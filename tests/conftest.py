import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import create_app
from app.services.cache_service import CacheService
from app.services.open_meteo_client import OpenMeteoClient


@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings."""
    return Settings(
        redis_url="redis://localhost:6379/0",
        log_level="DEBUG",
        log_format="console",
        cache_ttl_seconds=60,
    )


@pytest.fixture
async def fake_redis():
    """Provide fake Redis for testing."""
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
async def cache_service(fake_redis, test_settings) -> CacheService:
    """Provide cache service with fake Redis."""
    return CacheService(fake_redis, test_settings)


@pytest.fixture
def open_meteo_client(test_settings) -> OpenMeteoClient:
    """Provide Open-Meteo client."""
    return OpenMeteoClient(test_settings)


@pytest.fixture
async def app(fake_redis):
    """Create test application with fake Redis."""
    application = create_app()
    application.state.redis = fake_redis
    return application


@pytest.fixture
async def client(app) -> AsyncClient:
    """Provide async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
