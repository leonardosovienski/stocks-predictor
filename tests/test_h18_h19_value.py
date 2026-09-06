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
    """Mexeu num param [H18/H19-FROZEN] -> quebra alto AQUI.

    Lacres RE-EMITIDOS em 2026-09-06 (re-pré-registro, HANDOFF): entraram
    `known_at_policy` e `split_base`. Legítimo porque H18/H19 NUNCA rodaram
    — nenhum resultado foi observado, então isto é revisão de pré-registro,
    não mover a trave depois do chute."""
    from config import h18_frozen_config_hash, h19_frozen_config_hash, load_config
    cfg = load_config()
    assert h18_frozen_config_hash(cfg) == "cbea4d3c98ac3422"
    assert h19_frozen_config_hash(cfg) == "d96753f2af7b39a6"


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


# --- Regressão da auditoria 2026-09-04: colisão de coluna no FRE -------------
# Os testes acima usam um cabeçalho SINTÉTICO com duas colunas separadas
# (`Quantidade_Total_Acoes` + `Quantidade_Acoes_Circulacao`) que a CVM não
# publica. Os testes abaixo usam o cabeçalho REAL registrado pelo operador no
# HANDOFF.md:58-61 ("fonte confirmada", `tools/explore_dividend_sources.py`),
# onde a única coluna de quantidade é `Quantidade_Total_Acoes_Circulacao`.

# Cabeçalho GOLDEN: as 15 colunas do `fre_cia_aberta_distribuicao_capital_2023.csv`
# real, obtidas do arquivo baixado do Portal de Dados Abertos da CVM pelo
# operador em 2026-09-05. Não é sintético e não é de memória.
_FRE_HEADER_REAL = (
    "CNPJ_Companhia;Data_Referencia;Versao;ID_Documento;Nome_Companhia;"
    "Quantidade_Acionistas_PF;Quantidade_Acionistas_PJ;"
    "Quantidade_Acionistas_Investidores_Institucionais;"
    "Quantidade_Acoes_Ordinarias_Circulacao;Percentual_Acoes_Ordinarias_Circulacao;"
    "Quantidade_Acoes_Preferenciais_Circulacao;Percentual_Acoes_Preferenciais_Circulacao;"
    "Quantidade_Total_Acoes_Circulacao;Percentual_Total_Acoes_Circulacao;"
    "Data_Ultima_Assembleia")

# Linhas GOLDEN: as três primeiras companhias do arquivo real de 2023, verbatim.
_FRE_ROWS_REAL = [
    ["00.000.000/0001-91", "2023-12-31", "19", "137597", "BCO BRASIL S.A.",
     "1143917", "14856", "1266", "2842247534", "49.596000", "0", "0.000000",
     "2842247534", "49.596000", "2024-04-15"],
    ["00.000.208/0001-00", "2023-12-31", "13", "135745", "BRB BANCO DE BRASILIA S.A.",
     "2843", "33", "0", "39346566", "14.045000", "2608000", "3.146000",
     "41954566", "11.556000", "2023-04-28"],
    ["00.001.180/0001-26", "2023-12-31", "23", "136627", "AXIA ENERGIA S.A.",
     "144406", "10701", "677", "1977170723", "97.541000", "268875696", "95.997000",
     "2246046419", "97.354000", "2024-04-26"],
]


def _fre_zip_with_header(header, rows):
    import io as _io
    import zipfile as _zip
    lines = [header] + [";".join(r) for r in rows]
    buf = _io.BytesIO()
    with _zip.ZipFile(buf, "w") as zf:
        zf.writestr("fre_cia_aberta_distribuicao_capital_2020.csv",
                    "\n".join(lines).encode("latin-1"))
    return buf.getvalue()


