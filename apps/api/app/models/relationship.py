"""SQLAlchemy Models for Relationships, Permissions, and User Preferences.

Adheres to:
- Database Design & ERD Specification §9-10
- API Contract v2 §15-17
- Engineering Rules §6 (Authorization & Security Standards)
"""

from enum import Enum
import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RelationshipType(str, Enum):
    """Types of interpersonal platform connections."""

    CAREGIVER = "CAREGIVER"
    PARENT = "PARENT"
    GUARDIAN = "GUARDIAN"
    RESEARCH_ASSESSOR = "RESEARCH_ASSESSOR"


class RelationshipStatus(str, Enum):
    """Relationship lifecycle states."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


class PermissionType(str, Enum):
    """Fine-grained permission tokens."""

    VIEW_PROGRESS = "VIEW_PROGRESS"
    VIEW_SESSIONS = "VIEW_SESSIONS"
    VIEW_MEMORIES = "VIEW_MEMORIES"
    CREATE_MEMORY = "CREATE_MEMORY"
    VERIFY_MEMORY = "VERIFY_MEMORY"
    EDIT_MEMORY = "EDIT_MEMORY"
    ARCHIVE_MEMORY = "ARCHIVE_MEMORY"
    VIEW_AI_ACTIVITY = "VIEW_AI_ACTIVITY"
    VIEW_SAFETY_EVENTS = "VIEW_SAFETY_EVENTS"


class Relationship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Interpersonal connection connecting a subject (Elder/Child) to a related user (Caregiver/Parent)."""

    __tablename__ = "relationships"

    subject_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The primary user receiving assistance (e.g. Elder or Child)",
    )
    related_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The supporting user (e.g. Caregiver, Parent)",
    )
    relationship_type: Mapped[str] = mapped_column(
        String(32),
        default=RelationshipType.CAREGIVER.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=RelationshipStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    # Relationships
    permissions: Mapped[list["RelationshipPermission"]] = relationship(
        "RelationshipPermission",
        back_populates="relationship",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "subject_user_id",
            "related_user_id",
            "relationship_type",
            name="uq_subject_related_relationship",
        ),
    )


class RelationshipPermission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Fine-grained permissions granted within an active relationship."""

    __tablename__ = "relationship_permissions"

    relationship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("relationships.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Permission identifier name (e.g. VIEW_PROGRESS, VIEW_MEMORIES)",
    )
    granted: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    relationship: Mapped[Relationship] = relationship(
        "Relationship",
        back_populates="permissions",
    )

    __table_args__ = (
        UniqueConstraint(
            "relationship_id",
            "permission",
            name="uq_relationship_permission",
        ),
    )


class UserPreference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Fine-grained behavioral and notification preferences per user."""

    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    preferences: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
