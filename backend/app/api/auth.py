"""Authentication API endpoints."""

from datetime import datetime, timedelta, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SESSION_COOKIE_NAME, get_current_user
from app.config import settings
from app.database import get_db
from app.models.session import Session
from app.models.user import User
from app.schemas import UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SESSION_TTL_DAYS = 30


def _session_expiration() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)


def _new_session_id() -> str:
    return secrets.token_urlsafe(48)


def _set_session_cookie(response: Response, session_id: str) -> None:
    max_age = SESSION_TTL_DAYS * 24 * 60 * 60
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        max_age=max_age,
        expires=max_age,
        path="/",
    )


def _password_len_bytes(password: str) -> int:
    return len(password.encode("utf-8"))


async def _enforce_session_limit(db: AsyncSession, user_id) -> None:
    """Keep only the newest N-1 sessions before creating a new one."""
    max_sessions = max(1, settings.auth_max_sessions_per_user)
    if max_sessions <= 1:
        old_sessions_result = await db.execute(
            select(Session).where(Session.user_id == user_id)
        )
    else:
        old_sessions_result = await db.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.created_at.desc())
        )
    old_sessions = list(old_sessions_result.scalars().all())
    keep_existing = max(0, max_sessions - 1)
    for stale_session in old_sessions[keep_existing:]:
        await db.delete(stale_session)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Register a new user and create an authenticated session."""
    pw_len = _password_len_bytes(data.password)
    if pw_len < 8 or pw_len > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be between 8 and 72 characters.",
        )

    email = data.email.strip().lower()
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        name=data.name.strip(),
        email=email,
        password_hash=pwd_context.hash(data.password),
        preferred_language=data.preferred_language,
        risk_tolerance=data.risk_tolerance,
    )
    session_id = _new_session_id()
    session = Session(
        id=session_id,
        user=user,
        expires_at=_session_expiration(),
    )

    try:
        db.add_all([user, session])
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    _set_session_cookie(response, session_id)
    return user


@router.post("/login", response_model=UserResponse)
async def login(
    data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate with email/password and create a server-side session."""
    email = data.email.strip().lower()
    if _password_len_bytes(data.password) > 72:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    await _enforce_session_limit(db, user.id)
    session_id = _new_session_id()
    session = Session(
        id=session_id,
        user_id=user.id,
        expires_at=_session_expiration(),
    )
    db.add(session)
    await db.commit()

    _set_session_cookie(response, session_id)
    return user


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """Invalidate current session and clear auth cookie."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if session:
            await db.delete(session)
            await db.commit()
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"status": "logged_out"}


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user."""
    return user
