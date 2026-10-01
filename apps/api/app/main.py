"""FastAPI Application Entry Point.

Configures middlewares (CORS, Request-ID), lifespan management,
error handling, and router registration adhering to API Contract v2.
"""

import uuid
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.health import liveness_probe, readiness_probe
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import logger
from app.lifespan import lifespan

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# Middlewares
# ------------------------------------------------------------------------------

# 1. CORS Middleware (restricted to approved frontend origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# 2. Correlation ID Middleware (API Contract v2 §5)
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next: Callable) -> Response:
    """Ensure every request has a correlation ID for end-to-end traceability."""
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ------------------------------------------------------------------------------
# Standard Error Envelope Handler (API Contract v2 §6)
# ------------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled exceptions and return safe standard error envelope."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "Unhandled exception for request %s: %s", request_id, str(exc), exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
                "request_id": request_id,
                "details": [],
            }
        },
        headers={"X-Request-ID": request_id},
    )


# ------------------------------------------------------------------------------
# Root Probes (API Contract v2 §84)
# ------------------------------------------------------------------------------
app.add_api_route("/health/live", liveness_probe, methods=["GET"], tags=["health"])
app.add_api_route("/health/ready", readiness_probe, methods=["GET"], tags=["health"])

# ------------------------------------------------------------------------------
# API Version 1 Routers
# ------------------------------------------------------------------------------
app.include_router(api_v1_router, prefix=settings.api_v1_str)
