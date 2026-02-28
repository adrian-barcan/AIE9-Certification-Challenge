"""Transactions API: upload CSV, list sources, list transactions, delete source."""

import uuid
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.transaction import Transaction, TransactionSource
from app.schemas import (
    TransactionSourceResponse,
    TransactionResponse,
    TransactionIngestResponse,
)
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def _source_to_response(source: TransactionSource, count: Optional[int] = None) -> TransactionSourceResponse:
    return TransactionSourceResponse(
        id=source.id,
        user_id=source.user_id,
        bank_label=source.bank_label,
        imported_at=source.imported_at,
        format=source.format,
        transaction_count=count,
    )


@router.post("/ingest", response_model=TransactionIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_transactions(
    user_id: uuid.UUID,
    file: UploadFile = File(...),
    bank_label: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
) -> TransactionIngestResponse:
    """Upload a CSV bank statement. We auto-detect format (BRD, BCR, Raiffeisen). Parse, categorize (Mistral), anonymize, and store."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported.",
        )
    content = await file.read()
    try:
        service = TransactionService(db)
        source, count, used_ollama = await service.ingest_csv(
            user_id=user_id,
            content=content,
            filename=file.filename or "upload.csv",
            bank_label=bank_label,
        )
        await db.commit()
        await db.refresh(source)
        return TransactionIngestResponse(
            source_id=source.id,
            transactions_imported=count,
            bank_label=source.bank_label,
            categorization_source="ollama" if used_ollama else "rules",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError as e:
        await db.rollback()
        err_msg = str(getattr(e, "orig", e)).lower()
        if "users" in err_msg or "user_id" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found. Create a user (e.g. from the app welcome screen) and try again.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data error: {err_msg}",
        )
    except Exception as e:
        logger.exception("Ingest failed: %s", e)
        await db.rollback()
        detail = str(e) if str(e) else "Import failed."
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


@router.get("/sources", response_model=List[TransactionSourceResponse])
async def list_sources(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[TransactionSourceResponse]:
    """List transaction sources (imports) for the user. No sensitive data."""
    service = TransactionService(db)
    sources = await service.list_sources(user_id)
    out = []
    for s in sources:
        result = await db.execute(
            select(func.count(Transaction.id)).where(Transaction.source_id == s.id)
        )
        count = result.scalar() or 0
        out.append(_source_to_response(s, count=count))
    return out


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    user_id: uuid.UUID,
    source_id: Optional[uuid.UUID] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 500,
    db: AsyncSession = Depends(get_db),
) -> List[TransactionResponse]:
    """List anonymized transactions (category, date, amount). Optional filters by source and date range."""
    service = TransactionService(db)
    transactions = await service.list_transactions(
        user_id=user_id,
        source_id=source_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )
    return [TransactionResponse.model_validate(t) for t in transactions]


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a transaction source and all its transactions."""
    service = TransactionService(db)
    deleted = await service.delete_source(source_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found.",
        )
    await db.commit()