def test_real_fre_header_derives_total_shares_and_total_float():
    """GOLDEN contra o arquivo real da CVM (2023).

    Dois bugs que este teste tranca:

    1. `free_float` casava `Quantidade_Acoes_Ordinarias_Circulacao` — o float
       só das ORDINÁRIAS — porque o keyword genérico "circulacao" pegava a
       primeira coluna com essa palavra. Agora casa a coluna TOTAL.
    2. `shares_outstanding` recebia a quantidade EM CIRCULAÇÃO como se fosse
       o capital total. O arquivo não publica ações totais; elas são
       DERIVADAS de quantidade ÷ percentual.

    BCO BRASIL: 2.842.247.534 / 0,49596 = 5.730.799.931 ações — a contagem
    real da companhia, e o dobro do que a implementação anterior usaria."""
    import ingest_cvm
    zb = _fre_zip_with_header(_FRE_HEADER_REAL, _FRE_ROWS_REAL)
    rows = ingest_cvm.parse_fre_float_rows(
        ingest_cvm._open_fre_distribuicao_capital_main(zb))
    by = {r["company"]: r for r in rows}

    bb = by["BCO BRASIL S.A."]
    assert bb["free_float"] == 2_842_247_534.0             # coluna TOTAL, não ON
    assert abs(bb["shares_outstanding"] - 5_730_799_931) < 1.0
    # o erro que este teste existe para impedir: float tratado como total
    assert bb["shares_outstanding"] != bb["free_float"]

    axia = by["AXIA ENERGIA S.A."]
    assert axia["free_float"] == 2_246_046_419.0
    assert abs(axia["shares_outstanding"] - 2_307_092_075) < 1.0


def test_derived_total_is_consistent_with_on_plus_pn_legs():
    """Checagem cruzada interna do arquivo real: o total derivado da linha
    TOTAL bate com a soma dos totais derivados das pernas ON e PN. Se a
    derivação estivesse errada, as duas rotas divergiriam."""
    import ingest_cvm
    for row in _FRE_ROWS_REAL:
        on = ingest_cvm._derive_total_shares(float(row[8]), float(row[9]))
        pn = ingest_cvm._derive_total_shares(float(row[10]), float(row[11]))
        total = ingest_cvm._derive_total_shares(float(row[12]), float(row[13]))
        soma = (on or 0.0) + (pn or 0.0)
        assert abs(soma - total) / total < 1e-4, row[4]


def test_derive_total_shares_refuses_impossible_inputs():
    """Sem número fabricado: percentual ausente, zero, negativo ou >100 ->
    None. Nunca um total menor que o próprio free float."""
    import ingest_cvm
    d = ingest_cvm._derive_total_shares
    assert d(1000.0, None) is None
    assert d(None, 50.0) is None
    assert d(1000.0, 0.0) is None
    assert d(1000.0, -5.0) is None
    assert d(1000.0, 100.5) is None
    assert d(1000.0, 100.0) == 1000.0        # 100% em circulação é válido


def test_percentual_is_parsed_as_en_not_br():
    """`49.596000` é 49,596% (formato EN). Parseado com a convenção BR
    (remover o ponto) viraria 49596000 e o total derivado ficaria ~10^6x
    menor — corrupção silenciosa, o modo de falha que `_to_float` documenta."""
    import ingest_cvm
    zb = _fre_zip_with_header(_FRE_HEADER_REAL, _FRE_ROWS_REAL[:1])
    rows = ingest_cvm.parse_fre_float_rows(
        ingest_cvm._open_fre_distribuicao_capital_main(zb))
    assert rows[0]["shares_outstanding"] > rows[0]["free_float"]
    assert rows[0]["shares_outstanding"] < rows[0]["free_float"] * 10


