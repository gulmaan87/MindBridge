"""Tests for Database Session, Declarative Base, and Mixins."""

import pytest
from sqlalchemy import Column, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.session import async_session_factory, engine, get_db_session


class DummyModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Dummy model to test declarative base and mixins."""

    __tablename__ = "test_dummy_model"
    name = Column(String(50), nullable=False)


def test_declarative_base_and_mixins():
    """Verify that models inheriting Base and mixins possess expected UUID and timestamp columns."""
    assert hasattr(DummyModel, "id")
    assert hasattr(DummyModel, "created_at")
    assert hasattr(DummyModel, "updated_at")
    assert hasattr(DummyModel, "name")
    assert DummyModel.__tablename__ == "test_dummy_model"


@pytest.mark.asyncio
async def test_session_generator_lifecycle():
    """Verify get_db_session yields an AsyncSession and closes cleanly."""
    gen = get_db_session()
    session = await anext(gen)
    try:
        assert isinstance(session, AsyncSession)
        assert session.is_active
    finally:
        with pytest.raises(StopAsyncIteration):
            await anext(gen)


def test_engine_and_session_factory_configuration():
    """Verify engine and session factory are instantiated with valid attributes."""
    assert engine is not None
    assert async_session_factory is not None
    assert issubclass(async_session_factory.class_, AsyncSession)
