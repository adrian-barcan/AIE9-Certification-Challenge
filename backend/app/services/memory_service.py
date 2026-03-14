"""CoALA Memory Consolidation Service.

Provides working memory summarization and fact/preference extraction for the chat agent.
"""

import json
import logging
from typing import Any, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """Analyze this conversation turn and extract structured information to remember.

User message: {user_message}
Assistant response: {assistant_response}

Output a JSON object with exactly these keys (use null if nothing to extract):
- "preferences": object with optional keys: "risk_tolerance" (conservative/moderate/aggressive), "preferred_language" (ro/en)
- "facts": list of strings, each a concise financial fact the user stated (e.g. "User has 50000 RON saved", "User interested in TEZAUR bonds")

Only include preferences/facts that the USER explicitly stated or clearly implied. Do not infer from the assistant's response.
Output ONLY valid JSON, no other text."""


class MemoryService:
    """Manages conversation history summarization."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.summary_model,
            api_key=settings.openai_api_key,
            temperature=0.1,
            max_retries=3,
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

    async def extract_facts_and_preferences(
        self, user_message: str, assistant_response: str
    ) -> dict[str, Any]:
        """Extract user preferences and financial facts from a conversation turn.

        Returns:
            Dict with "preferences" (dict) and "facts" (list of str).
        """
        if not user_message or not assistant_response:
            return {"preferences": {}, "facts": []}
        prompt = EXTRACT_PROMPT.format(
            user_message=user_message[:1000],
            assistant_response=assistant_response[:1500],
        )
        try:
            response = await self.llm.ainvoke([SystemMessage(content=prompt)])
            text = (response.content or "").strip()
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            data = json.loads(text)
            return {
                "preferences": data.get("preferences") or {},
                "facts": data.get("facts") or [],
            }
        except Exception as e:
            logger.warning("Failed to extract facts/preferences: %s", e)
            return {"preferences": {}, "facts": []}


memory_service = MemoryService()