def test_ingest_fre_shares_fails_loud_when_total_shares_underivable(tmp_path):
    """Sem a coluna de PERCENTUAL não há como derivar as ações totais, e sem
    ações totais não há capitalização de mercado — logo não há múltiplo.
    Fail-loud: exceção, nunca `0` em silêncio nem o free float no lugar."""
    import pytest
    import ingest_cvm
    conn = db.get_connection(tmp_path / "s.db")
    # mesmo arquivo real, mas SEM a coluna de percentual: derivação impossível
    zb = _fre_zip_with_header(
        "CNPJ_Companhia;Data_Referencia;Nome_Companhia;Quantidade_Total_Acoes_Circulacao",
        [["00.000.000/0001-91", "2023-12-31", "CIA X", "2842247534"]])
    with pytest.raises(ValueError, match="quantidade TOTAL de ações"):
        ingest_cvm.ingest_fre_shares_year(
            conn, 2023, {ingest_cvm._norm("CIA X"): "AAAA3"}, zbytes=zb)
    assert conn.execute("SELECT COUNT(*) FROM fundamentals").fetchone()[0] == 0


def test_ingest_fre_shares_persists_derived_total_from_real_header(tmp_path):
    """Ponta a ponta contra o cabeçalho real: o que chega em `fundamentals`
    é o capital TOTAL derivado, não a quantidade em circulação."""
    import ingest_cvm
    conn = db.get_connection(tmp_path / "s.db")
    zb = _fre_zip_with_header(_FRE_HEADER_REAL, _FRE_ROWS_REAL)
    n = ingest_cvm.ingest_fre_shares_year(
        conn, 2023, {ingest_cvm._norm("BCO BRASIL S.A."): "BBAS3"}, zbytes=zb)
    assert n == 1
    ref, shares = conn.execute(
        "SELECT ref_date, shares_outstanding FROM fundamentals"
        " WHERE ticker='BBAS3'").fetchone()
    assert ref == "2023-12-31"
    assert abs(shares - 5_730_799_931) < 1.0
    assert shares != 2_842_247_534.0          # nunca o free float


def test_distinct_total_and_float_columns_still_resolve_separately():
    """A defesa é contra COLISÃO, não contra o caso legítimo: um cabeçalho
    que de fato traga as duas quantidades em colunas distintas continua
    resolvendo as duas."""
    import ingest_cvm
    zb = _fre_zip_with_header(
        "Nome_Companhia;Data_Referencia;Quantidade_Total_Acoes;Quantidade_Acoes_Circulacao",
        [["CIA X", "2020-12-31", "1.000.000", "400.000"]])
    rows = ingest_cvm.parse_fre_float_rows(
        ingest_cvm._open_fre_distribuicao_capital_main(zb))
    assert rows[0]["shares_outstanding"] == 1_000_000.0
    assert rows[0]["free_float"] == 400_000.0


def test_collision_with_pct_is_info_not_warning(caplog):
    """Higiene de sinal (achado de operação 2026-09-05): o cabeçalho real da
    CVM cai SEMPRE na colisão, e antes isso emitia WARNING dizendo
    `shares_outstanding=None` — sem contar que o total é derivado logo em
    seguida. Aviso que assusta sem informar treina o operador a ignorar
    avisos. Com percentual disponível nada se perde: é INFO."""
    import logging
    import ingest_cvm
    zb = _fre_zip_with_header(_FRE_HEADER_REAL, _FRE_ROWS_REAL[:1])
    with caplog.at_level(logging.INFO):
        rows = ingest_cvm.parse_fre_float_rows(
            ingest_cvm._open_fre_distribuicao_capital_main(zb))
    assert rows[0]["shares_outstanding"] is not None      # derivou
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert [r for r in caplog.records if r.levelno == logging.INFO]


def test_collision_without_pct_still_warns(caplog):
    """Sem a coluna de percentual a derivação é impossível e o dado SE PERDE
    — aí o WARNING é devido."""
    import logging
    import ingest_cvm
    zb = _fre_zip_with_header(
        "CNPJ_Companhia;Data_Referencia;Nome_Companhia;Quantidade_Total_Acoes_Circulacao",
        [["00.000.000/0001-91", "2023-12-31", "CIA X", "2842247534"]])
    with caplog.at_level(logging.INFO):
        rows = ingest_cvm.parse_fre_float_rows(
            ingest_cvm._open_fre_distribuicao_capital_main(zb))
    assert rows[0]["shares_outstanding"] is None
    assert [r for r in caplog.records if r.levelno >= logging.WARNING]


