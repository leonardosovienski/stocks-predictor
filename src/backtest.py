"""M5 — Walk-forward + pedágio de 2 lentes (PSR + bootstrap pareado) + veredito.

Encadeia M2-M4 numa passada forward mensal: a cada rebalance, universo point-in-time →
sinal momentum 12-1 → carteira quintil → segura até o próximo mês. Produz a curva DIÁRIA
de retornos da estratégia E do benchmark (equiponderado do universo), pareadas no tempo
— para o bloco-21-PREGÕES da H1 fazer sentido (periodicidade diária).

Veredito pelo PEDÁGIO canônico:
- Lente 1 (PSR): P(Sharpe da estratégia > Sharpe do benchmark), corrige não-normalidade.
- Lente 2 (block bootstrap PAREADO): IC da diferença de Sharpe; reamostra os pares
  (estratégia, benchmark) JUNTOS — preserva a cross-correlação. H1 COMPROVADA só se o
  IC 95% não cruzar zero.

Simplificações desta passada (registradas): retorno por preço ajustado de fechamento
(custo de turnover no rebalance); a robustez de execução a 3 preços (abertura/fechamento
D+1 / pior dos dois) e o purge/embargo formal ficam para a evolução do M5.
"""
import logging
import math
import statistics
import sys

import adjust
import db
import execution
import factor
import portfolio
from config import load_config
from returns import month_end_dates

logger = logging.getLogger(__name__)
import universe
from predictor_core.stats import block_bootstrap_ci, probabilistic_sharpe_ratio, sharpe


def _daily_returns(dates, closes):
    return {dates[i]: closes[i] / closes[i - 1] - 1.0
            for i in range(1, len(closes)) if closes[i - 1] > 0}


def walk_forward(conn, cfg):
    """Retorna (strat_diaria, bench_diaria) — listas pareadas de retornos diários.

    Custo de transação: proporcional ao turnover REAL entre rebalanceamentos consecutivos.
    Papéis que permanecem no portfólio não pagam custo; só entradas e saídas pagam.
    Fórmula: cost_period = (n_saindo + n_entrando) / n_portfolio × one_way_cost
    onde one_way_cost = fee + slippage por lado.
    """
    f, u = cfg["factor"], cfg["universe"]
    e, bt = cfg["execution"], cfg["backtest"]
    lookback_mom, skip = f.get("lookback_days", 252), f.get("skip_days", 21)
    top_n = u.get("top_n", 60)
    liq_lb, min_hist = u.get("lookback_trading_days", 126), u.get("min_history_days", 252)
    quant = 0.2  # top_quintile
    one_way = e.get("b3_fee_pct", 0.0003) + e.get("spread_slippage_pct", 0.0015)
    test_start = bt.get("test_start", "0000-00-00")

    series, dret = {}, {}
    # Só mercado à vista (Achado 6): evita construir séries de ~130k opções/termo que
    # nunca entram no universo — correção E performance (era a origem da lentidão).
    for tk in [r[0] for r in conn.execute(
            "SELECT DISTINCT ticker FROM prices_raw WHERE market_type=?",
            (universe.SPOT_MARKET,))]:
        dates, closes = adjust.adjusted_series(conn, tk)
        series[tk] = (dates, closes)
        dret[tk] = _daily_returns(dates, closes)

    all_dates = sorted({d for dates, _ in series.values() for d in dates})
    rebal = [d for d in month_end_dates(all_dates) if d >= test_start]

    strat, bench = [], []
    prev_port: set = set()
    for t, t1 in zip(rebal, rebal[1:]):
        uni = universe.select_universe(conn, t, top_n=top_n, lookback=liq_lb, min_history=min_hist)
        if not uni:
            continue
        sub = {tk: series[tk] for tk in uni if tk in series}
        port_dict = portfolio.select_portfolio(factor.signals(sub, t, lookback_mom, skip), quant)
        port = list(port_dict)
        if not port:
            prev_port = set()
            continue

        port_set = set(port)
        n = len(port_set)
        # custo proporcional ao turnover real, normalizado pelo peso 1/n da posição.
        # prev vazio (1ª carteira) => tudo entrando => custo de entrada por posição.
        period_cost = execution.calculate_turnover_cost(prev_port, port_set, one_way) / n
        prev_port = port_set

        period = [d for d in all_dates if t < d <= t1]
        for j, d in enumerate(period):
            srets = [dret[tk][d] for tk in port if d in dret[tk]]
            brets = [dret[tk][d] for tk in uni if d in dret[tk]]
            if not srets or not brets:
                continue
            s = sum(srets) / len(srets) - (period_cost if j == 0 else 0.0)
            strat.append(s)
            bench.append(sum(brets) / len(brets))
    return strat, bench


def judge(strat, bench, cfg):
    """Pedágio de 2 lentes sobre as séries pareadas. Veredito da H1."""
    b = cfg.get("bootstrap", {})
    n_boot, block = b.get("n_boot", 10_000), b.get("block_length", 21)
    conf, seed = b.get("confidence", 0.95), b.get("seed", 42)
    if not strat:
        # Achado 5: série VAZIA não é "amostra curta" — é ausência de dados (pipeline
        # não produziu nenhum par; ex.: DB com histórico < 252+lookback). Não pode se
        # disfarçar de veredito estatístico. Falha visível, não silenciosa.
        logger.warning("judge: walk_forward não produziu nenhum par strat/bench — "
                       "dados insuficientes (verifique histórico do DB e test_start)")
        return {"n": 0, "psr": None, "sharpe_diff_ci": (None, None),
                "veredito": "SEM DADOS (pipeline vazio — histórico insuficiente)"}
    if len(strat) < 2 * block:
        return {"n": len(strat), "psr": None, "sharpe_diff_ci": (None, None),
                "veredito": "INCONCLUSIVO (amostra curta)"}

    def per_period(xs):
        sd = statistics.pstdev(xs) if len(xs) > 1 else 0.0
        return statistics.mean(xs) / sd if sd else 0.0

    psr = probabilistic_sharpe_ratio(strat, benchmark_sharpe=per_period(bench))

    def diff_sharpe(window):
        d = sharpe([x[0] for x in window], 252) - sharpe([x[1] for x in window], 252)
        return d if math.isfinite(d) else None

    lo, hi, _ = block_bootstrap_ci(list(zip(strat, bench)), diff_sharpe,
                                   block_length=block, n_boot=n_boot, confidence=conf, seed=seed)
    comprovada = lo is not None and lo > 0
    return {"n": len(strat), "psr": psr, "sharpe_diff_ci": (lo, hi),
            "veredito": "COMPROVADA" if comprovada else "não comprovada (IC cruza 0 / negativo)"}


def run(cfg=None, conn=None):
    cfg = cfg or load_config()
    conn = conn or db.get_connection()
    strat, bench = walk_forward(conn, cfg)
    verdict = judge(strat, bench, cfg)
    print(f"walk-forward: {verdict['n']} pregões | PSR={verdict['psr']} | "
          f"IC95% ΔSharpe={verdict['sharpe_diff_ci']} | H1: {verdict['veredito']}")
    return verdict


if __name__ == "__main__":
    if run() is None:
        sys.exit(1)
