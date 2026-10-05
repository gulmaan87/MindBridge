"""Pydantic Schemas for Relationship & Permission endpoints.

Covers:
- Relationship CRUD and state machine transitions
- Fine-grained RelationshipPermission management
(API Contract v2 §15-17, Engineering Rules §6)
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.relationship import PermissionType, RelationshipStatus, RelationshipType


# ---------------------------------------------------------------------------
# Relationship schemas
# ---------------------------------------------------------------------------


class RelationshipCreate(BaseModel):
    """Payload to initiate a new pending relationship."""

    related_user_id: uuid.UUID = Field(..., description="User ID of the supporting person (caregiver / parent)")
    relationship_type: RelationshipType = Field(
        RelationshipType.CAREGIVER,
        description="Type of interpersonal connection",
    )


class RelationshipStatusUpdate(BaseModel):
    """Payload to transition a relationship's status."""

    status: RelationshipStatus = Field(..., description="New status for the relationship")


class PermissionRead(BaseModel):
    """Single permission entry within a relationship."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    permission: PermissionType
    granted: bool
    created_at: datetime


class RelationshipRead(BaseModel):
    """Full relationship detail including nested permissions."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_user_id: uuid.UUID
    related_user_id: uuid.UUID
    relationship_type: RelationshipType
    status: RelationshipStatus
    permissions: list[PermissionRead] = []
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Permission schemas
# ---------------------------------------------------------------------------


class PermissionUpsert(BaseModel):
    """Grant or revoke a fine-grained permission on a relationship."""

    permission: PermissionType = Field(..., description="Permission token to upsert")
    granted: bool = Field(True, description="True to grant, False to explicitly revoke")
