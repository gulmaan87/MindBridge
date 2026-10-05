"""SQLAlchemy Models for Users, Profiles, and Roles.

Adheres to:
- Database Design & ERD Specification §5-8
- API Contract v2 §7-11
- Engineering Rules §6 (Identity & Security Standards)
"""

import uuid
from datetime import date, datetime
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserStatus(str, Enum):
    """User account status."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"
    PENDING = "PENDING"


class ProfileType(str, Enum):
    """Differentiated user persona experience."""

    ELDER = "ELDER"
    CHILD = "CHILD"
    CAREGIVER = "CAREGIVER"
    PARENT = "PARENT"
    ADMIN = "ADMIN"
    RESEARCHER = "RESEARCHER"


class UserRole(Base):
    """Association table connecting users to their authorization roles."""

    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """System and relationship-scoped authorization roles."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique role identifier name (e.g. ELDER, CAREGIVER, ADMIN)",
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Human-readable description of role permissions",
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin",
    )


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Authenticated platform user identity."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
        index=True,
        doc="Primary verified or pending email address",
    )
    phone: Mapped[str | None] = mapped_column(
        String(32),
        unique=True,
        nullable=True,
        index=True,
        doc="Optional international telephone number",
    )
    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="bcrypt-hashed authentication credential",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=UserStatus.ACTIVE.value,
        nullable=False,
        doc="Account state (ACTIVE, SUSPENDED, DELETED, PENDING)",
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    phone_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of most recent successful authentication",
    )

    # Relationships
    roles: Mapped[list[Role]] = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin",
    )
    profiles: Mapped[list["Profile"]] = relationship(
        "Profile",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Profile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Participant persona profile associated with a user account."""

    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to owning user account",
    )
    profile_type: Mapped[str] = mapped_column(
        String(32),
        default=ProfileType.ELDER.value,
        nullable=False,
        doc="Persona type: ELDER, CHILD, CAREGIVER, PARENT, ADMIN, RESEARCHER",
    )
    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Display name shown in games and caregiver portal",
    )
    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Date of birth for age-adaptive game difficulty scaling",
    )
    timezone: Mapped[str] = mapped_column(
        String(64),
        default="UTC",
        nullable=False,
        doc="IANA timezone string for scheduling memory reminders",
    )
    language: Mapped[str] = mapped_column(
        String(16),
        default="en",
        nullable=False,
        doc="Preferred language code (e.g. en, es, hi)",
    )
    accessibility_config: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="High contrast, large fonts, audio narration preferences",
    )
    preferences: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="Notification and cognitive engagement preferences",
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User",
        back_populates="profiles",
    )
