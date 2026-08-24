"""Testes de regressão da auditoria 2026-08-24 (branch audit/2026-08-24-fixes).

Cada teste aqui reproduz um bug confirmado da auditoria no código do domínio
RJ e trava a correção — sem tocar valores [RJ-FROZEN], as 8 famílias
pré-registradas ou o FDR BH alpha=0.10.
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import rj_families as families
import rj_families_next as nextgen


# --- Bug A: fallback `known_at or event_date` = lookahead informacional -----

def test_ownership_event_without_known_at_is_not_eligible():
    """Protocolo §8/§10: event_date NÃO é known_at. Evento sem known_at
    válido não pode contar como sinal — antes da correção contava (lookahead)."""
    events = [{"event_type": "investidor_5pct", "event_date": "2020-05-10",
               "known_at": None}]
    assert families.ownership(events, "2020-05-20") == 0
    events2 = [{"event_type": "investidor_5pct", "event_date": "2020-05-10"}]
    assert families.ownership(events2, "2020-05-20") == 0
    # known_at válido dentro da janela continua sinalizando
    ok = [{"event_type": "investidor_5pct", "event_date": "2020-05-10",
           "known_at": "2020-05-12"}]
    assert families.ownership(ok, "2020-05-20") == 1


def test_info_trigger_event_without_known_at_is_not_eligible():
    events = [{"event_type": "fato_relevante", "event_date": "2020-05-10",
               "known_at": None}]
    assert families.info_trigger(events, "2020-05-15") == 0
    ok = [{"event_type": "fato_relevante", "event_date": "2020-05-10",
           "known_at": "2020-05-11"}]
    assert families.info_trigger(ok, "2020-05-15") == 1


def test_equity_issuance_event_without_known_at_is_not_eligible():
    events = [{"event_type": "aumento_capital", "event_date": "2020-05-10",
               "known_at": None}]
    assert nextgen.equity_issuance(events, "2020-05-20") == 0


def test_ownership_invalid_trough_date_is_unavailable_not_zero():
    """Fundo inválido = dado INDISPONÍVEL (None), nunca 0 — zero seria
    'sabemos que não houve evento', que é exatamente o que não sabemos."""
    assert families.ownership([], "nao-e-data") is None
    assert families.info_trigger([], "2020-13-99") is None
    assert nextgen.equity_issuance([], "lixo") is None
