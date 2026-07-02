"""M5 — Walk-forward + pedágio de 2 lentes (PSR + bootstrap pareado) + veredito.

Encadeia M2-M4 numa passada forward mensal: a cada rebalance, universo point-in-time →
sinal momentum 12-1 → carteira quintil → segura até o próximo mês. Produz a curva DIÁRIA
de retornos da estratégia E do benchmark (equiponderado do universo), pareadas no tempo.

EXECUÇÃO (Onda 1, 2026-07-02 — pré-dado): a transição de carteira acontece na ABERTURA
do primeiro pregão utilizável após o sinal (execution.price = next_open [H1-FROZEN]).
No dia de transição o retorno compõe (1 + gap overnight da carteira ANTIGA) ×
(1 + retorno intraday da carteira NOVA) − custo. Custo = roundtrip × TURNOVER REAL
(fração da carteira trocada), debitado incondicionalmente no primeiro dia utilizável
do período. Benchmark e carteiras aleatórias seguem as MESMAS regras de execução e
custo (tratamento simétrico — formalização registrada no HANDOFF).

BENCHMARKS (design §2, fixados a priori):
(a) carteira equiponderada do universo point-in-time, mesmas regras de execução/custo;
(b) carteiras aleatórias com MESMO nº de posições e turnover casado com o do modelo —
    a posição do modelo na distribuição delas sai no veredito (consultivo).

Veredito pelo PEDÁGIO de 2 lentes — AMBAS obrigatórias (Onda 1; antes o PSR era
decorativo, defeito da auditoria 2026-07-02):
- Lente 1 (PSR ≥ psr_min [H1-FROZEN]): corrige não-normalidade.
- Lente 2 (block bootstrap PAREADO, stationary + intervalo studentized): IC 95% da
  diferença de Sharpe excluindo zero.
"""
import math
import random
import statistics
import sys

import adjust
import db
import execution
import factor
import portfolio
from config import load_config
from returns import month_end_dates
import universe
from predictor_core.stats import block_bootstrap_ci, probabilistic_sharpe_ratio, sharpe


def _daily_maps(dates, opens, closes):
    """{data: retorno} para close-a-close, intraday (open→close) e overnight
    (close anterior→open) — os blocos da execução na abertura de D+1."""
    c2c, intra, over = {}, {}, {}
    for i, d in enumerate(dates):
        if opens[i] > 0:
            intra[d] = closes[i] / opens[i] - 1.0
        if i > 0 and closes[i - 1] > 0:
            c2c[d] = closes[i] / closes[i - 1] - 1.0
            if opens[i] > 0:
                over[d] = opens[i] / closes[i - 1] - 1.0
    return c2c, intra, over


def _mean_over(kind_map, tickers, d):
    """Média equiponderada do retorno `kind` dos tickers COM dado em d. None se nenhum."""
    vals = [kind_map[tk][d] for tk in tickers if d in kind_map[tk]]
    return sum(vals) / len(vals) if vals else None


class _Book:
    """Uma carteira simulada (estratégia, benchmark ou aleatória)."""
    __slots__ = ("weights", "target", "cost_pending", "rets")

    def __init__(self):
        self.weights: dict = {}
        self.target: dict = {}
        self.cost_pending = 0.0
        self.rets: list[float] = []

    def set_target(self, target: dict, roundtrip: float):
        self.target = target
        self.cost_pending = roundtrip * execution.turnover(self.weights, target)

    def day_return(self, maps, d, transition: bool):
        c2c, intra, over = maps
        if transition:
            it = _mean_over(intra, self.target, d)
            if it is None:
                return None
            ov = _mean_over(over, self.weights, d) or 0.0   # 1ª carteira: sem gap
            return (1.0 + ov) * (1.0 + it) - 1.0 - self.cost_pending

        r = _mean_over(c2c, self.weights, d)
        return r

    def commit_transition(self):
        self.weights = self.target
        self.cost_pending = 0.0


