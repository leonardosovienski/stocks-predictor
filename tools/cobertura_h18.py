"""Script AD-HOC (não faz parte do pacote) — COBERTURA DE DADO das
hipóteses de fundamento. Somente leitura.

Responde os critérios 2, 3 e 4 da auditoria de 2026-09-04
(`reports/auditoria_2026-09-04.md`), que nunca foram medidos:

  2. `shares_outstanding` não-nulo para fração relevante do universo
  3. as duas pernas do múltiplo (fundamento DFP + ações FRE) coexistindo
     ELEGÍVEIS nas datas de rebalance
  4. tamanho do universo com sinal por rebalance, comparável ao de
     H7/H9/H12/H13 (hipóteses já rodadas)

════════════════════════════════════════════════════════════════════════
TRAVA DELIBERADA — leia antes de alterar este arquivo
════════════════════════════════════════════════════════════════════════
Este script mede COBERTURA, nunca DESEMPENHO. Ele conta quantos papéis
têm sinal em cada data; jamais imprime, ordena, agrega ou retorna o VALOR
de um sinal, nem retorno, Sharpe, PSR ou DSR.

O motivo não é estilo: o pedágio estatístico do projeto (IC95% + DSR com
N crescente) existe para impedir que alguém escolha rodar uma hipótese
DEPOIS de espiar como ela se sai. Ver o desempenho aqui contaminaria
qualquer decisão posterior sobre rodar a H18 para valer, e essa
contaminação é irreversível — não há como "desver" um resultado.

Por isso as funções de sinal são consumidas SÓ via `len()`. Se você
precisar de algo que este script não dá, e a resposta exigir olhar
desempenho: PARE e pergunte ao operador, não relaxe a trava.
════════════════════════════════════════════════════════════════════════

Não escreve nada: nem no banco, nem em `trials.json`, nem em `reports/`.

Uso:
    python tools/cobertura_h18.py
    python tools/cobertura_h18.py --desde 2018-01-01
"""
import sys

sys.path.insert(0, "stocks_predictor")
import db  # noqa: E402
import factor  # noqa: E402
import universe as universe_mod  # noqa: E402
from config import load_config  # noqa: E402
from returns import month_end_dates  # noqa: E402

EMBARGO = 90    # [H18/H19-FROZEN] — lido do config abaixo; nunca alterado aqui


def _mediana(xs):
    s = sorted(xs)
    if not s:
        return 0.0
    m = len(s) // 2
    return float(s[m]) if len(s) % 2 else (s[m - 1] + s[m]) / 2.0


def _arg(flag, default=None):
    for i, a in enumerate(sys.argv):
        if a == flag and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def cobertura_bruta(conn):
    """Critério 2: contagem de linhas em `fundamentals`, por coluna.
    Independe de universo e de data — é a foto do que a ingestão produziu."""
    print("═" * 68)
    print("CRITÉRIO 2 — cobertura bruta da tabela `fundamentals`")
    print("═" * 68)
    total, tickers = conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT ticker) FROM fundamentals").fetchone()
    print(f"  linhas totais: {total}   tickers distintos: {tickers}")
    if not total:
        print("  !! tabela vazia — rodar a ingestão antes")
        return
    print(f"\n  {'coluna':26s} {'não-nulas':>10s} {'%':>7s} {'tickers':>8s}")
    for col in ("lucro_liquido", "patrimonio_liquido", "shares_outstanding",
                "roe", "leverage", "net_margin", "receita_liquida", "accruals"):
        n, tk = conn.execute(
            f"SELECT COUNT({col}), COUNT(DISTINCT CASE WHEN {col} IS NOT NULL"
            f" THEN ticker END) FROM fundamentals").fetchone()
        print(f"  {col:26s} {n:10d} {100.0 * n / total:6.1f}% {tk:8d}")

    faixa = conn.execute(
        "SELECT MIN(ref_date), MAX(ref_date) FROM fundamentals"
        " WHERE shares_outstanding IS NOT NULL").fetchone()
    print(f"\n  ref_date com shares_outstanding: {faixa[0]} .. {faixa[1]}")


