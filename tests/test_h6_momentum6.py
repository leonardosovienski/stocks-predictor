"""H6 — momentum 6-1 (pré-registro 2026-08-27).

Mesma maquinaria da H1 (universo/custos/pareamento/pedágio); só o sinal muda
(janela mais curta: 126 pregões, skip 21). O smoke valida o encadeamento e o
DSR com a trial nova; o veredito real é da rodada única em dados reais.
"""
import datetime

import backtest
import cotahist
import db
import trials_gate


def _dates(n, start=(2016, 7, 1)):
    base = datetime.date(*start)
    return [(base + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]


def _synthetic_conn(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    tickers = [f"T{c}{c}{c}3" for c in "ABCDEFGHIJKL"]
    cotahist.load_prices(conn, cotahist.synthetic_cotahist(tickers, _dates(900), seed=11),
                         "COTAHIST_SYNTH.TXT")
    return conn


def test_run_h6_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}

    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)     # h1 + h2 no tmp
    v = backtest.run_h6(cfg, conn, trials_path=tp)
    conn.close()

    assert "H6:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3     # h1 + h2 + h6 neste registro tmp
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


def test_h6_frozen_config_hash_golden():
    """Mexeu num param [H6-FROZEN] -> quebra alto AQUI (pré-registro 2026-08-27)."""
    from config import h6_frozen_config_hash, load_config
    assert h6_frozen_config_hash(load_config()) == "7ff75a9ade2ee9fb"


def test_h6_frozen_hash_ignores_operational_params():
    from config import h6_frozen_config_hash, load_config
    cfg = load_config()
    base = h6_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h6_frozen_config_hash(cfg) == base
    cfg["h6_factor"]["lookback_days"] = 5             # tocar num FROZEN muda o lacre
    assert h6_frozen_config_hash(cfg) != base