# --- known_at observado + base de desdobramento (re-pré-registro 2026-09-06) ---

def test_known_at_observado_manda_sobre_o_embargo(tmp_path):
    """A linha com `known_at` gravado usa a data OBSERVADA, e o embargo é
    ignorado para ela. Aqui o embargo diria 2021-03-31 (ref + 90d) mas o
    documento só ficou público em 2021-05-30: entre 01/04 e 29/05 o sinal
    NÃO pode ver o dado."""
    conn = db.get_connection(tmp_path / "s.db")
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, lucro_liquido, known_at, source)"
        " VALUES (?,?,?,?,?)", ("AAAA3", "2020-12-31", 100.0, "2021-05-30", "CVM FRE"))
    conn.commit()
    f = factor._fundamental_signals
    assert f(conn, ["AAAA3"], "2021-04-15", 90, "lucro_liquido") == {}   # embargo diria SIM
    assert f(conn, ["AAAA3"], "2021-05-29", 90, "lucro_liquido") == {}
    assert f(conn, ["AAAA3"], "2021-05-30", 90, "lucro_liquido") == {"AAAA3": 100.0}


def test_known_at_nulo_cai_no_embargo_sem_mudar_comportamento(tmp_path):
    """Linha SEM `known_at` (todas as da DFP hoje) mantém o embargo byte a
    byte — é o que preserva H7/H9/H12/H13/H17."""
    conn = db.get_connection(tmp_path / "s.db")
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, lucro_liquido, source)"
        " VALUES (?,?,?,?)", ("AAAA3", "2020-12-31", 100.0, "CVM DFP"))
    conn.commit()
    f = factor._fundamental_signals
    assert f(conn, ["AAAA3"], "2021-03-30", 90, "lucro_liquido") == {}
    assert f(conn, ["AAAA3"], "2021-03-31", 90, "lucro_liquido") == {"AAAA3": 100.0}


def test_split_entre_fre_e_asof_corrige_a_base_das_acoes(tmp_path):
    """BUG REAL (BBAS3 dobrou entre FRE 2022 e FRE 2023): preço vem de `asof`,
    ações vêm da `ref_date` do FRE. Com um split 1:2 no meio, o preço já caiu
    à metade e a contagem antiga subestimaria o market cap em 50% — dobrando
    o E/P e jogando o papel para o quintil 'barato' por artefato mecânico."""
    conn = _one_ticker_conn(tmp_path, price=10.0, shares=1000.0, lucro=500.0, pl=2000.0,
                            fund_ref="2020-12-31", shares_ref="2020-12-31")
    sem_split = factor.earnings_yield_signals(conn, ["AAAA3"], "2021-06-20")
    conn.execute(
        "INSERT INTO adjustments(ticker, ex_date, factor, type, source, approved_by)"
        " VALUES (?,?,?,?,?,?)",
        ("AAAA3", "2021-03-01", 0.5, "split", "inferred", "operador"))
    conn.commit()
    com_split = factor.earnings_yield_signals(conn, ["AAAA3"], "2021-06-20")
    # ações 1000 -> 2000 (dividido pelo fator 0,5): market cap dobra, E/P cai à metade
    assert abs(com_split["AAAA3"] - sem_split["AAAA3"] / 2.0) < 1e-12


