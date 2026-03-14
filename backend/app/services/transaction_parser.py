"""CSV transaction parser with ING and generic bank parsing strategies."""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Canonical schema: what we extract from every CSV.
CANONICAL_DATE = "date"
CANONICAL_AMOUNT = "amount"
CANONICAL_DESCRIPTION = "description"
CANONICAL_TYPE = "type"  # "debit" | "credit"
CANONICAL_CURRENCY = "currency"

SUPPORTED_BANKS_MSG = "Unsupported export format. Currently supported: ING, BRD, BCR, Raiffeisen."

# Romanian month names for ING-style dates, e.g. "26 februarie 2026".
RO_MONTHS = {
    "ianuarie": 1,
    "februarie": 2,
    "martie": 3,
    "aprilie": 4,
    "mai": 5,
    "iunie": 6,
    "iulie": 7,
    "august": 8,
    "septembrie": 9,
    "octombrie": 10,
    "noiembrie": 11,
    "decembrie": 12,
}

ING_DETAIL_PREFIXES: tuple[str, ...] = (
    "tranzactie la:",
    "beneficiar:",
    "detalii:",
    "ordonator:",
    "din contul:",
    "in contul:",
)

# Bank layouts: canonical field -> list of possible normalized headers.
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


@dataclass
class ParsedTransaction:
    """One row normalized from CSV."""

    date: datetime
    amount: float  # signed: negative = outflow
    description: str
    type: str  # "debit" | "credit"
    currency: str
    raw_row: dict[str, Any]  # for optional account_id extraction; not stored


def normalize_header(value: str) -> str:
    return " ".join(value.lower().strip().split())


def normalize_detail_text(value: str) -> str:
    return " ".join((value or "").split())


def parse_date_generic(value: str) -> datetime | None:
    if not value or not str(value).strip():
        return None
    parsed = str(value).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(parsed, fmt).replace(tzinfo=None)
        except ValueError:
            continue
    return None


def parse_date_ro(value: str) -> datetime | None:
    if not value or not str(value).strip():
        return None
    parts = str(value).strip().lower().split()
    if len(parts) != 3:
        return None
    try:
        day = int(parts[0])
        month = RO_MONTHS.get(parts[1])
        year = int(parts[2])
    except (ValueError, KeyError):
        return None
    if month is None or day < 1 or day > 31 or year < 1990 or year > 2100:
        return None
    return datetime(year, month, day)


def parse_amount(value: Any) -> float | None:
    if value is None or value == "":
        return None
    normalized = str(value).strip().replace("\u00a0", " ").replace(" ", "").replace('"', "")
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def infer_type_from_amount(amount: float) -> str:
    return "credit" if amount >= 0 else "debit"


def is_ing_header(row: list[str]) -> bool:
    normalized = [normalize_header(str(h)) for h in row]
    has_data = any("data" in header for header in normalized)
    has_details = any("detalii" in header and "tranzactie" in header for header in normalized)
    has_debit = any("debit" in header for header in normalized)
    has_credit = any("credit" in header for header in normalized)
    return bool(has_data and has_details and has_debit and has_credit)


def detect_layout(headers: list[str]) -> tuple[str | None, dict[str, int]]:
    normalized = [normalize_header(h) for h in headers]
    for layout_name, layout in LAYOUTS.items():
        mapping: dict[str, int] = {}
        for canonical_field, candidates in layout.items():
            for index, header in enumerate(normalized):
                if any(candidate in header or header in candidate for candidate in candidates):
                    mapping[canonical_field] = index
                    break
        if (
            CANONICAL_DATE in mapping
            and CANONICAL_AMOUNT in mapping
            and CANONICAL_DESCRIPTION in mapping
        ):
            return layout_name, mapping
    return None, {}


