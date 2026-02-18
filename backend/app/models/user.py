"""User model for simple identity management.

No passwords or authentication — just a name and UUID for demo purposes.
The user_id is stored in the frontend's localStorage and sent with every request.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """A user account with simple name-based identity.

    Attributes:
        id: UUID primary key.
        name: Display name entered on first visit.
        preferred_language: User's preferred language (ro/en), auto-detected from chat.
        risk_tolerance: Investment risk tolerance (conservative/moderate/aggressive).
        created_at: Account creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    preferred_language: Mapped[str] = mapped_column(
        String(5),
        default="ro",
        nullable=False,
    )
    risk_tolerance: Mapped[str] = mapped_column(
        String(20),
        default="moderate",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name='{self.name}')>"