def _matched_random_target(rng, uni, k, prev: dict, model_turnover: float) -> dict:
    """Carteira aleatória com MESMO nº de posições (k) e turnover casado com o do
    modelo: mantém ~(1-turnover)·k nomes da própria carteira anterior (ainda no
    universo), completa com sorteio uniforme."""
    keep_n = min(len(prev), round((1.0 - model_turnover) * k))
    still_valid = [t for t in prev if t in set(uni)]
    kept = rng.sample(still_valid, min(keep_n, len(still_valid)))
    pool = [t for t in uni if t not in set(kept)]
    fill = rng.sample(pool, min(k - len(kept), len(pool)))
    names = kept + fill
    if not names:
        return {}
    w = 1.0 / len(names)
    return {t: w for t in names}


def _walk(conn, cfg, n_random=0):
    """Motor único: estratégia + benchmark + n_random aleatórias na mesma passada.
    Retorna (strat, bench, rand_rets) — listas diárias pareadas no tempo."""
    f, u = cfg["factor"], cfg["universe"]
    e, bt = cfg["execution"], cfg["backtest"]
    lookback_mom, skip = f.get("lookback_days", 252), f.get("skip_days", 21)
    top_n = u.get("top_n", 60)
    liq_lb, min_hist = u.get("lookback_trading_days", 126), u.get("min_history_days", 252)
    quant = 0.2  # top_quintile [H1-FROZEN]
    roundtrip = execution.roundtrip_cost(
        e.get("b3_fee_pct", 0.0003), e.get("spread_slippage_pct", 0.0015))
    test_start = bt.get("test_start", "0000-00-00")
    embargo = bt.get("purge_embargo_months", 0)

    series, maps_c2c, maps_intra, maps_over = {}, {}, {}, {}
    for tk in [r[0] for r in conn.execute("SELECT DISTINCT ticker FROM prices_raw")]:
        dates, opens, closes = adjust.adjusted_series_oc(conn, tk)
        series[tk] = (dates, closes)
        maps_c2c[tk], maps_intra[tk], maps_over[tk] = _daily_maps(dates, opens, closes)
    maps = (maps_c2c, maps_intra, maps_over)

    all_dates = sorted({d for dates, _ in series.values() for d in dates})
    rebal = [d for d in month_end_dates(all_dates) if d >= test_start]
    rebal = rebal[embargo:]          # purge/embargo entre aquecimento e teste (§8)

    strat_book, bench_book = _Book(), _Book()
    rng = random.Random(cfg.get("benchmark", {}).get("random_seed", 271828))
    rand_books = [_Book() for _ in range(n_random)]

    for t, t1 in zip(rebal, rebal[1:]):
        uni = universe.select_universe(conn, t, top_n=top_n, lookback=liq_lb,
                                       min_history=min_hist)
        if not uni:
            continue
        sub = {tk: series[tk] for tk in uni if tk in series}
        port = portfolio.select_portfolio(factor.signals(sub, t, lookback_mom, skip), quant)
        if not port:
            continue

        strat_book.set_target(port, roundtrip)
        model_to = execution.turnover(strat_book.weights, port)
        w_uni = 1.0 / len(uni)
        bench_book.set_target({tk: w_uni for tk in uni}, roundtrip)
        for rb in rand_books:
            rb.set_target(
                _matched_random_target(rng, uni, len(port), rb.weights, model_to),
                roundtrip)

        transitioned = False
        for d in [d for d in all_dates if t < d <= t1]:
            s = strat_book.day_return(maps, d, not transitioned)
            b = bench_book.day_return(maps, d, not transitioned)
            if s is None or b is None:
                continue                       # dia sem dado: pareamento preservado
            rr = [rb.day_return(maps, d, not transitioned) for rb in rand_books]
            strat_book.rets.append(s)
            bench_book.rets.append(b)
            for rb, r in zip(rand_books, rr):
                rb.rets.append(r if r is not None else 0.0)
            if not transitioned:
                for bk in (strat_book, bench_book, *rand_books):
                    bk.commit_transition()
                transitioned = True

    return strat_book.rets, bench_book.rets, [rb.rets for rb in rand_books]


