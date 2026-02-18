"""Goals business logic service.

Provides goal calculation tools that the Goals sub-agent uses.
Wraps database operations with financial logic (feasibility, projections).
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal, GoalStatus


class GoalsService:
    """Financial goals service with calculation tools.

    Provides CRUD operations plus financial computations that the
    Goals sub-agent uses to give advice.

    Attributes:
        db: Async database session.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with a database session.

        Args:
            db: Async SQLAlchemy session.
        """
        self.db = db

    async def list_goals(self, user_id: uuid.UUID) -> list[Goal]:
        """List all goals for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            List of goals ordered by creation date (newest first).
        """
        result = await self.db.execute(
            select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_goal(self, goal_id: uuid.UUID) -> Optional[Goal]:
        """Get a goal by ID.

        Args:
            goal_id: The goal's UUID.

        Returns:
            The goal or None if not found.
        """
        result = await self.db.execute(select(Goal).where(Goal.id == goal_id))
        return result.scalar_one_or_none()

    async def create_goal(
        self,
        user_id: uuid.UUID,
        name: str,
        target_amount: float,
        icon: str = "🎯",
        monthly_contribution: float = 0,
        deadline: Optional[datetime] = None,
        priority: str = "medium",
        notes: Optional[str] = None,
    ) -> Goal:
        """Create a new financial goal.

        Args:
            user_id: Owner's UUID.
            name: Goal name (e.g., "Mașină nouă").
            target_amount: Target amount in RON.
            icon: Emoji icon for the goal.
            monthly_contribution: Planned monthly savings (RON).
            deadline: Target completion date.
            priority: Goal priority (low/medium/high).
            notes: Optional notes.

        Returns:
            The created goal.
        """
        goal = Goal(
            user_id=user_id,
            name=name,
            target_amount=target_amount,
            icon=icon,
            monthly_contribution=monthly_contribution,
            deadline=deadline,
            priority=priority,
            notes=notes,
        )
        self.db.add(goal)
        await self.db.flush()
        await self.db.refresh(goal)
        return goal

    @staticmethod
    def calculate_months_to_goal(
        target_amount: float,
        saved_amount: float,
        monthly_contribution: float,
    ) -> Optional[int]:
        """Calculate how many months until goal is reached.

        Args:
            target_amount: Total target in RON.
            saved_amount: Amount already saved in RON.
            monthly_contribution: Monthly savings in RON.

        Returns:
            Number of months remaining, or None if monthly_contribution is 0.
        """
        remaining = target_amount - saved_amount
        if remaining <= 0:
            return 0
        if monthly_contribution <= 0:
            return None
        return int(remaining / monthly_contribution) + 1

    @staticmethod
    def calculate_required_monthly(
        target_amount: float,
        saved_amount: float,
        months: int,
    ) -> float:
        """Calculate required monthly contribution to meet a deadline.

        Args:
            target_amount: Total target in RON.
            saved_amount: Amount already saved in RON.
            months: Number of months until deadline.

        Returns:
            Required monthly contribution in RON.
        """
        remaining = target_amount - saved_amount
        if remaining <= 0 or months <= 0:
            return 0.0
        return round(remaining / months, 2)

    @staticmethod
    def check_goal_feasibility(
        target_amount: float,
        saved_amount: float,
        monthly_contribution: float,
        deadline: Optional[datetime] = None,
    ) -> dict:
        """Analyze whether a goal is feasible with current parameters.

        Args:
            target_amount: Total target in RON.
            saved_amount: Amount already saved in RON.
            monthly_contribution: Monthly savings in RON.
            deadline: Optional target date.

        Returns:
            Dict with feasibility analysis including months_needed,
            on_track status, and required_monthly if deadline is set.
        """
        remaining = target_amount - saved_amount
        progress_pct = (saved_amount / target_amount * 100) if target_amount > 0 else 0

        result = {
            "remaining_amount": round(remaining, 2),
            "progress_percent": round(progress_pct, 1),
            "monthly_contribution": monthly_contribution,
        }

        if monthly_contribution > 0:
            months_needed = int(remaining / monthly_contribution) + 1
            result["months_needed"] = months_needed
            result["estimated_completion_months"] = months_needed
        else:
            result["months_needed"] = None
            result["estimated_completion_months"] = None

        if deadline:
            now = datetime.now(timezone.utc)
            months_until_deadline = max(
                0,
                (deadline.year - now.year) * 12 + (deadline.month - now.month),
            )
            result["months_until_deadline"] = months_until_deadline

            if months_until_deadline > 0:
                required = round(remaining / months_until_deadline, 2)
                result["required_monthly_for_deadline"] = required
                result["on_track"] = monthly_contribution >= required
            else:
                result["on_track"] = remaining <= 0
        else:
            result["on_track"] = None

        return result

    async def get_goals_summary(self, user_id: uuid.UUID) -> str:
        """Generate a text summary of all user goals for the agent.

        Args:
            user_id: The user's UUID.

        Returns:
            Formatted text summary of all goals with progress and feasibility.
        """
        goals = await self.list_goals(user_id)
        if not goals:
            return "Utilizatorul nu are obiective financiare definite."

        lines = [f"Obiective financiare ({len(goals)} total):\n"]
        for g in goals:
            feasibility = self.check_goal_feasibility(
                float(g.target_amount),
                float(g.saved_amount),
                float(g.monthly_contribution),
                g.deadline,
            )
            status_icon = "✅" if g.status == GoalStatus.COMPLETED.value else "🔄"
            lines.append(
                f"{status_icon} {g.icon} {g.name}: "
                f"{g.saved_amount:,.0f} / {g.target_amount:,.0f} RON "
                f"({g.progress_percent:.0f}%)"
            )
            if feasibility.get("months_needed"):
                lines.append(f"   → {feasibility['months_needed']} luni rămase la {g.monthly_contribution:,.0f} RON/lună")
            if feasibility.get("on_track") is not None:
                track = "pe drumul cel bun" if feasibility["on_track"] else "în urmă"
                lines.append(f"   → Status: {track}")

        return "\n".join(lines)
