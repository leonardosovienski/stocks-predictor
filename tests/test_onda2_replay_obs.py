"""Onda 2 — anti-lookahead ESTRUTURAL (replay) + telemetria (obs) no pipeline.

O walk-forward agora roda sobre replay.replay: o handler acumula histórico só do
passado e é IMPOSSÍVEL o sinal receber uma data futura — verificado aqui por espião
em factor.signals. A telemetria JSONL cobre ingest/quarentena/walk/veredito.
"""
import os
import zipfile

import backtest
import db
import factor
from predictor_core import obs

from tests.test_backtest_onda1 import _TCFG, _build_db


def _events():
    return obs.read_events(os.environ["PREDICTOR_EVENTS_PATH"])


# ---------------------------------------------------------------------------
# replay: o sinal só recebe passado acumulado
# ---------------------------------------------------------------------------

def test_signals_receive_only_accumulated_past(tmp_path, monkeypatch):
    """Espião em factor.signals: TODA série entregue ao sinal termina em <= asof.
    Não é filtro por convenção — o histórico é acumulado evento a evento pelo
    replay, então o futuro nem existe na memória do passo."""
    conn, _ = _build_db(tmp_path)
    orig = factor.signals
    asofs = []

    def spy(series_by_ticker, asof, lookback=252, skip=21):
        assert series_by_ticker, "sinal sem série alguma"
        for tk, (dates, closes) in series_by_ticker.items():
            assert dates and len(dates) == len(closes), tk
            assert max(dates) <= asof, (
                f"LOOKAHEAD: {tk} tem data {max(dates)} > asof {asof}")
        asofs.append(asof)
        return orig(series_by_ticker, asof, lookback, skip)

    monkeypatch.setattr(factor, "signals", spy)
    strat, bench, _ = backtest._walk(conn, _TCFG)
    assert asofs == ["2024-01-20", "2024-02-20"]   # sinais nos month-ends, e só neles
    assert len(strat) == len(bench) == 30          # fev(20) + mar(10), pareado
    conn.close()


def test_replay_engine_reproduces_hand_computed_returns(tmp_path):
    """Regressão de equivalência: o motor sobre replay produz EXATAMENTE os números
    conferidos na mão pelos testes da Onda 1 (entrada D+1 open, custo por turnover)."""
    conn, a_prices = _build_db(tmp_path)
    strat, _, _ = backtest._walk(conn, _TCFG)
    o, c = a_prices["2024-02-01"]
    cost = 2.0 * (0.0003 + 0.0015)
    assert abs(strat[0] - ((c / o - 1.0) - cost)) < 1e-12
    conn.close()


# ---------------------------------------------------------------------------
# obs: telemetria nos pontos de decisão
# ---------------------------------------------------------------------------

def test_walk_and_judge_emit_envelope_events(tmp_path):
    conn, _ = _build_db(tmp_path)
    backtest.run(_TCFG, conn)
    evs = _events()
    names = [e["event"] for e in evs]
    assert "walk_forward" in names and "judge" in names
    wf = next(e for e in evs if e["event"] == "walk_forward")
    assert tuple(wf.keys()) == obs.ENVELOPE_KEYS          # envelope rígido
    assert wf["domain"] == "predictor-stocks"
    assert wf["metrics"]["rebalances"] == 2
    assert wf["metrics"]["days"] == 30
    jd = next(e for e in evs if e["event"] == "judge")
    assert "veredito" in jd["metadata"]
    conn.close()


def test_quarantine_scan_emits_event(tmp_path):
    import adjust
    conn = db.get_connection(tmp_path / "q.db")
    n = adjust.scan_and_quarantine(conn, threshold=0.3)
    evs = _events()
    ev = next(e for e in evs if e["event"] == "quarantine_scan")
    assert ev["metrics"]["quarantined"] == n
    conn.close()


def test_ingest_emits_event(tmp_path):
    import cotahist
    import ingest_cotahist
    line = cotahist.synthetic_cotahist(["AAAA3"], ["20240102"])[0]
    zp = tmp_path / "COTAHIST_TEST.ZIP"
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("COTAHIST.TXT", line)
    n = ingest_cotahist.parse_cotahist(zp, tmp_path / "i.db")
    assert n == 1
    ev = next(e for e in _events() if e["event"] == "ingest")
    assert ev["metrics"]["rows"] == 1
    assert ev["metadata"]["source_file"] == "COTAHIST_TEST.ZIP"
