"""Testes do pipeline integrado RJ (rj_pipeline) e da invariância de escala
do ajuste corporativo sobre as famílias.

Pipeline: sobe um SQLite sintético COMPLETO (prices_raw, rj_universe,
rj_events via migrations reais de db.py) e roda `run_pipeline` de ponta a
ponta — é o elo que faltava entre "mecânica validada em sintético solto"
(power gate) e "hipótese real": garante que universo -> episódios -> scores
-> judge -> persistência funciona contra o schema verdadeiro.

Invariância do ajuste: multiplicar TODOS os preços anteriores a uma ex_date
futura por um fator constante (o que `adjust.adjusted_closes` faz quando um
split é adjudicado DEPOIS do fundo) não pode mudar nenhum score de família
baseado em razão — se mudar, o ajuste retroativo vazou informação futura
nas features point-in-time.
"""
import pathlib
import random
import sys

import pytest
import yaml

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import adjust
import db
import rj_families as families
import rj_pipeline as pipeline


@pytest.fixture()
def cfg():
    with open(ROOT / "config_rj.yaml", encoding="utf-8") as f:
        c = yaml.safe_load(f)
    c["judge"]["n_boot"] = 200   # rápido em teste; hipótese real usa o config
    return c


def _calendar(n_days=600, start="2019-01-02"):
    import datetime
    d = datetime.date.fromisoformat(start)
    dates = []
    while len(dates) < n_days:
        if d.weekday() < 5:
            dates.append(d.isoformat())
        d += datetime.timedelta(days=1)
    return dates


