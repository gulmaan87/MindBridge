"""Relationships API — state machine + object-level authorization.

Endpoints:
  POST   /relationships                          Create (PENDING) relationship
  GET    /relationships                          List relationships for current user
  GET    /relationships/{id}                     Get single relationship (participants only)
  PATCH  /relationships/{id}/status             Transition status (state machine)
  POST   /relationships/{id}/permissions         Upsert a fine-grained permission
  DELETE /relationships/{id}/permissions/{perm}  Remove a permission entry

Authorization rules (Engineering Rules §6):
- Only the subject_user can approve/reject (PENDING → ACTIVE | REJECTED)
- Only the subject_user can revoke (ACTIVE → REVOKED)
- Only the related_user (or subject) can request (POST /relationships)
- Permission management is restricted to the subject_user of the relationship
- Both participants can GET their shared relationship
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.relationship import (
    PermissionType,
    Relationship,
    RelationshipPermission,
    RelationshipStatus,
)
from app.models.user import User
from app.schemas.relationship import (
    PermissionRead,
    PermissionUpsert,
    RelationshipCreate,
    RelationshipRead,
    RelationshipStatusUpdate,
)

router = APIRouter(prefix="/relationships", tags=["Relationships"])

# ---------------------------------------------------------------------------
# Valid state-machine transitions
# { current_status: {allowed_next_statuses} }
# ---------------------------------------------------------------------------
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    RelationshipStatus.PENDING.value: {
        RelationshipStatus.ACTIVE.value,
        RelationshipStatus.REJECTED.value,
    },
    RelationshipStatus.ACTIVE.value: {
        RelationshipStatus.REVOKED.value,
    },
    RelationshipStatus.REJECTED.value: set(),
    RelationshipStatus.REVOKED.value: set(),
}

# Transitions that only the *subject_user* (the person being cared for) may perform
_SUBJECT_ONLY_TRANSITIONS: set[str] = {
    RelationshipStatus.ACTIVE.value,
    RelationshipStatus.REJECTED.value,
    RelationshipStatus.REVOKED.value,
}


async def _get_relationship_or_404(
    relationship_id: uuid.UUID,
    db: AsyncSession,
) -> Relationship:
    """Load a relationship by PK or raise 404."""
    stmt = select(Relationship).where(Relationship.id == relationship_id)
    result = await db.execute(stmt)
    rel = result.scalar_one_or_none()
    if not rel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found.")
    return rel


def _assert_participant(rel: Relationship, user: User) -> None:
    """Raise 403 if user is not a participant in the relationship."""
    if user.id not in {rel.subject_user_id, rel.related_user_id}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this relationship.",
        )


def _assert_subject(rel: Relationship, user: User) -> None:
    """Raise 403 if user is not the *subject* (primary) user of the relationship."""
    if user.id != rel.subject_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the subject user may perform this action.",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=RelationshipRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a pending relationship request",
)
async def create_relationship(
    payload: RelationshipCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> RelationshipRead:
    """The authenticated user becomes the *subject*; the payload specifies the related (supporting) user."""
    if payload.related_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="You cannot create a relationship with yourself.",
        )

    # Ensure the related user exists
    stmt = select(User).where(User.id == payload.related_user_id)
    result = await db.execute(stmt)
    related_user = result.scalar_one_or_none()
    if not related_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Related user not found.")

    # Check uniqueness (SQLAlchemy will also enforce DB constraint, but friendlier error here)
    existing_stmt = select(Relationship).where(
        Relationship.subject_user_id == current_user.id,
        Relationship.related_user_id == payload.related_user_id,
        Relationship.relationship_type == payload.relationship_type.value,
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A relationship of this type already exists between these users.",
        )

    rel = Relationship(
        subject_user_id=current_user.id,
        related_user_id=payload.related_user_id,
        relationship_type=payload.relationship_type.value,
        status=RelationshipStatus.PENDING.value,
    )
    db.add(rel)
    await db.commit()
    await db.refresh(rel)
    return RelationshipRead.model_validate(rel)


@router.get(
    "",
    response_model=list[RelationshipRead],
    summary="List all relationships involving the current user",
)
async def list_relationships(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[RelationshipRead]:
    """Returns all relationships where the user is either subject or related party."""
    stmt = select(Relationship).where(
        (Relationship.subject_user_id == current_user.id)
        | (Relationship.related_user_id == current_user.id)
    )
    result = await db.execute(stmt)
    rels = result.scalars().all()
    return [RelationshipRead.model_validate(r) for r in rels]


@router.get(
    "/{relationship_id}",
    response_model=RelationshipRead,
    summary="Get a single relationship by ID",
)
async def get_relationship(
    relationship_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> RelationshipRead:
    rel = await _get_relationship_or_404(relationship_id, db)
    _assert_participant(rel, current_user)
    return RelationshipRead.model_validate(rel)


@router.patch(
    "/{relationship_id}/status",
    response_model=RelationshipRead,
    summary="Transition relationship status (state machine)",
)
async def update_relationship_status(
    relationship_id: uuid.UUID,
    payload: RelationshipStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> RelationshipRead:
    """Enforces state-machine transitions and role-based authorization."""
    rel = await _get_relationship_or_404(relationship_id, db)
    _assert_participant(rel, current_user)

    new_status = payload.status.value
    current_status = rel.status

    # Validate transition is allowed
    allowed = _ALLOWED_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot transition from '{current_status}' to '{new_status}'.",
        )

    # Subject-only transitions require the subject user
    if new_status in _SUBJECT_ONLY_TRANSITIONS:
        _assert_subject(rel, current_user)

    rel.status = new_status
    await db.commit()
    await db.refresh(rel)
    return RelationshipRead.model_validate(rel)


@router.post(
    "/{relationship_id}/permissions",
    response_model=PermissionRead,
    status_code=status.HTTP_200_OK,
    summary="Grant or revoke a fine-grained permission on an active relationship",
)
async def upsert_permission(
    relationship_id: uuid.UUID,
    payload: PermissionUpsert,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> PermissionRead:
    """Only the *subject_user* of the relationship may manage permissions."""
    rel = await _get_relationship_or_404(relationship_id, db)
    _assert_subject(rel, current_user)

    if rel.status != RelationshipStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Permissions can only be managed on ACTIVE relationships.",
        )

    # Upsert: find existing or create new
    stmt = select(RelationshipPermission).where(
        RelationshipPermission.relationship_id == relationship_id,
        RelationshipPermission.permission == payload.permission.value,
    )
    result = await db.execute(stmt)
    perm = result.scalar_one_or_none()

    if perm:
        perm.granted = payload.granted
    else:
        perm = RelationshipPermission(
            relationship_id=relationship_id,
            permission=payload.permission.value,
            granted=payload.granted,
        )
        db.add(perm)

    await db.commit()
    await db.refresh(perm)
    return PermissionRead.model_validate(perm)


@router.delete(
    "/{relationship_id}/permissions/{permission}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a permission entry from a relationship",
)
async def delete_permission(
    relationship_id: uuid.UUID,
    permission: PermissionType,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """Only the *subject_user* may delete permission entries."""
    rel = await _get_relationship_or_404(relationship_id, db)
    _assert_subject(rel, current_user)

    stmt = select(RelationshipPermission).where(
        RelationshipPermission.relationship_id == relationship_id,
        RelationshipPermission.permission == permission.value,
    )
    result = await db.execute(stmt)
    perm = result.scalar_one_or_none()
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission entry not found.")

    await db.delete(perm)
    await db.commit()
