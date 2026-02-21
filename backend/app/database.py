"""Database connection and session management.

Provides async SQLAlchemy engine and session factory for PostgreSQL.
Tables are created via Base.metadata.create_all() on app startup.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# Async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency that provides a database session.

    Yields:
        AsyncSession: An async database session that auto-closes.
    """
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def create_tables() -> None:
    """Create all database tables.

    Called once on app startup. Uses create_all() which is
    appropriate for a demo (no Alembic migrations needed).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
