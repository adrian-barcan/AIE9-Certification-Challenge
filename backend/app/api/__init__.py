"""API package — FastAPI route registration."""

from app.api.auth import router as auth_router
from app.api.goals import router as goals_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.transactions import router as transactions_router

__all__ = [
    "auth_router",
    "goals_router",
    "chat_router",
    "documents_router",
    "transactions_router",
]
