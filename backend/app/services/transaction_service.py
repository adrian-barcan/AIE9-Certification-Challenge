"""Transaction ingest and query service.

Orchestrates: parse CSV -> Mistral categorize -> anonymize -> store.
Lists sources and transactions (anonymized only).
Provides anonymized summary for savings_insights agent tool.
"""

import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction, TransactionSource
from app.services.transaction_parser import parse_csv, ParsedTransaction
from app.services.mistral_categorizer import categorize_batch
from app.services.transaction_anonymizer import (
    hash_description,
    source_hash_for_upload,
    build_anonymized,
    AnonymizedTransaction,
)

# Use timezone-naive for DB if DB stores UTC; keep consistency with parser (naive)
def _ensure_tz(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=None)
    return dt


class TransactionService:
    """Ingest and query anonymized transactions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def ingest_csv(
        self,
        user_id: uuid.UUID,
        content: bytes,
        filename: str = "upload.csv",
        bank_label: str = "",
    ) -> tuple[TransactionSource, int]:
        """Parse CSV, categorize with Mistral, anonymize, and store.

        Returns:
            (created TransactionSource, number of transactions stored).
        """
        layout_name, parsed = parse_csv(content, filename)
        if not parsed:
            source_hash = source_hash_for_upload(str(user_id), filename, "")
            source = TransactionSource(
                user_id=user_id,
                source_account_hash=source_hash,
                bank_label=bank_label.strip() or f"{layout_name} import",
                format="csv",
            )
            self.db.add(source)
            await self.db.flush()
            return source, 0, False

        # Categorize (Mistral or rule fallback; fail-fast if Ollama down)
        items = [(p.description, p.amount) for p in parsed]
        categories, used_ollama = await categorize_batch(items)

        # Description hashes for dedup/recurrence (then discard descriptions)
        desc_hashes = [hash_description(p.description) for p in parsed]
        dates = [_ensure_tz(p.date) for p in parsed]
        amounts = [p.amount for p in parsed]
        currencies = [p.currency for p in parsed]

        account_id = f"{filename}:{layout_name}:{desc_hashes[0] if desc_hashes else ''}"
        source_hash, anon_list = build_anonymized(
            dates=dates,
            amounts=amounts,
            currencies=currencies,
            categories=categories,
            description_hashes=desc_hashes,
            user_id=str(user_id),
            account_id_for_hash=account_id,
        )

        label = bank_label.strip() or f"{layout_name} import"
        source = TransactionSource(
            user_id=user_id,
            source_account_hash=source_hash,
            bank_label=label,
            format="csv",
        )
        self.db.add(source)
        await self.db.flush()

        for a in anon_list:
            tx = Transaction(
                user_id=user_id,
                source_id=source.id,
                date=a.date,
                amount=a.amount,
                currency=a.currency,
                category=a.category,
                is_recurring=a.is_recurring,
                description_hash=a.description_hash,
            )
            self.db.add(tx)
        await self.db.flush()
        count = len(anon_list)
        return source, count, used_ollama

    async def list_sources(self, user_id: uuid.UUID) -> list[TransactionSource]:
        """List transaction sources for a user."""
        result = await self.db.execute(
            select(TransactionSource)
            .where(TransactionSource.user_id == user_id)
            .order_by(TransactionSource.imported_at.desc())
        )
        return list(result.scalars().all())

    async def get_source(
        self, source_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[TransactionSource]:
        """Get one source if it belongs to the user."""
        result = await self.db.execute(
            select(TransactionSource).where(
                TransactionSource.id == source_id,
                TransactionSource.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_source(self, source_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a source and its transactions. Returns True if deleted."""
        source = await self.get_source(source_id, user_id)
        if not source:
            return False
        await self.db.delete(source)
        await self.db.flush()
        return True

    async def list_transactions(
        self,
        user_id: uuid.UUID,
        source_id: Optional[uuid.UUID] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 500,
    ) -> list[Transaction]:
        """List anonymized transactions for a user (optional filters)."""
        q = select(Transaction).where(Transaction.user_id == user_id)
        if source_id is not None:
            q = q.where(Transaction.source_id == source_id)
        if from_date is not None:
            q = q.where(Transaction.date >= from_date)
        if to_date is not None:
            q = q.where(Transaction.date <= to_date)
        q = q.order_by(Transaction.date.desc()).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_savings_insights_summary(self, user_id: uuid.UUID) -> str:
        """Build anonymized summary for the agent: spending by category, recurring, fees.
        Used by savings_insights tool; only aggregates, no PII.
        """
        since = datetime.utcnow() - timedelta(days=365)
        txs = await self.list_transactions(user_id=user_id, from_date=since, limit=2000)
        if not txs:
            return (
                "The user has no imported transactions yet. "
                "Suggest they upload a CSV bank statement from the Transactions page to get saving opportunities."
            )
        # Outflows (negative amount) by category
        by_category: dict[str, float] = defaultdict(float)
        recurring_total = 0.0
        fee_total = 0.0
        for t in txs:
            amt = float(t.amount)
            if amt >= 0:
                continue
            out = abs(amt)
            by_category[t.category] += out
            if t.is_recurring:
                recurring_total += out
            if t.category.endswith("_FEE"):
                fee_total += out
        lines = ["Anonymized transaction summary (categories and amounts only):"]
        lines.append("Monthly spending by category (outflows, last 12 months):")
        for cat in sorted(by_category.keys()):
            lines.append(f"  - {cat}: {by_category[cat]:,.0f} RON")
        if recurring_total > 0:
            lines.append(f"Recurring outflows (total): {recurring_total:,.0f} RON")
        if fee_total > 0:
            lines.append(f"Fees (total): {fee_total:,.0f} RON")
        lines.append(f"Total transactions considered: {len(txs)}")
        return "\n".join(lines)
