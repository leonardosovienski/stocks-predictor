"""H15 — volume anormal (pré-registro 2026-09-04).

Mesma maquinaria da H1; o sinal é volume médio recente vs. longo prazo
(`factor.volume_surge_signals`) — `volume_fin` já vive em `prices_raw`
desde o M1, nunca usado como sinal de seleção, zero dado novo.
"""
import datetime

import pytest

import backtest
import cotahist
import db
import factor
import trials_gate
import universe


def _dates(n, start=(2016, 7, 1)):
    base = datetime.date(*start)
    return [(base + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]


def _synthetic_conn(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    tickers = [f"T{c}{c}{c}3" for c in "ABCDEFGHIJKL"]
    cotahist.load_prices(conn, cotahist.synthetic_cotahist(tickers, _dates(900), seed=11),
                         "COTAHIST_SYNTH.TXT")
    return conn


def test_run_h15_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}

    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)     # h1 + h2 no tmp
    v = backtest.run_h15(cfg, conn, trials_path=tp)
    conn.close()

    assert "H15:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3     # h1 + h2 + h15 neste registro tmp
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


def test_h15_frozen_config_hash_golden():
    """Mexeu num param [H15-FROZEN] -> quebra alto AQUI (pré-registro 2026-09-04)."""
    from config import h15_frozen_config_hash, load_config
    assert h15_frozen_config_hash(load_config()) == "a4d7e124231d6a5b"


def test_h15_frozen_hash_ignores_operational_params():
    from config import h15_frozen_config_hash, load_config
    cfg = load_config()
    base = h15_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h15_frozen_config_hash(cfg) == base
    cfg["h15_factor"]["short_lookback_days"] = 5      # tocar num FROZEN muda o lacre
    assert h15_frozen_config_hash(cfg) != base


def _insert_price(conn, ticker, date, volume):
    conn.execute(
        "INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,low,close,"
        "volume_fin,qty,quote_factor,source_file) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (date, ticker, "02", universe.SPOT_MARKET, 10.0, 10.0, 10.0, 10.0,
         volume, 100, 1, "TEST.TXT"))


def test_volume_surge_signals_known_value(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    # 253 pregões: 252 antes de asof (janela longa completa) + o próprio
    # asof (excluído, "date < asof"). Dos 252 elegíveis, os 21 mais
    # recentes (janela curta) têm volume 3000; os 231 restantes, 1000 —
    # surto concentrado bem no fim da janela longa.
    n_total = 253
    dates = [f"2020-{(1 + i // 28):02d}-{(1 + i % 28):02d}" for i in range(n_total)]
    long_lb, short_lb = 252, 21
    surge_vol, base_vol = 3000.0, 1000.0
    for i, d in enumerate(dates[:-1]):    # todos exceto o próprio asof
        vol = surge_vol if i >= (n_total - 1 - short_lb) else base_vol
        _insert_price(conn, "AAAA3", d, vol)
    _insert_price(conn, "AAAA3", dates[-1], 999_999.0)   # asof: não pode contar
    conn.commit()

    out = factor.volume_surge_signals(conn, ["AAAA3"], dates[-1],
                                      short_lookback=short_lb, long_lookback=long_lb)
    expected_long = (base_vol * (long_lb - short_lb) + surge_vol * short_lb) / long_lb
    expected_short = surge_vol
    assert out["AAAA3"] == pytest.approx(expected_short / expected_long - 1.0)


def test_volume_surge_signals_none_without_full_history(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    _insert_price(conn, "AAAA3", "2020-01-01", 1000.0)
    conn.commit()
    out = factor.volume_surge_signals(conn, ["AAAA3"], "2020-06-01",
                                      short_lookback=21, long_lookback=252)
    assert "AAAA3" not in out


def test_volume_surge_signals_point_in_time_excludes_asof_day(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    dates = [f"2020-{(1 + i // 28):02d}-{(1 + i % 28):02d}" for i in range(253)]
    for d in dates[:-1]:
        _insert_price(conn, "AAAA3", d, 1000.0)
    # volume do PRÓPRIO dia asof é absurdo (1_000_000) — não pode contaminar
    # a média, já que não é conhecido antes do fechamento desse dia.
    _insert_price(conn, "AAAA3", dates[-1], 1_000_000.0)
    conn.commit()
    out = factor.volume_surge_signals(conn, ["AAAA3"], dates[-1],
                                      short_lookback=21, long_lookback=252)
    assert out["AAAA3"] == 0.0    # média curta == média longa == 1000.0 (sem o dia de asof)
