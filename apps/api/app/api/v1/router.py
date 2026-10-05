"""API v1 Central Router.

Aggregates all domain routers under /api/v1 prefix.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router

api_v1_router = APIRouter()

# Mount health & auth endpoints
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
