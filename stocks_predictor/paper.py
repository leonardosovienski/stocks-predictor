"""M6 — Paper ledger forward: o ANTI-TAUTOLOGIA.

Registra a carteira (parte EVAL do ledger `decisions`, frozen_mode=1) num `asof` ANTES
de qualquer preço futuro existir — a única validação que nenhum lookahead pode
contaminar. Quando os preços chegam, a parte RISK é preenchida WRITE-ONCE via COALESCE
(coleta posterior não reescreve o que já foi registrado).

Operacional: roda no cron diário em rede limpa (mesmo padrão do domínio 1). Começa após
o veredito da H1 (M6) e nunca para.
"""
import datetime

import adjust
import db
import execution
import factor
import portfolio
import universe
from execution import next_open_after
from returns import month_end_dates


def record_forward(conn, cfg, asof, run_id) -> int:
    """Registra a EVAL da carteira em `asof` (frozen_mode=1). Quintil superior =>
    conviction 'quintil_superior'; resto do universo => 'resto'. Retorna nº de linhas."""
    u, f = cfg["universe"], cfg["factor"]
    uni = universe.select_universe(
        conn, asof, u.get("top_n", 60), u.get("lookback_trading_days", 126),
        u.get("min_history_days", 252))
    series = {tk: adjust.adjusted_series(conn, tk) for tk in uni}
    sig = factor.signals(series, asof, f.get("lookback_days", 252), f.get("skip_days", 21))
    port = portfolio.select_portfolio(sig, 0.2)
    ranked = sorted(sig.items(), key=lambda kv: -kv[1])
    for rank, (tk, s) in enumerate(ranked, 1):
        band = "quintil_superior" if tk in port else "resto"
        conn.execute(
            "INSERT OR IGNORE INTO decisions(run_id,asof,ticker,signal_value,rank,"
            "conviction_band,frozen_mode) VALUES(?,?,?,?,?,?,1)",
            (run_id, asof, tk, s, rank, band))
    conn.commit()
    return len(ranked)


def settle_executions(conn, cfg) -> int:
    """Preenche exec_date/exec_price das decisões forward sem execução, na ABERTURA de
    D+1 após o asof — WRITE-ONCE via COALESCE (preço futuro não reescreve registro feito).

    Leitura blindada como o resto da camada (Red Team 06/2026): só mercado à
    vista (um banco carregado com avista_only=False não pode liquidar a preço
    de opção/termo) e GROUP BY date (re-ingest sob outro source_file duplicaria
    a linha e o preço de execução dependeria da ordem do scan)."""
    pending = conn.execute(
        "SELECT DISTINCT run_id, asof, ticker FROM decisions "
        "WHERE frozen_mode=1 AND exec_price IS NULL").fetchall()
    filled = 0
    series_cache: dict[str, tuple[list, list]] = {}
    for run_id, asof, tk in [(r[0], r[1], r[2]) for r in pending]:
        if tk not in series_cache:
            # abertura POR AÇÃO (÷ quote_factor) — correção na leitura, 2026-07-18
            prices = conn.execute(
                f"SELECT date, MAX({db.price_expr('open')}) FROM prices_raw "
                "WHERE ticker=? AND market_type=? GROUP BY date ORDER BY date",
                (tk, universe.SPOT_MARKET)).fetchall()
            series_cache[tk] = ([r[0] for r in prices], [r[1] for r in prices])
        dates, opens = series_cache[tk]
        nxt = next_open_after(dates, opens, asof)
        if nxt is None:
            continue
        exec_date, exec_price = nxt
        conn.execute(
            "UPDATE decisions SET exec_date=COALESCE(exec_date,?), "
            "exec_price=COALESCE(exec_price,?) WHERE run_id=? AND asof=? AND ticker=?",
            (exec_date, exec_price, run_id, asof, tk))
        filled += 1
    conn.commit()
    return filled


