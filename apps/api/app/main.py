"""FastAPI Application Entry Point.

Configures middlewares (CORS, Request-ID), lifespan management,
error handling, and router registration adhering to API Contract v2.
"""

import re
import uuid
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
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

# 1. CORS Middleware (restricted to approved frontend origins and headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID", "Idempotency-Key", "If-Match"],
    expose_headers=["X-Request-ID"],
)

# Safe pattern for incoming correlation IDs: alphanumeric, underscores, hyphens (max 64 chars)
_SAFE_REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")
_MAX_REQUEST_BODY_BYTES = 2 * 1024 * 1024  # 2 MB limit for standard JSON payloads


# 2. Security Headers Middleware (OWASP Secure Headers & Engineering Rules §10)
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
    """Enforce strict defensive security headers on all API responses."""
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not settings.debug:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# 3. Request Payload Size Limiting Middleware (DoS Protection - Engineering Rules §5)
@app.middleware("http")
async def request_size_limit_middleware(request: Request, call_next: Callable) -> Response:
    """Prevent memory exhaustion / denial of service by rejecting oversized bodies."""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > _MAX_REQUEST_BODY_BYTES:
                request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": {
                            "code": "PAYLOAD_TOO_LARGE",
                            "message": f"Request body exceeds maximum allowed size of {_MAX_REQUEST_BODY_BYTES} bytes.",
                            "request_id": request_id,
                            "details": [],
                        }
                    },
                    headers={"X-Request-ID": request_id},
                )
        except ValueError:
            pass
    return await call_next(request)


# 4. Correlation ID Middleware with Malformed Input Sanitization (API Contract v2 §5, Engineering Rules §5)
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next: Callable) -> Response:
    """Validate or replace correlation IDs to prevent header injection and malformed logs."""
    raw_id = request.headers.get("X-Request-ID")
    if raw_id and _SAFE_REQUEST_ID_REGEX.match(raw_id):
        request_id = raw_id
    else:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ------------------------------------------------------------------------------
# Standard Error Envelope Handler (API Contract v2 §6)
# ------------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Wrap Pydantic validation errors in the standard error envelope (API Contract v2 §6)."""
    request_id = getattr(request.state, "request_id", "unknown")
    details = [
        {"field": " -> ".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "request_id": request_id,
                "details": details,
            }
        },
        headers={"X-Request-ID": request_id},
    )


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
