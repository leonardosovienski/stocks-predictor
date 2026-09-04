"""Analista somente-leitura (§9b) — formatação do briefing Markdown."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "stocks_predictor"))

import analyst


def test_fmt_ptbr_uses_dot_as_thousands_separator():
    # achado de varredura 2026-09-04: `{:,.0f}` puro usa vírgula (convenção
    # US) — em PT-BR a vírgula é o separador DECIMAL, então "1,234,567"
    # lido por um operador brasileiro sugeriria ~1,23, não ~1,23 milhão.
    assert analyst._fmt_ptbr(1_234_567) == "1.234.567"
    assert analyst._fmt_ptbr(999) == "999"
    assert analyst._fmt_ptbr(0) == "0"


def _state(universe):
    return {
        "n_prices": 10, "n_tickers": 2, "date_range": ("2024-01-01", "2024-01-02"),
        "universe_asof": "2024-01-02" if universe else None,
        "universe": universe,
        "quarantine_open": [],
        "top_convictions": [], "last_run": None,
    }


def test_build_brief_liquidity_line_uses_ptbr_thousands():
    state = _state([("PETR4", 1, 1_234_567.0)])
    md = analyst.build_brief(state)
    assert "R$ 1.234.567" in md
    assert "R$ 1,234,567" not in md
