"""SQLAlchemy Declarative Base and Common Mixins.

Follows SQLAlchemy 2.0 mapped_column paradigms and enforces:
- Non-sequential UUID primary keys (Engineering Rules §5, Postgres Schema §4)
- UTC timestamp tracking (Postgres Schema §5)
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy database models."""


class UUIDPrimaryKeyMixin:
    """Mixin that provides a client/server-generated UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique primary key identifier (UUIDv4).",
    )


class TimestampMixin:
    """Mixin that provides timezone-aware created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp when the record was created.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="UTC timestamp when the record was last modified.",
    )
