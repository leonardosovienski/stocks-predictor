"""Onda 1 — correções do pipeline de julgamento (auditoria 2026-07-02).

Cobre: (1) PSR como Lente 1 OBRIGATÓRIA do pedágio; (2) judge respeita
bootstrap.method/interval do config; (3) entrada na ABERTURA de D+1 (não no
fechamento do dia do sinal); (4) custo × turnover real (carteira repetida não paga);
(5) carteiras aleatórias com percentil consultivo no veredito.
"""
import random

import pytest

import backtest
import db
import execution


# ---------------------------------------------------------------------------
# Lente 1 (PSR) obrigatória
# ---------------------------------------------------------------------------

def _paired_series(n=240, edge=0.002, seed=7):
    rng = random.Random(seed)
    bench = [rng.gauss(0.0003, 0.01) for _ in range(n)]
    strat = [b + edge for b in bench]
    return strat, bench


def _cfg(psr_min=0.5, **bootstrap_extra):
    boot = {"n_boot": 300, "block_length": 5, "confidence": 0.95, "seed": 1,
            "method": "stationary", "interval": "studentized", "psr_min": psr_min}
    boot.update(bootstrap_extra)
    return {"bootstrap": boot}


def test_psr_gate_verdict_needs_both_lenses():
    """Mesmas séries: com psr_min alcançável => COMPROVADA; com psr_min impossível
    (>1) a Lente 2 continua passando mas a Lente 1 barra — prova que o PSR deixou
    de ser decorativo."""
    strat, bench = _paired_series()
    v_ok = backtest.judge(strat, bench, _cfg(psr_min=0.5))
    assert v_ok["veredito"] == "COMPROVADA", v_ok
    assert v_ok["sharpe_diff_ci"][0] > 0            # Lente 2 passa nas duas variantes

    v_blocked = backtest.judge(strat, bench, _cfg(psr_min=1.01))
    assert v_blocked["veredito"].startswith("não comprovada (Lente 1"), v_blocked
    assert v_blocked["sharpe_diff_ci"][0] > 0       # só a Lente 1 barrou


def test_lens2_failure_reported_when_no_edge():
    """Sem edge (diferença de média zero, só ruído), a Lente 2 barra."""
    rng = random.Random(11)
    bench = [rng.gauss(0.0003, 0.01) for _ in range(240)]
    strat = [b + rng.gauss(0.0, 0.002) for b in bench]   # ruído sem edge
    v = backtest.judge(strat, bench, _cfg(psr_min=0.0))
    assert v["veredito"].startswith("não comprovada (Lente 2"), v


def test_judge_passes_method_and_interval_from_config(monkeypatch):
    """method/interval do config chegam ao block_bootstrap_ci — antes o judge nem
    lia `method` e rodava moving contra uma H1 que pré-registra stationary."""
    seen = {}

    def spy(series, statistic, **kw):
        seen.update(kw)
        return 0.1, 0.2, [0.1]

    monkeypatch.setattr(backtest, "block_bootstrap_ci", spy)
    strat, bench = _paired_series()
    backtest.judge(strat, bench, _cfg(method="stationary", interval="studentized"))
    assert seen["method"] == "stationary"
    assert seen["interval"] == "studentized"


# ---------------------------------------------------------------------------
# Execução D+1 na abertura + custo por turnover (DB na unha, números conferíveis)
# ---------------------------------------------------------------------------

_TCFG = {
    "factor": {"lookback_days": 6, "skip_days": 1},
    "universe": {"top_n": 2, "lookback_trading_days": 5, "min_history_days": 10},
    "execution": {"b3_fee_pct": 0.0003, "spread_slippage_pct": 0.0015},
    "backtest": {"test_start": "2024-01-01"},
    "bootstrap": {"n_boot": 100, "block_length": 5, "seed": 1},
}
_COST = 2.0 * (0.0003 + 0.0015)


def _insert(conn, ticker, rows):
    """rows: [(date, open, close)] — volume alto p/ ranquear no universo."""
    conn.executemany(
        "INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,low,close,"
        "volume_fin,qty,quote_factor,source_file) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        [(d, ticker, "02", "010", o, max(o, c), min(o, c), c, 1e6, 1000, 1, "test")
         for d, o, c in rows])
    conn.commit()


