"""Consent API — record, list, and revoke user consent.

Endpoints:
  POST   /consents            Record a new consent decision
  GET    /consents            List all consent records for current user
  GET    /consents/{id}       Get a single consent record
  PATCH  /consents/{id}/revoke  Revoke an active consent

Authorization rules (Engineering Rules §6 – Consent & Privacy):
- Users may only read/modify their own consent records.
- Consent records are immutable once created; revocation creates a revoked_at timestamp.
- Duplicate active consents of the same type are prevented at the API layer.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.consent import Consent, ConsentType
from app.models.user import User
from app.schemas.consent import ConsentCreate, ConsentRead, ConsentRevoke

router = APIRouter(prefix="/consents", tags=["Consent"])


async def _get_consent_or_404(consent_id: uuid.UUID, db: AsyncSession) -> Consent:
    stmt = select(Consent).where(Consent.id == consent_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent record not found.")
    return record


@router.post(
    "",
    response_model=ConsentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new consent decision",
)
async def create_consent(
    payload: ConsentCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ConsentRead:
    """Record a new consent entry for the authenticated user.

    If an active (non-revoked) consent of the same type and version already
    exists, a 409 Conflict is returned — use PATCH /consents/{id}/revoke first.
    """
    existing_stmt = select(Consent).where(
        Consent.user_id == current_user.id,
        Consent.consent_type == payload.consent_type.value,
        Consent.version == payload.version,
        Consent.revoked_at.is_(None),
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"An active '{payload.consent_type.value}' consent (v{payload.version}) "
                "already exists. Revoke it before recording a new one."
            ),
        )

    now = datetime.now(UTC)
    record = Consent(
        user_id=current_user.id,
        consent_type=payload.consent_type.value,
        version=payload.version,
        granted=payload.granted,
        granted_at=now,
        revoked_at=None,
        metadata_payload=payload.metadata_payload,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return ConsentRead.model_validate(record)


@router.get(
    "",
    response_model=list[ConsentRead],
    summary="List all consent records for the current user",
)
async def list_consents(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[ConsentRead]:
    stmt = select(Consent).where(Consent.user_id == current_user.id).order_by(Consent.created_at.desc())
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [ConsentRead.model_validate(r) for r in records]


@router.get(
    "/{consent_id}",
    response_model=ConsentRead,
    summary="Get a single consent record",
)
async def get_consent(
    consent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ConsentRead:
    record = await _get_consent_or_404(consent_id, db)
    if record.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return ConsentRead.model_validate(record)


@router.patch(
    "/{consent_id}/revoke",
    response_model=ConsentRead,
    summary="Revoke an active consent record",
)
async def revoke_consent(
    consent_id: uuid.UUID,
    payload: ConsentRevoke = ConsentRevoke(),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ConsentRead:
    """Stamps revoked_at on the consent record; sets granted=False."""
    record = await _get_consent_or_404(consent_id, db)
    if record.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if record.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This consent record has already been revoked.",
        )

    record.revoked_at = payload.revoked_at or datetime.now(UTC)
    record.granted = False
    await db.commit()
    await db.refresh(record)
    return ConsentRead.model_validate(record)
