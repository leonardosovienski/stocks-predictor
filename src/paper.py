"""M6 — Paper ledger forward: o ANTI-TAUTOLOGIA.

Registra a carteira (parte EVAL do ledger `decisions`, frozen_mode=1) num `asof` ANTES
de qualquer preço futuro existir — a única validação que nenhum lookahead pode
contaminar. Quando os preços chegam, a parte RISK é preenchida WRITE-ONCE via COALESCE
(coleta posterior não reescreve o que já foi registrado).

Operacional: roda no cron diário em rede limpa (mesmo padrão do domínio 1). Começa após
o veredito da H1 (M6) e nunca para.
"""
import adjust
import db
import factor
import portfolio
import universe
from config import load_config
from execution import next_open_after


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
    D+1 após o asof — WRITE-ONCE via COALESCE (preço futuro não reescreve registro feito)."""
    pending = conn.execute(
        "SELECT DISTINCT run_id, asof, ticker FROM decisions "
        "WHERE frozen_mode=1 AND exec_price IS NULL").fetchall()
    filled = 0
    for run_id, asof, tk in [(r[0], r[1], r[2]) for r in pending]:
        prices = conn.execute(
            "SELECT date, open FROM prices_raw WHERE ticker=? ORDER BY date", (tk,)).fetchall()
        nxt = next_open_after([r[0] for r in prices], [r[1] for r in prices], asof)
        if nxt is None:
            continue
        exec_date, exec_price, _gap = nxt
        conn.execute(
            "UPDATE decisions SET exec_date=COALESCE(exec_date,?), "
            "exec_price=COALESCE(exec_price,?) WHERE run_id=? AND asof=? AND ticker=?",
            (exec_date, exec_price, run_id, asof, tk))
        filled += 1
    conn.commit()
    return filled


def main():
    cfg = load_config()
    conn = db.get_connection()
    run_id = db.new_run(conn, {"paper": True}, notes="paper forward")
    print("paper forward pronto — chame record_forward(conn, cfg, asof, run_id) no cron.")
    return run_id


if __name__ == "__main__":
    main()
