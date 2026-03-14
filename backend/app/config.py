"""Application configuration.

Loads all settings from environment variables / .env file using Pydantic Settings.
Covers API keys, database connections, RAG parameters, and LLM model choices.
"""

import json
import os

from pydantic_settings import BaseSettings
from pydantic import Field, model_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # === LLM APIs ===
    openai_api_key: str = Field(..., description="OpenAI API key")
    tavily_api_key: str = Field(..., description="Tavily search API key")
    cohere_api_key: str = Field(..., description="Cohere API key for reranking")

    # === LangSmith ===
    langsmith_api_key: str = Field(default="", description="LangSmith API key")
    langchain_tracing_v2: bool = Field(default=False, description="Enable LangChain tracing (disable if rate-limited)")
    langchain_project: str = Field(default="financial-agent", description="LangSmith project name")

    @model_validator(mode="after")
    def disable_tracing_when_no_langsmith_key(self) -> "Settings":
        """Turn off LangChain tracing when LangSmith API key is missing or empty."""
        if not (self.langsmith_api_key and self.langsmith_api_key.strip()):
            object.__setattr__(self, "langchain_tracing_v2", False)
        return self

    # === PostgreSQL ===
    postgres_user: str = Field(default="financial_agent")
    postgres_password: str = Field(default="changeme")
    postgres_db: str = Field(default="financial_agent")
    postgres_host: str = Field(default="postgres")
    postgres_port: int = Field(default=5432)
    database_url: str = Field(
        default="postgresql+asyncpg://financial_agent:changeme@postgres:5432/financial_agent",
        description="Full async database URL",
    )

    # === Qdrant ===
    qdrant_host: str = Field(default="qdrant")
    qdrant_port: int = Field(default=6333)
    qdrant_collection: str = Field(default="financial_docs_ro")

    # === RAG Configuration ===
    rag_parent_chunk_size: int = Field(default=2000)
    rag_parent_chunk_overlap: int = Field(default=200)
    rag_child_chunk_size: int = Field(default=400)
    rag_child_chunk_overlap: int = Field(default=50)
    rag_top_k: int = Field(default=20, description="Initial retrieval count before reranking")
    rag_rerank_top_n: int = Field(default=12, description="Final count after Cohere reranking")
    embedding_model: str = Field(default="text-embedding-3-small")

    # === LLM Models ===
    supervisor_model: str = Field(default="gpt-4o", description="Model for the supervisor agent")
    specialist_model: str = Field(default="gpt-4o-mini", description="Model for specialist sub-agents")
    summary_model: str = Field(default="gpt-4o-mini", description="Model used to summarize chat history")

    # === Memory Configuration ===
    chat_history_limit: int = Field(default=100, description="Number of recent messages to keep active in memory before summarizing")

    # === Documents ===
    documents_path: str = Field(default="/app/documents", description="Path to financial PDFs")

    # === Transactions (Ollama + anonymization) ===
    ollama_base_url: str = Field(default="http://ollama:11434", description="Ollama API base URL for Mistral")
    mistral_model: str = Field(default="mistral", description="Ollama model name for categorization")
    anonymization_salt: str = Field(default="baniwise-transaction-salt", description="Salt for hashing account IDs (set in production)")
    savings_insights_days: int = Field(default=365, description="Lookback window in days for savings insights summary")
    savings_insights_limit: int = Field(default=2000, description="Max transactions to consider for savings insights")

    # === Auth / Session / CORS ===
    auth_cookie_secure: bool = Field(default=False, description="Use Secure flag for session cookie (enable in production HTTPS)")
    auth_max_sessions_per_user: int = Field(default=5, description="Maximum number of active sessions per user")
    auth_session_cleanup_interval_seconds: int = Field(default=900, description="How often to cleanup expired sessions")
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Allowed CORS origins as CSV or JSON array string",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from CSV or JSON env format."""
        raw = self.cors_origins.strip()
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(origin).strip() for origin in parsed if str(origin).strip()]
            except json.JSONDecodeError:
                pass
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()

# Sync tracing to env so LangChain (which reads os.environ) respects it
os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2).lower()
if settings.langsmith_api_key:
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
