"""CSV transaction parser with bank layout detection.

Parses CSV exports from Romanian banks. Detects layout from header row,
maps to canonical schema (date, amount, description, type, currency).
No external API; stdlib csv only.
"""

import csv
import io
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Canonical schema: what we extract from every CSV
CANONICAL_DATE = "date"
CANONICAL_AMOUNT = "amount"
CANONICAL_DESCRIPTION = "description"
CANONICAL_TYPE = "type"  # "debit" | "credit"
CANONICAL_CURRENCY = "currency"

SUPPORTED_BANKS_MSG = "Unsupported export format. Currently supported: ING, BRD, BCR, Raiffeisen."

# Romanian month names for ING-style "26 februarie 2026"
RO_MONTHS = {
    "ianuarie": 1, "februarie": 2, "martie": 3, "aprilie": 4, "mai": 5, "iunie": 6,
    "iulie": 7, "august": 8, "septembrie": 9, "octombrie": 10, "noiembrie": 11, "decembrie": 12,
}


@dataclass
class ParsedTransaction:
    """One row normalized from CSV."""

    date: datetime
    amount: float  # signed: negative = outflow
    description: str
    type: str  # "debit" | "credit"
    currency: str
    raw_row: dict[str, Any]  # for optional account_id extraction; not stored


def _normalize_header(h: str) -> str:
    """Lowercase, strip, collapse spaces."""
    return " ".join(h.lower().strip().split())


# Bank layouts: header substring or exact normalized header -> canonical field name.
# Each layout has a name and a dict: canonical_field -> list of possible header names (normalized).
BankLayout = dict[str, list[str]]

LAYOUTS: dict[str, BankLayout] = {
    "BRD": {
        CANONICAL_DATE: ["data", "data tranzacție", "data tranzactie", "data tranzacţie", "date"],
        CANONICAL_AMOUNT: ["suma", "amount", "sumă", "suma debit", "suma credit"],
        CANONICAL_DESCRIPTION: ["descriere", "description", "detalii", "explicație", "explicatie"],
        CANONICAL_TYPE: ["tip", "type", "debit/credit", "debit", "credit"],
        CANONICAL_CURRENCY: ["monedă", "moneda", "currency", "valuta"],
    },
    "BCR": {
        CANONICAL_DATE: ["data", "data tranzacție", "data tranzactie", "date", "data operatiunii"],
        CANONICAL_AMOUNT: ["suma", "sumă", "amount", "debit", "credit", "sold"],
        CANONICAL_DESCRIPTION: ["descriere", "description", "detalii", "explicație", "explicatie", "operatiune"],
        CANONICAL_TYPE: ["tip", "type", "debit/credit"],
        CANONICAL_CURRENCY: ["monedă", "moneda", "currency", "valuta"],
    },
    "Raiffeisen": {
        CANONICAL_DATE: ["data", "date", "data tranzacție", "data tranzactie", "booking date"],
        CANONICAL_AMOUNT: ["amount", "suma", "sumă", "debit", "credit", "transaction amount"],
        CANONICAL_DESCRIPTION: ["description", "descriere", "detalii", "details", "beneficiary", "payer"],
        CANONICAL_TYPE: ["type", "tip", "debit/credit"],
        CANONICAL_CURRENCY: ["currency", "monedă", "moneda", "valuta"],
    },
}


def _detect_layout(headers: list[str]) -> tuple[str | None, dict[str, int]]:
    """Match headers to a known layout. Returns (layout_name, field_to_col_index)."""
    normalized = [_normalize_header(h) for h in headers]
    for layout_name, layout in LAYOUTS.items():
        mapping: dict[str, int] = {}
        for canonical_field, possible_headers in layout.items():
            for i, h in enumerate(normalized):
                for ph in possible_headers:
                    if ph in h or h in ph:
                        mapping[canonical_field] = i
                        break
                if canonical_field in mapping:
                    break
        # Need at least date, amount, description to be useful
        if CANONICAL_DATE in mapping and CANONICAL_AMOUNT in mapping and CANONICAL_DESCRIPTION in mapping:
            return layout_name, mapping
    return None, {}


def _parse_date(val: str) -> datetime | None:
    """Parse common date formats (DD.MM.YYYY, YYYY-MM-DD, DD/MM/YYYY)."""
    if not val or not str(val).strip():
        return None
    val = str(val).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(val, fmt).replace(tzinfo=None)
        except ValueError:
            continue
    return None


def _parse_date_ro(val: str) -> datetime | None:
    """Parse Romanian date like '26 februarie 2026' or '30 decembrie 2025'."""
    if not val or not str(val).strip():
        return None
    val = str(val).strip().lower()
    parts = val.split()
    if len(parts) != 3:
        return None
    try:
        day = int(parts[0])
        month = RO_MONTHS.get(parts[1])
        year = int(parts[2])
        if month is None or day < 1 or day > 31 or year < 1990 or year > 2100:
            return None
        return datetime(year, month, day)
    except (ValueError, KeyError):
        return None


def _parse_amount(val: Any) -> float | None:
    """Parse amount: allow 1.234,56 or 80.000,00 or 1,234.56 or -123.45."""
    if val is None or val == "":
        return None
    s = str(val).strip().replace("\u00a0", " ").replace(" ", "").replace('"', "")
    # Romanian: 80.000,00 or 1.234,56 -> remove dots (thousands), comma -> decimal
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    else:
        pass
    s = s.replace(" ", "")
    try:
        return float(s)
    except ValueError:
        return None