def walk_forward(conn, cfg):
    """Retorna (strat_diaria, bench_diaria) — listas pareadas de retornos diários."""
    strat, bench, _ = _walk(conn, cfg, n_random=0)
    return strat, bench


def judge(strat, bench, cfg, rand_returns=None):
    """Pedágio de 2 lentes sobre as séries pareadas — AMBAS obrigatórias.
    rand_returns (opcional): distribuição de carteiras aleatórias; a posição do
    modelo nela sai no veredito como CONSULTIVA (design §2b)."""
    b = cfg.get("bootstrap", {})
    n_boot, block = b.get("n_boot", 10_000), b.get("block_length", 21)
    conf, seed = b.get("confidence", 0.95), b.get("seed", 42)
    method = b.get("method", "stationary")
    interval = b.get("interval", "studentized")
    psr_min = b.get("psr_min", 0.95)
    if len(strat) < 2 * block:
        return {"n": len(strat), "psr": None, "psr_min": psr_min,
                "sharpe_diff_ci": (None, None), "rand_percentile": None,
                "veredito": "INCONCLUSIVO (amostra curta)"}

    def per_period(xs):
        sd = statistics.pstdev(xs) if len(xs) > 1 else 0.0
        return statistics.mean(xs) / sd if sd else 0.0

    psr = probabilistic_sharpe_ratio(strat, benchmark_sharpe=per_period(bench))

    def diff_sharpe(window):
        d = sharpe([x[0] for x in window], 252) - sharpe([x[1] for x in window], 252)
        return d if math.isfinite(d) else None

    lo, hi, _ = block_bootstrap_ci(list(zip(strat, bench)), diff_sharpe,
                                   block_length=block, n_boot=n_boot, confidence=conf,
                                   seed=seed, method=method, interval=interval)

    rand_pct = None
    if rand_returns:
        s_model = sharpe(strat, 252)
        rand_sharpes = [sharpe(r, 252) for r in rand_returns if len(r) >= 2]
        rand_sharpes = [s for s in rand_sharpes if math.isfinite(s)]
        if rand_sharpes and math.isfinite(s_model):
            rand_pct = sum(1 for s in rand_sharpes if s < s_model) / len(rand_sharpes)

    lens1 = psr is not None and math.isfinite(psr) and psr >= psr_min
    lens2 = lo is not None and lo > 0
    if lens1 and lens2:
        veredito = "COMPROVADA"
    elif not lens2:
        veredito = "não comprovada (Lente 2: IC cruza 0 / negativo)"
    else:
        veredito = f"não comprovada (Lente 1: PSR {psr:.3f} < {psr_min})"
    return {"n": len(strat), "psr": psr, "psr_min": psr_min,
            "sharpe_diff_ci": (lo, hi), "rand_percentile": rand_pct,
            "veredito": veredito}


def run(cfg=None, conn=None):
    cfg = cfg or load_config()
    conn = conn or db.get_connection()
    n_random = cfg.get("benchmark", {}).get("n_random", 0)
    strat, bench, rand_returns = _walk(conn, cfg, n_random=n_random)
    verdict = judge(strat, bench, cfg, rand_returns=rand_returns)
    pct = verdict["rand_percentile"]
    print(f"walk-forward: {verdict['n']} pregões | PSR={verdict['psr']} "
          f"(min {verdict['psr_min']}) | IC95% ΔSharpe={verdict['sharpe_diff_ci']} | "
          f"percentil vs aleatórias={pct if pct is not None else 'n/a'} | "
          f"H1: {verdict['veredito']}")
    return verdict


if __name__ == "__main__":
    if run() is None:
        sys.exit(1)
