"""H18 (E/P) e H19 (B/M) — os primeiros fatores de VALOR do domínio
(pré-registro 2026-09-04).

Dezesseis hipóteses julgadas e nenhuma tinha medido o PREÇO PAGO pelo
fundamento. Habilitados por `fundamentals.shares_outstanding` (migração
0011): sem contagem de ações não há capitalização de mercado, logo não há
múltiplo. H18 e H19 são SEPARADAS de propósito (fluxo vs. estoque) — cada
uma julgada uma vez, com seu próprio N no DSR.
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
    for i, t in enumerate(tickers):
        # lucro e PL variando por ticker -> E/P e B/M variam no ranking
        conn.execute(
            "INSERT INTO fundamentals(ticker, ref_date, lucro_liquido,"
            " patrimonio_liquido, source) VALUES (?,?,?,?,?)",
            (t, "2016-12-31", 50.0 + 10.0 * i, 500.0 + 100.0 * i,
             "CVM DFP 2016 (sintético)"))
        # ações vêm de linha SEPARADA, source do FRE — como na ingestão real
        conn.execute(
            "INSERT INTO fundamentals(ticker, ref_date, shares_outstanding, source)"
            " VALUES (?,?,?,?)",
            (t, "2016-12-31", 1_000.0, "CVM FRE 2016 (sintético)"))
    conn.commit()
    return conn


def test_run_h18_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}
    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)
    v = backtest.run_h18(cfg, conn, trials_path=tp)
    conn.close()
    assert "H18:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


def test_run_h19_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}
    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)
    v = backtest.run_h19(cfg, conn, trials_path=tp)
    conn.close()
    assert "H19:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


def test_h18_h19_frozen_config_hash_golden():
    """Mexeu num param [H18/H19-FROZEN] -> quebra alto AQUI."""
    from config import h18_frozen_config_hash, h19_frozen_config_hash, load_config
    cfg = load_config()
    assert h18_frozen_config_hash(cfg) == "dded266f1bb712f1"
    assert h19_frozen_config_hash(cfg) == "dabaa53adc9b9349"


def test_h18_h19_are_distinct_seals():
    """As duas hipóteses não podem compartilhar lacre — são trials separadas."""
    from config import h18_frozen_config_hash, h19_frozen_config_hash, load_config
    cfg = load_config()
    assert h18_frozen_config_hash(cfg) != h19_frozen_config_hash(cfg)


def test_h18_frozen_hash_ignores_operational_params():
    from config import h18_frozen_config_hash, load_config
    cfg = load_config()
    base = h18_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h18_frozen_config_hash(cfg) == base
    cfg["h18_factor"]["disclosure_embargo_days"] = 5
    assert h18_frozen_config_hash(cfg) != base


def _one_ticker_conn(tmp_path, price, shares, lucro, pl,
                     fund_ref="2020-12-31", shares_ref="2020-12-31"):
    conn = db.get_connection(tmp_path / "s.db")
    cotahist.load_prices(
        conn, cotahist.synthetic_cotahist(["AAAA3"], _dates(30, (2021, 6, 1)), seed=3),
        "COTAHIST_SYNTH.TXT")
    # sobrescreve o fechamento do dia alvo com um preço conhecido
    conn.execute("UPDATE prices_raw SET close=?, quote_factor=1 WHERE ticker='AAAA3'",
                 (price,))
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, lucro_liquido, patrimonio_liquido,"
        " source) VALUES (?,?,?,?,?)", ("AAAA3", fund_ref, lucro, pl, "CVM DFP"))
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, shares_outstanding, source)"
        " VALUES (?,?,?,?)", ("AAAA3", shares_ref, shares, "CVM FRE"))
    conn.commit()
    return conn


def test_earnings_yield_is_fundamental_over_market_cap(tmp_path):
    """E/P = lucro / (preço × ações), com as ações vindo de linha FRE separada."""
    conn = _one_ticker_conn(tmp_path, price=10.0, shares=1000.0, lucro=500.0, pl=2000.0)
    v = factor.earnings_yield_signals(conn, ["AAAA3"], "2021-06-20")
    assert abs(v["AAAA3"] - 500.0 / (10.0 * 1000.0)) < 1e-12    # 0.05


def test_book_to_market_uses_equity_not_earnings(tmp_path):
    """H19 é fator DISTINTO de H18 — mesmo preço/ações, numerador diferente."""
    conn = _one_ticker_conn(tmp_path, price=10.0, shares=1000.0, lucro=500.0, pl=2000.0)
    ep = factor.earnings_yield_signals(conn, ["AAAA3"], "2021-06-20")["AAAA3"]
    bm = factor.book_to_market_signals(conn, ["AAAA3"], "2021-06-20")["AAAA3"]
    assert abs(bm - 2000.0 / (10.0 * 1000.0)) < 1e-12           # 0.20
    assert bm != ep


def test_value_signals_embargo_blocks_early_asof(tmp_path):
    """Anti-lookahead: antes do embargo vencer, o papel não tem sinal —
    nem por E/P nem por B/M."""
    conn = _one_ticker_conn(tmp_path, price=10.0, shares=1000.0, lucro=500.0, pl=2000.0)
    # 2021-03-01 é 60 dias após ref_date 2020-12-31; embargo de 90 não venceu
    assert factor.earnings_yield_signals(conn, ["AAAA3"], "2021-03-01") == {}
    assert factor.book_to_market_signals(conn, ["AAAA3"], "2021-03-01") == {}


def test_value_signals_excluded_when_shares_missing(tmp_path):
    """Sem contagem de ações não há capitalização de mercado -> fora do sinal
    (dado indisponível > múltiplo fabricado)."""
    conn = db.get_connection(tmp_path / "s.db")
    cotahist.load_prices(
        conn, cotahist.synthetic_cotahist(["AAAA3"], _dates(30, (2021, 6, 1)), seed=3),
        "COTAHIST_SYNTH.TXT")
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, lucro_liquido, patrimonio_liquido,"
        " source) VALUES (?,?,?,?,?)", ("AAAA3", "2020-12-31", 500.0, 2000.0, "CVM DFP"))
    conn.commit()
    assert factor.earnings_yield_signals(conn, ["AAAA3"], "2021-06-20") == {}
    assert factor.book_to_market_signals(conn, ["AAAA3"], "2021-06-20") == {}


def test_value_signals_exclude_non_positive_fundamental(tmp_path):
    """Prejuízo / PL negativo invertem o múltiplo e fariam a empresa parecer
    "baratíssima" no ranking — ficam FORA, como o ROE sobre PL negativo."""
    conn = _one_ticker_conn(tmp_path, price=10.0, shares=1000.0, lucro=-500.0, pl=-200.0)
    assert factor.earnings_yield_signals(conn, ["AAAA3"], "2021-06-20") == {}
    assert factor.book_to_market_signals(conn, ["AAAA3"], "2021-06-20") == {}


def test_price_at_applies_quote_factor(tmp_path):
    """O preço do múltiplo é POR AÇÃO: cotação em lote (FATCOT) tem que ser
    dividida, senão a capitalização sai inflada pelo tamanho do lote."""
    conn = db.get_connection(tmp_path / "s.db")
    cotahist.load_prices(
        conn, cotahist.synthetic_cotahist(["AAAA3"], _dates(30, (2021, 6, 1)), seed=3),
        "COTAHIST_SYNTH.TXT")
    conn.execute("UPDATE prices_raw SET close=1000.0, quote_factor=100 WHERE ticker='AAAA3'")
    conn.commit()
    assert factor._price_at(conn, "AAAA3", "2021-06-20") == 10.0


def test_price_at_is_point_in_time(tmp_path):
    """Nada depois de `asof` entra: preço futuro alto não pode vazar para o
    múltiplo de uma data anterior."""
    conn = db.get_connection(tmp_path / "s.db")
    cotahist.load_prices(
        conn, cotahist.synthetic_cotahist(["AAAA3"], _dates(30, (2021, 6, 1)), seed=3),
        "COTAHIST_SYNTH.TXT")
    conn.execute("UPDATE prices_raw SET close=10.0, quote_factor=1 WHERE ticker='AAAA3'")
    conn.execute("UPDATE prices_raw SET close=999.0 WHERE ticker='AAAA3' AND date>'2021-06-20'")
    conn.commit()
    assert factor._price_at(conn, "AAAA3", "2021-06-20") == 10.0


def test_value_signals_do_not_force_align_dfp_and_fre_dates(tmp_path):
    """DFP e FRE têm datas de referência próprias. Cada perna é resolvida pelo
    seu próprio caminho point-in-time; datas diferentes não invalidam o sinal
    (nem são casadas à força na ingestão)."""
    conn = _one_ticker_conn(tmp_path, price=10.0, shares=1000.0, lucro=500.0, pl=2000.0,
                            fund_ref="2020-12-31", shares_ref="2021-01-31")
    v = factor.earnings_yield_signals(conn, ["AAAA3"], "2021-06-20")
    assert abs(v["AAAA3"] - 0.05) < 1e-12


def _fre_zip_bytes(rows):
    """Zip FRE mínimo com o CSV `distribuicao_capital` principal."""
    import io as _io
    import zipfile as _zip
    header = ("Nome_Companhia;Data_Referencia;Quantidade_Total_Acoes;"
              "Quantidade_Acoes_Circulacao")
    lines = [header] + [";".join(r) for r in rows]
    buf = _io.BytesIO()
    with _zip.ZipFile(buf, "w") as zf:
        zf.writestr("fre_cia_aberta_distribuicao_capital_2020.csv",
                    "\n".join(lines).encode("latin-1"))
    return buf.getvalue()


def test_ingest_fre_shares_persists_and_is_idempotent(tmp_path):
    """O parser do FRE já lia `shares_outstanding` desde a família liquidity,
    mas jogava fora. Aqui ele PERSISTE — e re-executar o mesmo ano não
    duplica nem recontabiliza (mesma disciplina de `ingest_dfp_year`)."""
    import ingest_cvm
    conn = db.get_connection(tmp_path / "s.db")
    zb = _fre_zip_bytes([["CIA X", "2020-12-31", "1.000.000", "400.000"]])
    ticker_of = {ingest_cvm._norm("CIA X"): "AAAA3"}

    n1 = ingest_cvm.ingest_fre_shares_year(conn, 2020, ticker_of, zbytes=zb)
    assert n1 == 1
    row = conn.execute(
        "SELECT ref_date, shares_outstanding, source FROM fundamentals"
        " WHERE ticker='AAAA3'").fetchone()
    assert tuple(row) == ("2020-12-31", 1_000_000.0, "CVM FRE 2020")

    n2 = ingest_cvm.ingest_fre_shares_year(conn, 2020, ticker_of, zbytes=zb)
    assert n2 == 0                                     # nada mudou no re-run
    assert conn.execute("SELECT COUNT(*) FROM fundamentals").fetchone()[0] == 1


def test_ingest_fre_shares_skips_unmapped_company(tmp_path):
    """Companhia sem ticker mapeado exige revisão humana — nunca entra com
    ticker adivinhado."""
    import ingest_cvm
    conn = db.get_connection(tmp_path / "s.db")
    zb = _fre_zip_bytes([["CIA DESCONHECIDA", "2020-12-31", "1.000.000", "400.000"]])
    assert ingest_cvm.ingest_fre_shares_year(conn, 2020, {}, zbytes=zb) == 0
    assert conn.execute("SELECT COUNT(*) FROM fundamentals").fetchone()[0] == 0