def test_split_fora_da_janela_nao_altera_nada(tmp_path):
    """Evento ANTERIOR à ref_date do FRE já está refletido na contagem
    publicada; evento POSTERIOR a asof ainda não aconteceu."""
    conn = _one_ticker_conn(tmp_path, price=10.0, shares=1000.0, lucro=500.0, pl=2000.0,
                            fund_ref="2020-12-31", shares_ref="2020-12-31")
    base = factor.earnings_yield_signals(conn, ["AAAA3"], "2021-06-20")
    conn.execute(
        "INSERT INTO adjustments(ticker, ex_date, factor, type, source, approved_by)"
        " VALUES (?,?,?,?,?,?)",
        ("AAAA3", "2019-01-01", 0.5, "split", "inferred", "operador"))
    conn.execute(
        "INSERT INTO adjustments(ticker, ex_date, factor, type, source, approved_by)"
        " VALUES (?,?,?,?,?,?)",
        ("AAAA3", "2025-01-01", 0.5, "split", "inferred", "operador"))
    conn.commit()
    assert factor.earnings_yield_signals(conn, ["AAAA3"], "2021-06-20") == base


def test_provento_nao_altera_contagem_de_acoes(tmp_path):
    """Só split/grupamento mudam quantidade de ações. Um dividendo em
    `adjustments` (que também mexe em preço) não pode mexer na contagem."""
    conn = _one_ticker_conn(tmp_path, price=10.0, shares=1000.0, lucro=500.0, pl=2000.0,
                            fund_ref="2020-12-31", shares_ref="2020-12-31")
    base = factor.earnings_yield_signals(conn, ["AAAA3"], "2021-06-20")
    conn.execute(
        "INSERT INTO adjustments(ticker, ex_date, factor, type, source, approved_by)"
        " VALUES (?,?,?,?,?,?)",
        ("AAAA3", "2021-03-01", 0.97, "dividendo", "csv_manual", "operador"))
    conn.commit()
    assert factor.earnings_yield_signals(conn, ["AAAA3"], "2021-06-20") == base


def test_split_nao_aprovado_e_ignorado(tmp_path):
    """`approved_by IS NULL` = proposta pendente de revisão humana. Mesma
    disciplina de `adjust._load`: não entra no cálculo."""
    conn = _one_ticker_conn(tmp_path, price=10.0, shares=1000.0, lucro=500.0, pl=2000.0,
                            fund_ref="2020-12-31", shares_ref="2020-12-31")
    base = factor.earnings_yield_signals(conn, ["AAAA3"], "2021-06-20")
    conn.execute(
        "INSERT INTO adjustments(ticker, ex_date, factor, type, source)"
        " VALUES (?,?,?,?,?)", ("AAAA3", "2021-03-01", 0.5, "split", "inferred"))
    conn.commit()
    assert factor.earnings_yield_signals(conn, ["AAAA3"], "2021-06-20") == base


def test_ingest_fre_grava_known_at_do_dt_receb(tmp_path):
    """Ponta a ponta com os cabeçalhos REAIS: o `DT_RECEB` do arquivo
    principal chega em `fundamentals.known_at`, casado por ID_Documento."""
    import ingest_cvm
    import io as _io
    import zipfile as _zip
    buf = _io.BytesIO()
    with _zip.ZipFile(buf, "w") as zf:
        zf.writestr("fre_cia_aberta_2023.csv",
                    ("CNPJ_CIA;DT_REFER;VERSAO;DENOM_CIA;CD_CVM;CATEG_DOC;ID_DOC;"
                     "DT_RECEB;LINK_DOC\n"
                     "00.000.000/0001-91;2023-12-31;19;BCO BRASIL S.A.;001023;"
                     "FRE WEB;137597;2023-05-30;http://x").encode("latin-1"))
        zf.writestr("fre_cia_aberta_distribuicao_capital_2023.csv",
                    (_FRE_HEADER_REAL + "\n" + ";".join(_FRE_ROWS_REAL[0])).encode("latin-1"))
    zb = buf.getvalue()
    assert ingest_cvm.parse_fre_received_dates(zb) == {"137597": "2023-05-30"}

    conn = db.get_connection(tmp_path / "s.db")
    n = ingest_cvm.ingest_fre_shares_year(
        conn, 2023, {ingest_cvm._norm("BCO BRASIL S.A."): "BBAS3"}, zbytes=zb)
    assert n == 1
    ref, shares, known = conn.execute(
        "SELECT ref_date, shares_outstanding, known_at FROM fundamentals"
        " WHERE ticker='BBAS3'").fetchone()
    assert (ref, known) == ("2023-12-31", "2023-05-30")
    assert abs(shares - 5_730_799_931) < 1.0
    # o embargo diria 2024-03-30; a data observada é ~10 meses ANTES
    assert factor._fundamental_signals(
        conn, ["BBAS3"], "2023-06-01", 90, "shares_outstanding") != {}


