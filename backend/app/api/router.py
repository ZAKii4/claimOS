"""
Root API router — mounts versioned sub-routers.
"""

from fastapi import APIRouter

from app.api.v1.router import router as v1_router
from app.config.settings import get_settings

settings = get_settings()

router = APIRouter()
router.include_router(v1_router, prefix=settings.API_V1_PREFIX)
