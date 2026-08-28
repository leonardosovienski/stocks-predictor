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
from execution import equal_weight_turnover_cost
from returns import month_end_dates
import universe
from predictor_core.measurement.bootstrap import bootstrap_ci
from predictor_core.measurement.stats import (max_drawdown,
                                              probabilistic_sharpe_ratio, sharpe)

# equal_weight_turnover_cost agora vive em execution.py (canônica, ao lado da versão
# bruta calculate_turnover_cost — achado de revisão de código 2026-08-28: a duplicata
# local aqui arriscava divergir da correção já diagnosticada). Import acima mantém
# `backtest.equal_weight_turnover_cost` funcionando para quem já chamava por aqui.


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
    adjust.require_scanned(conn)
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


def _max_dd(returns):
    """Max drawdown da curva de capital (base 1.0) de uma série de retornos."""
    eq, v = [], 1.0
    for r in returns:
        v *= 1.0 + r
        eq.append(v)
    return max_drawdown(eq)


def _h4_extra_criteria(strat, bench, cfg):
    """Critério (iii) da H4 ("julgado por Sharpe líquido E drawdown", design §10):
    maxDD da estratégia <= maxDD do benchmark. Isolado do runner genérico porque só
    a H4 tem um 3º critério além de IC+DSR."""
    dd_s = dd_b = None
    failures = []
    if strat and cfg.get("h4_criteria", {}).get("require_maxdd_not_worse", True):
        dd_s, dd_b = _max_dd(strat), _max_dd(bench)
        if dd_s > dd_b:
            failures.append(f"maxDD estratégia {dd_s:.2%} > benchmark {dd_b:.2%}")
    return failures, {"maxdd_strat": dd_s, "maxdd_bench": dd_b}, f"maxDD strat/bench={dd_s}/{dd_b} | "


def _run_hypothesis(hypothesis, trial_name, frozen_keys, criteria_section, notes,
                    cfg, conn, write_report, run_id, trials_path,
                    signal_fn=None, take="top", portfolio_fn=None,
                    extra_criteria=None):
    """Runner comum das hipóteses H2+ (achado de revisão de código 2026-08-28: os
    run_hN eram 5 funções quase idênticas copiadas à mão — a mesma duplicação que já
    causou o bug real do clobber de sharpe da H2, ver `trials_gate.register_hypothesis`).
    Cada `run_hN` abaixo fica só com o que É específico dela: extrair os parâmetros
    `[hN-FROZEN]` do config e montar `signal_fn`/`take`/`portfolio_fn`."""
    import trials_gate
    strat, bench = walk_forward(conn, cfg, signal_fn=signal_fn, take=take,
                                portfolio_fn=portfolio_fn)
    base = judge(strat, bench, cfg)
    extra_failures, extra_fields, extra_text = [], {}, ""
    if extra_criteria is not None:
        extra_failures, extra_fields, extra_text = extra_criteria(strat, bench, cfg)
    verdict = trials_gate.apply_dsr(
        base, strat, cfg, trials_path=trials_path,
        trial_name=trial_name, frozen_keys=frozen_keys,
        criteria_section=criteria_section, extra_failures=extra_failures, notes=notes)
    verdict.update(extra_fields)
    return _conclude(verdict, strat, bench, cfg, hypothesis, write_report, run_id,
                     extra=extra_text)


def run_h2(cfg=None, conn=None, write_report=False, run_id=None, trials_path=None):
    """H2 — baixa volatilidade (pré-registro 2026-07-16). MESMA maquinaria da H1
    (universo/custos/pareamento/pedágio); o que muda é o sinal (vol realizada,
    quintil INFERIOR) e o critério extra da 2ª hipótese: DSR >= dsr_min,
    descontado por todas as tentativas do trials.json (trials_gate)."""
    cfg = cfg or load_config()
    conn = conn or db.get_connection()
    lb = cfg.get("h2_factor", {}).get("lookback_days", 252)
    return _run_hypothesis(
        "H2", "h2-lowvol-252", None, "h2_criteria", None,
        cfg, conn, write_report, run_id, trials_path,
        signal_fn=lambda sub, asof: factor.vol_signals(sub, asof, lb), take="bottom")