def _mk_dates(year, month, days):
    return [f"{year}-{month:02d}-{day:02d}" for day in days]


def _build_db(tmp_path):
    """AAAA3 sobe 2%/dia com gap de abertura de -0.5%; BBBB3 flat. 3 meses.
    Momentum top-1 = AAAA3 em todos os rebalances (turnover 0 no 2º)."""
    conn = db.get_connection(tmp_path / "t.db")
    days = list(range(1, 21))
    dates = (_mk_dates(2024, 1, days) + _mk_dates(2024, 2, days)
             + _mk_dates(2024, 3, list(range(1, 11))))
    a_rows, b_rows = [], []
    close_a = 10.0
    for d in dates:
        open_a = close_a * 0.995          # gap de abertura ≠ fechamento anterior
        close_a = open_a * 1.02
        a_rows.append((d, open_a, close_a))
        b_rows.append((d, 10.0, 10.0))
    _insert(conn, "AAAA3", a_rows)
    _insert(conn, "BBBB3", b_rows)
    return conn, dict((d, (o, c)) for d, o, c in a_rows)


def test_entry_at_next_open_not_at_signal_close(tmp_path):
    """1º dia do período: retorno = close/open do PRÓPRIO D+1 − custo, e NÃO
    close(D+1)/close(sinal) − custo (execução no fechamento do sinal é preço
    inatingível — era o defeito E9 da auditoria)."""
    conn, a_prices = _build_db(tmp_path)
    strat, bench, _ = backtest._walk(conn, _TCFG)
    o, c = a_prices["2024-02-01"]         # D+1 do sinal de 2024-01-20
    expected_open_entry = (c / o - 1.0) - _COST
    assert strat[0] == pytest.approx(expected_open_entry, abs=1e-12)
    # e difere do close-to-close (o gap de -0.5% fica de fora da posição)
    prev_close = a_prices["2024-01-20"][1]
    naive = (c / prev_close - 1.0) - _COST
    assert abs(strat[0] - naive) > 1e-4
    conn.close()


def test_cost_proportional_to_turnover_zero_when_same_portfolio(tmp_path):
    """2º rebalance mantém AAAA3 => turnover 0 => transição SEM custo: o retorno do
    1º dia do 2º período compõe overnight+intraday sem débito."""
    conn, a_prices = _build_db(tmp_path)
    strat, _, _ = backtest._walk(conn, _TCFG)
    # 1º período tem 20 dias (fev); o 21º retorno é a transição de março
    o, c = a_prices["2024-03-01"]
    prev_close = a_prices["2024-02-20"][1]
    expected_no_cost = (o / prev_close) * (c / o) - 1.0
    assert strat[20] == pytest.approx(expected_no_cost, abs=1e-12)
    conn.close()


def test_benchmark_pays_same_execution_and_costs(tmp_path):
    """Benchmark equiponderado paga o MESMO modelo de execução/custo (tratamento
    simétrico — antes ele era gross e implicitamente rebalanceado de graça)."""
    conn, a_prices = _build_db(tmp_path)
    _, bench, _ = backtest._walk(conn, _TCFG)
    o, c = a_prices["2024-02-01"]
    intra_a, intra_b = c / o - 1.0, 0.0
    expected = (intra_a + intra_b) / 2.0 - _COST
    assert bench[0] == pytest.approx(expected, abs=1e-12)
    conn.close()


def test_random_portfolios_paired_and_percentile(tmp_path):
    """Aleatórias: mesmas datas (pareadas), mesmo nº de posições; percentil
    consultivo do modelo entra no veredito."""
    conn, _ = _build_db(tmp_path)
    strat, bench, rand = backtest._walk(conn, _TCFG, n_random=5)
    assert len(rand) == 5
    assert all(len(r) == len(strat) for r in rand)
    v = backtest.judge(strat, bench, _TCFG, rand_returns=rand)
    if v["rand_percentile"] is not None:
        assert 0.0 <= v["rand_percentile"] <= 1.0
    conn.close()
