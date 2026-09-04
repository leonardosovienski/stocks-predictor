"""H9 — fator de qualidade, alavancagem isolada (pré-registro 2026-09-04).

Mesma maquinaria da H7 (universo/custos/pareamento/pedágio/embargo de
divulgação); o sinal é alavancagem (quintil INFERIOR, empresas menos
endividadas) em vez de ROE. O smoke valida o encadeamento e o DSR com a
trial nova; o veredito real é da rodada única em dado real (mesma
`fundamentals` já ingerida pela H7 — `leverage` vem da mesma linha do ROE,
sem ingestão nova).
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
    # leverage sintética, um valor por ticker, ref_date bem antes da janela de
    # teste (2016-12-31) para que o embargo de 90 dias já tenha vencido em
    # qualquer rebalance de 2018+ usado pelo smoke.
    for i, t in enumerate(tickers):
        lev = 0.20 + 0.02 * i
        conn.execute(
            "INSERT INTO fundamentals(ticker, ref_date, ativo_total, passivo_total,"
            " patrimonio_liquido, lucro_liquido, roe, leverage, source)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (t, "2016-12-31", 1000.0, 400.0 + 1000.0 * lev, 600.0 - 1000.0 * lev,
             60.0, 0.1, lev, "CVM DFP 2016 (sintético)"))
    conn.commit()
    return conn


def test_run_h9_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}

    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)     # h1 + h2 no tmp
    v = backtest.run_h9(cfg, conn, trials_path=tp)
    conn.close()

    assert "H9:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3     # h1 + h2 + h9 neste registro tmp
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


def test_h9_frozen_config_hash_golden():
    """Mexeu num param [H9-FROZEN] -> quebra alto AQUI (pré-registro 2026-09-04)."""
    from config import h9_frozen_config_hash, load_config
    assert h9_frozen_config_hash(load_config()) == "af797c56c2ab36b7"


def test_h9_frozen_hash_ignores_operational_params():
    from config import h9_frozen_config_hash, load_config
    cfg = load_config()
    base = h9_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h9_frozen_config_hash(cfg) == base
    cfg["h9_factor"]["disclosure_embargo_days"] = 5    # tocar num FROZEN muda o lacre
    assert h9_frozen_config_hash(cfg) != base


def test_leverage_signals_embargo_blocks_early_asof(tmp_path):
    """Mesmo ponto central da H7, agora para alavancagem: sem o embargo,
    `ref_date` sozinho vazaria dado contábil antes da publicação real."""
    conn = db.get_connection(tmp_path / "s.db")
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, ativo_total, passivo_total,"
        " patrimonio_liquido, lucro_liquido, roe, leverage, source)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        ("AAAA3", "2020-12-31", 1000.0, 600.0, 400.0, 60.0, 0.15, 0.2, "CVM DFP 2020"))
    conn.commit()

    too_early = factor.leverage_signals(conn, ["AAAA3"], "2021-03-01", disclosure_embargo_days=90)
    assert "AAAA3" not in too_early    # 60 dias após ref_date, embargo de 90 ainda não venceu

    after_embargo = factor.leverage_signals(conn, ["AAAA3"], "2021-04-01", disclosure_embargo_days=90)
    assert after_embargo["AAAA3"] == 0.2    # 91 dias após ref_date, embargo já venceu
