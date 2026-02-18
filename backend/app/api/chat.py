"""Chat API endpoint.

Handles chat messages by routing them through the LangGraph agent.
Supports streaming responses via Server-Sent Events (SSE).
"""

import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas import ChatRequest
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
        """Generate SSE events from agent response."""
        try:
            async for token in agent_service.stream(
                message=data.message,
                user_id=str(data.user_id),
                session_id=data.session_id,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
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
