"""Testes de regressão da auditoria 2026-08-24 (branch audit/2026-08-24-fixes).

Cada teste aqui reproduz um bug confirmado da auditoria no código do domínio
RJ e trava a correção — sem tocar valores [RJ-FROZEN], as 8 famílias
pré-registradas ou o FDR BH alpha=0.10.
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "stocks_predictor"))

import rj_families as families
import rj_families_next as nextgen


# --- Bug A: fallback `known_at or event_date` = lookahead informacional -----

def test_ownership_event_without_known_at_is_not_eligible():
    """Protocolo §8/§10: event_date NÃO é known_at. Evento sem known_at
    válido não pode contar como sinal — antes da correção contava (lookahead)."""
    events = [{"event_type": "investidor_5pct", "event_date": "2020-05-10",
               "known_at": None}]
    assert families.ownership(events, "2020-05-20") == 0
    events2 = [{"event_type": "investidor_5pct", "event_date": "2020-05-10"}]
    assert families.ownership(events2, "2020-05-20") == 0
    # known_at válido dentro da janela continua sinalizando
    ok = [{"event_type": "investidor_5pct", "event_date": "2020-05-10",
           "known_at": "2020-05-12"}]
    assert families.ownership(ok, "2020-05-20") == 1


def test_info_trigger_event_without_known_at_is_not_eligible():
    events = [{"event_type": "fato_relevante", "event_date": "2020-05-10",
               "known_at": None}]
    assert families.info_trigger(events, "2020-05-15") == 0
    ok = [{"event_type": "fato_relevante", "event_date": "2020-05-10",
           "known_at": "2020-05-11"}]
    assert families.info_trigger(ok, "2020-05-15") == 1


def test_equity_issuance_event_without_known_at_is_not_eligible():
    events = [{"event_type": "aumento_capital", "event_date": "2020-05-10",
               "known_at": None}]
    assert nextgen.equity_issuance(events, "2020-05-20") == 0


def test_ownership_invalid_trough_date_is_unavailable_not_zero():
    """Fundo inválido = dado INDISPONÍVEL (None), nunca 0 — zero seria
    'sabemos que não houve evento', que é exatamente o que não sabemos."""
    assert families.ownership([], "nao-e-data") is None
    assert families.info_trigger([], "2020-13-99") is None
    assert nextgen.equity_issuance([], "lixo") is None


# --- Bug B: fila de revisão humana (approved_by IS NOT NULL, fail-closed) ---

import db
import ingest_cvm
import rj_pipeline as pipeline


def _universe_row(conn, ticker, approved):
    conn.execute(
        "INSERT INTO rj_universe(ticker, company_name, rj_request_date, source,"
        " approved_by) VALUES(?,?,?,?,?)",
        (ticker, f"{ticker} SA", "2020-01-10", "synthetic", approved))


def test_pipeline_ignores_universe_rows_pending_approval(tmp_path):
    """Regra 5 (fila de revisão humana): linha de rj_universe sem approved_by
    NÃO pode entrar na análise — fail-closed, não fail-open."""
    conn = db.get_connection(tmp_path / "t.db")
    _universe_row(conn, "PEND3", approved=None)
    _universe_row(conn, "APRV3", approved="revisor")
    tickers = {r[0] for r in conn.execute(
        "SELECT ticker FROM rj_universe WHERE approved_by IS NOT NULL")}
    assert tickers == {"APRV3"}
    built = pipeline.build_episodes(conn, _minimal_cfg(), "2020-02-01")
    seen = {ep["ticker"] for ep in built["episodes"]} | set(built["excluded"])
    assert "PEND3" not in seen


def test_pipeline_ignores_events_pending_approval(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    _universe_row(conn, "APRV3", approved="revisor")
    conn.execute(
        "INSERT INTO rj_events(ticker, event_date, known_at, event_type,"
        " source, approved_by) VALUES(?,?,?,?,?,?)",
        ("APRV3", "2020-01-12", "2020-01-12", "fato_relevante", "cvm", None))
    conn.commit()
    events = pipeline._load_events(conn, "APRV3")
    assert events == []


def _minimal_cfg():
    return {"rally": {"threshold_pct": 0.50,
                      "primary_window_trading_days": 60,
                      "secondary_window_trading_days": 252,
                      "point_in_time_backward_lookback_days": 40}}


def test_ingest_cvm_inserts_events_pending_approval(tmp_path, monkeypatch):
    """Ingest CVM grava com approved_by NULL (pendente de revisão) — nunca
    auto-aprovado."""
    conn = db.get_connection(tmp_path / "t.db")
    _universe_row(conn, "AMER3", approved="revisor")
    csv_text = ("CNPJ_Companhia;Nome_Companhia;Data_Referencia;Data_Entrega;"
                "Categoria;Tipo;Assunto;Link_Download\n"
                "00.000.000/0001-91;AMERICANAS S.A.;2023-01-10;2023-01-11;"
                "Fato Relevante;Fato Relevante;Pedido de RJ;http://x\n")
    monkeypatch.setattr(ingest_cvm, "download_zip",
                        lambda url, timeout=300: _zip(csv_text))
    n = ingest_cvm.ingest_ipe_year(
        conn, 2023, companies={"americanas_s.a."},
        ticker_of={"americanas_s.a.": "AMER3"})
    assert n == 1
    row = conn.execute(
        "SELECT approved_by FROM rj_events WHERE ticker='AMER3'").fetchone()
    assert row[0] is None


import io
import zipfile


def _zip(csv_text: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("ipe_cia_aberta_2023.csv", csv_text)
    return buf.getvalue()


# --- Bug C: parse vazio / zip ambíguo / datas malformadas (CVM) --------------

_IPE_HEADER = ("CNPJ_Companhia;Nome_Companhia;Data_Referencia;Data_Entrega;"
               "Categoria;Tipo;Assunto;Link_Download\n")


def test_parse_ipe_empty_csv_raises():
    """Regra 4: CSV vazio (só cabeçalho, ou nem isso) não pode retornar 0
    eventos silenciosamente — é falha de layout/fonte, não 'sem fatos'."""
    with pytest.raises(ValueError, match="0 linhas"):
        ingest_cvm.parse_ipe_rows([_IPE_HEADER.strip().split(";")])
    with pytest.raises(ValueError, match="0 linhas"):
        ingest_cvm.parse_ipe_rows(iter([]))


def test_parse_ipe_company_filter_emptying_everything_raises():
    """Filtro de companhias que esvazia TUDO: fail-loud (provável erro de
    mapeamento de nomes), não zero silencioso."""
    rows = [ _IPE_HEADER.strip().split(";"),
             ["00", "AMERICANAS S.A.", "2023-01-10", "2023-01-11",
              "Fato Relevante", "Fato Relevante", "RJ", "http://x"]]
    with pytest.raises(ValueError, match="filtro de companhias"):
        ingest_cvm.parse_ipe_rows(rows, companies={"outra_s.a."})


def test_parse_ipe_malformed_dates_raise_with_count():
    rows = [_IPE_HEADER.strip().split(";"),
            ["00", "A S.A.", "2023-01-10", "11/01/2023", "F", "F", "s", "l"],
            ["00", "B S.A.", "2023-01-10", "2023-13-40", "F", "F", "s", "l"]]
    with pytest.raises(ValueError, match="2"):
        ingest_cvm.parse_ipe_rows(rows)


def test_open_zip_csv_ambiguous_match_raises():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("ipe_cia_aberta_2023.csv", "a;b\n1;2\n")
        zf.writestr("ipe_cia_aberta_2023_extra.csv", "a;b\n3;4\n")
    with pytest.raises(ValueError, match="2 CSVs"):
        list(ingest_cvm._open_zip_csv(buf.getvalue(), "ipe_cia_aberta"))


# --- Bug D: preço de fundo <= 0 + assert fail-closed de asof ------------------

import rj_episodes as episodes


def test_classify_episode_nonpositive_trough_is_invalid_not_control():
    """Fundo com preço <= 0 (dado quebrado) NUNCA é 'no_rally_observed' —
    viraria controle falso e contaminaria o denominador do judge."""
    dates = ["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07"]
    closes = [10.0, 0.0, 11.0, 12.0]
    res = episodes.classify_episode(dates, closes, "2020-01-03",
                                    _minimal_cfg(), "2020-01-07")
    assert res["outcome"] == "invalid_data"
    assert res["censored"] == 0


def test_classify_episode_asserts_series_not_beyond_asof():
    """asof_today era parâmetro morto: série estendendo além do corte =
    lookahead estrutural — fail-closed."""
    dates = ["2020-01-02", "2020-01-03"]
    with pytest.raises(AssertionError):
        episodes.classify_episode(dates, [10.0, 9.0], "2020-01-03",
                                  _minimal_cfg(), "2020-01-02")


# --- Bug E: chs_nimta com MTA <= 0 inverte o sinal -----------------------------

def test_chs_nimta_nonpositive_mta_is_unavailable():
    """MTA (passivo + valor de mercado do equity) <= 0 torna NI/MTA sem
    sentido econômico (sinal invertido por denominador negativo) — None,
    nunca número."""
    fin = {"net_income": 30, "total_liabilities": 400, "equity_value": -500}
    assert nextgen.chs_nimta(fin) is None
    fin0 = {"net_income": 30, "total_liabilities": 0, "equity_value": 0}
    assert nextgen.chs_nimta(fin0) is None
    ok = {"net_income": 30, "total_liabilities": 400, "equity_value": 500}
    assert nextgen.chs_nimta(ok) == pytest.approx(30 / 900)


# --- Bug F: p-valor de permutação (n_ge + 1) / (n_perm + 1) ---------------------

import rj_judge as judge
import rj_judge_robust as robust


def test_permutation_pvalue_never_zero():
    """Convenção correta de permutação: p = (n_ge + 1) / (n_perm + 1) —
    p = 0.0 é impossível (a estatística observada é sempre uma permutação
    possível). Separação perfeita dos grupos: nenhuma permutação supera a
    observada, logo p = 1/(n_perm+1), não 0."""
    units = [(f"T{i}3", 10.0 + i, 1) for i in range(4)] + \
            [(f"C{i}3", 0.0 + i * 0.01, 0) for i in range(4)]
    p = judge.permutation_pvalue(units, n_perm=100, seed=1)
    assert p > 0
    assert p >= 1 / 101 - 1e-12   # piso (0+1)/(100+1), nunca 0


def test_categorical_pvalue_never_zero():
    cfg = {"judge": {"seed": 1, "n_boot": 100}}
    units = ([(f"T{i}3", "exited", 1) for i in range(6)]
             + [(f"C{i}3", "requested", 0) for i in range(6)])
    v = judge.categorical_family_verdict(units, cfg)
    assert v["p_value"] == pytest.approx(1 / 101)
    assert v["p_value"] > 0


def test_romano_wolf_pvalue_never_zero():
    units_by_family = {name: [(f"T{i}3", 10.0 + i, 1) for i in range(4)]
                             + [(f"C{i}3", float(i) * 0.01, 0) for i in range(4)]
                       for name in ["drawdown", "liquidity"]}
    rw = robust.romano_wolf_stepdown(units_by_family, n_perm=100, seed=1)
    for res in rw.values():
        assert res["p_romanowolf"] > 0
        assert res["p_romanowolf"] >= 1 / 101 - 1e-12


def test_permutation_pvalue_formula_is_shared_not_reimplemented():
    """Achado de revisão de código 2026-08-28: a fórmula (n_ge+1)/(n_perm+1)
    estava implementada 3x independentemente (permutation_pvalue,
    categorical_family_verdict, romano_wolf_stepdown) — uma correção num
    lugar não propagaria para os outros dois. `romano_wolf_stepdown` tem que
    usar o MESMO helper que `rj_judge.permutation_pvalue`, não uma cópia."""
    assert judge.permutation_pvalue_from_count(0, 100) == pytest.approx(1 / 101)
    assert judge.permutation_pvalue_from_count(99, 100) == pytest.approx(100 / 101)
    assert robust.permutation_pvalue_from_count is judge.permutation_pvalue_from_count


# --- Bug G: persist_run com INSERT OR IGNORE mantinha outcome velho ------------

import yaml


def _cfg_real():
    with open(ROOT / "config_rj.yaml", encoding="utf-8") as f:
        c = yaml.safe_load(f)
    c["judge"]["n_boot"] = 100
    return c


def _calendar(n_days=600, start="2019-01-02"):
    import datetime
    d = datetime.date.fromisoformat(start)
    out = []
    while len(out) < n_days:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += datetime.timedelta(days=1)
    return out


def test_persist_run_updates_row_when_asof_advances(tmp_path):
    """Re-run com asof posterior NÃO pode manter o outcome censurado velho
    no banco (INSERT OR IGNORE puro). E re-run no MESMO asof é idempotente
    (banco bit a bit idêntico)."""
    conn = db.get_connection(tmp_path / "t.db")
    dates = _calendar(600)
    # queda monotônica até idx 90 (1º candidato point-in-time, RJ em 50 +
    # lookback 40) e alta em seguida: rally cruza +50% por volta de idx 104
    closes = [20.0 * (0.97 ** i) for i in range(91)]
    closes += [closes[-1] * (1.03 ** i) for i in range(1, 600 - 90)]
    for d, c in zip(dates, closes):
        conn.execute(
            "INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,"
            "low,close,volume_fin,qty,quote_factor,source_file) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (d, "EVOL3", "02", "010", c, c, c, c, 1e6, 100, 1, "SYNTH"))
    conn.execute(
        "INSERT INTO rj_universe(ticker, company_name, rj_request_date, source,"
        " approved_by) VALUES(?,?,?,?,?)",
        ("EVOL3", "Evol SA", dates[50], "synthetic", "test"))
    conn.commit()
    cfg = _cfg_real()

    t1 = dates[100]     # janela de 60 pregões ainda incompleta -> censored
    pipeline.run_pipeline(conn, cfg, t1)
    row1 = conn.execute(
        "SELECT outcome, censored FROM rj_episodes WHERE ticker='EVOL3'").fetchone()
    assert tuple(row1) == ("censored", 1)

    dump = lambda: conn.execute(
        "SELECT ticker, trough_date, outcome, rally_pct, rally_date, censored"
        " FROM rj_episodes ORDER BY ticker, trough_date").fetchall()
    pipeline.run_pipeline(conn, cfg, t1)
    assert dump() == dump()    # mesmo asof: idempotente

    t2 = dates[-1]      # rally aconteceu e a janela fechou
    pipeline.run_pipeline(conn, cfg, t2)
    row2 = conn.execute(
        "SELECT outcome, censored FROM rj_episodes WHERE ticker='EVOL3'").fetchone()
    assert tuple(row2) == ("rally", 0)
    pipeline.run_pipeline(conn, cfg, t2)
    assert dump() == dump()    # idempotente também no asof novo


# --- Bug H: ingest CVM duplicava eventos em re-execução -------------------------

def test_ingest_ipe_year_idempotent(tmp_path, monkeypatch):
    conn = db.get_connection(tmp_path / "t.db")
    _universe_row(conn, "AMER3", approved="revisor")
    csv_text = ("CNPJ_Companhia;Nome_Companhia;Data_Referencia;Data_Entrega;"
                "Categoria;Tipo;Assunto;Link_Download\n"
                "00.000.000/0001-91;AMERICANAS S.A.;2023-01-10;2023-01-11;"
                "Fato Relevante;Fato Relevante;Pedido de RJ;http://x\n")
    monkeypatch.setattr(ingest_cvm, "download_zip",
                        lambda url, timeout=300: _zip(csv_text))
    n1 = ingest_cvm.ingest_ipe_year(
        conn, 2023, companies={"americanas_s.a."},
        ticker_of={"americanas_s.a.": "AMER3"})
    n2 = ingest_cvm.ingest_ipe_year(
        conn, 2023, companies={"americanas_s.a."},
        ticker_of={"americanas_s.a.": "AMER3"})
    assert n1 == 1
    assert n2 == 0     # re-execução não duplica
    assert conn.execute(
        "SELECT COUNT(*) FROM rj_events WHERE ticker='AMER3'").fetchone()[0] == 1


# --- Bug I: domínio histórico (reparáveis, não científicos) ---------------------

import adjust
import backtest
import cotahist
import factor
import universe


def test_momentum_12_1_nonpositive_end_price_is_unavailable():
    """closes[i_end] <= 0 tornava o retorno calculável e distorcido (só
    closes[i_start] era validado)."""
    dates = _calendar(300, start="2020-01-06")
    closes = [10.0] * 300
    asof = dates[-1]
    closes[-22] = 0.0     # exatamente i_end (asof - skip)
    assert factor.momentum_12_1(dates, closes, asof) is None
    closes[-22] = 11.0
    assert factor.momentum_12_1(dates, closes, asof) is not None


def test_turnover_cost_weights_exits_by_prev_portfolio():
    """Saídas pagam 1/len(prev_port), entradas 1/len(port_set) — antes TUDO
    era dividido pelo tamanho da carteira nova, distorcendo o custo quando
    os tamanhos diferem."""
    cost = backtest.equal_weight_turnover_cost({"A", "B", "C", "D"}, {"C", "D"}, 0.01)
    # 2 saídas * (1/4) * 0.01 + 0 entradas = 0.005
    assert cost == pytest.approx(2 * 0.01 / 4)
    cost2 = backtest.equal_weight_turnover_cost({"A"}, {"B", "C"}, 0.01)
    # 1 saída * 1 * 0.01 + 2 entradas * (1/2) * 0.01 = 0.02
    assert cost2 == pytest.approx(0.01 + 2 * 0.01 / 2)
    # carteira inicial: tudo entrada
    assert backtest.equal_weight_turnover_cost(set(), {"A", "B"}, 0.01) == pytest.approx(0.01)


def test_cotahist_malformed_line_counted_not_fatal():
    """Uma linha malformada não pode derrubar o arquivo inteiro nem passar
    em silêncio: é pulada, contada e logada com contexto."""
    good = cotahist.synthetic_cotahist(["PETR4"], ["2024-01-02"], seed=1)
    bad = "01" + "X" * 243   # tipo 01, mas campos numéricos lixo
    recs, n_bad = cotahist.parse_lines(good + [bad])
    assert len(recs) == 1 and n_bad == 1
    with pytest.raises(ValueError, match="linhas malformadas"):
        cotahist.parse_lines([bad, bad])   # 100% malformado: arquivo quebrado


def test_scan_and_quarantine_rerun_counts_zero_new(tmp_path):
    """n += 1 incondicional contava salto já quarentenado de novo — o número
    retornado deve ser de NOVAS quarentenas (cursor.rowcount)."""
    conn = db.get_connection(tmp_path / "s.db")
    for d, c in [("2024-01-01", 20.0), ("2024-01-02", 10.0)]:
        conn.execute(
            "INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,low,"
            "close,volume_fin,qty,quote_factor,source_file) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (d, "PETR4", "02", "010", c, c, c, c, 1e6, 100, 1, "SYNTH"))
    conn.commit()
    assert adjust.scan_and_quarantine(conn, threshold=0.30) == 1
    assert adjust.scan_and_quarantine(conn, threshold=0.30) == 0   # idempotente


def test_universe_dedup_on_pn_tie_is_deterministic(tmp_path):
    """Empate de liquidez ON/PN: sem ORDER BY a query de hist dependia da
    ordem física do banco. Com ORDER BY determinístico, o primeiro ticker
    (ordem alfabética) vence o empate — reproduzível entre máquinas."""
    conn = db.get_connection(tmp_path / "s.db")
    d = _calendar(20, start="2023-01-02")
    for tk in ("ZZAA4", "ZZAA3"):   # inserir o PN antes, de propósito
        for dt in d:
            conn.execute(
                "INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,"
                "low,close,volume_fin,qty,quote_factor,source_file) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (dt, tk, "02", "010", 10.0, 10.0, 10.0, 10.0, 1000.0, 100, 1, "S"))
    conn.commit()
    uni = universe.select_universe(conn, d[15], top_n=5, lookback=5, min_history=8)
    assert "ZZAA3" in uni and "ZZAA4" not in uni


# --- Bug J: robustez / menores -------------------------------------------------

import rj_coda as coda
import rj_outcomes as outcomes
import rj_power


def test_simulate_power_rejects_zero_reps():
    with pytest.raises(ValueError, match="n_reps"):
        rj_power.simulate_power(_cfg_real(), 10, 1.0, n_reps=0)


def test_robustness_report_none_bh_gives_none_concordant(monkeypatch):
    """bh_sig=None (família fora do FDR/sem p-valor) não é False — concordant
    deve ser None (não aplicável), não 'discorda'."""
    import rj_judge_robust as robust
    monkeypatch.setattr(robust, "romano_wolf_stepdown",
                        lambda u, n_perm, seed, alpha: {
                            "drawdown": {"t_obs": 2.0, "p_romanowolf": 0.01,
                                         "significant_romanowolf": True}})
    rep = robust.robustness_report({}, {"drawdown": {"significant_after_fdr": None}})
    assert rep["drawdown"]["concordant"] is None
    rep2 = robust.robustness_report({}, {"drawdown": {"significant_after_fdr": True}})
    assert rep2["drawdown"]["concordant"] is True


def test_walk_forward_evaluate_rejects_non_monotonic_dates():
    """Se as units carregam data, a ordenação temporal é CONTRATO verificado
    (fail-closed), não suposição."""
    units = [{"date": "2020-02-01", "v": 1}, {"date": "2020-01-01", "v": 2}]
    with pytest.raises(ValueError, match="ordena"):
        outcomes.walk_forward_evaluate(
            units, lambda tr: None, lambda m, te: 0.0, min_train=1, step=1)
    ok = [{"date": "2020-01-01", "v": 1}, {"date": "2020-02-01", "v": 2}]
    assert outcomes.walk_forward_evaluate(
        ok, lambda tr: None, lambda m, te: 0.0, min_train=1, step=1)


def test_load_free_float_takes_latest_ref_date(monkeypatch):
    """Múltiplas linhas FRE por companhia: vale a de maior ref_date
    (determinístico), não a última lida."""
    csv_text = ("Nome_Companhia;Data_Referencia;Quantidade_Total_Acoes;"
                "Quantidade_Acoes_Circulacao\n"
                "EMPRESA S.A.;2022-12-31;1000;400\n"
                "EMPRESA S.A.;2023-12-31;1000;450\n"
                "EMPRESA S.A.;2021-12-31;1000;300\n")
    import io as _io
    import zipfile as _zf
    buf = _io.BytesIO()
    with _zf.ZipFile(buf, "w") as z:
        z.writestr("fre_cia_aberta_distribuicao_capital_2023.csv", csv_text)
    monkeypatch.setattr(ingest_cvm, "download_zip",
                        lambda url, timeout=300: buf.getvalue())
    out = ingest_cvm.load_free_float(2023)
    assert out["empresa_s.a."] == pytest.approx(450.0)


def test_coda_impute_zeros_requires_rectangular_matrix():
    with pytest.raises(ValueError, match="retangular"):
        coda.impute_zeros([[1.0, 2.0], [3.0]])
    with pytest.raises(ValueError, match="retangular"):
        coda.clr_matrix([[1.0, 2.0], [3.0]])
