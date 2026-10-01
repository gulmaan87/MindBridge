"""SQLAlchemy Async Engine and Session Management.

Manages connection pooling, async session lifecycle, and FastAPI dependency injection.
(Engineering Rules §5, Backend Project Structure §14)
"""

import logging
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Engine creation with sensible pooling defaults
engine_kwargs: dict[str, Any] = {
    "echo": settings.debug and settings.log_level.upper() == "DEBUG",
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}

# Only configure pool size / overflow if using a pooled connection (not NullPool/SQLite in tests)
if not settings.database_url.startswith("sqlite"):
    engine_kwargs.update(
        {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
        }
    )

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    **engine_kwargs,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a request-scoped AsyncSession.

    Ensures that uncommitted changes are rolled back on uncaught exceptions
    and the connection is returned to the pool once the request is complete.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db_connection() -> None:
    """Dispose all connections in the pool on application shutdown."""
    logger.info("Closing database connection pool.")
    await engine.dispose()
