"""Database Models Package for MindBridge.

Exports all SQLAlchemy models so that Alembic and metadata auto-discovery
can detect all table schemas.
(Backend Project Structure §15)
"""

from app.models.user import Profile, ProfileType, Role, User, UserRole, UserStatus

__all__ = [
    "Profile",
    "ProfileType",
    "Role",
    "User",
    "UserRole",
    "UserStatus",
]
