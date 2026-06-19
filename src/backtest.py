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
import math
import statistics
import sys

import adjust
import db
import factor
import portfolio
from config import load_config
from returns import month_end_dates
import universe
from predictor_core.obs import emit_event
from predictor_core.stats import block_bootstrap_ci, probabilistic_sharpe_ratio, sharpe


def _daily_returns(dates, closes):
    return {dates[i]: closes[i] / closes[i - 1] - 1.0
            for i in range(1, len(closes)) if closes[i - 1] > 0}


def walk_forward(conn, cfg):
    """Retorna (strat_diaria, bench_diaria) — listas pareadas de retornos diários."""
    f, u = cfg["factor"], cfg["universe"]
    e, bt = cfg["execution"], cfg["backtest"]
    lookback_mom, skip = f.get("lookback_days", 252), f.get("skip_days", 21)
    top_n = u.get("top_n", 60)
    liq_lb, min_hist = u.get("lookback_trading_days", 126), u.get("min_history_days", 252)
    quant = 0.2  # top_quintile
    cost = 2.0 * (e.get("b3_fee_pct", 0.0003) + e.get("spread_slippage_pct", 0.0015))
    test_start = bt.get("test_start", "0000-00-00")

    series, dret = {}, {}
    for tk in [r[0] for r in conn.execute("SELECT DISTINCT ticker FROM prices_raw")]:
        dates, closes = adjust.adjusted_series(conn, tk)
        series[tk] = (dates, closes)
        dret[tk] = _daily_returns(dates, closes)

    all_dates = sorted({d for dates, _ in series.values() for d in dates})
    rebal = [d for d in month_end_dates(all_dates) if d >= test_start]

    strat, bench = [], []
    for t, t1 in zip(rebal, rebal[1:]):
        uni = universe.select_universe(conn, t, top_n=top_n, lookback=liq_lb, min_history=min_hist)
        if not uni:
            continue
        sub = {tk: series[tk] for tk in uni if tk in series}
        port = list(portfolio.select_portfolio(factor.signals(sub, t, lookback_mom, skip), quant))
        if not port:
            continue
        period = [d for d in all_dates if t < d <= t1]
        for j, d in enumerate(period):
            srets = [dret[tk][d] for tk in port if d in dret[tk]]
            brets = [dret[tk][d] for tk in uni if d in dret[tk]]
            if not srets or not brets:
                continue
            s = sum(srets) / len(srets) - (cost if j == 0 else 0.0)   # custo no rebalance
            strat.append(s)
            bench.append(sum(brets) / len(brets))
    return strat, bench


def judge(strat, bench, cfg):
    """Pedágio de 2 lentes sobre as séries pareadas. Veredito da H1."""
    b = cfg.get("bootstrap", {})
    n_boot, block = b.get("n_boot", 10_000), b.get("block_length", 21)
    conf, seed = b.get("confidence", 0.95), b.get("seed", 42)
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
    lo, hi = verdict["sharpe_diff_ci"]
    metrics = {"n": verdict["n"]}
    if verdict["psr"] is not None:
        metrics["psr"] = round(float(verdict["psr"]), 4)
    if lo is not None:
        metrics["ic_lower"] = round(float(lo), 4)
    if hi is not None:
        metrics["ic_upper"] = round(float(hi), 4)
    emit_event("stocks", "backtest_completed",
               metrics=metrics,
               metadata={"veredito": verdict["veredito"]})
    return verdict


if __name__ == "__main__":
    if run() is None:
        sys.exit(1)
