from fastapi import APIRouter

from app.api import health, weather

api_router = APIRouter()

api_router.include_router(weather.router, tags=["weather"])
api_router.include_router(health.router, tags=["health"])
