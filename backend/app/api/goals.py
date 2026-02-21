"""Goals API endpoints.

Full CRUD for financial goals, plus a contribution endpoint.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.goal import Goal
from app.schemas import GoalCreate, GoalUpdate, GoalContribute, GoalResponse

router = APIRouter(prefix="/api/goals", tags=["goals"])


@router.get("/", response_model=List[GoalResponse])
async def list_goals(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[Goal]:
    """List all goals for a user.

    Args:
        user_id: The user's UUID (query param).
        db: Database session.

    Returns:
        List of goals belonging to the user.
    """
    result = await db.execute(
        select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    user_id: uuid.UUID,
    data: GoalCreate,
    db: AsyncSession = Depends(get_db),
) -> Goal:
    """Create a new financial goal.

    Args:
        user_id: The user's UUID (query param).
        data: Goal creation data.
        db: Database session.

    Returns:
        The created goal.
    """
    goal = Goal(user_id=user_id, **data.model_dump())
    db.add(goal)
    await db.flush()
    await db.commit()
    await db.refresh(goal)
    return goal


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Goal:
    """Get a goal by ID.

    Args:
        goal_id: The goal's UUID.
        db: Database session.

    Returns:
        The goal record.

    Raises:
        HTTPException: If goal not found.
    """
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: uuid.UUID,
    data: GoalUpdate,
    db: AsyncSession = Depends(get_db),
) -> Goal:
    """Update a goal (partial update).

    Args:
        goal_id: The goal's UUID.
        data: Fields to update.
        db: Database session.

    Returns:
        The updated goal.

    Raises:
        HTTPException: If goal not found.
    """
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)

    await db.flush()
    await db.commit()
    await db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a goal.

    Args:
        goal_id: The goal's UUID.
        db: Database session.

    Raises:
        HTTPException: If goal not found.
    """
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    await db.delete(goal)
    await db.commit()


@router.post("/{goal_id}/contribute", response_model=GoalResponse)
async def contribute_to_goal(
    goal_id: uuid.UUID,
    data: GoalContribute,
    db: AsyncSession = Depends(get_db),
) -> Goal:
    """Add a contribution to a goal.

    Args:
        goal_id: The goal's UUID.
        data: Contribution amount.
        db: Database session.

    Returns:
        The updated goal with new saved_amount.

    Raises:
        HTTPException: If goal not found.
    """
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    goal.saved_amount = float(goal.saved_amount) + data.amount
    await db.flush()
    await db.commit()
    await db.refresh(goal)
    return goal
