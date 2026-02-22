"""Financial goal model.

Tracks user savings goals with target amounts, contributions, deadlines,
and priority levels. Supports calculations like months-to-goal and
required monthly contribution.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class GoalStatus(str, Enum):
    """Status of a financial goal."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class GoalPriority(str, Enum):
    """Priority level of a financial goal."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Goal(Base):
    """A financial savings goal.

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the user who owns this goal.
        name: Goal name (e.g., "Mașină", "Vacanță").
        icon: Emoji icon for the goal (e.g., "🚗", "🏖️").
        target_amount: Total amount to save (RON).
        saved_amount: Amount saved so far (RON).
        monthly_contribution: Planned monthly contribution (RON).
        deadline: Target completion date.
        priority: Goal priority (low/medium/high).
        status: Goal status (active/completed/paused/cancelled).
        notes: Optional notes about the goal.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    icon: Mapped[str] = mapped_column(String(10), default="🎯", nullable=False)
    target_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    saved_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        nullable=False,
    )
    monthly_contribution: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        nullable=False,
    )
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    priority: Mapped[str] = mapped_column(
        String(10),
        default=GoalPriority.MEDIUM.value,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="RON",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(15),
        default=GoalStatus.ACTIVE.value,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    @property
    def progress_percent(self) -> float:
        """Calculate goal completion percentage.

        Returns:
            Percentage of target amount saved (0-100).
        """
        if self.target_amount <= 0:
            return 0.0
        return min(100.0, (float(self.saved_amount) / float(self.target_amount)) * 100)

    @property
    def remaining_amount(self) -> float:
        """Calculate remaining amount to reach the goal.

        Returns:
            Remaining RON needed.
        """
        return max(0.0, float(self.target_amount) - float(self.saved_amount))

    def __repr__(self) -> str:
        return (
            f"<Goal(id={self.id}, name='{self.name}', "
            f"progress={self.progress_percent:.1f}%)>"
        )
