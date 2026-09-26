"""Application Lifespan Context Manager.

Handles graceful startup, resource initialization, and shutdown
without deprecated event decorators.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown events."""
    setup_logging()
    settings = get_settings()

    logger.info(
        "Starting %s [environment=%s, debug=%s]",
        settings.app_name,
        settings.app_env,
        settings.debug,
    )

    # Startup tasks (connection pool pre-warming will attach here in Day 4)
    yield

    # Shutdown tasks (graceful connection draining)
    logger.info("Shutting down %s gracefully", settings.app_name)
