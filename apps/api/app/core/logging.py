"""Structured Logging Module.

Provides standard logging configuration adhering to Engineering Rules §7
(no secret logging, no user personal data in application logs).
"""

import logging
import sys

from app.core.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """Configure structured logging for the application."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s (req:%(request_id)s): %(message)s"
        if "%(request_id)s" in logging.BASIC_FORMAT
        else "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Suppress excessive verbosity from noisy third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger("mindbridge")
