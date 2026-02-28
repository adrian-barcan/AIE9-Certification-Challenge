"""Transaction and transaction source models.

Stores only anonymized data: no raw descriptions or account numbers.
TransactionSource = one uploaded file (one account hash). Transaction = one row (category, amount, date).
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class TransactionSource(Base):
    """One imported transaction source (e.g. one CSV upload per account).

    Attributes:
        id: UUID primary key.
        user_id: Owner.
        source_account_hash: Hash of (account_id + user_id + salt); no raw IBAN.
        bank_label: User-defined label (e.g. "BRD Current").
        imported_at: When the file was imported.
        format: Import format (e.g. "csv").
    """

    __tablename__ = "transaction_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_account_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    bank_label: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    format: Mapped[str] = mapped_column(String(20), default="csv", nullable=False)

    def __repr__(self) -> str:
        return f"<TransactionSource(id={self.id}, user_id={self.user_id}, bank_label='{self.bank_label}')>"


class Transaction(Base):
    """A single anonymized transaction.

    No raw description or account number. Only category, amount, date, and optional
    description_hash for deduplication/recurrence detection.
    """

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transaction_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RON", nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    is_recurring: Mapped[bool] = mapped_column(default=False, nullable=False)
    description_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (Index("ix_transactions_user_date", "user_id", "date"),)

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, date={self.date}, amount={self.amount}, category='{self.category}')>"
