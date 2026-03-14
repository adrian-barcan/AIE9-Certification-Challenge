"""Transaction categorization via Mistral (Ollama) with rule-based fallback."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Literal

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Fee types are more detailed; anything ending with _FEE is a fee subcategory.
CATEGORIES: list[str] = [
    "SUBSCRIPTION",
    "GROCERIES",
    "DINING",
    "FUEL_TRANSPORT",
    "PUBLIC_TRANSPORT",
    "TAXI_AND_RIDESHARE",
    "PARKING_AND_TOLLS",
    "CAR_MAINTENANCE",
    "OTHER_TRANSPORT",
    "ACCOUNT_MAINTENANCE_FEE",
    "ATM_FEE",
    "TRANSFER_FEE",
    "CARD_FEE",
    "OVERDRAFT_FEE",
    "LOAN_INTEREST_FEE",
    "FOREIGN_EXCHANGE_FEE",
    "OTHER_FEE",
    "SALARY_INCOME",
    "OTHER_INCOME",
    "INVESTMENT",
    "INTERNAL_TRANSFER",
    "PERSONAL_TRANSFER",
    "UTILITIES",
    "ELECTRONICS_SHOPPING",
    "CLOTHING_SHOPPING",
    "HOME_GARDEN_SHOPPING",
    "BEAUTY_AND_PERSONAL_CARE",
    "OTHER_SHOPPING",
    "PHARMACY_HEALTH",
    "DOCTOR_AND_CLINIC",
    "DENTAL_HEALTH",
    "OPTICS_HEALTH",
    "HEALTH_INSURANCE",
    "OTHER_HEALTH",
    "OTHER",
]
CATEGORIES_SET = set(CATEGORIES)
CATEGORIES_STR = ", ".join(CATEGORIES)

PROMPT_CONTEXT = """Context for Romanian bank exports:
- "Cumparare POS" means card purchase; use merchant clues from "Tranzactie la".
- "Transfer Home'Bank" is a money transfer, not automatically a fee.
- "Incasare" means incoming transfer/income.
- Transfers between own accounts should be INTERNAL_TRANSFER.
- Transfer fees should be TRANSFER_FEE only when wording indicates a fee/commission."""

OLLAMA_PROMPT_TEMPLATE = """Return only one category from this exact list: {categories}.
{context}
Transaction description: {description}
Amount: {amount}
Transaction type: {tx_type}
Reply with only the single category word, nothing else."""

RuleMode = Literal["contains", "prefix", "regex"]


@dataclass(frozen=True, slots=True)
class TransactionSignal:
    description: str
    amount: float
    tx_type: str | None = None

    @property
    def normalized_text(self) -> str:
        return normalize_text(self.description)

    @property
    def inferred_type(self) -> str:
        return (self.tx_type or ("credit" if self.amount >= 0 else "debit")).lower()


@dataclass(frozen=True, slots=True)
class KeywordRule:
    pattern: str
    category: str
    priority: int
    mode: RuleMode = "contains"


def normalize_text(value: str) -> str:
    return " ".join((value or "").lower().split())


def _build_rules(category: str, patterns: tuple[str, ...], start_priority: int) -> list[KeywordRule]:
    return [
        KeywordRule(pattern=p, category=category, priority=start_priority - idx)
        for idx, p in enumerate(patterns)
    ]


RULE_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("SUBSCRIPTION", ("netflix", "spotify", "youtube", "orange", "yoxo", "digi", "vodafone", "abonament", "subscription")),
    ("PUBLIC_TRANSPORT", ("abonament stb", "abonament ratb", "stb", "ratb", "metro", "tramvai", "tram", "autobuz", "bus ", "cfr", "train", "tren")),
    ("GROCERIES", ("kaufland", "lidl", "carrefour", "mega image", "penny", "groceries")),
    ("DINING", ("restaurant", "mcdonald", "kfc", "pizza", "wolt", "tazz", "glovo", "cafe", "cafelier", "bistro", "food", "dining")),
    ("FUEL_TRANSPORT", ("petrom", "omv", "mobil", "shell", "molnar", "rompetrol", "benzina", "fuel", "gas station")),
    ("TAXI_AND_RIDESHARE", ("uber", "bolt", "taxi", "ride")),
    ("PARKING_AND_TOLLS", ("parcare", "parking", "amparcat", "e-parking", "rovinieta", "toll", "vignette")),
    ("CAR_MAINTENANCE", ("service auto", "reparatii auto", "anvelope", "tires", "mechanic", "auto spa", "spalatorie")),
    ("OTHER_TRANSPORT", ("transport",)),
    ("ATM_FEE", ("retragere atm", "atm fee", "atm", "cash withdrawal")),
    ("TRANSFER_FEE", ("comision transfer", "transfer fee")),
    ("CARD_FEE", ("emisie card", "administrare card", "card")),
    ("OVERDRAFT_FEE", ("descoperit", "overdraft")),
    ("LOAN_INTEREST_FEE", ("dobanda credit", "dobanda", "interest")),
    ("FOREIGN_EXCHANGE_FEE", ("schimb valutar", "curs valutar", "fx")),
    ("ACCOUNT_MAINTENANCE_FEE", ("cont administrare", "account fee", "maintenance fee", "brd", "bcr", "raiffeisen", "banca")),
    ("OTHER_FEE", ("comision", "commission", "taxa", "fee")),
    ("UTILITIES", ("electric", "gaz", "apa", "enel", "e-on", "utilities")),
    ("ELECTRONICS_SHOPPING", ("emag", "altex", "mediagalaxy", "cel", "laptop", "telefon", "phone", "tv", "electronics")),
    ("CLOTHING_SHOPPING", ("zara", "h&m", "h.m", "c&a", "decathlon", "fashion", "clothing", "haine", "incaltaminte")),
    ("HOME_GARDEN_SHOPPING", ("ikea", "dedeman", "jumbo", "leroy merlin", "mobila", "furniture")),
    ("BEAUTY_AND_PERSONAL_CARE", ("dm ", "sephora", "cosmetice", "beauty")),
    ("OTHER_SHOPPING", ("shopping",)),
    ("PHARMACY_HEALTH", ("farmacie", "pharmacy", "dona", "medicamente", "catena", "sensiblu")),
    ("DOCTOR_AND_CLINIC", ("doctor", "medic", "clinica", "spital", "hospital", "analize")),
    ("DENTAL_HEALTH", ("dentist", "stomatologie", "dental", "dentar")),
    ("OPTICS_HEALTH", ("optician", "ochelari", "lentile", "lenses")),
    ("HEALTH_INSURANCE", ("asigurare medicala", "health insurance", "cas")),
    ("SALARY_INCOME", ("salariu", "salary")),
    ("INVESTMENT", ("tradeville", "alimentare bvb", "retragere d8ds", "fond", "broker", "invest", "brk")),
    ("OTHER_HEALTH", ("health",)),
)


def _compile_rules() -> tuple[KeywordRule, ...]:
    rules: list[KeywordRule] = []
    priority = 10_000
    for category, patterns in RULE_GROUPS:
        built = _build_rules(category=category, patterns=patterns, start_priority=priority)
        rules.extend(built)
        priority -= 100
    return tuple(sorted(rules, key=lambda r: r.priority, reverse=True))


KEYWORD_RULES: tuple[KeywordRule, ...] = _compile_rules()


def apply_high_priority_transfer_income_rules(signal: TransactionSignal) -> str | None:
    text = signal.normalized_text
    tx_type = signal.inferred_type

    if (
        "incasare" in text
        and tx_type == "credit"
        and ("plata catre alta banca" in text or "ordonator:" in text or "din contul:" in text)
    ):
        if "tradeville" in text or "bvb" in text or "invest" in text:
            return "INVESTMENT"
        if "salariu" in text or "salary" in text:
            return "SALARY_INCOME"
        return "INTERNAL_TRANSFER"

    if "transfer home'bank" in text and tx_type == "debit":
        if "tradeville" in text or "bvb" in text or "invest" in text:
            return "INVESTMENT"
        return "PERSONAL_TRANSFER"

    return None


def _rule_matches(rule: KeywordRule, text: str) -> bool:
    if rule.mode == "prefix":
        return text.startswith(rule.pattern)
    if rule.mode == "regex":
        return re.search(rule.pattern, text) is not None
    return rule.pattern in text


def match_keyword_rules(text: str) -> str | None:
    for rule in KEYWORD_RULES:
        if _rule_matches(rule, text):
            return rule.category
    return None


def fallback_category_for_unmatched(signal: TransactionSignal) -> str:
    if signal.inferred_type == "credit":
        return "OTHER_INCOME"
    if signal.amount < 0 and abs(signal.amount) < 50:
        return "OTHER_FEE"
    return "OTHER"


def build_prompt(signal: TransactionSignal) -> str:
    return OLLAMA_PROMPT_TEMPLATE.format(
        categories=CATEGORIES_STR,
        context=PROMPT_CONTEXT,
        description=signal.description[:500],
        amount=signal.amount,
        tx_type=signal.inferred_type,
    )


def parse_ollama_category(raw_response: str) -> str:
    response = (raw_response or "").strip().upper()
    for category in CATEGORIES:
        if category in response or response == category:
            return category
    for word in re.split(r"\s+", response):
        if word in CATEGORIES_SET:
            return word
    return "OTHER"


class RuleCategorizer:
    def categorize(self, signal: TransactionSignal) -> str:
        high_priority_category = apply_high_priority_transfer_income_rules(signal)
        if high_priority_category is not None:
            return high_priority_category
        keyword_category = match_keyword_rules(signal.normalized_text)
        if keyword_category is not None:
            return keyword_category
        return fallback_category_for_unmatched(signal)


class OllamaCategorizer:
    def __init__(self, timeout_seconds: float = 120.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def categorize(self, signal: TransactionSignal) -> str | None:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
        payload = {
            "model": settings.mistral_model,
            "prompt": build_prompt(signal),
            "stream": False,
        }
        try:
            # First request can take 60s+ while Ollama loads the model.
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return parse_ollama_category(data.get("response") or "")
        except Exception as e:
            logger.warning("Ollama categorization failed: %s", e)
            return None


class CategorizerOrchestrator:
    def __init__(self) -> None:
        self.rule_categorizer = RuleCategorizer()
        self.ollama_categorizer = OllamaCategorizer()

    async def categorize_transaction(self, signal: TransactionSignal, *, use_ollama: bool = True) -> tuple[str, bool]:
        if use_ollama:
            category = await self.ollama_categorizer.categorize(signal)
            if category is not None:
                return category, True
        return self.rule_categorizer.categorize(signal), False

    async def categorize_batch(self, signals: list[TransactionSignal]) -> tuple[list[str], bool]:
        if not signals:
            return [], False

        first_category, ollama_ok = await self.categorize_transaction(signals[0], use_ollama=True)
        if not ollama_ok:
            logger.info(
                "Ollama unavailable or failed for first transaction; using rule-based categorization for all %d items",
                len(signals),
            )
            categories = [first_category]
            categories.extend(self.rule_categorizer.categorize(signal) for signal in signals[1:])
            return categories, False

        logger.info("Ollama connected; categorizing %d transactions with Mistral", len(signals))
        categories = [first_category]
        for signal in signals[1:]:
            category, _ = await self.categorize_transaction(signal, use_ollama=True)
            categories.append(category)
        return categories, True


_ORCHESTRATOR = CategorizerOrchestrator()


def _to_signal(description: str, amount: float, tx_type: str | None) -> TransactionSignal:
    return TransactionSignal(description=description or "", amount=amount, tx_type=tx_type)


async def categorize_transaction(
    description: str,
    amount: float = 0.0,
    tx_type: str | None = None,
    *,
    use_ollama: bool = True,
) -> tuple[str, bool]:
    """Return (category, used_ollama)."""
    return await _ORCHESTRATOR.categorize_transaction(
        _to_signal(description, amount, tx_type), use_ollama=use_ollama
    )


async def categorize_batch(items: list[tuple[str, float, str | None]]) -> tuple[list[str], bool]:
    """Categorize multiple transactions with Ollama fail-fast and rule fallback."""
    signals = [_to_signal(description, amount, tx_type) for description, amount, tx_type in items]
    return await _ORCHESTRATOR.categorize_batch(signals)
