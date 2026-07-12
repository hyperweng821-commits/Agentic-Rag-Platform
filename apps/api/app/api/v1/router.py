"""Version 1 endpoint registry."""

from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router

API_V1_PREFIX = "/v1"

router = APIRouter(prefix=API_V1_PREFIX)
router.include_router(health_router, prefix="/health", tags=["health"])
