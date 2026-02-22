"""CoALA Memory Consolidation Service.

Provides working memory summarization for the chat agent.
"""

import logging
from typing import List
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class MemoryService:
    """Manages conversation history summarization."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.summary_model,
            api_key=settings.openai_api_key,
            temperature=0.1,
        )
        
        self.summary_prompt = """You are a helpful assistant that summarizes conversation history.
Your goal is to create a concise, running summary of the conversation so far.

Current Summary:
{current_summary}

New Messages to Summarize:
{new_messages}

Please provide an updated, concise summary of the ENTIRE conversation so far.
Focus on key facts, user preferences, names, specific financial instruments discussed, and the overall context.
DO NOT respond to the messages, just summarize the facts."""

    async def summarize_messages(self, messages: List[BaseMessage], current_summary: str = "") -> str:
        """Summarize a list of messages and combine with an existing summary."""
        if not messages:
            return current_summary
            
        # Format new messages for the prompt
        formatted_messages = []
        for m in messages:
            role = "User" if isinstance(m, HumanMessage) else "Assistant"
            if m.content:
                formatted_messages.append(f"{role}: {m.content}")
                
        messages_text = "\n".join(formatted_messages)
        
        prompt = self.summary_prompt.format(
            current_summary=current_summary or "No previous summary.",
            new_messages=messages_text
        )
        
        try:
            response = await self.llm.ainvoke([SystemMessage(content=prompt)])
            return response.content
        except Exception as e:
            logger.error(f"Failed to summarize messages: {e}")
            return current_summary

memory_service = MemoryService()
