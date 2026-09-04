"""H11 — momentum 12-1 em RETORNO TOTAL (pré-registro 2026-09-04).

Mesmo sinal da H1, mas sobre `adjust.total_return_series` (proventos
reinvestidos) em vez de só-preço, e janela restrita 2018-2022 (cobertura
real de `dividends`). O smoke valida o encadeamento (dado sintético,
proventos inseridos direto); o veredito real é da rodada única em dado
real.
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
    cotahist.load_prices(conn, cotahist.synthetic_cotahist(tickers, _dates(2400), seed=11),
                         "COTAHIST_SYNTH.TXT")
    # proventos sintéticos espalhados pela janela 2018-2022 (dentro do
    # calendário sintético gerado, que começa em 2016-07-01 e cobre 2400
    # dias corridos — passa de 2022 confortavelmente).
    for i, t in enumerate(tickers):
        conn.execute(
            "INSERT INTO dividends(ticker, ex_date, value_per_share, source)"
            " VALUES (?,?,?,?)",
            (t, "2019-06-15", 0.10 + 0.01 * i, "sintético"))
    conn.commit()
    return conn


def test_run_h11_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}

    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)     # h1 + h2 no tmp
    v = backtest.run_h11(cfg, conn, trials_path=tp)
    conn.close()

    assert "H11:" in capsys.readouterr().out
    assert v["n"] > 0 and v.get("n_trials") == 3     # h1 + h2 + h11 neste registro tmp
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


def test_h11_frozen_config_hash_golden():
    """Mexeu num param [H11-FROZEN] -> quebra alto AQUI (pré-registro 2026-09-04)."""
    from config import h11_frozen_config_hash, load_config
    assert h11_frozen_config_hash(load_config()) == "1a75b7f12695cc97"


def test_h11_frozen_hash_ignores_operational_params():
    from config import h11_frozen_config_hash, load_config
    cfg = load_config()
    base = h11_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h11_frozen_config_hash(cfg) == base
    cfg["h11_backtest"]["test_end"] = "2021-12-31"    # tocar num FROZEN muda o lacre
    assert h11_frozen_config_hash(cfg) != base


def test_run_h11_does_not_mutate_shared_config(tmp_path):
    """H11 sobrescreve backtest.test_start/test_end SÓ pra própria rodada —
    não pode vazar pro cfg compartilhado (que H1-H10 continuam usando)."""
    from config import load_config
    cfg = load_config()
    original_test_start = cfg["backtest"]["test_start"]
    assert "test_end" not in cfg["backtest"]

    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)
    backtest.run_h11(cfg, conn, trials_path=tp)
    conn.close()

    assert cfg["backtest"]["test_start"] == original_test_start
    assert "test_end" not in cfg["backtest"]
