"""M4 — momentum 12-1, carteira quintil, execução D+1 + ANTI-LOOKAHEAD (exec_ts > signal_ts)."""
import datetime

import execution
import factor
import portfolio


def _daily(n):
    base = datetime.date(2022, 1, 3)
    return [(base + datetime.timedelta(days=i)).isoformat() for i in range(n)]


def test_momentum_12_1_matches_window():
    dates = _daily(300)
    closes = [100.0 * (1.001 ** i) for i in range(300)]
    asof = dates[280]
    m = factor.momentum_12_1(dates, closes, asof, lookback=252, skip=21)
    esperado = 1.001 ** (252 - 21) - 1.0          # close[280-21]/close[280-252]-1
    assert abs(m - esperado) < 1e-6


def test_momentum_none_without_history():
    dates = _daily(100)
    closes = [100.0] * 100
    assert factor.momentum_12_1(dates, closes, dates[50], lookback=252, skip=21) is None


def test_portfolio_top_quintile_equal_weight():
    sig = {f"T{i}": float(i) for i in range(10)}   # T9 maior
    p = portfolio.select_portfolio(sig, quantile=0.2)
    assert set(p) == {"T8", "T9"}                  # top 20% de 10 = 2
    assert all(abs(w - 0.5) < 1e-9 for w in p.values())


def test_portfolio_is_long_only_top():
    sig = {"A": -0.5, "B": 0.1, "C": 0.3, "D": 0.9, "E": 0.5}
    p = portfolio.select_portfolio(sig, quantile=0.2)   # round(5*0.2)=1 -> só o maior
    assert set(p) == {"D"}


def test_execution_strictly_after_signal_antilookahead():
    dates = ["2024-01-31", "2024-02-01", "2024-02-02"]
    opens = [10.0, 10.5, 10.7]
    exec_date, exec_price = execution.next_open_after(dates, opens, "2024-01-31")
    assert (exec_date, exec_price) == ("2024-02-01", 10.5)
    assert exec_date > "2024-01-31"                # exec_ts > signal_ts: anti-lookahead


def test_execution_no_future_is_none():
    assert execution.next_open_after(["2024-01-31"], [10.0], "2024-01-31") is None


def test_net_return_applies_roundtrip_cost():
    r = execution.net_return(10.0, 11.0, 0.0003, 0.0015)
    assert abs(r - (0.10 - 0.0036)) < 1e-9          # 0.36% ida-e-volta


def test_turnover_cost_accuracy():
    """BLINDAGEM: o custo cobra SÓ o que entrou e saiu — não o portfólio inteiro.
    Se alguém 'otimizar' cobrando sobre toda a carteira, este teste quebra."""
    cps = 0.0018                                     # custo por lado (0.03% + 0.15%)
    # carteira idêntica: zero turnover => custo zero (papéis mantidos não operam)
    assert execution.calculate_turnover_cost({"A", "B", "C"}, {"A", "B", "C"}, cps) == 0.0
    # turnover total: 3 saem, 3 entram => 6 lados
    assert abs(execution.calculate_turnover_cost({"A", "B", "C"}, {"X", "Y", "Z"}, cps)
               - 6 * cps) < 1e-12
    # turnover parcial: 1 sai (C), 1 entra (D) => 2 lados, NÃO o portfólio inteiro
    assert abs(execution.calculate_turnover_cost({"A", "B", "C"}, {"A", "B", "D"}, cps)
               - 2 * cps) < 1e-12
    # carteira inicial (prev vazio): tudo entrando => 1 lado por posição
    assert abs(execution.calculate_turnover_cost(set(), {"A", "B"}, cps) - 2 * cps) < 1e-12


def test_equal_weight_turnover_cost_is_the_one_canonical_implementation():
    """Achado de revisão de código 2026-08-28: a versão NORMALIZADA e correta
    do custo de turnover (a que `backtest.walk_forward` realmente usa) vivia
    duplicada como função privada dentro de backtest.py, arriscando divergir
    da canônica em execution.py. `backtest.equal_weight_turnover_cost` tem
    que ser o MESMO objeto de `execution.equal_weight_turnover_cost` — não
    uma cópia — e blindar o mesmo caso (carteira encolhendo/crescendo) que
    motivou a correção original."""
    import backtest
    assert backtest.equal_weight_turnover_cost is execution.equal_weight_turnover_cost
    cps = 0.0018
    # carteira de 4 encolhe pra 2: 2 saem (pesavam 1/4 cada), nenhuma entra
    cost = execution.equal_weight_turnover_cost({"A", "B", "C", "D"}, {"C", "D"}, cps)
    assert abs(cost - 2 * cps / 4) < 1e-12
    # carteira de 1 cresce pra 3: 2 entram (passam a pesar 1/3 cada)
    cost2 = execution.equal_weight_turnover_cost({"A"}, {"A", "B", "C"}, cps)
    assert abs(cost2 - 2 * cps / 3) < 1e-12