def run_h4(cfg=None, conn=None, write_report=False, run_id=None, trials_path=None):
    """H4 — sizing por volatility targeting (pré-registro 2026-07-18): universo
    INTEIRO com peso ∝ 1/vol realizada 252d vs. o MESMO universo equiponderado.
    Critérios (todos, fixados a priori): (i) IC95% diff-Sharpe > 0;
    (ii) DSR >= dsr_min (N=3 tentativas); (iii) maxDD da estratégia <= maxDD do
    benchmark ("julgado por Sharpe líquido E drawdown", design §10)."""
    from config import H4_FROZEN_KEYS
    cfg = cfg or load_config()
    conn = conn or db.get_connection()
    lb = cfg.get("h4_weighting", {}).get("vol_lookback_days", 252)
    return _run_hypothesis(
        "H4", "h4-invvol-sizing-252", H4_FROZEN_KEYS, "h4_criteria",
        "rodada única da H4 (sizing 1/vol; sharpe por-período realizado)",
        cfg, conn, write_report, run_id, trials_path,
        portfolio_fn=lambda sub, asof: portfolio.inverse_vol_weights(
            factor.vol_signals(sub, asof, lb)),
        extra_criteria=_h4_extra_criteria)


def run_h5(cfg=None, conn=None, write_report=False, run_id=None, trials_path=None):
    """H5 — reversão de curto prazo (pré-registro 2026-07-18): quintil INFERIOR
    do retorno de 21 pregões (perdedores do mês), mesma maquinaria de
    universo/custos/pedágio. Critérios: (i) IC95% diff-Sharpe > 0;
    (ii) DSR >= dsr_min (N=4 tentativas). O sinal é momentum_12_1 com
    lookback=21, skip=0 — retorno de [asof-21, asof] na série ajustada."""
    from config import H5_FROZEN_KEYS
    cfg = cfg or load_config()
    conn = conn or db.get_connection()
    h5f = cfg.get("h5_factor", {})
    lb, skip = h5f.get("lookback_days", 21), h5f.get("skip_days", 0)
    return _run_hypothesis(
        "H5", "h5-strev-21", H5_FROZEN_KEYS, "h5_criteria",
        "rodada única da H5 (reversão 21d; sharpe por-período realizado)",
        cfg, conn, write_report, run_id, trials_path,
        signal_fn=lambda sub, asof: factor.signals(sub, asof, lb, skip), take="bottom")


def run_h6(cfg=None, conn=None, write_report=False, run_id=None, trials_path=None):
    """H6 — momentum 6-1 (pré-registro 2026-08-27): MESMA maquinaria da H1,
    janela mais curta (126 pregões ~6 meses, skip 21) — hipótese de que a B3
    (menos líquida/eficiente que mercados desenvolvidos) incorpora momentum
    numa janela mais curta que o clássico 12-1 (que fracassou na H1)."""
    from config import H6_FROZEN_KEYS
    cfg = cfg or load_config()
    conn = conn or db.get_connection()
    h6f = cfg.get("h6_factor", {})
    lb, skip = h6f.get("lookback_days", 126), h6f.get("skip_days", 21)
    return _run_hypothesis(
        "H6", "h6-momentum-6-1", H6_FROZEN_KEYS, "h6_criteria",
        "rodada única da H6 (momentum 6-1; sharpe por-período realizado)",
        cfg, conn, write_report, run_id, trials_path,
        signal_fn=lambda sub, asof: factor.signals(sub, asof, lb, skip), take="top")


def run_h8(cfg=None, conn=None, write_report=False, run_id=None, trials_path=None):
    """H8 — filtro duplo momentum ∩ baixa vol (pré-registro 2026-08-27): top
    `h8_portfolio.momentum_quantile` do universo por momentum 12-1, depois a
    fração `h8_portfolio.vol_quantile` de menor vol realizada DENTRO desse
    subconjunto. H1 (momentum isolado) e H2 (baixa vol isolada) fracassaram —
    hipótese distinta: a interseção filtra o lado mais arriscado do momentum."""
    from config import H8_FROZEN_KEYS
    cfg = cfg or load_config()
    conn = conn or db.get_connection()
    h8f = cfg.get("h8_factor", {})
    mom_lb = h8f.get("momentum_lookback_days", 252)
    mom_skip = h8f.get("momentum_skip_days", 21)
    vol_lb = h8f.get("vol_lookback_days", 252)
    h8p = cfg.get("h8_portfolio", {})
    mom_q = h8p.get("momentum_quantile", 0.4)
    vol_q = h8p.get("vol_quantile", 0.5)

    def _pf(sub, asof):
        mom = factor.signals(sub, asof, mom_lb, mom_skip)
        vol = factor.vol_signals(sub, asof, vol_lb)
        return portfolio.momentum_lowvol_double_filter(mom, vol, mom_q, vol_q)

    return _run_hypothesis(
        "H8", "h8-mom-lowvol-double", H8_FROZEN_KEYS, "h8_criteria",
        "rodada única da H8 (filtro duplo momentum top ∩ baixa vol; "
        "sharpe por-período realizado)",
        cfg, conn, write_report, run_id, trials_path, portfolio_fn=_pf)


if __name__ == "__main__":
    if run() is None:
        sys.exit(1)
