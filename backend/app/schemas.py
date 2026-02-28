"""Pydantic schemas for API request/response validation.

Mirrors SQLAlchemy models but used for FastAPI endpoint serialization.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# === User Schemas ===

class UserCreate(BaseModel):
    """Request schema for creating a new user."""
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    preferred_language: str = Field(default="ro", description="Preferred language (ro or en)")
    risk_tolerance: str = Field(default="moderate", description="Risk tolerance (conservative, moderate, aggressive)")


class UserResponse(BaseModel):
    """Response schema for user data."""
    id: uuid.UUID
    name: str
    preferred_language: str
    risk_tolerance: str
    created_at: datetime

    model_config = {"from_attributes": True}


# === Goal Schemas ===

class GoalCreate(BaseModel):
    """Request schema for creating a new goal."""
    name: str = Field(..., min_length=1, max_length=200)
    icon: str = Field(default="🎯", max_length=10)
    target_amount: float = Field(..., gt=0, description="Target amount in RON")
    monthly_contribution: float = Field(default=0, ge=0)
    deadline: Optional[datetime] = None
    priority: str = Field(default="medium")
    currency: str = Field(default="RON", max_length=3)
    notes: Optional[str] = None


class GoalUpdate(BaseModel):
    """Request schema for updating a goal (partial)."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    icon: Optional[str] = Field(None, max_length=10)
    target_amount: Optional[float] = Field(None, gt=0)
    monthly_contribution: Optional[float] = Field(None, ge=0)
    deadline: Optional[datetime] = None
    priority: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[str] = None
    notes: Optional[str] = None


class GoalContribute(BaseModel):
    """Request schema for adding a contribution to a goal."""
    amount: float = Field(..., gt=0, description="Contribution amount in RON")


class GoalResponse(BaseModel):
    """Response schema for goal data."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    icon: str
    target_amount: float
    saved_amount: float
    monthly_contribution: float
    deadline: Optional[datetime]
    priority: str
    currency: str
    status: str
    notes: Optional[str]
    progress_percent: float
    remaining_amount: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# === Chat Schemas ===

class ChatRequest(BaseModel):
    """Request schema for chat messages."""
    message: str = Field(..., min_length=1, description="User message")
    user_id: uuid.UUID = Field(..., description="User identifier")
    session_id: str = Field(default="default", description="Conversation thread ID")


class ChatSessionCreate(BaseModel):
    """Request schema for creating a chat session."""
    user_id: uuid.UUID
    title: str = Field(default="New Conversation", max_length=200)


class ChatSessionUpdate(BaseModel):
    """Request schema for updating a chat session."""
    title: str = Field(..., max_length=200)


class ChatSessionResponse(BaseModel):
    """Response schema for chat session data."""
    id: str
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    """Response schema for a single chat message in history."""
    role: str
    content: str
    timestamp: Optional[datetime] = None


# === Document Schemas ===

class DocumentInfo(BaseModel):
    """Response schema for an indexed document."""
    filename: str
    chunk_count: int
    indexed_at: Optional[datetime] = None


class IngestResponse(BaseModel):
    """Response schema for document ingestion."""
    documents_processed: int
    total_chunks: int
    collection: str


# === Transaction Schemas ===

class TransactionSourceResponse(BaseModel):
    """Response schema for a transaction source (no sensitive data)."""
    id: uuid.UUID
    user_id: uuid.UUID
    bank_label: str
    imported_at: datetime
    format: str
    transaction_count: Optional[int] = None

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    """Response schema for a single anonymized transaction."""
    id: uuid.UUID
    user_id: uuid.UUID
    source_id: uuid.UUID
    date: datetime
    amount: float
    currency: str
    category: str
    is_recurring: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionIngestResponse(BaseModel):
    """Response schema after uploading a CSV."""
    source_id: uuid.UUID
    transactions_imported: int
    bank_label: str
    categorization_source: str = "rules"  # "ollama" if Mistral was used, "rules" if fallback