def _insert_company(conn, ticker, dates, closes, rj_idx,
                    plan_idx=None, events=()):
    """Empresa sintética completa: preços + linha de universo + eventos."""
    for d, c in zip(dates, closes):
        conn.execute(
            "INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,"
            "low,close,volume_fin,qty,quote_factor,source_file) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (d, ticker, "02", "010", c, c, c, c, 1_000_000.0, 100, 1, "SYNTH"))
    conn.execute(
        "INSERT INTO rj_universe(ticker, company_name, rj_request_date,"
        " plan_presented_date, source, approved_by) VALUES(?,?,?,?,?,?)",
        (ticker, f"Synth {ticker}", dates[rj_idx],
         dates[plan_idx] if plan_idx else None, "synthetic", "test"))
    for ev_date, ev_type in events:
        conn.execute(
            "INSERT INTO rj_events(ticker, event_date, known_at, event_type,"
            " source, approved_by) VALUES(?,?,?,?,?,?)",
            (ticker, ev_date, ev_date, ev_type, "synthetic", "test"))
    conn.commit()


def _series(dates, rng, rj_idx, rally=True):
    """Cai até ~60 pregões pós-RJ (vira candidato point-in-time) e depois
    dispara (+80% em 30 pregões) ou fica lateral."""
    closes = [20.0]
    trough_idx = rj_idx + 60
    for _ in range(1, trough_idx):
        closes.append(max(0.05, closes[-1] * (1 + rng.gauss(-0.008, 0.01))))
    drift = 0.03 if rally else 0.0
    for _ in range(trough_idx, len(dates)):
        closes.append(max(0.05, closes[-1] * (1 + rng.gauss(drift, 0.01))))
    return closes


def test_pipeline_end_to_end_on_synthetic_db(tmp_path, cfg):
    conn = db.get_connection(tmp_path / "test.db")
    dates = _calendar(600)
    rng = random.Random(11)
    _insert_company(conn, "RALLY3", dates, _series(dates, rng, 50, rally=True),
                    rj_idx=50, events=[(dates[95], "fato_relevante")])
    _insert_company(conn, "FLAT3", dates, _series(dates, rng, 50, rally=False),
                    rj_idx=50)
    asof = dates[-1]

    report = pipeline.run_pipeline(conn, cfg, asof)

    assert report["universe_size"] == 2
    assert report["excluded"] == {}
    assert report["n_primary_analyzed"] >= 1
    for ep in report["episodes"]:
        assert ep["outcome_primary_window"] in (
            "rally", "no_rally_observed", "censored")
        assert "drawdown" in ep["scores"]
    # persistência: episódios e scores gravados e idempotentes
    n_ep = conn.execute("SELECT COUNT(*) FROM rj_episodes").fetchone()[0]
    assert n_ep == len(report["episodes"])
    persisted = conn.execute(
        "SELECT secondary_outcome, secondary_censored FROM rj_episodes"
    ).fetchall()
    assert len(persisted) == n_ep
    assert all(outcome is not None and censored is not None
               for outcome, censored in persisted)
    pipeline.run_pipeline(conn, cfg, asof)
    assert conn.execute("SELECT COUNT(*) FROM rj_episodes").fetchone()[0] == n_ep


def test_pipeline_excludes_company_without_prices(tmp_path, cfg):
    conn = db.get_connection(tmp_path / "test.db")
    dates = _calendar(600)
    rng = random.Random(12)
    _insert_company(conn, "RALLY3", dates, _series(dates, rng, 50), rj_idx=50)
    conn.execute(
        "INSERT INTO rj_universe(ticker, company_name, rj_request_date, source,"
        " approved_by) VALUES(?,?,?,?,?)",
        ("NOPX3", "Sem Preco SA", dates[50], "synthetic", "test"))
    conn.commit()
    report = pipeline.run_pipeline(conn, cfg, dates[-1])
    assert report["excluded"].get("NOPX3") == "sem serie de precos no banco"


def test_pipeline_reports_censored_separately(tmp_path, cfg):
    """Empresa cujo fundo é recente demais (janela de 60 pregões não completou
    antes do asof) sai da análise primária como CENSURADO, nunca como controle."""
    conn = db.get_connection(tmp_path / "test.db")
    dates = _calendar(600)
    # leve ALTA até ~len-100 (nunca mínimo da janela retroativa), depois queda
    # monotônica: o PRIMEIRO candidato point-in-time só aparece ~40 pregões
    # dentro da queda (perto do fim), e a janela primária de 60 pregões não
    # completa até o asof => censura. (Trecho plano empataria o min() e faria
    # todo dia ser "candidato" — por isso a inclinação.)
    n_flat = len(dates) - 60
    closes = ([10.0 + 0.01 * i for i in range(n_flat)]
              + [10.0 + 0.01 * n_flat - 0.5 * i for i in range(60)])
    asof = dates[-1]
    _insert_company(conn, "CENS3", dates, closes, rj_idx=50)
    report = pipeline.run_pipeline(conn, cfg, asof)
    primaries = [ep for ep in report["episodes"] if ep["is_primary"] == 1]
    assert primaries and primaries[0]["outcome_primary_window"] == "censored"
    assert report["n_censored_excluded"] == len(primaries)
    assert report["n_primary_analyzed"] == 0


def test_pipeline_liquidity_unavailable_without_free_float(tmp_path, cfg):
    conn = db.get_connection(tmp_path / "test.db")
    dates = _calendar(600)
    rng = random.Random(14)
    _insert_company(conn, "RALLY3", dates, _series(dates, rng, 50), rj_idx=50)
    report = pipeline.run_pipeline(conn, cfg, dates[-1], free_float=None)
    primaries = [ep for ep in report["episodes"] if ep["is_primary"] == 1]
    assert all(ep["scores"]["liquidity"] is None for ep in primaries)
    assert report["missing_scores_by_family"]["liquidity"] == len(primaries)


def test_ownership_family_is_always_unavailable_pending_real_ingester(tmp_path, cfg):
    """Achado de revisão de código 2026-08-28: `families.ownership` só é
    elegível com rj_events.event_type="investidor_5pct", mas NENHUM ingestor
    deste repo produz esse tipo (só fato_relevante/ipe_outro via
    ingest_cvm.ingest_ipe_year) — mesmo inserindo o evento diretamente na
    tabela (bypassando o ingestor real), `compute_family_scores` tem que
    reportar `ownership` como indisponível (None), nunca 0 (que afirmaria
    falsamente "sabemos que não houve entrada de investidor >=5%")."""
    conn = db.get_connection(tmp_path / "test.db")
    dates = _calendar(600)
    rng = random.Random(21)
    # evento "investidor_5pct" bem perto do fundo — se a família estivesse
    # ativa, isto dispararia ownership=1. Mesmo assim deve sair None.
    _insert_company(conn, "RALLY3", dates, _series(dates, rng, 50, rally=True),
                    rj_idx=50, events=[(dates[109], "investidor_5pct")])
    report = pipeline.run_pipeline(conn, cfg, dates[-1])
    primaries = [ep for ep in report["episodes"] if ep["is_primary"] == 1]
    assert primaries
    assert all(ep["scores"]["ownership"] is None for ep in primaries)


def test_persist_run_does_not_overwrite_score_with_null(tmp_path, cfg):
    """Achado de revisão de código 2026-08-28: `persist_run` gravava um score
    válido de uma rodada anterior e uma rodada SEGUINTE com aquela família
    indisponível (None) apagava o valor com NULL — `value IS NOT ?` com
    parâmetro None vira `IS NOT NULL` no SQLite e casa qualquer valor
    existente. Score persistido tem que sobreviver a uma rodada com dado
    faltante para a mesma família/episódio."""
    conn = db.get_connection(tmp_path / "test.db")
    dates = _calendar(600)
    rng = random.Random(22)
    ff = {"RALLY3": 1_000_000}
    _insert_company(conn, "RALLY3", dates, _series(dates, rng, 50, rally=True),
                    rj_idx=50)
    asof = dates[-1]
    built = pipeline.build_episodes(conn, cfg, asof)
    for ep in built["episodes"]:
        ep["scores"] = pipeline.compute_family_scores(conn, ep, cfg, ff, asof)
    pipeline.persist_run(conn, built, asof)
    ep_id = conn.execute("SELECT id FROM rj_episodes WHERE ticker='RALLY3'").fetchone()[0]
    before = conn.execute(
        "SELECT value FROM rj_family_scores WHERE episode_id=? AND family='liquidity'",
        (ep_id,)).fetchone()[0]
    assert before is not None    # score real gravado com free_float presente

    # 2ª rodada SEM free_float: liquidity sai None para este episódio.
    built2 = pipeline.build_episodes(conn, cfg, asof)
    for ep in built2["episodes"]:
        ep["scores"] = pipeline.compute_family_scores(conn, ep, cfg, None, asof)
    pipeline.persist_run(conn, built2, asof)
    after = conn.execute(
        "SELECT value FROM rj_family_scores WHERE episode_id=? AND family='liquidity'",
        (ep_id,)).fetchone()[0]
    assert after == before      # score anterior NÃO foi apagado com NULL


def test_adjustment_applied_after_trough_does_not_change_family_scores():
    """[anti-vazamento do ajuste retroativo] Um split adjudicado com ex_date
    DEPOIS do fundo escala todos os preços anteriores por um fator constante.
    Como as famílias contínuas são razões, os scores no fundo têm que ser
    IDÊNTICOS com e sem o ajuste futuro — qualquer diferença seria informação
    de D+k vazando para a decisão em D via tabela de ajustes."""
    dates = _calendar(400)
    closes = [10.0 * (0.995 ** i) for i in range(400)]
    trough = dates[200]
    adjusted = adjust.adjusted_closes(dates, closes, [(dates[300], 0.5)])

    assert families.drawdown(dates, closes, trough, dates[0]) == pytest.approx(
        families.drawdown(dates, adjusted, trough, dates[0]))
    assert families.momentum_volatility(dates, closes, trough) == pytest.approx(
        families.momentum_volatility(dates, adjusted, trough))


def test_adjustment_between_high_and_trough_is_economic_not_leakage():
    """Split ENTRE a máxima pré-RJ e o fundo DEVE mudar o drawdown — não é
    vazamento: sem o ajuste, a queda artificial do split seria confundida com
    drawdown real. O teste trava que o ajuste atua onde deve."""
    dates = _calendar(400)
    closes = [100.0] * 100 + [50.0] * 300   # "queda" de 50% que é só split 1:2
    adjusted = adjust.adjusted_closes(dates, closes, [(dates[100], 0.5)])
    trough = dates[200]
    raw_dd = families.drawdown(dates, closes, trough, dates[0])
    adj_dd = families.drawdown(dates, adjusted, trough, dates[0])
    assert raw_dd == pytest.approx(0.5)      # split cru finge drawdown de 50%
    assert adj_dd == pytest.approx(0.0)      # ajustado: não houve queda real