def _infer_type_from_amount(amount: float) -> str:
    return "credit" if amount >= 0 else "debit"


def _is_ing_header(row: list[str]) -> bool:
    """Check if this row is ING Bank header: Data, Detalii tranzactie, Debit, Credit."""
    normalized = [_normalize_header(str(h)) for h in row]
    has_data = any("data" in n for n in normalized)
    has_detalii = any("detalii" in n and "tranzactie" in n for n in normalized)
    has_debit = any("debit" in n for n in normalized)
    has_credit = any("credit" in n for n in normalized)
    return bool(has_data and has_detalii and has_debit and has_credit)


def _parse_ing_csv(rows: list[list[str]], filename: str) -> tuple[str, list[ParsedTransaction]]:
    """Parse ING Bank Romania export: multi-row blocks, Romanian dates, Debit/Credit columns.
    rows must start with the header row (caller passes rows[header_idx:]).
    """
    if not rows:
        return "ING", []
    headers = [str(h).strip() for h in rows[0]]
    # ING columns: Data=0, Detalii tranzactie=3, Debit=5, Credit=6
    col_date, col_desc, col_debit, col_credit = 0, 3, 5, 6
    out: list[ParsedTransaction] = []
    for row in rows[1:]:
        if len(row) <= max(col_date, col_desc, col_debit, col_credit):
            continue
        date_val = row[col_date].strip() if col_date < len(row) else ""
        if not date_val or "titular" in date_val.lower() or "data" == date_val.lower():
            continue
        dt = _parse_date_ro(date_val)
        if dt is None:
            continue
        desc = (row[col_desc].strip() if col_desc < len(row) else "") or ""
        debit_s = (row[col_debit].strip() if col_debit < len(row) else "").replace('"', "")
        credit_s = (row[col_credit].strip() if col_credit < len(row) else "").replace('"', "")
        amount: float | None = None
        if debit_s and _parse_amount(debit_s) is not None:
            amount = -abs(_parse_amount(debit_s) or 0)
        elif credit_s and _parse_amount(credit_s) is not None:
            amount = abs(_parse_amount(credit_s) or 0)
        if amount is None:
            continue
        tx_type = "credit" if amount >= 0 else "debit"
        out.append(
            ParsedTransaction(
                date=dt,
                amount=amount,
                description=desc,
                type=tx_type,
                currency="RON",
                raw_row={headers[i]: row[i] for i in range(min(len(headers), len(row)))},
            )
        )
    logger.info("Parsed %d transactions from %s (layout=ING)", len(out), filename or "upload")
    return "ING", out


def parse_csv(content: bytes | str, filename: str = "") -> tuple[str, list[ParsedTransaction]]:
    """Parse CSV content and return (detected_layout_name, list of parsed transactions).

    Args:
        content: Raw CSV bytes or string.
        filename: Optional filename (for logging).

    Returns:
        (layout_name, [ParsedTransaction, ...]). layout_name is e.g. "ING", "BRD", "BCR", "Raiffeisen".

    Raises:
        ValueError: If no known layout matches or CSV is invalid.
    """
    if isinstance(content, bytes):
        text = content.decode("utf-8", errors="ignore")
    else:
        text = content
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise ValueError("CSV file is empty.")
    # Try ING first (multi-row format with Romanian dates)
    for header_idx in (0, 1):
        if header_idx < len(rows) and _is_ing_header(rows[header_idx]):
            # Use from this header row onward (skip any "Titular cont" line above)
            return _parse_ing_csv(rows[header_idx:], filename)
    headers = [str(h).strip() for h in rows[0]]
    layout_name, mapping = _detect_layout(headers)
    if not layout_name or not mapping:
        raise ValueError(SUPPORTED_BANKS_MSG)
    data_rows = rows[1:]
    out: list[ParsedTransaction] = []
    for row in data_rows:
        if len(row) <= max(mapping.values()):
            continue
        date_val = row[mapping[CANONICAL_DATE]] if CANONICAL_DATE in mapping else ""
        amount_val = row[mapping[CANONICAL_AMOUNT]] if CANONICAL_AMOUNT in mapping else ""
        desc_val = (row[mapping[CANONICAL_DESCRIPTION]] if CANONICAL_DESCRIPTION in mapping else "").strip() or ""
        currency_val = (row[mapping[CANONICAL_CURRENCY]] if CANONICAL_CURRENCY in mapping else "RON").strip() or "RON"
        dt = _parse_date(date_val)
        amount = _parse_amount(amount_val)
        if dt is None or amount is None:
            continue
        # Some banks have separate debit/credit columns; here we assume one amount column (signed)
        type_val = ""
        if CANONICAL_TYPE in mapping:
            type_val = str(row[mapping[CANONICAL_TYPE]]).strip().lower()
        if type_val in ("debit", "out", "minus"):
            amount = -abs(amount)
        elif type_val in ("credit", "in", "plus"):
            amount = abs(amount)
        tx_type = _infer_type_from_amount(amount)
        out.append(
            ParsedTransaction(
                date=dt,
                amount=amount,
                description=desc_val,
                type=tx_type,
                currency=currency_val[:3].upper() if currency_val else "RON",
                raw_row={headers[i]: row[i] for i in range(min(len(headers), len(row)))},
            )
        )
    logger.info("Parsed %d transactions from %s (layout=%s)", len(out), filename or "upload", layout_name)
    return layout_name, out
