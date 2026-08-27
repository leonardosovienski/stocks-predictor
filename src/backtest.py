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
import execution
import factor
import portfolio
from config import load_config
from returns import month_end_dates
import universe
from predictor_core.measurement.bootstrap import bootstrap_ci
from predictor_core.measurement.stats import (max_drawdown,
                                              probabilistic_sharpe_ratio, sharpe)


def equal_weight_turnover_cost(prev_port, port_set, cost_per_side):
    """Arrasto de turnover para carteira EQUIPONDERADA, já normalizado:
    cada SAÍDA pesa 1/len(prev_port) (peso que ela tinha), cada ENTRADA pesa
    1/len(port_set) (peso que ela passa a ter). Dividir tudo pelo tamanho da
    carteira nova (comportamento anterior) superestimava o custo das saídas
    quando a carteira encolhia e subestimava quando crescia.

    Carteira inicial (prev vazio): tudo é entrada => 1 * cost_per_side,
    independente do tamanho — igual à convenção de weighted_turnover_cost.
    """
    prev_port, port_set = set(prev_port), set(port_set)
    exits = len(prev_port - port_set)
    entries = len(port_set - prev_port)
    cost = entries * cost_per_side / len(port_set) if port_set else 0.0
    if prev_port:
        cost += exits * cost_per_side / len(prev_port)
    return cost


def _daily_returns(dates, closes):
    return {dates[i]: closes[i] / closes[i - 1] - 1.0
            for i in range(1, len(closes)) if closes[i - 1] > 0}


def walk_forward(conn, cfg, signal_fn=None, take="top", portfolio_fn=None):
    """Retorna (strat_diaria, bench_diaria) — listas pareadas de retornos diários.

    Custo de transação: proporcional ao turnover REAL entre rebalanceamentos
    consecutivos — papel que permanece na carteira não opera, logo não paga.
    cost_period = (n_saindo + n_entrando) × one_way / n_portfolio. Cobrar o
    roundtrip da carteira INTEIRA todo mês (modelo anterior) assumia turnover de
    100% e superestimava o arrasto contra a estratégia (auditoria Red Team 06/2026).

    `signal_fn(sub, asof) -> {ticker: sinal}` e `take` ("top"/"bottom") permitem
    plugar outra hipótese (H2: vol realizada, quintil inferior) na MESMA
    maquinaria de universo/custos/pareamento. Defaults = H1 exata.

    `portfolio_fn(sub, asof) -> {ticker: peso}` (H4+) troca a CONSTRUÇÃO por
    uma carteira PONDERADA (Σw=1): retorno diário = média ponderada
    (re-normalizada pelos presentes no dia) e custo = turnover de pesos
    (Σ|Δw| × lado). Quando presente, ignora signal_fn/take. O caminho
    equiponderado de H1/H2 permanece intocado.
    """
    f, u = cfg["factor"], cfg["universe"]
    e, bt = cfg["execution"], cfg["backtest"]
    lookback_mom, skip = f.get("lookback_days", 252), f.get("skip_days", 21)
    if signal_fn is None:
        signal_fn = lambda sub, asof: factor.signals(sub, asof, lookback_mom, skip)
    top_n = u.get("top_n", 60)
    liq_lb, min_hist = u.get("lookback_trading_days", 126), u.get("min_history_days", 252)
    quant = 0.2  # top_quintile
    one_way = execution.one_way_cost(
        e.get("b3_fee_pct", 0.0003), e.get("spread_slippage_pct", 0.0015))
    test_start = bt.get("test_start", "0000-00-00")

    # carga PREGUIÇOSA e memoizada: só tickers que entram em algum universo mensal —
    # o banco tem centenas de papéis (deslistados, curtos, quarentenados) que nunca
    # ranqueiam no top-N e cuja série nunca seria lida.
    series, dret = {}, {}

    def _load(tk):
        if tk not in series:
            dates, closes = adjust.adjusted_series(conn, tk)
            series[tk] = (dates, closes)
            dret[tk] = _daily_returns(dates, closes)

    all_dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM prices_raw WHERE market_type = ? ORDER BY date",
        (universe.SPOT_MARKET,))]
    rebal = [d for d in month_end_dates(all_dates) if d >= test_start]

    strat, bench = [], []
    prev_port: set = set()
    prev_w: dict = {}
    for t, t1 in zip(rebal, rebal[1:]):
        uni = universe.select_universe(conn, t, top_n=top_n, lookback=liq_lb, min_history=min_hist)
        if not uni:
            continue
        for tk in uni:
            _load(tk)
        sub = {tk: series[tk] for tk in uni}
        if portfolio_fn is None:
            port = list(portfolio.select_portfolio(signal_fn(sub, t), quant, take=take))
            if not port:
                prev_port = set()
                continue
            port_set = set(port)
            # custo do turnover real: saídas pesam 1/len(prev_port), entradas
            # 1/len(port_set) — ver equal_weight_turnover_cost.
            period_cost = equal_weight_turnover_cost(prev_port, port_set, one_way)
            prev_port = port_set
            weights = None
        else:
            weights = portfolio_fn(sub, t)
            if not weights:
                prev_w = {}
                continue
            period_cost = execution.weighted_turnover_cost(prev_w, weights, one_way)
            prev_w = weights

        period = [d for d in all_dates if t < d <= t1]
        cost_pending = True   # cobra no 1º par de retornos REGISTRADO, não em j==0
        # (bug corrigido: se o 1º pregão do período não tiver retorno válido,
        # `continue` pulava o índice sem cobrar, e o `j` nunca mais voltava a
        # 0 — o custo do rebalance inteiro sumia do período, inflando o
        # retorno líquido).
        for d in period:
            brets = [dret[tk][d] for tk in uni if d in dret[tk]]
            if weights is None:
                # ativo sem retorno no dia (suspensão/iliquidez) NÃO é
                # descartado da média silenciosamente — entraria como peso
                # extra grátis para os sobreviventes (viés de sobrevivência).
                # Convenção declarada: retorno 0 no dia sem cotação, mantendo
                # o denominador em len(port) inteiro.
                srets = [dret[tk].get(d, 0.0) for tk in port]
                if not brets:
                    continue
                s = sum(srets) / len(port) - (period_cost if cost_pending else 0.0)
            else:
                sw = [(w, dret[tk].get(d, 0.0)) for tk, w in weights.items()]
                den = sum(w for w, _ in sw)
                if not brets or den <= 0:
                    continue
                s = sum(w * r for w, r in sw) / den - (period_cost if cost_pending else 0.0)
            cost_pending = False
            strat.append(s)
            bench.append(sum(brets) / len(brets))
    return strat, bench


