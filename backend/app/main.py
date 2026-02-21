"""FastAPI application entry point.

Initializes the app, registers routers, creates database tables on startup,
and configures CORS for frontend communication.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.api import users_router, goals_router, chat_router, documents_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    
    # Initialize Langgraph checkpointer
    from app.services.agent_service import agent_service
    await agent_service.setup()
    logger.info("Agent service initialized.")
    
    yield
    
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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(users_router)
app.include_router(goals_router)
app.include_router(chat_router)
app.include_router(documents_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Status and service name.
    """
    return {"status": "healthy", "service": "financial-agent-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
