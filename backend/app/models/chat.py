"""Chat Session model for persistence.

Associates a LangGraph thread_id with a given User.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ChatSession(Base):
    """Database model for an agent conversation session."""
    __tablename__ = "chat_sessions"

    # We use a string ID here to easily match LangGraph's thread_id checkpointer.
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    
    title: Mapped[str] = mapped_column(String(200), default="New Conversation")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
