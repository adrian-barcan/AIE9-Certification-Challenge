"""LangGraph Supervisor agent for the Personal Financial Agent.

Implements the Supervisor pattern (AIE9 Session 5) with three specialist
sub-agents: RAG (document queries), Market (live search via Tavily),
and Goals (financial goals management).

Memory architecture (3 of 5 CoALA types from AIE9 Session 6):
- Short-term: MemorySaver checkpointer (conversation context via thread_id)
- Long-term: InMemoryStore namespace (user_id, "profile") for persistent preferences
- Semantic: InMemoryStore namespace (user_id, "knowledge") with embedding search

Usage:
    service = AgentService()
    async for chunk in service.stream("Ce este TEZAUR?", user_id, session_id):
        print(chunk)
"""

import logging
import uuid
from typing import Annotated, Any, AsyncGenerator, Literal, Optional, Sequence

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    RemoveMessage,
)
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from langgraph.graph import END, StateGraph, add_messages
from langgraph.prebuilt import create_react_agent
from psycopg_pool import AsyncConnectionPool
from tavily import AsyncTavilyClient

from app.config import settings
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

# ===================================================================
# System Prompts
# ===================================================================

SUPERVISOR_SYSTEM_PROMPT = """You are a Personal Financial Agent for Romanian investors.
Your name is BaniWise. You help users with:
1. Questions about Romanian financial instruments (TEZAUR, FIDELIS, BVB, etc.)
2. Real-time market data and financial news
3. Managing financial savings goals

IMPORTANT RULES:
- ALWAYS respond in the SAME LANGUAGE the user writes in. If they write in Romanian, respond in Romanian. If in English, respond in English. Auto-detect the language.
- When discussing investment products, ALWAYS add a MiFID II disclaimer at the end.
- Cite sources when using information from documents.
- Be helpful, professional, and encouraging about financial goals.
- Use the appropriate specialist tool for each type of query.

You have access to the following tools:
- rag_query: Search Romanian financial documents (regulations, TEZAUR, FIDELIS, BVB guides)
- market_search: Search for live market data, exchange rates, financial news
- goals_summary: Get the user's current financial goals and progress

Route queries to the right tool:
- Questions about financial products, regulations, definitions → rag_query
- Questions about current prices, exchange rates, news → market_search
- Questions about the user's goals, savings progress → goals_summary
- General financial advice → combine knowledge from tools as needed

{user_context}

CURRENT USER ID (always use this value when calling goals_summary or create_goal): {user_id}

MiFID II DISCLAIMER (add when discussing investments):
"⚠️ Această informație este doar în scop educativ și nu reprezintă o recomandare de investiții conform Directivei MiFID II. Consultați un consilier financiar autorizat înainte de a lua decizii de investiții."
"""


# ===================================================================
# Tools (available to the agent)
# ===================================================================

@tool
async def rag_query(question: str) -> str:
    """Search Romanian financial documents for information about financial instruments, regulations, and investment products.

    Use this tool when the user asks about: TEZAUR, FIDELIS, BVB, ASF regulations,
    Romanian financial products, tax implications, or any financial knowledge topic.

    Args:
        question: The financial question to search documents for.

    Returns:
        Formatted context from relevant document chunks with source citations.
    """
    try:
        context = await rag_service.get_context_for_prompt(question)
        return context
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        return f"Nu am putut accesa documentele financiare: {str(e)}"


@tool
async def market_search(query: str) -> str:
    """Search for live market data, exchange rates, stock prices, and financial news.

    Use this tool when the user asks about: current BVB prices, EUR/RON exchange rate,
    financial news, market trends, or any real-time financial information.

    Args:
        query: The market/financial search query.

    Returns:
        Search results with relevant market information.
    """
    try:
        client = AsyncTavilyClient(api_key=settings.tavily_api_key)
        response = await client.search(
            query=query,
            search_depth="advanced",
            max_results=3,
            include_answer=True,
        )
        # Format results
        parts = []
        if response.get("answer"):
            parts.append(f"Summary: {response['answer']}")
        for result in response.get("results", [])[:3]:
            parts.append(f"- {result.get('title', 'N/A')}: {result.get('content', '')[:200]}")
            parts.append(f"  Source: {result.get('url', '')}")
        return "\n".join(parts) if parts else "Nu am găsit rezultate relevante."
    except Exception as e:
        logger.error(f"Market search failed: {e}")
        return f"Căutarea pe piață a eșuat: {str(e)}"


