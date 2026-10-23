"""Profile schemas for GET /profiles/me and PATCH /profiles/me.

Adheres to API Contract v2 §14.
"""

from pydantic import BaseModel, ConfigDict, Field


class ProfileUpdate(BaseModel):
    """Mutable fields on a user's profile (API Contract v2 §14)."""

    display_name: str | None = Field(None, min_length=1, max_length=255)
    timezone: str | None = Field(None, max_length=64, description="IANA timezone string, e.g. Asia/Kolkata")
    language: str | None = Field(None, max_length=16, description="BCP-47 language code, e.g. en, hi")
    accessibility_config: dict | None = Field(
        None,
        description="Accessibility preferences: font_scale, high_contrast, audio_narration",
    )


class ProfileDetail(BaseModel):
    """Full profile representation returned from GET /profiles/me."""

    model_config = ConfigDict(from_attributes=True)

    id: object  # uuid.UUID — kept as `object` to avoid circular import; serialized as str
    profile_type: str
    display_name: str
    timezone: str
    language: str
    accessibility_config: dict | None
    preferences: dict | None
