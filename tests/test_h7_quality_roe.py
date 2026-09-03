"""H7 — fator de qualidade, ROE isolado (pré-registro 2026-09-03).

Mesma maquinaria da H1 (universo/custos/pareamento/pedágio); o sinal vem de
`fundamentals` (DFP da CVM) em vez de preço, com embargo de divulgação sobre
`ref_date` (`factor.roe_signals`). O smoke valida o encadeamento (dado
sintético inserido direto na tabela) e o DSR com a trial nova; o veredito real
exige `ingest_dfp_year` com anos reais contra o `stocks.db` real.
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
    # ROE sintético, um valor por ticker, ref_date bem antes da janela de teste
    # (2016-12-31) para que o embargo de 90 dias já tenha vencido em qualquer
    # rebalance de 2018+ usado pelo smoke.
    for i, t in enumerate(tickers):
        roe = 0.05 + 0.01 * i
        conn.execute(
            "INSERT INTO fundamentals(ticker, ref_date, ativo_total, passivo_total,"
            " patrimonio_liquido, lucro_liquido, roe, leverage, source)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (t, "2016-12-31", 1000.0, 400.0, 600.0, 600.0 * roe, roe, 0.4,
             "CVM DFP 2016 (sintético)"))
    conn.commit()
    return conn


def test_run_h7_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}

    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)     # h1 + h2 no tmp
    v = backtest.run_h7(cfg, conn, trials_path=tp)
    conn.close()

    assert "H7:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3     # h1 + h2 + h7 neste registro tmp
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


def test_h7_frozen_config_hash_golden():
    """Mexeu num param [H7-FROZEN] -> quebra alto AQUI (pré-registro 2026-09-03)."""
    from config import h7_frozen_config_hash, load_config
    assert h7_frozen_config_hash(load_config()) == "61fd7d1c73999c73"


def test_h7_frozen_hash_ignores_operational_params():
    from config import h7_frozen_config_hash, load_config
    cfg = load_config()
    base = h7_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h7_frozen_config_hash(cfg) == base
    cfg["h7_factor"]["disclosure_embargo_days"] = 5    # tocar num FROZEN muda o lacre
    assert h7_frozen_config_hash(cfg) != base


def test_roe_signals_embargo_blocks_early_asof(tmp_path):
    """Ponto central da H7: sem o embargo, `ref_date` sozinho vazaria dado
    contábil antes da publicação real (lookahead). Com embargo de 90 dias,
    um `asof` a 60 dias de `ref_date` não pode ver o ROE ainda."""
    conn = db.get_connection(tmp_path / "s.db")
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, ativo_total, passivo_total,"
        " patrimonio_liquido, lucro_liquido, roe, leverage, source)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        ("AAAA3", "2020-12-31", 1000.0, 400.0, 600.0, 60.0, 0.1, 0.4, "CVM DFP 2020"))
    conn.commit()

    too_early = factor.roe_signals(conn, ["AAAA3"], "2021-03-01", disclosure_embargo_days=90)
    assert "AAAA3" not in too_early    # 60 dias após ref_date, embargo de 90 ainda não venceu

    after_embargo = factor.roe_signals(conn, ["AAAA3"], "2021-04-01", disclosure_embargo_days=90)
    assert after_embargo["AAAA3"] == 0.1    # 91 dias após ref_date, embargo já venceu


def test_roe_signals_picks_most_recent_eligible_ref_date(tmp_path):
    """Duas rodadas de DFP para o mesmo ticker: em `asof`, o sinal deve usar a
    mais RECENTE cujo embargo já venceu — não a mais antiga, nem uma futura."""
    conn = db.get_connection(tmp_path / "s.db")
    rows = [
        ("AAAA3", "2019-12-31", 0.05),
        ("AAAA3", "2020-12-31", 0.08),
    ]
    for t, ref, roe in rows:
        conn.execute(
            "INSERT INTO fundamentals(ticker, ref_date, ativo_total, passivo_total,"
            " patrimonio_liquido, lucro_liquido, roe, leverage, source)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (t, ref, 1000.0, 400.0, 600.0, 600.0 * roe, roe, 0.4, "CVM DFP (sintético)"))
    conn.commit()

    # asof entre os dois embargos: só a rodada de 2019 já venceu.
    mid = factor.roe_signals(conn, ["AAAA3"], "2020-06-01", disclosure_embargo_days=90)
    assert mid["AAAA3"] == 0.05

    # asof após os dois embargos: usa a mais recente (2020).
    late = factor.roe_signals(conn, ["AAAA3"], "2021-06-01", disclosure_embargo_days=90)
    assert late["AAAA3"] == 0.08