def judge(strat, bench, cfg):
    """Pedágio de 2 lentes sobre as séries pareadas. Veredito da H1."""
    b = cfg.get("bootstrap", {})
    n_boot, block = b.get("n_boot", 10_000), b.get("block_length", 21)
    conf, seed = b.get("confidence", 0.95), b.get("seed", 42)
    scheme = b.get("method", "stationary")   # H1 pré-registra STATIONARY (bloco 21)
    if not strat:
        # série VAZIA não é "amostra curta" — é ausência de dados (o pipeline não
        # produziu nenhum par). Não pode se disfarçar de veredito estatístico.
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

    lo, hi, _ = bootstrap_ci(list(zip(strat, bench)), diff_sharpe, scheme=scheme,
                             block_length=block, n_boot=n_boot, confidence=conf, seed=seed)
    comprovada = lo is not None and lo > 0
    return {"n": len(strat), "psr": psr, "sharpe_diff_ci": (lo, hi),
            "veredito": "COMPROVADA" if comprovada else "não comprovada (IC cruza 0 / negativo)"}


def run(cfg=None, conn=None, write_report=False, run_id=None):
    cfg = cfg or load_config()
    conn = conn or db.get_connection()
    strat, bench = walk_forward(conn, cfg)
    verdict = judge(strat, bench, cfg)
    print(f"walk-forward: {verdict['n']} pregões | PSR={verdict['psr']} | "
          f"IC95% diff-Sharpe={verdict['sharpe_diff_ci']} | H1: {verdict['veredito']}")
    if write_report:
        import report
        path = report.write_report(verdict, strat, bench, cfg, run_id=run_id)
        print(f"relatório: {path}")
    return verdict


def _conclude(verdict, strat, bench, cfg, hypothesis, write_report, run_id, extra=""):
    """Fecho comum das hipóteses H2+: imprime a linha do veredito (com DSR) e,
    se pedido, grava o relatório rotulado. Retorna o verdict inalterado."""
    print(f"walk-forward {hypothesis}: {verdict['n']} pregões | PSR={verdict['psr']} | "
          f"IC95% diff-Sharpe={verdict['sharpe_diff_ci']} | "
          f"DSR={verdict.get('dsr')} (N={verdict.get('n_trials')}) | "
          f"{extra}{hypothesis}: {verdict['veredito']}")
    if write_report:
        import report
        path = report.write_report(verdict, strat, bench, cfg, run_id=run_id,
                                   hypothesis=hypothesis)
        print(f"relatório: {path}")
    return verdict


