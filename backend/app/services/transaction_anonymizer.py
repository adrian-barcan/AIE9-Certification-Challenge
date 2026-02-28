"""Anonymization for transaction data before storage.

Hashes account identifiers; never stores raw description (only category + optional
description_hash for dedup). Used after Mistral categorization.
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AnonymizedTransaction:
    """Record ready for DB: no PII."""

    date: datetime
    amount: float
    currency: str
    category: str
    is_recurring: bool
    description_hash: str | None


def hash_account(account_id: str, user_id: str) -> str:
    """Hash account identifier so it is never stored in raw form."""
    raw = f"{settings.anonymization_salt}:{user_id}:{account_id}"
    return hashlib.sha256(raw.encode()).hexdigest()


def hash_description(description: str) -> str:
    """Hash description for deduplication / recurrence detection only. Not reversible."""
    return hashlib.sha256(description.encode()).hexdigest()


def source_hash_for_upload(user_id: str, filename: str, first_row_preview: str = "") -> str:
    """Produce a stable source_account_hash when we have no real account ID (e.g. CSV upload).

    Uses user_id + filename + optional first row so the same file re-uploaded gets the same hash.
    """
    raw = f"{settings.anonymization_salt}:{user_id}:{filename}:{first_row_preview}"
    return hashlib.sha256(raw.encode()).hexdigest()


def detect_recurring(
    description_hashes: list[str],
    amounts: list[float],
    tolerance_ron: float = 0.01,
) -> list[bool]:
    """Mark transactions as recurring if same description_hash + same amount (within tolerance) appears.

    Simple heuristic: if there are duplicates (same hash, same amount band), mark as recurring.
    """
    n = len(description_hashes)
    recurring = [False] * n
    for i in range(n):
        h, a = description_hashes[i], amounts[i]
        for j in range(n):
            if i == j:
                continue
            if description_hashes[j] == h and abs(amounts[j] - a) <= tolerance_ron:
                recurring[i] = True
                break
    return recurring


def build_anonymized(
    dates: list[datetime],
    amounts: list[float],
    currencies: list[str],
    categories: list[str],
    description_hashes: list[str],
    user_id: str,
    account_id_for_hash: str,
) -> tuple[str, list[AnonymizedTransaction]]:
    """Build source_account_hash and list of anonymized transactions with recurrence flags.

    Args:
        dates, amounts, currencies, categories, description_hashes: parallel lists (from parser + Mistral).
        user_id: For hashing.
        account_id_for_hash: Optional account ID (or upload identifier) for source hash.

    Returns:
        (source_account_hash, [AnonymizedTransaction, ...])
    """
    source_hash = hash_account(account_id_for_hash, user_id)
    recurring = detect_recurring(description_hashes, amounts)
    out = [
        AnonymizedTransaction(
            date=d,
            amount=amt,
            currency=cur,
            category=cat,
            is_recurring=rec,
            description_hash=dh or None,
        )
        for d, amt, cur, cat, rec, dh in zip(
            dates, amounts, currencies, categories, recurring, description_hashes
        )
    ]
    return source_hash, out
