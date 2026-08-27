"""H8 — filtro duplo momentum ∩ baixa vol (pré-registro 2026-08-27).

Top `h8_portfolio.momentum_quantile` do universo por momentum, depois a
fração `h8_portfolio.vol_quantile` de menor vol realizada DENTRO desse
subconjunto. H1 (momentum isolado) e H2 (baixa vol isolada) fracassaram —
esta é a interseção das duas, não repescagem de nenhuma isolada.
"""
import datetime

import pytest

import backtest
import cotahist
import db
import portfolio
import trials_gate


# ---------- construção da carteira de filtro duplo ----------

def test_double_filter_known_values():
    mom = {"A": 0.30, "B": 0.25, "C": 0.20, "D": 0.15, "E": 0.10,
           "F": 0.05, "G": 0.0, "H": -0.05, "I": -0.10, "J": -0.20}
    vol = {"A": 0.5, "B": 0.1, "C": 0.4, "D": 0.2, "E": 0.3,
           "F": 0.15, "G": 0.6, "H": 0.05, "I": 0.25, "J": 0.35}
    w = portfolio.momentum_lowvol_double_filter(mom, vol, momentum_quantile=0.4,
                                                vol_quantile=0.5)
    # top 40% de 10 por momentum -> {A,B,C,D}; metade de menor vol dentro
    # desse subconjunto (B=0.1, D=0.2, C=0.4, A=0.5) -> {B, D}
    assert set(w) == {"B", "D"}
    assert w["B"] == pytest.approx(0.5) and w["D"] == pytest.approx(0.5)


def test_double_filter_requires_both_signals():
    mom = {"A": 0.1, "B": 0.2}
    vol = {"A": 0.1}                                   # B sem vol -> fora
    w = portfolio.momentum_lowvol_double_filter(mom, vol)
    assert set(w) <= {"A"}


def test_double_filter_empty_when_no_overlap():
    assert portfolio.momentum_lowvol_double_filter({"A": 0.1}, {"B": 0.1}) == {}
    assert portfolio.momentum_lowvol_double_filter({}, {}) == {}


# ---------- run_h8 end-to-end em sintético ----------

def _dates(n, start=(2016, 7, 1)):
    base = datetime.date(*start)
    return [(base + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]


def _synthetic_conn(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    tickers = [f"T{c}{c}{c}3" for c in "ABCDEFGHIJKL"]
    cotahist.load_prices(conn, cotahist.synthetic_cotahist(tickers, _dates(900), seed=11),
                         "COTAHIST_SYNTH.TXT")
    return conn


def test_run_h8_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}

    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)     # h1 + h2 no tmp
    v = backtest.run_h8(cfg, conn, trials_path=tp)
    conn.close()

    assert "H8:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3     # h1 + h2 + h8 neste registro tmp
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


# ---------- lacre por máquina da H8 ----------

def test_h8_frozen_config_hash_golden():
    """Mexeu num param [H8-FROZEN] -> quebra alto AQUI (pré-registro 2026-08-27)."""
    from config import h8_frozen_config_hash, load_config
    assert h8_frozen_config_hash(load_config()) == "8bad7034233189c0"


def test_h8_frozen_hash_ignores_operational_params():
    from config import h8_frozen_config_hash, load_config
    cfg = load_config()
    base = h8_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h8_frozen_config_hash(cfg) == base
    cfg["h8_portfolio"]["momentum_quantile"] = 0.9    # tocar num FROZEN muda o lacre
    assert h8_frozen_config_hash(cfg) != base