@tool
async def goals_summary(user_id: str) -> str:
    """Get a summary of the user's financial goals and progress.

    Use this tool when the user asks about their savings goals, progress,
    or financial objectives.

    Args:
        user_id: The user's UUID as a string.

    Returns:
        Formatted summary of all user goals with progress and feasibility.
    """
    try:
        from app.database import async_session
        from app.services.goals_service import GoalsService

        async with async_session() as db:
            service = GoalsService(db)
            summary = await service.get_goals_summary(uuid.UUID(user_id))
            return summary
    except Exception as e:
        logger.error(f"Goals summary failed: {e}")
        return f"Nu am putut accesa obiectivele: {str(e)}"


@tool
async def create_goal(
    user_id: str,
    name: str,
    target_amount: float,
    icon: str = "🎯",
    monthly_contribution: float = 0,
) -> str:
    """Create a new financial savings goal for the user.

    Use this when the user wants to set a new financial goal.

    Args:
        user_id: The user's UUID as a string.
        name: Goal name (e.g., "Mașină", "Vacanță").
        target_amount: Target amount in RON.
        icon: Emoji icon for the goal.
        monthly_contribution: Planned monthly savings in RON.

    Returns:
        Confirmation message with goal details.
    """
    try:
        from app.database import async_session
        from app.services.goals_service import GoalsService

        async with async_session() as db:
            service = GoalsService(db)
            goal = await service.create_goal(
                user_id=uuid.UUID(user_id),
                name=name,
                target_amount=target_amount,
                icon=icon,
                monthly_contribution=monthly_contribution,
            )
            await db.commit()
            months = GoalsService.calculate_months_to_goal(
                target_amount, 0, monthly_contribution
            )
            months_text = f" (~{months} luni)" if months else ""
            return (
                f"✅ Obiectiv creat: {icon} {name}\n"
                f"Țintă: {target_amount:,.0f} RON{months_text}\n"
                f"Contribuție lunară: {monthly_contribution:,.0f} RON"
            )
    except Exception as e:
        logger.error(f"Create goal failed: {e}")
        return f"Nu am putut crea obiectivul: {str(e)}"


# ===================================================================
# Agent Service
# ===================================================================