def settle_exits(conn, cfg) -> int:
    """Preenche exit_date/exit_price/cost_paid/realized_return_net/holding_days das
    decisões forward já EXECUTADAS (exec_price preenchido), na ABERTURA de D+1 após o
    PRÓXIMO rebalance mensal (mesma convenção 'segura até o próximo mês' de
    `backtest.walk_forward` — reaproveitada aqui, não inventada: é a única cadência
    de holding já pré-registrada no design). WRITE-ONCE via COALESCE.

    Achado de auditoria (2026-08-30): sem esta função, `decisions.realized_return_net`
    nunca era escrito por nenhum código do repositório — o ledger forward (M6) nunca
    conseguia produzir o veredito real que existe para produzir. `next_asof` é o
    próximo fim-de-mês do calendário à vista estritamente após `asof`; se ainda não
    houver pregão suficiente (posição ainda 'aberta' no fim do histórico carregado),
    a linha fica pendente e é reprocessada na próxima chamada (nada é escrito cedo
    demais — mesmo espírito anti-lookahead do resto do M6)."""
    e = cfg.get("execution", {})
    fee_pct = e.get("b3_fee_pct", 0.0003) + e.get("brokerage_pct", 0.0)
    slippage_pct = e.get("spread_slippage_pct", 0.0015)
    all_dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM prices_raw WHERE market_type=? ORDER BY date",
        (universe.SPOT_MARKET,))]
    month_ends = month_end_dates(all_dates)
    pending = conn.execute(
        "SELECT run_id, asof, ticker, exec_price, exec_date FROM decisions "
        "WHERE frozen_mode=1 AND exec_price IS NOT NULL AND exit_price IS NULL"
    ).fetchall()
    filled = 0
    series_cache: dict[str, tuple[list, list]] = {}
    for run_id, asof, tk, entry_price, exec_date in [
            (r[0], r[1], r[2], r[3], r[4]) for r in pending]:
        next_asof = next((d for d in month_ends if d > asof), None)
        if next_asof is None:
            continue    # ainda dentro do mês do exec_date — posição segue aberta
        if tk not in series_cache:
            prices = conn.execute(
                f"SELECT date, MAX({db.price_expr('open')}) FROM prices_raw "
                "WHERE ticker=? AND market_type=? GROUP BY date ORDER BY date",
                (tk, universe.SPOT_MARKET)).fetchall()
            series_cache[tk] = ([r[0] for r in prices], [r[1] for r in prices])
        dates, opens = series_cache[tk]
        nxt = next_open_after(dates, opens, next_asof)
        if nxt is None:
            continue
        exit_date, exit_price = nxt
        cost_paid = execution.roundtrip_cost(fee_pct, slippage_pct) * entry_price
        realized_return_net = execution.net_return(entry_price, exit_price, fee_pct, slippage_pct)
        # holding_days conta da EXECUÇÃO real (exec_date), não do sinal (asof) —
        # o preenchimento em settle_executions() ocorre em D+1 (ou mais, com
        # feriado/fim de semana no meio), então usar asof infla o campo pelo
        # atraso sinal->execução em toda linha (achado de varredura 2026-09-04).
        holding_days = (datetime.date.fromisoformat(exit_date)
                        - datetime.date.fromisoformat(exec_date)).days
        conn.execute(
            "UPDATE decisions SET exit_date=COALESCE(exit_date,?), "
            "exit_price=COALESCE(exit_price,?), cost_paid=COALESCE(cost_paid,?), "
            "realized_return_net=COALESCE(realized_return_net,?), "
            "holding_days=COALESCE(holding_days,?) "
            "WHERE run_id=? AND asof=? AND ticker=?",
            (exit_date, exit_price, cost_paid, realized_return_net, holding_days,
             run_id, asof, tk))
        filled += 1
    conn.commit()
    return filled


def main():
    conn = db.get_connection()
    run_id = db.new_run(conn, {"paper": True}, notes="paper forward")
    print("paper forward pronto — chame record_forward(conn, cfg, asof, run_id) no cron.")
    return run_id


if __name__ == "__main__":
    main()
