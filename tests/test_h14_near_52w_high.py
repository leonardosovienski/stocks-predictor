"""H14 — proximidade da máxima de 52 semanas (pré-registro 2026-09-04).

Mesma maquinaria da H1 (universo/custos/pareamento/pedágio); o sinal é
`close(asof)/max(close, 252 pregões)` em vez de retorno acumulado (George &
Hwang 2004) — fator de preço distinto de momentum, zero dado novo.
"""
import datetime

import backtest
import cotahist
import db
import factor
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


def test_run_h14_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}

    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)     # h1 + h2 no tmp
    v = backtest.run_h14(cfg, conn, trials_path=tp)
    conn.close()

    assert "H14:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3     # h1 + h2 + h14 neste registro tmp
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


def test_h14_frozen_config_hash_golden():
    """Mexeu num param [H14-FROZEN] -> quebra alto AQUI (pré-registro 2026-09-04)."""
    from config import h14_frozen_config_hash, load_config
    assert h14_frozen_config_hash(load_config()) == "21b9c2ca735a8684"


def test_h14_frozen_hash_ignores_operational_params():
    from config import h14_frozen_config_hash, load_config
    cfg = load_config()
    base = h14_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h14_frozen_config_hash(cfg) == base
    cfg["h14_factor"]["lookback_days"] = 5            # tocar num FROZEN muda o lacre
    assert h14_frozen_config_hash(cfg) != base


def test_near_52w_high_known_value():
    dates = [f"2020-01-{d:02d}" for d in range(1, 11)]
    closes = [10.0, 12.0, 15.0, 11.0, 13.0, 9.0, 14.0, 8.0, 10.0, 12.0]
    # máxima da janela [asof-9, asof] = 15.0 (dia 3); close(asof)=12.0
    v = factor.near_52w_high(dates, closes, "2020-01-10", lookback=9)
    assert v == 12.0 / 15.0


def test_near_52w_high_none_without_full_history():
    dates = [f"2020-01-{d:02d}" for d in range(1, 6)]
    closes = [10.0, 11.0, 12.0, 13.0, 14.0]
    assert factor.near_52w_high(dates, closes, "2020-01-05", lookback=252) is None


def test_near_52w_high_signals_point_in_time():
    # preço bem mais alto DEPOIS de asof não pode contaminar a máxima da janela.
    dates = [f"2020-01-{d:02d}" for d in range(1, 21)]
    closes = [10.0] * 10 + [100.0] * 10   # salto acontece só depois do dia 10
    series = {"AAAA3": (dates, closes)}
    out = factor.near_52w_high_signals(series, "2020-01-10", lookback=9)
    assert out["AAAA3"] == 1.0    # todos os preços até asof são 10.0 -> proximidade máxima
