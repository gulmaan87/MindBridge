"""API v1 Central Router.

Aggregates all domain routers under /api/v1 prefix.
"""

from app.api.v1.health import router as health_router
from fastapi import APIRouter

api_v1_router = APIRouter()

# Mount health endpoints under /api/v1/health
api_v1_router.include_router(health_router)
