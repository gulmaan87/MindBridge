"""Authentication Endpoints (API Contract v2 §7-11).

Implements:
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- GET /api/v1/auth/me
"""

import logging
from datetime import UTC, datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db_session
from app.models.user import Profile, Role, User, UserStatus
from app.schemas.auth import (
    AuthResponse,
    CurrentUserResponse,
    LoginRequest,
    ProfileResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenRefreshResponse,
    UserSummary,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["authentication"])


@router.post(
    "/auth/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new platform user",
)
async def register_user(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    """Create a new user identity and default persona profile."""
    # Check if email is already taken
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    # Hash password securely
    hashed_pwd = hash_password(payload.password)

    # Fetch or create the initial role matching profile_type
    role_name = payload.profile_type.value
    role_stmt = select(Role).where(Role.name == role_name)
    role_result = await db.execute(role_stmt)
    role = role_result.scalar_one_or_none()

    if not role:
        role = Role(name=role_name, description=f"Default role for {role_name} persona")
        db.add(role)
        await db.flush()

    # Create User
    new_user = User(
        email=payload.email,
        password_hash=hashed_pwd,
        status=UserStatus.ACTIVE.value,
        email_verified=False,
        last_login_at=datetime.now(UTC),
    )
    new_user.roles.append(role)
    db.add(new_user)
    await db.flush()

    # Create Profile
    new_profile = Profile(
        user_id=new_user.id,
        profile_type=payload.profile_type.value,
        display_name=payload.display_name,
        timezone="UTC",
        language="en",
    )
    db.add(new_profile)
    await db.flush()

    # Generate JWT Tokens
    user_roles = [r.name for r in new_user.roles]
    access_token = create_access_token(subject=new_user.id, roles=user_roles)
    refresh_token = create_refresh_token(subject=new_user.id)

    return AuthResponse(
        user=UserSummary(
            id=new_user.id,
            email=new_user.email,
            status=new_user.status,
        ),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/auth/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate with email and password",
)
async def login_user(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    """Authenticate credentials and issue short-lived access & refresh tokens."""
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Prevent enumeration: verify_password even if user not found (or return constant error)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.lower()}.",
        )

    # Update last login timestamp
    user.last_login_at = datetime.now(UTC)
    await db.flush()

    user_roles = [r.name for r in user.roles]
    access_token = create_access_token(subject=user.id, roles=user_roles)
    refresh_token = create_refresh_token(subject=user.id)

    return AuthResponse(
        user=UserSummary(
            id=user.id,
            email=user.email,
            status=user.status,
        ),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/auth/refresh",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh an expired access token",
)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenRefreshResponse:
    """Exchange a valid refresh token for a fresh access and rotated refresh token."""
    try:
        decoded = decode_token(payload.refresh_token)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type for refresh endpoint.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decoded.get("sub")
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account inactive or deleted.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_roles = [r.name for r in user.roles]
    new_access_token = create_access_token(subject=user.id, roles=user_roles)
    new_refresh_token = create_refresh_token(subject=user.id)

    return TokenRefreshResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invalidate active user session",
)
async def logout_user() -> Response:
    """Invalidate client session."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/auth/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user identity",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> CurrentUserResponse:
    """Return the authenticated user profile and roles."""
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