def run_h2(cfg=None, conn=None, write_report=False, run_id=None, trials_path=None):
    """H2 — baixa volatilidade (pré-registro 2026-07-16). MESMA maquinaria da H1
    (universo/custos/pareamento/pedágio); o que muda é o sinal (vol realizada,
    quintil INFERIOR) e o critério extra da 2ª hipótese: DSR >= dsr_min,
    descontado por todas as tentativas do trials.json (trials_gate)."""
    import trials_gate
    cfg = cfg or load_config()
    conn = conn or db.get_connection()
    lb = cfg.get("h2_factor", {}).get("lookback_days", 252)
    strat, bench = walk_forward(
        conn, cfg, signal_fn=lambda sub, asof: factor.vol_signals(sub, asof, lb),
        take="bottom")
    verdict = trials_gate.apply_dsr(judge(strat, bench, cfg), strat, cfg,
                                    trials_path=trials_path)
    return _conclude(verdict, strat, bench, cfg, "H2", write_report, run_id)


def _max_dd(returns):
    """Max drawdown da curva de capital (base 1.0) de uma série de retornos."""
    eq, v = [], 1.0
    for r in returns:
        v *= 1.0 + r
        eq.append(v)
    return max_drawdown(eq)


def run_h4(cfg=None, conn=None, write_report=False, run_id=None, trials_path=None):
    """H4 — sizing por volatility targeting (pré-registro 2026-07-18): universo
    INTEIRO com peso ∝ 1/vol realizada 252d vs. o MESMO universo equiponderado.
    Critérios (todos, fixados a priori): (i) IC95% diff-Sharpe > 0;
    (ii) DSR >= dsr_min (N=3 tentativas); (iii) maxDD da estratégia <= maxDD do
    benchmark ("julgado por Sharpe líquido E drawdown", design §10)."""
    import trials_gate
    from config import H4_FROZEN_KEYS
    cfg = cfg or load_config()
    conn = conn or db.get_connection()
    lb = cfg.get("h4_weighting", {}).get("vol_lookback_days", 252)
    strat, bench = walk_forward(
        conn, cfg,
        portfolio_fn=lambda sub, asof: portfolio.inverse_vol_weights(
            factor.vol_signals(sub, asof, lb)))
    base = judge(strat, bench, cfg)
    extra, dd_s, dd_b = [], None, None
    if strat and cfg.get("h4_criteria", {}).get("require_maxdd_not_worse", True):
        dd_s, dd_b = _max_dd(strat), _max_dd(bench)
        if dd_s > dd_b:
            extra.append(f"maxDD estratégia {dd_s:.2%} > benchmark {dd_b:.2%}")
    verdict = trials_gate.apply_dsr(
        base, strat, cfg, trials_path=trials_path,
        trial_name="h4-invvol-sizing-252", frozen_keys=H4_FROZEN_KEYS,
        criteria_section="h4_criteria", extra_failures=extra,
        notes="rodada única da H4 (sizing 1/vol; sharpe por-período realizado)")
    verdict["maxdd_strat"], verdict["maxdd_bench"] = dd_s, dd_b
    return _conclude(verdict, strat, bench, cfg, "H4", write_report, run_id,
                     extra=f"maxDD strat/bench={dd_s}/{dd_b} | ")


def run_h5(cfg=None, conn=None, write_report=False, run_id=None, trials_path=None):
    """H5 — reversão de curto prazo (pré-registro 2026-07-18): quintil INFERIOR
    do retorno de 21 pregões (perdedores do mês), mesma maquinaria de
    universo/custos/pedágio. Critérios: (i) IC95% diff-Sharpe > 0;
    (ii) DSR >= dsr_min (N=4 tentativas). O sinal é momentum_12_1 com
    lookback=21, skip=0 — retorno de [asof-21, asof] na série ajustada."""
    import trials_gate
    from config import H5_FROZEN_KEYS
    cfg = cfg or load_config()
    conn = conn or db.get_connection()
    h5f = cfg.get("h5_factor", {})
    lb, skip = h5f.get("lookback_days", 21), h5f.get("skip_days", 0)
    strat, bench = walk_forward(
        conn, cfg, signal_fn=lambda sub, asof: factor.signals(sub, asof, lb, skip),
        take="bottom")
    verdict = trials_gate.apply_dsr(
        judge(strat, bench, cfg), strat, cfg, trials_path=trials_path,
        trial_name="h5-strev-21", frozen_keys=H5_FROZEN_KEYS,
        criteria_section="h5_criteria",
        notes="rodada única da H5 (reversão 21d; sharpe por-período realizado)")
    return _conclude(verdict, strat, bench, cfg, "H5", write_report, run_id)


if __name__ == "__main__":
    if run() is None:
        sys.exit(1)
