"""Persistence and Transaction Lifecycle Integration Tests.

Verifies:
1. Model persistence with UUIDv4 primary keys and UTC timestamps (PostgreSQL Schema §4-5).
2. Clean transaction rollback behavior on error.
3. Session isolation between test cases.
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import Column, String, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PersistenceAuditItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Test model for persistence validation."""

    __tablename__ = "test_persistence_audit_items"
    title = Column(String(100), nullable=False)
    status = Column(String(20), default="active", nullable=False)


@pytest.mark.asyncio
async def test_insert_and_retrieve_entity(db_session: AsyncSession):
    """Verify entity insertion generates UUIDv4 and timezone-aware created_at/updated_at."""
    item = PersistenceAuditItem(title="Cognitive Baseline Check")
    db_session.add(item)
    await db_session.flush()

    # Verify UUID primary key
    assert item.id is not None
    assert isinstance(item.id, uuid.UUID)
    assert item.id.version == 4

    # Verify Timestamps
    assert item.created_at is not None
    assert isinstance(item.created_at, datetime)
    assert item.created_at.tzinfo is not None

    # Query back from database
    stmt = select(PersistenceAuditItem).where(PersistenceAuditItem.id == item.id)
    result = await db_session.execute(stmt)
    fetched = result.scalar_one()

    assert fetched.title == "Cognitive Baseline Check"
    assert fetched.status == "active"
    assert fetched.id == item.id


@pytest.mark.asyncio
async def test_transaction_rollback_on_failure(db_session: AsyncSession):
    """Verify that failed transactions roll back without committing dirty state."""
    item_valid = PersistenceAuditItem(title="Committed Item")
    db_session.add(item_valid)
    await db_session.flush()

    from sqlalchemy.exc import IntegrityError

    # Trigger a nested savepoint rollback on integrity violation
    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            item_invalid = PersistenceAuditItem(title=None)  # Violates nullable=False
            db_session.add(item_invalid)
            await db_session.flush()

    # The outer session should still have the valid item intact
    stmt = select(PersistenceAuditItem).where(PersistenceAuditItem.id == item_valid.id)
    result = await db_session.execute(stmt)
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_session_isolation(db_session: AsyncSession):
    """Verify that records from prior test runs do not leak across test boundaries."""
    stmt = select(PersistenceAuditItem)
    result = await db_session.execute(stmt)
    records = result.scalars().all()
    # Should be empty because each test fixture rolls back its transaction
    assert len(records) == 0
