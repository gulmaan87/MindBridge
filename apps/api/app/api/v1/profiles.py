"""Profiles and /users/me endpoints.

Endpoints (API Contract v2 §11, §14):
  GET   /users/me       Canonical current-user route (replaces /auth/me per contract)
  GET   /profiles/me    Current user's primary profile
  PATCH /profiles/me    Update mutable profile fields
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import CurrentUserResponse, ProfileResponse
from app.schemas.profile import ProfileDetail, ProfileUpdate

router = APIRouter(tags=["Users & Profiles"])


# ---------------------------------------------------------------------------
# G1 — GET /users/me  (API Contract v2 §11)
# The canonical path specified in the contract; /auth/me is kept as an alias.
# ---------------------------------------------------------------------------


@router.get(
    "/users/me",
    response_model=CurrentUserResponse,
    summary="Get current authenticated user identity (canonical route)",
)
async def get_users_me(
    current_user: User = Depends(get_current_user),
) -> CurrentUserResponse:
    """Returns the authenticated user's identity, roles, and profiles.

    This is the contract-specified path (§11). The `/auth/me` endpoint
    remains available as a backwards-compatible alias.
    """
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        status=current_user.status,
        email_verified=current_user.email_verified,
        roles=[r.name for r in current_user.roles],
        profiles=[
            ProfileResponse(
                id=p.id,
                profile_type=p.profile_type,
                display_name=p.display_name,
                timezone=p.timezone,
                language=p.language,
            )
            for p in current_user.profiles
        ],
        created_at=current_user.created_at,
    )


# ---------------------------------------------------------------------------
# G2 — GET + PATCH /profiles/me  (API Contract v2 §14)
# ---------------------------------------------------------------------------


def _primary_profile(user: User):
    """Return the user's first profile or raise 404."""
    if not user.profiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile found for this user.",
        )
    return user.profiles[0]


@router.get(
    "/profiles/me",
    response_model=ProfileDetail,
    summary="Get the current user's primary profile",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> ProfileDetail:
    """Returns the first (primary) profile belonging to the authenticated user."""
    profile = _primary_profile(current_user)
    return ProfileDetail.model_validate(profile)


@router.patch(
    "/profiles/me",
    response_model=ProfileDetail,
    summary="Update mutable fields on the current user's primary profile",
)
async def update_my_profile(
    payload: ProfileUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProfileDetail:
    """Partially update the authenticated user's profile.

    Only supplied (non-None) fields are applied; all other fields are preserved.
    """
    profile = _primary_profile(current_user)

    if payload.display_name is not None:
        profile.display_name = payload.display_name
    if payload.timezone is not None:
        profile.timezone = payload.timezone
    if payload.language is not None:
        profile.language = payload.language
    if payload.accessibility_config is not None:
        profile.accessibility_config = payload.accessibility_config

    await db.commit()
    await db.refresh(profile)
    return ProfileDetail.model_validate(profile)
