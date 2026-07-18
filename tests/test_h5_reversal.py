"""H5 — reversão de curto prazo (21 pregões, quintil inferior).

O sinal reusa momentum_12_1(lookback=21, skip=0) — o teste âncora aqui é que
isso É o retorno de 21 pregões, point-in-time. Maquinaria de carteira/custos já
coberta por H1/H2; o smoke valida o encadeamento e o DSR com a trial nova.
"""
import datetime

import pytest

import backtest
import cotahist
import db
import factor
import trials_gate


def test_reversal_signal_is_21d_return():
    dates = [f"2024-02-{d:02d}" for d in range(1, 24)]      # 23 pregões
    closes = [100.0 + i for i in range(23)]                  # sobe 1/dia
    r = factor.momentum_12_1(dates, closes, "2024-02-23", lookback=21, skip=0)
    # closes[22]/closes[1] - 1 = 122/101 - 1
    assert r == pytest.approx(122.0 / 101.0 - 1.0)


def test_reversal_signal_point_in_time():
    dates = [f"2024-02-{d:02d}" for d in range(1, 24)]
    closes = [100.0 + i for i in range(23)]
    asof = "2024-02-22"
    before = factor.momentum_12_1(dates, closes, asof, lookback=21, skip=0)
    mutated = closes[:22] + [99999.0]                        # futuro absurdo
    assert factor.momentum_12_1(dates, mutated, asof, lookback=21, skip=0) == before


def _dates(n, start=(2016, 7, 1)):
    base = datetime.date(*start)
    return [(base + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]


def test_run_h5_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}

    conn = db.get_connection(tmp_path / "s.db")
    tickers = [f"T{c}{c}{c}3" for c in "ABCDEFGHIJKL"]
    cotahist.load_prices(conn, cotahist.synthetic_cotahist(tickers, _dates(900), seed=11),
                         "COTAHIST_SYNTH.TXT")

    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)     # h1 + h2 no tmp
    v = backtest.run_h5(cfg, conn, trials_path=tp)
    conn.close()

    assert "H5:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3     # h1 + h2 + h5 neste registro tmp
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


def test_h5_frozen_config_hash_golden():
    """Mexeu num param [H5-FROZEN] -> quebra alto AQUI (pré-registro 2026-07-18)."""
    from config import h5_frozen_config_hash, load_config
    assert h5_frozen_config_hash(load_config()) == "77f0e1a65033aad7"


def test_h5_frozen_hash_ignores_operational_params():
    from config import h5_frozen_config_hash, load_config
    cfg = load_config()
    base = h5_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h5_frozen_config_hash(cfg) == base
    cfg["h5_factor"]["lookback_days"] = 5            # tocar num FROZEN muda o lacre
    assert h5_frozen_config_hash(cfg) != base
