"""User model for authenticated identity management."""

import uuid
from datetime import datetime

from typing import List

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """A user account with email/password authentication.

    Attributes:
        id: UUID primary key.
        name: Display name entered on registration.
        email: Unique email used for login.
        password_hash: Bcrypt hash of the user password.
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
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
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

    # Relationships
    chat_sessions: Mapped[List["ChatSession"]] = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")
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