def test_julgadas_ignoram_known_at_mesmo_quando_existe(tmp_path):
    """PROTEÇÃO DAS JÁ JULGADAS. Com a DFP passando a gravar `known_at`,
    H7/H9/H12 mudariam de comportamento por efeito colateral da ingestão —
    e o veredito delas é registro histórico, selado com o embargo estimado.
    Cada hipótese declara sua política; nenhuma herda a da outra."""
    conn = db.get_connection(tmp_path / "s.db")
    conn.execute(
        "INSERT INTO fundamentals(ticker, ref_date, roe, net_margin, accruals,"
        " known_at, source) VALUES (?,?,?,?,?,?,?)",
        ("AAAA3", "2020-12-31", 0.2, 0.1, 0.05, "2021-02-08", "CVM DFP"))
    conn.commit()
    cedo = "2021-02-10"        # depois do known_at, ANTES do embargo (2021-03-31)
    # julgadas: presas ao embargo, não veem
    assert factor.roe_signals(conn, ["AAAA3"], cedo) == {}
    assert factor.net_margin_signals(conn, ["AAAA3"], cedo) == {}
    # H17 (nunca rodada, re-pré-registrada): usa a data observada
    assert factor.accruals_signals(conn, ["AAAA3"], cedo) == {"AAAA3": 0.05}
    # no embargo, todas veem
    tarde = "2021-03-31"
    assert factor.roe_signals(conn, ["AAAA3"], tarde) == {"AAAA3": 0.2}
    assert factor.accruals_signals(conn, ["AAAA3"], tarde) == {"AAAA3": 0.05}


def test_parse_dfp_received_dates_pega_a_versao_mais_antiga():
    """Retificação tem DT_RECEB próprio; vale a data em que o exercício ficou
    público pela PRIMEIRA vez."""
    import ingest_cvm
    import io as _io
    import zipfile as _zip
    buf = _io.BytesIO()
    with _zip.ZipFile(buf, "w") as zf:
        zf.writestr("dfp_cia_aberta_2023.csv",
                    ("CNPJ_CIA;DT_REFER;VERSAO;DENOM_CIA;CD_CVM;CATEG_DOC;ID_DOC;"
                     "DT_RECEB;LINK_DOC\n"
                     "00.000.000/0001-91;2023-12-31;2;BB;001023;DFP;9;2024-07-01;x\n"
                     "00.000.000/0001-91;2023-12-31;1;BB;001023;DFP;8;2024-02-08;x"
                     ).encode("latin-1"))
    got = ingest_cvm.parse_dfp_received_dates(buf.getvalue(), 2023)
    assert got == {("00000000000191", "2023-12-31"): "2024-02-08"}


