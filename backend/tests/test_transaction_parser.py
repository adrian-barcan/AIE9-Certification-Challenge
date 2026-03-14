import importlib.util
from pathlib import Path
import sys


def _load_parser_module():
    module_path = Path(__file__).resolve().parents[1] / "app" / "services" / "transaction_parser.py"
    spec = importlib.util.spec_from_file_location("transaction_parser_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


parser_module = _load_parser_module()
parse_csv = parser_module.parse_csv


def test_parse_ing_multiline_details_are_aggregated():
    csv_text = """Titular cont: DL Adrian Barcan,,,,,,
Data,,,Detalii tranzactie,,Debit,Credit
04 februarie 2026,,,Cumparare POS,,"25,47",
,,,Data finalizarii (decontarii): 04-02-2026,,,
,,,Tranzactie la:WWW.ORANGE.RO/YOXO  RO  BUCURESTI,,,
02 februarie 2026,,,Transfer Home'Bank,,"700,00",
,,,Beneficiar:Tradeville S.A.,,,
,,,Detalii:alimentare BVB LEI,,,
02 februarie 2026,,,Incasare,,,"800,00"
,,,Ordonator:ADRIAN BARCAN,,,
,,,Din contul:RO54RZBR0000060021103711,,,
,,,Detalii:Plata catre alta banca,,,
"""
    layout, parsed = parse_csv(csv_text, "sample_ing.csv")
    assert layout == "ING"
    assert len(parsed) == 3
    assert "Tranzactie la:WWW.ORANGE.RO/YOXO" in parsed[0].description
    assert "Beneficiar:Tradeville S.A." in parsed[1].description
    assert "Detalii:Plata catre alta banca" in parsed[2].description
    assert parsed[0].amount == -25.47
    assert parsed[2].amount == 800.0


def test_parse_generic_layout_brd_like():
    csv_text = """Data,Descriere,Suma,Tip,Moneda
02-02-2026,Transfer catre broker,700,debit,RON
03-02-2026,Incasare transfer intern,800,credit,RON
"""
    layout, parsed = parse_csv(csv_text, "sample_brd.csv")
    assert layout == "BRD"
    assert len(parsed) == 2
    assert parsed[0].amount == -700.0
    assert parsed[1].amount == 800.0
    assert parsed[1].type == "credit"
