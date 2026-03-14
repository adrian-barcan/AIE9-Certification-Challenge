"""FastAPI application entry point.

Initializes the app, registers routers, creates database tables on startup,
and configures CORS for frontend communication.
"""

import asyncio
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import delete

from app.api import auth_router, goals_router, chat_router, documents_router, transactions_router
from app.config import settings
from app.database import async_session, create_tables
from app.models.session import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _cleanup_expired_sessions_once() -> int:
    """Delete expired auth sessions and return deleted row count."""
    async with async_session() as session:
        result = await session.execute(
            delete(Session).where(Session.expires_at <= datetime.now(timezone.utc))
        )
        await session.commit()
        return int(result.rowcount or 0)


async def _expired_session_cleanup_worker(stop_event: asyncio.Event) -> None:
    """Run periodic cleanup for expired sessions."""
    interval_seconds = max(60, settings.auth_session_cleanup_interval_seconds)
    while not stop_event.is_set():
        deleted = await _cleanup_expired_sessions_once()
        if deleted:
            logger.info("Removed %s expired auth sessions.", deleted)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs on startup and shutdown.

    Startup:
        - Creates database tables via create_all().
        - Intializes LangGraph agent and Postgres checkpointer.

    Shutdown:
        - Closes agent checkpointer connections.
    """
    logger.info("Starting Financial Agent API...")
    await create_tables()
    logger.info("Database tables created.")

    deleted = await _cleanup_expired_sessions_once()
    if deleted:
        logger.info("Removed %s expired auth sessions at startup.", deleted)

    cleanup_stop_event = asyncio.Event()
    cleanup_task = asyncio.create_task(_expired_session_cleanup_worker(cleanup_stop_event))

    # Initialize Langgraph checkpointer
    from app.services.agent_service import agent_service
    await agent_service.setup()
    logger.info("Agent service initialized.")

    yield

    cleanup_stop_event.set()
    await cleanup_task

    await agent_service.close()
    logger.info("Shutting down Financial Agent API.")


app = FastAPI(
    title="Personal Financial Agent API",
    description=(
        "AI-powered financial assistant for Romanian investors. "
        "Uses RAG, LangGraph agents, and financial goal tracking."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend (Next.js on :3000) to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(goals_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(transactions_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Status and service name.
    """
    return {"status": "healthy", "service": "financial-agent-api"}


async def _check_ollama(base_url: str, configured: str) -> dict:
    import httpx
    url = f"{base_url.rstrip('/')}/api/tags"
    async with httpx.AsyncClient(timeout=3.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
    models = [m.get("name", "") for m in data.get("models", [])]
    available = any(configured in n for n in models)
    return {
        "ollama": "connected",
        "base_url": base_url,
        "configured_model": configured,
        "model_available": available,
        "models": models,
    }


@app.get("/health/ollama", tags=["health"])
async def health_ollama() -> dict:
    """Check if Ollama is reachable and the configured model is available.
    Used for transaction categorization (Mistral). If unavailable, backend uses rule-based fallback.
    """
    base_url = ""
    configured = "mistral"
    try:
        from app.config import settings
        base_url = settings.ollama_base_url or ""
        configured = settings.mistral_model or "mistral"
    except Exception:
        pass
    if not base_url:
        return {
            "ollama": "unavailable",
            "base_url": "",
            "configured_model": configured,
            "error": "OLLAMA_BASE_URL not set",
        }
    try:
        return await asyncio.wait_for(_check_ollama(base_url, configured), timeout=5.0)
    except asyncio.TimeoutError:
        return {
            "ollama": "unavailable",
            "base_url": base_url,
            "configured_model": configured,
            "error": "Ollama check timed out after 5s",
        }
    except Exception as e:
        return {
            "ollama": "unavailable",
            "base_url": base_url,
            "configured_model": configured,
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
