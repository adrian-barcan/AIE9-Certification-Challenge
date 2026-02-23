"""Chat API endpoint.

Handles chat messages by routing them through the LangGraph agent.
Supports streaming responses via Server-Sent Events (SSE).
"""

import json
import logging

import uuid
import traceback
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.chat import ChatSession
from app.schemas import ChatRequest, ChatSessionCreate, ChatSessionResponse, ChatSessionUpdate
from app.services.agent_service import agent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/")
async def chat(data: ChatRequest) -> StreamingResponse:
    """Send a message to the financial agent and receive a streaming response.

    Uses Server-Sent Events (SSE) to stream tokens as they are generated.

    Args:
        data: Chat request with message, user_id, and session_id.

    Returns:
        Streaming response with agent's reply tokens.
    """

    async def event_stream():
        """Generate SSE events from agent response (tokens and status placeholders)."""
        try:
            async for item in agent_service.stream(
                message=data.message,
                user_id=str(data.user_id),
                session_id=data.session_id,
            ):
                # item is either {"token": str} or {"status": str}
                if isinstance(item, dict):
                    yield f"data: {json.dumps(item)}\n\n"
                else:
                    yield f"data: {json.dumps({'token': item})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            logger.error(traceback.format_exc())
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/sync")
async def chat_sync(data: ChatRequest) -> dict:
    """Send a message and get a complete (non-streaming) response.

    Useful for testing and programmatic access.

    Args:
        data: Chat request with message, user_id, and session_id.

    Returns:
        Dict with the full agent response.
    """
    try:
        response = await agent_service.chat(
            message=data.message,
            user_id=str(data.user_id),
            session_id=data.session_id,
        )
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"error": str(e)}


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str) -> list:
    """Get conversation history for a session.

    Args:
        session_id: The conversation thread ID.

    Returns:
        List of messages in the conversation.
    """
    return await agent_service.get_history(session_id)


@router.get("/sessions/{user_id}", response_model=list[ChatSessionResponse])
async def get_chat_sessions(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get all chat sessions for a specific user."""
    result = await db.execute(
        select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc())
    )
    return result.scalars().all()


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(data: ChatSessionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new chat session for a user."""
    session_id = str(uuid.uuid4())
    new_session = ChatSession(
        id=session_id,
        user_id=data.user_id,
        title=data.title,
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(session_id: str, data: ChatSessionUpdate, db: AsyncSession = Depends(get_db)):
    """Update a chat session (e.g. title)."""
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalars().first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.title = data.title
    await db.commit()
    await db.refresh(session)
    return session


@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a chat session."""
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalars().first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    await db.delete(session)
    await db.commit()
    return {"status": "deleted"}