def _dfp_zip(year=2023, cnpj="00.000.000/0001-91", nome="BCO BRASIL S.A.",
             ref="2023-12-31", receb="2024-02-08"):
    """Zip DFP mínimo COM arquivo principal, cabeçalhos reais da CVM."""
    import io as _io
    import zipfile as _zip

    def demo(*linhas):
        return ("CNPJ_CIA;DT_REFER;VERSAO;DENOM_CIA;ORDEM_EXERC;CD_CONTA;"
                "DS_CONTA;VL_CONTA\n" + "\n".join(linhas)).encode("latin-1")

    def ln(cd, ds, vl):
        return f"{cnpj};{ref};1;{nome};ÚLTIMO;{cd};{ds};{vl}"

    buf = _io.BytesIO()
    with _zip.ZipFile(buf, "w") as zf:
        zf.writestr(f"dfp_cia_aberta_{year}.csv",
                    ("CNPJ_CIA;DT_REFER;VERSAO;DENOM_CIA;CD_CVM;CATEG_DOC;ID_DOC;"
                     "DT_RECEB;LINK_DOC\n"
                     f"{cnpj};{ref};1;{nome};001023;DFP;133944;{receb};x"
                     ).encode("latin-1"))
        zf.writestr(f"dfp_cia_aberta_BPA_con_{year}.csv",
                    demo(ln("1", "Ativo Total", "2000")))
        zf.writestr(f"dfp_cia_aberta_BPP_con_{year}.csv",
                    demo(ln("2", "Passivo Total", "2000"),
                         ln("2.03", "Patrimônio Líquido Consolidado", "800")))
        zf.writestr(f"dfp_cia_aberta_DRE_con_{year}.csv",
                    demo(ln("3.11", "Lucro Líquido do Período", "100"),
                         ln("3.01", "Receita de Venda de Bens e/ou Serviços", "1500")))
        zf.writestr(f"dfp_cia_aberta_DFC_MI_con_{year}.csv",
                    demo(ln("6.01", "Caixa Líquido Atividades Operacionais", "90")))
    return buf.getvalue()


def test_ingest_dfp_grava_known_at_do_dt_receb(tmp_path):
    """REGRESSÃO (bug de 2026-09-06, pego só na rodada real): a consulta de
    `known_at` usava só o CNPJ contra um dicionário chaveado por
    (cnpj, ref_date). Nunca casava — `known_at` ficava NULL em 100% das
    linhas e a ingestão reportava "0 linhas gravadas" sem erro nenhum.

    O teste de então cobria `parse_dfp_received_dates` isolado; a JUNÇÃO,
    que era onde estava o bug, não tinha cobertura. Este teste é ponta a
    ponta de propósito."""
    import ingest_cvm
    conn = db.get_connection(tmp_path / "s.db")
    zb = _dfp_zip()
    n = ingest_cvm.ingest_dfp_year(
        conn, 2023, ticker_of={ingest_cvm._norm("BCO BRASIL S.A."): "BBAS3"},
        zbytes=zb)
    assert n == 1
    ref, known, accr = conn.execute(
        "SELECT ref_date, known_at, accruals FROM fundamentals"
        " WHERE ticker='BBAS3'").fetchone()
    assert (ref, known) == ("2023-12-31", "2024-02-08")
    assert accr is not None

    # e o efeito que importa: H17 vê o dado em fevereiro, não no fim de março
    assert factor.accruals_signals(conn, ["BBAS3"], "2024-02-10") != {}
    # as JULGADAS continuam presas ao embargo, mesmo com known_at gravado
    assert factor.roe_signals(conn, ["BBAS3"], "2024-02-10") == {}
    assert factor.roe_signals(conn, ["BBAS3"], "2024-03-30") != {}


def test_ingest_dfp_known_at_e_idempotente(tmp_path):
    """Re-run não conta mudança depois que known_at já está preenchido."""
    import ingest_cvm
    conn = db.get_connection(tmp_path / "s.db")
    zb = _dfp_zip()
    tk = {ingest_cvm._norm("BCO BRASIL S.A."): "BBAS3"}
    assert ingest_cvm.ingest_dfp_year(conn, 2023, ticker_of=tk, zbytes=zb) == 1
    assert ingest_cvm.ingest_dfp_year(conn, 2023, ticker_of=tk, zbytes=zb) == 0