class IngParser:
    """Parses ING exports where each transaction spans multiple rows."""

    col_date = 0
    col_desc = 3
    col_debit = 5
    col_credit = 6

    @classmethod
    def is_transaction_start(cls, row: list[str]) -> bool:
        if len(row) <= cls.col_date:
            return False
        date_val = row[cls.col_date].strip()
        if not date_val:
            return False
        if "titular" in date_val.lower() or date_val.lower() == "data":
            return False
        return parse_date_ro(date_val) is not None

    @classmethod
    def collect_detail_rows(cls, rows: list[list[str]], start_idx: int) -> tuple[list[list[str]], int]:
        detail_rows: list[list[str]] = []
        idx = start_idx + 1
        while idx < len(rows):
            if cls.is_transaction_start(rows[idx]):
                break
            detail_rows.append(rows[idx])
            idx += 1
        return detail_rows, idx

    @classmethod
    def extract_detail_parts(cls, rows: list[list[str]]) -> list[str]:
        parts: list[str] = []
        seen: set[str] = set()
        for row in rows:
            detail_raw = row[cls.col_desc].strip() if cls.col_desc < len(row) else ""
            detail = normalize_detail_text(detail_raw)
            detail_lower = detail.lower()
            if detail and any(detail_lower.startswith(prefix) for prefix in ING_DETAIL_PREFIXES):
                if detail_lower not in seen:
                    parts.append(detail)
                    seen.add(detail_lower)
        return parts

    @classmethod
    def build_description(cls, base_description: str, detail_parts: list[str]) -> str:
        base = normalize_detail_text(base_description)
        if not detail_parts:
            return base
        return " | ".join([base] + detail_parts[:6])

    @classmethod
    def parse_ing_amount(cls, row: list[str]) -> float | None:
        debit_raw = row[cls.col_debit].strip() if cls.col_debit < len(row) else ""
        credit_raw = row[cls.col_credit].strip() if cls.col_credit < len(row) else ""
        debit = parse_amount(debit_raw) if debit_raw else None
        credit = parse_amount(credit_raw) if credit_raw else None
        if debit is not None:
            return -abs(debit)
        if credit is not None:
            return abs(credit)
        return None

    @classmethod
    def parse(cls, rows: list[list[str]], filename: str) -> tuple[str, list[ParsedTransaction]]:
        if not rows:
            return "ING", []
        headers = [str(h).strip() for h in rows[0]]
        out: list[ParsedTransaction] = []
        tx_rows = rows[1:]
        idx = 0
        while idx < len(tx_rows):
            row = tx_rows[idx]
            if not cls.is_transaction_start(row):
                idx += 1
                continue
            date_val = row[cls.col_date].strip()
            date = parse_date_ro(date_val)
            if date is None:
                idx += 1
                continue
            details, next_idx = cls.collect_detail_rows(tx_rows, idx)
            base_description = row[cls.col_desc].strip() if cls.col_desc < len(row) else ""
            description = cls.build_description(base_description, cls.extract_detail_parts(details))
            amount = cls.parse_ing_amount(row)
            if amount is None:
                idx = next_idx
                continue
            out.append(
                ParsedTransaction(
                    date=date,
                    amount=amount,
                    description=description,
                    type=infer_type_from_amount(amount),
                    currency="RON",
                    raw_row={headers[i]: row[i] for i in range(min(len(headers), len(row)))},
                )
            )
            idx = next_idx
        logger.info("Parsed %d transactions from %s (layout=ING)", len(out), filename or "upload")
        return "ING", out


class GenericHeaderParser:
    """Parses BRD/BCR/Raiffeisen style exports using header mapping."""

    @staticmethod
    def _row_to_transaction(
        row: list[str],
        headers: list[str],
        mapping: dict[str, int],
    ) -> ParsedTransaction | None:
        if len(row) <= max(mapping.values()):
            return None

        date_val = row[mapping[CANONICAL_DATE]] if CANONICAL_DATE in mapping else ""
        amount_val = row[mapping[CANONICAL_AMOUNT]] if CANONICAL_AMOUNT in mapping else ""
        desc_val = (
            row[mapping[CANONICAL_DESCRIPTION]] if CANONICAL_DESCRIPTION in mapping else ""
        ).strip()
        currency_val = (
            row[mapping[CANONICAL_CURRENCY]] if CANONICAL_CURRENCY in mapping else "RON"
        ).strip() or "RON"

        date = parse_date_generic(date_val)
        amount = parse_amount(amount_val)
        if date is None or amount is None:
            return None

        type_val = ""
        if CANONICAL_TYPE in mapping:
            type_val = str(row[mapping[CANONICAL_TYPE]]).strip().lower()
        if type_val in ("debit", "out", "minus"):
            amount = -abs(amount)
        elif type_val in ("credit", "in", "plus"):
            amount = abs(amount)

        return ParsedTransaction(
            date=date,
            amount=amount,
            description=desc_val or "",
            type=infer_type_from_amount(amount),
            currency=currency_val[:3].upper() if currency_val else "RON",
            raw_row={headers[i]: row[i] for i in range(min(len(headers), len(row)))},
        )

    @classmethod
    def parse(cls, rows: list[list[str]], filename: str) -> tuple[str, list[ParsedTransaction]]:
        headers = [str(h).strip() for h in rows[0]]
        layout_name, mapping = detect_layout(headers)
        if not layout_name or not mapping:
            raise ValueError(SUPPORTED_BANKS_MSG)

        out: list[ParsedTransaction] = []
        for row in rows[1:]:
            tx = cls._row_to_transaction(row, headers, mapping)
            if tx is not None:
                out.append(tx)

        logger.info("Parsed %d transactions from %s (layout=%s)", len(out), filename or "upload", layout_name)
        return layout_name, out


def _parse_ing_csv(rows: list[list[str]], filename: str) -> tuple[str, list[ParsedTransaction]]:
    """Backward-compatible wrapper around IngParser."""
    return IngParser.parse(rows, filename)


def parse_csv(content: bytes | str, filename: str = "") -> tuple[str, list[ParsedTransaction]]:
    """Parse CSV content and return (layout_name, parsed transactions)."""
    text = content.decode("utf-8", errors="ignore") if isinstance(content, bytes) else content
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise ValueError("CSV file is empty.")

    for header_idx in (0, 1):
        if header_idx < len(rows) and is_ing_header(rows[header_idx]):
            return IngParser.parse(rows[header_idx:], filename)

    return GenericHeaderParser.parse(rows, filename)
