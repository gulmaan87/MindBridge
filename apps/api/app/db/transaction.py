"""Transaction helper utilities for service layer operations.

Provides context manager boundaries to ensure atomic multi-entity mutations.
(Backend Project Structure §14)
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@asynccontextmanager
async def transaction_scope(
    session: AsyncSession,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional boundary around a series of operations."""
    try:
        yield session
        await session.commit()
    except Exception as exc:
        logger.error(f"Transaction failed and rolling back: {exc}")
        await session.rollback()
        raise
