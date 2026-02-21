"""User API endpoints.

Simple identity management — no passwords, no tokens.
User enters a name on first visit, gets a UUID back.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Create a new user with just a name.

    Args:
        data: User creation data (name only).
        db: Database session.

    Returns:
        The created user with generated UUID.
    """
    user = User(
        name=data.name,
        preferred_language=data.preferred_language,
        risk_tolerance=data.risk_tolerance,
    )
    db.add(user)
    await db.flush()
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get a user by ID.

    Args:
        user_id: The user's UUID.
        db: Database session.

    Returns:
        The user record.

    Raises:
        HTTPException: If user not found.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
