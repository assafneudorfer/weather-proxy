import pytest

from app.services.cache_service import CacheService


@pytest.mark.asyncio
async def test_cache_set_and_get(cache_service: CacheService):
    """Test setting and getting cache data."""
    test_data = {
        "city": "London",
        "temperature": 15.0,
        "humidity": 80.0,
    }

    await cache_service.set_weather("London", test_data)
    result = await cache_service.get_weather("London")

    assert result is not None
    assert result["city"] == "London"
    assert result["temperature"] == 15.0


@pytest.mark.asyncio
async def test_cache_miss(cache_service: CacheService):
    """Test cache miss returns None."""
    result = await cache_service.get_weather("NonexistentCity")
    assert result is None


@pytest.mark.asyncio
async def test_cache_key_case_insensitive(cache_service: CacheService):
    """Test cache keys are case insensitive."""
    test_data = {"city": "Paris", "temperature": 20.0}

    await cache_service.set_weather("PARIS", test_data)
    result = await cache_service.get_weather("paris")

    assert result is not None
    assert result["city"] == "Paris"


@pytest.mark.asyncio
async def test_health_check_success(cache_service: CacheService):
    """Test health check with working Redis."""
    result = await cache_service.health_check()
    assert result is True
