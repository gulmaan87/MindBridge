"""Pydantic Schemas for Consent endpoints.

Covers:
- Recording and revoking user consent
(API Contract v2 §18, Engineering Rules §6 – Consent & Privacy Standards)
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.consent import ConsentType


class ConsentCreate(BaseModel):
    """Record a new consent decision."""

    consent_type: ConsentType = Field(..., description="Category of consent being recorded")
    version: str = Field("1.0", description="Version of the terms/consent document")
    granted: bool = Field(True, description="Whether consent is being granted (True) or explicitly refused (False)")
    metadata_payload: dict | None = Field(
        None,
        description="Optional metadata: IP address, user agent, legal agreement reference",
    )


class ConsentRead(BaseModel):
    """Consent record returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    consent_type: ConsentType
    version: str
    granted: bool
    granted_at: datetime
    revoked_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ConsentRevoke(BaseModel):
    """Revoke an existing consent record."""

    revoked_at: datetime | None = Field(
        None,
        description="Explicit revocation timestamp; defaults to server UTC now if omitted",
    )
