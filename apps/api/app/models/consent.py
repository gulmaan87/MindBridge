"""SQLAlchemy Models for User Consent.

Adheres to:
- Database Design & ERD Specification §11
- API Contract v2 §18
- Engineering Rules §6 (Consent & Privacy Standards)
"""

from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ConsentType(str, Enum):
    """Categories of user consent."""

    DATA_PROCESSING = "DATA_PROCESSING"
    MEMORY_STORAGE = "MEMORY_STORAGE"
    CAREGIVER_ACCESS = "CAREGIVER_ACCESS"
    VOICE_PROCESSING = "VOICE_PROCESSING"
    RESEARCH_PARTICIPATION = "RESEARCH_PARTICIPATION"
    AI_PROCESSING = "AI_PROCESSING"


class Consent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Versioned user consent record."""

    __tablename__ = "consents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    consent_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Category of consent (e.g. DATA_PROCESSING, MEMORY_STORAGE)",
    )
    version: Mapped[str] = mapped_column(
        String(16),
        default="1.0",
        nullable=False,
        doc="Version of the terms/consent document",
    )
    granted: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether consent is currently active",
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Timestamp when consent was recorded",
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when consent was explicitly revoked",
    )
    metadata_payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="IP address, user agent, or legal agreement metadata",
    )
