"""Authentication and User Pydantic Schemas.

Adheres strictly to API Contract v2 §7-11.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import ProfileType


class RegisterRequest(BaseModel):
    """User registration payload."""

    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ..., min_length=8, max_length=128, description="Strong password (min 8 chars)"
    )
    display_name: str = Field(
        ..., min_length=1, max_length=255, description="Participant display name"
    )
    profile_type: ProfileType = Field(
        default=ProfileType.ELDER, description="Initial persona profile type"
    )


class LoginRequest(BaseModel):
    """User authentication payload."""

    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Plaintext password")


class RefreshTokenRequest(BaseModel):
    """Token refresh payload."""

    refresh_token: str = Field(..., description="Valid signed JWT refresh token")


class UserSummary(BaseModel):
    """User summary representation."""

    id: uuid.UUID
    email: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class ProfileResponse(BaseModel):
    """Participant profile representation."""

    id: uuid.UUID
    profile_type: str
    display_name: str
    timezone: str
    language: str

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """Authentication success payload with tokens and user metadata."""

    user: UserSummary
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class TokenRefreshResponse(BaseModel):
    """Token renewal response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class CurrentUserResponse(BaseModel):
    """Detailed current user identity payload (/users/me)."""

    id: uuid.UUID
    email: str
    status: str
    email_verified: bool
    roles: list[str]
    profiles: list[ProfileResponse]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
