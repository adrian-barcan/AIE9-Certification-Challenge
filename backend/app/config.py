"""Application configuration.

Loads all settings from environment variables / .env file using Pydantic Settings.
Covers API keys, database connections, RAG parameters, and LLM model choices.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # === LLM APIs ===
    openai_api_key: str = Field(..., description="OpenAI API key")
    tavily_api_key: str = Field(..., description="Tavily search API key")
    cohere_api_key: str = Field(..., description="Cohere API key for reranking")

    # === LangSmith ===
    langsmith_api_key: str = Field(default="", description="LangSmith API key")
    langchain_tracing_v2: bool = Field(default=True, description="Enable LangChain tracing")
    langchain_project: str = Field(default="financial-agent", description="LangSmith project name")

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
    rag_chunk_size: int = Field(default=512)
    rag_chunk_overlap: int = Field(default=64)
    rag_top_k: int = Field(default=5, description="Initial retrieval count before reranking")
    rag_rerank_top_n: int = Field(default=3, description="Final count after Cohere reranking")
    embedding_model: str = Field(default="text-embedding-3-small")

    # === LLM Models ===
    supervisor_model: str = Field(default="gpt-4o", description="Model for the supervisor agent")
    specialist_model: str = Field(default="gpt-4o-mini", description="Model for specialist sub-agents")

    # === Documents ===
    documents_path: str = Field(default="/app/documents", description="Path to financial PDFs")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()