def cobertura_por_rebalance(conn, cfg, desde):
    """Critérios 3 e 4: por data de rebalance, quantos papéis do universo
    point-in-time têm cada sinal DISPONÍVEL — nunca o valor do sinal."""
    u = cfg.get("universe", {})
    top_n = u.get("top_n", 60)
    liq_lb = u.get("lookback_trading_days", 126)
    min_hist = u.get("min_history_days", 252)
    emb18 = cfg.get("h18_factor", {}).get("disclosure_embargo_days", EMBARGO)
    emb19 = cfg.get("h19_factor", {}).get("disclosure_embargo_days", EMBARGO)

    all_dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM prices_raw WHERE market_type = ? ORDER BY date",
        (universe_mod.SPOT_MARKET,))]
    rebal = [d for d in month_end_dates(all_dates) if d >= desde]
    print("\n" + "═" * 68)
    print(f"CRITÉRIOS 3 e 4 — cobertura por rebalance ({len(rebal)} datas, "
          f"desde {desde})")
    print("═" * 68)
    if not rebal:
        print("  !! nenhuma data de rebalance — banco sem prices_raw?")
        return

    cols = ("universo", "lucro", "acoes", "E/P(H18)", "B/M(H19)",
            "roe(H7)", "lev(H9)", "marg(H12)", "accr(H17)")
    series = {c: [] for c in cols}
    for asof in rebal:
        uni = universe_mod.select_universe(conn, asof, top_n=top_n,
                                           lookback=liq_lb, min_history=min_hist)
        if not uni:
            continue
        f = factor._fundamental_signals
        # SÓ len(): nenhum valor de sinal é lido, impresso ou comparado.
        series["universo"].append(len(uni))
        series["lucro"].append(len(f(conn, uni, asof, emb18, "lucro_liquido")))
        series["acoes"].append(len(f(conn, uni, asof, emb18, "shares_outstanding")))
        series["E/P(H18)"].append(
            len(factor.earnings_yield_signals(conn, uni, asof, emb18)))
        series["B/M(H19)"].append(
            len(factor.book_to_market_signals(conn, uni, asof, emb19)))
        series["roe(H7)"].append(len(factor.roe_signals(conn, uni, asof, EMBARGO)))
        series["lev(H9)"].append(len(factor.leverage_signals(conn, uni, asof, EMBARGO)))
        series["marg(H12)"].append(
            len(factor.net_margin_signals(conn, uni, asof, EMBARGO)))
        series["accr(H17)"].append(
            len(factor.accruals_signals(conn, uni, asof, EMBARGO)))

    print(f"\n  {'sinal':12s} {'mediana':>8s} {'mín':>6s} {'máx':>6s} "
          f"{'datas c/ 0':>11s}")
    for c in cols:
        xs = series[c]
        if not xs:
            continue
        print(f"  {c:12s} {_mediana(xs):8.1f} {min(xs):6d} {max(xs):6d} "
              f"{sum(1 for x in xs if x == 0):11d}")

    uni_med = _mediana(series["universo"])
    print("\n  LEITURA:")
    print(f"  - critério 3 (as duas pernas juntas): mediana de "
          f"{_mediana(series['E/P(H18)']):.0f} papéis com E/P, contra "
          f"{_mediana(series['lucro']):.0f} com lucro e "
          f"{_mediana(series['acoes']):.0f} com ações — a perna mais escassa manda")
    print(f"  - critério 4 (comparação com hipóteses JÁ rodadas): H18 mediana "
          f"{_mediana(series['E/P(H18)']):.0f} vs. H7 {_mediana(series['roe(H7)']):.0f}, "
          f"H9 {_mediana(series['lev(H9)']):.0f}, H12 {_mediana(series['marg(H12)']):.0f}")
    print(f"  - universo point-in-time mediano: {uni_med:.0f} papéis")
    print("\n  (nenhum valor de sinal foi lido — só contagens; ver a TRAVA no topo)")


def main():
    cfg = load_config()
    desde = _arg("--desde", cfg.get("backtest", {}).get("test_start", "2018-01-01"))
    conn = db.get_connection()
    try:
        cobertura_bruta(conn)
        cobertura_por_rebalance(conn, cfg, desde)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
