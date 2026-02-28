"""Transaction categorization via Mistral (Ollama) with rule-based fallback.

Sends only description (and optional amount) to local Ollama; returns category only.
If Ollama is unavailable, falls back to keyword rules. No data leaves the server.
"""

import logging
import re
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Fee types are more detailed; anything ending with _FEE is a fee subcategory
CATEGORIES = [
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

CATEGORIES_STR = ", ".join(CATEGORIES)

OLLAMA_PROMPT = f"""Return only one word from this exact list: {CATEGORIES_STR}.
Transaction description: {{description}}
Amount: {{amount}}
Reply with only the single category word, nothing else."""

# Rule-based fallback: keyword (lowercase) -> category
RULE_KEYWORDS: dict[str, str] = {
    "netflix": "SUBSCRIPTION",
    "spotify": "SUBSCRIPTION",
    "youtube": "SUBSCRIPTION",
    "abonament stb": "PUBLIC_TRANSPORT",
    "abonament ratb": "PUBLIC_TRANSPORT",
    "abonament": "SUBSCRIPTION",
    "subscription": "SUBSCRIPTION",
    "kaufland": "GROCERIES",
    "lidl": "GROCERIES",
    "carrefour": "GROCERIES",
    "mega image": "GROCERIES",
    "penny": "GROCERIES",
    "groceries": "GROCERIES",
    "restaurant": "DINING",
    "mcdonald": "DINING",
    "kfc": "DINING",
    "pizza": "DINING",
    "food": "DINING",
    "dining": "DINING",
    # Transport subcategories (most specific first)
    "petrom": "FUEL_TRANSPORT",
    "omv": "FUEL_TRANSPORT",
    "mobil": "FUEL_TRANSPORT",
    "shell": "FUEL_TRANSPORT",
    "molnar": "FUEL_TRANSPORT",
    "rompetrol": "FUEL_TRANSPORT",
    "benzina": "FUEL_TRANSPORT",
    "fuel": "FUEL_TRANSPORT",
    "gas station": "FUEL_TRANSPORT",
    "stb": "PUBLIC_TRANSPORT",
    "ratb": "PUBLIC_TRANSPORT",
    "metro": "PUBLIC_TRANSPORT",
    "tramvai": "PUBLIC_TRANSPORT",
    "tram": "PUBLIC_TRANSPORT",
    "autobuz": "PUBLIC_TRANSPORT",
    "bus ": "PUBLIC_TRANSPORT",
    "cfr": "PUBLIC_TRANSPORT",
    "train": "PUBLIC_TRANSPORT",
    "tren": "PUBLIC_TRANSPORT",
    "uber": "TAXI_AND_RIDESHARE",
    "bolt": "TAXI_AND_RIDESHARE",
    "taxi": "TAXI_AND_RIDESHARE",
    "ride": "TAXI_AND_RIDESHARE",
    "parcare": "PARKING_AND_TOLLS",
    "parking": "PARKING_AND_TOLLS",
    "rovinieta": "PARKING_AND_TOLLS",
    "toll": "PARKING_AND_TOLLS",
    "vignette": "PARKING_AND_TOLLS",
    "service auto": "CAR_MAINTENANCE",
    "reparatii auto": "CAR_MAINTENANCE",
    "anvelope": "CAR_MAINTENANCE",
    "tires": "CAR_MAINTENANCE",
    "mechanic": "CAR_MAINTENANCE",
    "transport": "OTHER_TRANSPORT",
    # Fee subcategories (most specific first so they match before generic)
    "retragere atm": "ATM_FEE",
    "atm fee": "ATM_FEE",
    "atm": "ATM_FEE",
    "cash withdrawal": "ATM_FEE",
    "transfer": "TRANSFER_FEE",
    "comision transfer": "TRANSFER_FEE",
    "transfer fee": "TRANSFER_FEE",
    "card": "CARD_FEE",
    "emisie card": "CARD_FEE",
    "administrare card": "CARD_FEE",
    "descoperit": "OVERDRAFT_FEE",
    "overdraft": "OVERDRAFT_FEE",
    "dobanda": "LOAN_INTEREST_FEE",
    "interest": "LOAN_INTEREST_FEE",
    "dobanda credit": "LOAN_INTEREST_FEE",
    "schimb valutar": "FOREIGN_EXCHANGE_FEE",
    "curs valutar": "FOREIGN_EXCHANGE_FEE",
    "fx": "FOREIGN_EXCHANGE_FEE",
    "cont administrare": "ACCOUNT_MAINTENANCE_FEE",
    "account fee": "ACCOUNT_MAINTENANCE_FEE",
    "maintenance fee": "ACCOUNT_MAINTENANCE_FEE",
    "comision": "OTHER_FEE",
    "commission": "OTHER_FEE",
    "taxa": "OTHER_FEE",
    "fee": "OTHER_FEE",
    "brd": "ACCOUNT_MAINTENANCE_FEE",
    "bcr": "ACCOUNT_MAINTENANCE_FEE",
    "raiffeisen": "ACCOUNT_MAINTENANCE_FEE",
    "banca": "ACCOUNT_MAINTENANCE_FEE",
    "electric": "UTILITIES",
    "gaz": "UTILITIES",
    "apa": "UTILITIES",
    "enel": "UTILITIES",
    "e-on": "UTILITIES",
    "utilities": "UTILITIES",
    # Shopping subcategories (most specific first)
    "emag": "ELECTRONICS_SHOPPING",
    "altex": "ELECTRONICS_SHOPPING",
    "mediagalaxy": "ELECTRONICS_SHOPPING",
    "cel": "ELECTRONICS_SHOPPING",
    "laptop": "ELECTRONICS_SHOPPING",
    "telefon": "ELECTRONICS_SHOPPING",
    "phone": "ELECTRONICS_SHOPPING",
    "tv": "ELECTRONICS_SHOPPING",
    "electronics": "ELECTRONICS_SHOPPING",
    "zara": "CLOTHING_SHOPPING",
    "h&m": "CLOTHING_SHOPPING",
    "h.m": "CLOTHING_SHOPPING",
    "c&a": "CLOTHING_SHOPPING",
    "decathlon": "CLOTHING_SHOPPING",
    "fashion": "CLOTHING_SHOPPING",
    "clothing": "CLOTHING_SHOPPING",
    "haine": "CLOTHING_SHOPPING",
    "incaltaminte": "CLOTHING_SHOPPING",
    "ikea": "HOME_GARDEN_SHOPPING",
    "dedeman": "HOME_GARDEN_SHOPPING",
    "jumbo": "HOME_GARDEN_SHOPPING",
    "leroy merlin": "HOME_GARDEN_SHOPPING",
    "mobila": "HOME_GARDEN_SHOPPING",
    "furniture": "HOME_GARDEN_SHOPPING",
    "dm ": "BEAUTY_AND_PERSONAL_CARE",  # dm with space to avoid matching random letters
    "sephora": "BEAUTY_AND_PERSONAL_CARE",
    "cosmetice": "BEAUTY_AND_PERSONAL_CARE",
    "beauty": "BEAUTY_AND_PERSONAL_CARE",
    "shopping": "OTHER_SHOPPING",
    # Health subcategories (most specific first)
    "farmacie": "PHARMACY_HEALTH",
    "pharmacy": "PHARMACY_HEALTH",
    "medicamente": "PHARMACY_HEALTH",
    "catena": "PHARMACY_HEALTH",
    "sensiblu": "PHARMACY_HEALTH",
    "doctor": "DOCTOR_AND_CLINIC",
    "medic": "DOCTOR_AND_CLINIC",
    "clinica": "DOCTOR_AND_CLINIC",
    "spital": "DOCTOR_AND_CLINIC",
    "hospital": "DOCTOR_AND_CLINIC",
    "analize": "DOCTOR_AND_CLINIC",
    "dentist": "DENTAL_HEALTH",
    "stomatologie": "DENTAL_HEALTH",
    "dental": "DENTAL_HEALTH",
    "dentar": "DENTAL_HEALTH",
    "optician": "OPTICS_HEALTH",
    "ochelari": "OPTICS_HEALTH",
    "lentile": "OPTICS_HEALTH",
    "lenses": "OPTICS_HEALTH",
    "asigurare medicala": "HEALTH_INSURANCE",
    "health insurance": "HEALTH_INSURANCE",
    "cas": "HEALTH_INSURANCE",
    "health": "OTHER_HEALTH",
}


def _rule_based_category(description: str, amount: float) -> str:
    """Classify using keyword rules only."""
    text = (description or "").lower()
    for keyword, category in RULE_KEYWORDS.items():
        if keyword in text:
            return category
    # Negative small amounts often bank/fee charges
    if amount < 0 and abs(amount) < 50:
        return "OTHER_FEE"
    return "OTHER"


async def _ollama_categorize(description: str, amount: float) -> str | None:
    """Call Ollama to get one category. Returns None on failure."""
    url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
    prompt = OLLAMA_PROMPT.format(description=description[:500], amount=amount)
    payload = {
        "model": settings.mistral_model,
        "prompt": prompt,
        "stream": False,
    }
    try:
        # First request can take 60s+ while Ollama loads the model; use 120s timeout
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            response = (data.get("response") or "").strip().upper()
            for cat in CATEGORIES:
                if cat in response or response == cat:
                    return cat
            # Take first word that matches a category
            words = re.split(r"\s+", response)
            for w in words:
                if w in CATEGORIES:
                    return w
            return "OTHER"
    except Exception as e:
        logger.warning("Ollama categorization failed: %s", e)
        return None


async def categorize_transaction(
    description: str, amount: float = 0.0, *, use_ollama: bool = True
) -> tuple[str, bool]:
    """Return (category, used_ollama). If use_ollama and Ollama fails, returns rule-based and used_ollama=False."""
    if use_ollama:
        cat = await _ollama_categorize(description, amount)
        if cat is not None:
            return cat, True
    return _rule_based_category(description, amount), False


async def categorize_batch(
    items: list[tuple[str, float]],
) -> tuple[list[str], bool]:
    """Categorize multiple transactions. Tries Ollama on first item; if it fails, uses rules for entire batch.
    Returns (categories, used_ollama).
    """
    if not items:
        return [], False
    # Try Ollama on first transaction only (fail-fast)
    first_desc, first_amount = items[0]
    first_cat, ollama_ok = await categorize_transaction(first_desc, first_amount, use_ollama=True)
    if not ollama_ok:
        logger.info(
            "Ollama unavailable or failed for first transaction; using rule-based categorization for all %d items",
            len(items),
        )
        results = [first_cat]
        for desc, amount in items[1:]:
            results.append(_rule_based_category(desc, amount))
        return results, False
    logger.info("Ollama connected; categorizing %d transactions with Mistral", len(items))
    results = [first_cat]
    for desc, amount in items[1:]:
        cat, _ = await categorize_transaction(desc, amount, use_ollama=True)
        results.append(cat)
    return results, True
