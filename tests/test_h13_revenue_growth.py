"""H13 — crescimento de receita YoY (pré-registro 2026-09-04).

Primeira hipótese de CRESCIMENTO testada neste domínio — H1-H12 são todas
nível/valor. Mesma maquinaria de universo/custos/pareamento/pedágio/embargo
das anteriores contábeis; o sinal (`factor.revenue_growth_signals`) precisa
de DUAS linhas elegíveis de `receita_liquida` por ticker (a mais recente
sobre a anterior), não uma leitura só.
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
    # duas linhas por ticker (2015 e 2016), crescimento variando por ticker,
    # ambas bem antes da janela de teste (2018+) pro embargo já ter vencido.
    for i, t in enumerate(tickers):
        growth = 0.05 + 0.02 * i
        receita_2015 = 1000.0
        receita_2016 = receita_2015 * (1 + growth)
        conn.execute(
            "INSERT INTO fundamentals(ticker, ref_date, receita_liquida,"
            " lucro_liquido, source) VALUES (?,?,?,?,?)",
            (t, "2015-12-31", receita_2015, 50.0, "CVM DFP 2015 (sintético)"))
        conn.execute(
            "INSERT INTO fundamentals(ticker, ref_date, receita_liquida,"
            " lucro_liquido, source) VALUES (?,?,?,?,?)",
            (t, "2016-12-31", receita_2016, 55.0, "CVM DFP 2016 (sintético)"))
    conn.commit()
    return conn


def test_run_h13_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}

    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)     # h1 + h2 no tmp
    v = backtest.run_h13(cfg, conn, trials_path=tp)
    conn.close()

    assert "H13:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3     # h1 + h2 + h13 neste registro tmp
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


def test_h13_frozen_config_hash_golden():
    """Mexeu num param [H13-FROZEN] -> quebra alto AQUI (pré-registro 2026-09-04)."""
    from config import h13_frozen_config_hash, load_config
    assert h13_frozen_config_hash(load_config()) == "473ca87ab5b1f8a0"


def test_h13_frozen_hash_ignores_operational_params():
    from config import h13_frozen_config_hash, load_config
    cfg = load_config()
    base = h13_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h13_frozen_config_hash(cfg) == base
    cfg["h13_factor"]["disclosure_embargo_days"] = 5   # tocar num FROZEN muda o lacre
    assert h13_frozen_config_hash(cfg) != base


def test_revenue_growth_signals_needs_two_eligible_rows(tmp_path):
    """Uma linha só não basta — sem denominador anterior, sem crescimento
    fabricado."""
    conn = db.get_connection(tmp_path / "s.db")
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, receita_liquida,"
        " lucro_liquido, source) VALUES (?,?,?,?,?)",
        ("AAAA3", "2020-12-31", 1000.0, 100.0, "CVM DFP 2020"))
    conn.commit()
    v = factor.revenue_growth_signals(conn, ["AAAA3"], "2021-06-01", disclosure_embargo_days=90)
    assert "AAAA3" not in v


def test_revenue_growth_signals_known_value_and_embargo(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, receita_liquida,"
        " lucro_liquido, source) VALUES (?,?,?,?,?)",
        ("AAAA3", "2019-12-31", 1000.0, 90.0, "CVM DFP 2019"))
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, receita_liquida,"
        " lucro_liquido, source) VALUES (?,?,?,?,?)",
        ("AAAA3", "2020-12-31", 1200.0, 100.0, "CVM DFP 2020"))
    conn.commit()

    # 2021-06-01: 2020 elegível (embargo 90d vencido), 2019 também -> as DUAS
    # mais recentes elegíveis são exatamente essas -> growth = (1200-1000)/1000
    v = factor.revenue_growth_signals(conn, ["AAAA3"], "2021-06-01", disclosure_embargo_days=90)
    assert v["AAAA3"] == 0.2

    # 2021-03-01: 2020 ainda NÃO elegível (60d < embargo 90d) -> só 2019
    # elegível -> menos de 2 linhas -> fora
    too_early = factor.revenue_growth_signals(conn, ["AAAA3"], "2021-03-01",
                                              disclosure_embargo_days=90)
    assert "AAAA3" not in too_early


def test_revenue_growth_signals_nonpositive_previous_is_unavailable(tmp_path):
    """Receita anterior <=0 não pode virar denominador — sem crescimento
    fabricado sobre base inválida."""
    conn = db.get_connection(tmp_path / "s.db")
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, receita_liquida,"
        " lucro_liquido, source) VALUES (?,?,?,?,?)",
        ("AAAA3", "2019-12-31", 0.0, 10.0, "CVM DFP 2019"))
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, receita_liquida,"
        " lucro_liquido, source) VALUES (?,?,?,?,?)",
        ("AAAA3", "2020-12-31", 1200.0, 100.0, "CVM DFP 2020"))
    conn.commit()
    v = factor.revenue_growth_signals(conn, ["AAAA3"], "2021-06-01", disclosure_embargo_days=90)
    assert "AAAA3" not in v