class AgentService:
    """LangGraph Supervisor agent service.

    Builds and manages the financial agent graph with:
    - A supervisor node (GPT-4o) that routes to specialist tools
    - Short-term memory via AsyncPostgresSaver (conversation context)
    - Long-term memory via AsyncPostgresStore (user preferences)
    - Semantic memory via AsyncPostgresStore (learned financial facts)

    Attributes:
        llm: The supervisor LLM (GPT-4o).
        checkpointer: Short-term memory (conversation threads).
        store: Long-term + semantic memory store.
        graph: Compiled LangGraph agent.
    """

    def __init__(self) -> None:
        """Initialize the agent service with LLM layer."""
        self.llm = ChatOpenAI(
            model=settings.supervisor_model,
            api_key=settings.openai_api_key,
            temperature=0.3,
            streaming=True,
        )
        self.tools = [rag_query, market_search, goals_summary, create_goal]
        self.pool = None
        self.checkpointer = None
        self.store = None
        self.graph = None

    async def setup(self) -> None:
        """Initialize async Postgres connection pool, checkpointer, and store."""
        db_uri = settings.database_url.replace("+asyncpg", "")
        self.pool = AsyncConnectionPool(
            conninfo=db_uri,
            max_size=20,
            kwargs={"autocommit": True, "prepare_threshold": 0},
        )
        # pool.open() not needed explicitly in AsyncConnectionPool as it opens on wait() or first use
        await self.pool.wait()

        self.checkpointer = AsyncPostgresSaver(self.pool)
        self.store = AsyncPostgresStore(self.pool)

        # Setup tables for LangGraph checkpointer and store
        await self.checkpointer.setup()
        await self.store.setup()

        # Build the agent graph
        self.graph = create_react_agent(
            model=self.llm,
            tools=self.tools,
            checkpointer=self.checkpointer,
            store=self.store,
        )

    async def close(self) -> None:
        """Close connection pool cleanly."""
        if self.pool:
            await self.pool.close()

    async def _get_user_context(self, user_id: str) -> str:
        """Build user context from long-term and semantic memory.

        Args:
            user_id: The user's UUID string.

        Returns:
            Formatted user context for the system prompt.
        """
        parts = []

        # Long-term memory: user profile
        profile_namespace = (user_id, "profile")
        try:
            profile_items = self.store.search(profile_namespace)
            if profile_items:
                parts.append("User Profile:")
                for item in profile_items:
                    parts.append(f"  - {item.key}: {item.value}")
        except Exception:
            pass

        # Semantic memory: learned financial knowledge
        knowledge_namespace = (user_id, "knowledge")
        try:
            knowledge_items = self.store.search(knowledge_namespace)
            if knowledge_items:
                parts.append("Known Financial Context:")
                for item in knowledge_items[:5]:  # Limit to top 5
                    parts.append(f"  - {item.value.get('fact', '')}")
        except Exception:
            pass

        if parts:
            return "USER CONTEXT:\n" + "\n".join(parts)
        return ""

    async def _save_user_preference(
        self, user_id: str, key: str, value: Any
    ) -> None:
        """Save a user preference to long-term memory.

        Args:
            user_id: The user's UUID string.
            key: Preference key (e.g., "risk_tolerance").
            value: Preference value.
        """
        namespace = (user_id, "profile")
        self.store.put(namespace, key, {"value": value})

    async def chat(
        self,
        message: str,
        user_id: str,
        session_id: str = "default",
    ) -> str:
        """Send a message to the agent and get a response.

        Args:
            message: The user's message.
            user_id: The user's UUID string.
            session_id: Conversation thread ID for short-term memory.

        Returns:
            The agent's response text.
        """
        user_context = await self._get_user_context(user_id)
        system_prompt = SUPERVISOR_SYSTEM_PROMPT.format(user_context=user_context, user_id=user_id)

        config = {
            "configurable": {
                "thread_id": session_id,
                "user_id": user_id,
            }
        }

        # Truncate history to avoid token overflow
        try:
            state = await self.graph.aget_state(config)
            existing_messages = state.values.get("messages", [])
        except Exception:
            existing_messages = []

        trim_messages = []
        if len(existing_messages) > 10:
            for m in existing_messages[:-10]:
                if hasattr(m, "id") and m.id and not str(m.id).startswith("sys_"):
                    trim_messages.append(RemoveMessage(id=m.id))

        input_messages = {
            "messages": trim_messages + [
                SystemMessage(content=system_prompt, id=f"sys_{user_id}"),
                HumanMessage(content=message),
            ]
        }

        response = await self.graph.ainvoke(input_messages, config=config)
        # Extract the last AI message
        ai_messages = [
            m for m in response["messages"] if isinstance(m, AIMessage) and m.content
        ]
        if ai_messages:
            return ai_messages[-1].content
        return "Nu am putut genera un răspuns."

    async def stream(
        self,
        message: str,
        user_id: str,
        session_id: str = "default",
    ) -> AsyncGenerator[str, None]:
        """Stream agent response tokens.

        Args:
            message: The user's message.
            user_id: The user's UUID string.
            session_id: Conversation thread ID.

        Yields:
            Response tokens as they are generated.
        """
        user_context = await self._get_user_context(user_id)
        system_prompt = SUPERVISOR_SYSTEM_PROMPT.format(user_context=user_context, user_id=user_id)

        config = {
            "configurable": {
                "thread_id": session_id,
                "user_id": user_id,
            }
        }

        # Truncate history to avoid token overflow
        try:
            state = await self.graph.aget_state(config)
            existing_messages = state.values.get("messages", [])
        except Exception:
            existing_messages = []

        trim_messages = []
        if len(existing_messages) > 10:
            for m in existing_messages[:-10]:
                if hasattr(m, "id") and m.id and not str(m.id).startswith("sys_"):
                    trim_messages.append(RemoveMessage(id=m.id))

        input_messages = {
            "messages": trim_messages + [
                SystemMessage(content=system_prompt, id=f"sys_{user_id}"),
                HumanMessage(content=message),
            ]
        }

        async for event in self.graph.astream_events(
            input_messages, config=config, version="v2"
        ):
            if (
                event["event"] == "on_chat_model_stream"
                and event["data"]["chunk"].content
            ):
                yield event["data"]["chunk"].content

    async def get_history(self, session_id: str) -> list[dict]:
        """Get conversation history for a session.

        Args:
            session_id: The conversation thread ID.

        Returns:
            List of message dicts with role and content.
        """
        config = {"configurable": {"thread_id": session_id}}
        try:
            state = await self.graph.aget_state(config)
            messages = state.values.get("messages", [])
            history = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    history.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage) and msg.content:
                    history.append({"role": "assistant", "content": msg.content})
            return history
        except Exception:
            return []


# Singleton instance
agent_service = AgentService()


if __name__ == "__main__":
    import asyncio

    async def test():
        """Quick test of the agent."""
        print("Testing agent...")
        response = await agent_service.chat(
            message="Ce este TEZAUR?",
            user_id="test-user-123",
            session_id="test-session",
        )
        print(f"Response:\n{response}")

    asyncio.run(test())
