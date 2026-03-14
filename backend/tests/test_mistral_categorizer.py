import asyncio
import importlib.util
from pathlib import Path
import sys
import types


def _load_categorizer_module():
    if "httpx" not in sys.modules:
        httpx_stub = types.ModuleType("httpx")

        class _FailingAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return None

            async def post(self, *args, **kwargs):
                raise RuntimeError("httpx unavailable in unit tests")

        httpx_stub.AsyncClient = _FailingAsyncClient
        sys.modules["httpx"] = httpx_stub

    if "app.config" not in sys.modules:
        app_module = sys.modules.setdefault("app", types.ModuleType("app"))
        config_stub = types.ModuleType("app.config")

        class _Settings:
            ollama_base_url = "http://localhost:11434"
            mistral_model = "mistral"

        config_stub.settings = _Settings()
        sys.modules["app.config"] = config_stub
        setattr(app_module, "config", config_stub)

    module_path = Path(__file__).resolve().parents[1] / "app" / "services" / "mistral_categorizer.py"
    spec = importlib.util.spec_from_file_location("mistral_categorizer_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


categorizer = _load_categorizer_module()
TransactionSignal = categorizer.TransactionSignal
RuleCategorizer = categorizer.RuleCategorizer
parse_ollama_category = categorizer.parse_ollama_category
categorize_batch = categorizer.categorize_batch


def test_rule_categorizer_incasare_internal_transfer():
    signal = TransactionSignal(
        description="Incasare | Ordonator: ADRIAN BARCAN | Din contul: RO54... | Detalii: Plata catre alta banca",
        amount=800.0,
        tx_type="credit",
    )
    assert RuleCategorizer().categorize(signal) == "INTERNAL_TRANSFER"


def test_rule_categorizer_tradeville_transfer_is_investment():
    signal = TransactionSignal(
        description="Transfer Home'Bank | Beneficiar: Tradeville S.A. | Detalii: alimentare BVB LEI",
        amount=-700.0,
        tx_type="debit",
    )
    assert RuleCategorizer().categorize(signal) == "INVESTMENT"


def test_rule_categorizer_small_negative_defaults_to_other_fee():
    signal = TransactionSignal(
        description="Cumparare POS",
        amount=-9.0,
        tx_type="debit",
    )
    assert RuleCategorizer().categorize(signal) == "OTHER_FEE"


def test_parse_ollama_category_handles_noise():
    assert parse_ollama_category("The best match is INTERNAL_TRANSFER.") == "INTERNAL_TRANSFER"


def test_categorize_batch_rule_fallback():
    items = [
        ("Incasare | Ordonator: ADRIAN BARCAN | Din contul: RO54... | Detalii: Plata catre alta banca", 800.0, "credit"),
        ("Transfer Home'Bank | Beneficiar: Tradeville S.A. | Detalii: alimentare BVB LEI", -700.0, "debit"),
    ]
    categories, used_ollama = asyncio.run(categorize_batch(items))
    assert categories == ["INTERNAL_TRANSFER", "INVESTMENT"]
    assert used_ollama is False
