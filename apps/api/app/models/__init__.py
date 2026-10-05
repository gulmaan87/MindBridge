"""Database Models Package for MindBridge.

Exports all SQLAlchemy models so that Alembic and metadata auto-discovery
can detect all table schemas.
(Backend Project Structure §15)
"""

from app.models.consent import Consent, ConsentType
from app.models.relationship import (
    PermissionType,
    Relationship,
    RelationshipPermission,
    RelationshipStatus,
    RelationshipType,
    UserPreference,
)
from app.models.user import Profile, ProfileType, Role, User, UserRole, UserStatus

__all__ = [
    "User",
    "UserStatus",
    "Profile",
    "ProfileType",
    "Role",
    "UserRole",
    "Relationship",
    "RelationshipType",
    "RelationshipStatus",
    "RelationshipPermission",
    "PermissionType",
    "UserPreference",
    "Consent",
    "ConsentType",
]
