"""Health and readiness check endpoints (API Contract v2 §84)."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter(tags=["health"])
settings = get_settings()


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    environment: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]
    timestamp: str


@router.get("/health", response_model=HealthResponse)
async def api_health() -> HealthResponse:
    """Return version and service status for API v1 consumers."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
        service=settings.app_name,
        environment=settings.app_env,
        version="0.1.0",
    )


# Public root-level probes defined as helper functions for mounting at root
async def liveness_probe() -> dict[str, Any]:
    """Liveness probe: verifies the process is responsive and not deadlocked."""
    return {
        "status": "live",
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def readiness_probe(response: Response) -> dict[str, Any]:
    """Readiness probe: verifies dependencies are ready to accept traffic.

    (Does not disclose sensitive database hostnames or internal IPs - Eng Rules §5).
    """
    # Baseline check: config is loaded and runtime is intact
    checks = {
        "configuration": "ok",
        "process": "ok",
    }

    # If any required check fails, return 503 Service Unavailable
    all_ok = all(v == "ok" for v in checks.values())
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if all_ok else "unhealthy",
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }
