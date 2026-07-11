"""M2+ — Analista somente-leitura (consultivo). NÃO faz parte do pipeline de sinal.

Regras invioláveis (§9b do design):
- NUNCA escreve no banco (só SELECT).
- NUNCA resolve quarentena — apenas SINALIZA para o humano decidir.
- NÃO gera sinal de investimento (isso é proibido antes do veredito da H1, §11).
- Saída = artefato Markdown descartável em `reports/ai/`, datado.
- Deletar este arquivo não quebra nenhum teste do sistema de previsão.

É observabilidade consultiva: descreve o estado atual (universo, decisões, quarentena
pendente) em linguagem humana, para o operador. Sem LLM e sem dependência de runtime —
o "analista" aqui é determinístico e auditável; um analista-LLM plugaria nesta mesma
fronteira read-only, jamais escrevendo no banco.
"""
import pathlib

ROOT = pathlib.Path(__file__).parent.parent


def gather(conn):
    """Coleta SOMENTE-LEITURA do estado atual. Nenhum INSERT/UPDATE/DELETE."""
    state = {}
    state["n_prices"] = conn.execute("SELECT COUNT(*) FROM prices_raw").fetchone()[0]
    state["n_tickers"] = conn.execute(
        "SELECT COUNT(DISTINCT ticker) FROM prices_raw").fetchone()[0]
    state["date_range"] = conn.execute(
        "SELECT MIN(date), MAX(date) FROM prices_raw").fetchone()

    asof = conn.execute("SELECT MAX(asof_date) FROM universe_snapshots").fetchone()[0]
    state["universe_asof"] = asof
    state["universe"] = conn.execute(
        "SELECT ticker, rank, median_vol FROM universe_snapshots "
        "WHERE asof_date=? ORDER BY rank LIMIT 10", (asof,)).fetchall() if asof else []

    state["quarantine_open"] = conn.execute(
        "SELECT ticker, date, reason, raw_return FROM quarantine "
        "WHERE resolved_at IS NULL ORDER BY date DESC LIMIT 20").fetchall()

    last_run = conn.execute(
        "SELECT run_id FROM decisions ORDER BY inserted_at DESC LIMIT 1").fetchone()
    state["last_run"] = last_run[0] if last_run else None
    state["top_convictions"] = conn.execute(
        "SELECT ticker, rank, signal_value, exec_date, exec_price FROM decisions "
        "WHERE run_id=? AND conviction_band='quintil_superior' ORDER BY rank LIMIT 12",
        (state["last_run"],)).fetchall() if state["last_run"] else []
    return state


def build_brief(state):
    """Markdown consultivo. Descreve; não recomenda comprar/vender."""
    dr = state["date_range"] or (None, None)
    L = [
        "# predictor-stocks — Briefing do analista (somente-leitura)",
        "",
        "> Consultivo. NÃO é sinal de investimento e NÃO resolve quarentena — "
        "apenas descreve o estado e sinaliza pendências para decisão humana.",
        "",
        "## Cobertura de dados",
        f"- registros em `prices_raw`: **{state['n_prices']}** "
        f"({state['n_tickers']} tickers, {dr[0]} → {dr[1]})",
        "",
        "## Universo point-in-time mais recente",
    ]
    if state["universe_asof"]:
        L.append(f"- asof **{state['universe_asof']}** (top 10 por liquidez):")
        for tk, rank, med in state["universe"]:
            L.append(f"  - {rank:>2}. {tk} — mediana vol R$ {med:,.0f}")
    else:
        L.append("- (nenhum snapshot materializado ainda)")

    L += ["", "## Quarentena PENDENTE (requer decisão humana)"]
    if state["quarantine_open"]:
        L.append("> O analista NÃO resolve — lista para o operador investigar/registrar ajuste.")
        for tk, d, reason, rr in state["quarantine_open"]:
            rr_s = f"{rr * 100:.1f}%" if isinstance(rr, (int, float)) else "n/d"
            L.append(f"- **{tk}** {d}: {reason} (retorno {rr_s})")
    else:
        L.append("- nenhuma pendência aberta ✓")

    L += ["", "## Última carteira registrada no ledger (descritivo)"]
    if state["top_convictions"]:
        L.append(f"- run `{state['last_run']}` — quintil superior:")
        for tk, rank, sig, ed, ep in state["top_convictions"]:
            ep_s = f"{ep:.2f}" if isinstance(ep, (int, float)) else "pendente"
            L.append(f"  - {rank:>2}. {tk} — sinal {sig:.3f} | exec {ed or 'pendente'} @ {ep_s}")
    else:
        L.append("- (nenhuma decisão registrada ainda)")
    L.append("")
    return "\n".join(L)


def write_brief(conn, out_dir=None, stamp="adhoc"):
    """Gera o briefing em reports/ai/. SOMENTE-LEITURA no banco. Retorna o Path."""
    out = pathlib.Path(out_dir) if out_dir else ROOT / "reports" / "ai"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"brief_{stamp}.md"
    path.write_text(build_brief(gather(conn)), encoding="utf-8")
    return path


def main():
    import db
    conn = db.get_connection()
    try:
        print(f"briefing: {write_brief(conn)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
