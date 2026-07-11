"""predictor-stocks — ponto de entrada.

Uso:
    python main.py                          # status do projeto (somente leitura)
    python main.py ingest <COTAHIST.ZIP>    # M1: parse posicional -> prices_raw
    python main.py adjust                    # M2: detector de saltos -> quarentena
    python main.py universe <YYYY-MM-DD>     # M3: materializa o universo point-in-time
    python main.py backtest                  # M5: walk-forward + pedágio -> veredito H1
    python main.py paper <YYYY-MM-DD>        # M6: registra carteira forward + liquida exec
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor")]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _conn():
    import config as cfg_mod
    import db
    cfg = cfg_mod.load_config()
    return cfg, db.get_connection(ROOT / cfg["data"]["db_path"])


def status() -> int:
    from predictor_core import __version__ as core_version
    import config as cfg_mod
    import db

    print("=" * 60)
    print("predictor-stocks — status")
    print("=" * 60)
    print(f"\ncore vendorizado : {core_version}")
    print(f"code_version     : {db.get_code_version()}")

    cfg = cfg_mod.load_config()
    print(f"config_hash      : {cfg_mod.config_hash(cfg)}")
    print(f"frozen_hash (H1) : {cfg_mod.frozen_config_hash(cfg)}")
    print(f"  universo       : top {cfg['universe']['top_n']} por liquidez, "
          f"janela {cfg['universe']['lookback_trading_days']} pregões")
    print(f"  fator          : {cfg['factor']['name']} "
          f"({cfg['factor']['lookback_days']}-{cfg['factor']['skip_days']})")
    print(f"  carteira       : {cfg['portfolio']['quantile']}, {cfg['portfolio']['direction']}")
    print(f"  custo roundtrip: ~{2 * (cfg['execution']['b3_fee_pct'] + cfg['execution']['spread_slippage_pct']) * 100:.2f}%")

    db_path = ROOT / cfg["data"]["db_path"]
    print(f"\nbanco            : {db_path} "
          f"({'existe' if db_path.exists() else 'será criado na 1ª conexão'})")
    conn = db.get_connection(db_path)
    print("tabela           | linhas")
    print("-" * 30)
    for table in ("prices_raw", "adjustments", "quarantine",
                  "universe_snapshots", "decisions", "runs"):
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:<17}| {n}")
    conn.close()

    print("\nmarcos           : M1–M6 implementados (núcleo). Veredito real da H1 exige COTAHIST real.")
    print("testes           : py -3.12 -m pytest tests/ -q")
    return 0


def cmd_ingest(args) -> int:
    """M1 — parse posicional do COTAHIST (ZIP) -> prices_raw."""
    import ingest_cotahist
    if not args:
        print("uso: python main.py ingest <caminho_para_COTAHIST_AXXXX.ZIP>")
        return 1
    n = ingest_cotahist.parse_cotahist(args[0])
    print(f"ingeridos {n} registros de cotação de {args[0]}")
    return 0


def cmd_adjust(args) -> int:
    """M2 — detector de saltos -> quarentena (salto sem ajuste registrado)."""
    import adjust
    cfg, conn = _conn()
    thr = float(cfg.get("jump_detector", {}).get("threshold_abs", 0.30))
    n = adjust.scan_and_quarantine(conn, thr)
    print(f"quarentena: {n} salto(s) sem ajuste registrado (|r| > {thr:.0%})")
    conn.close()
    return 0


def cmd_universe(args) -> int:
    """M3 — materializa o universo point-in-time num asof."""
    import universe
    if not args:
        print("uso: python main.py universe <asof YYYY-MM-DD>")
        return 1
    cfg, conn = _conn()
    u = cfg["universe"]
    uni = universe.materialize_snapshot(
        conn, args[0], u["top_n"], u["lookback_trading_days"], u["min_history_days"])
    extra = "..." if len(uni) > 10 else ""
    print(f"universo em {args[0]}: {len(uni)} papéis — {', '.join(uni[:10])}{extra}")
    conn.close()
    return 0


def cmd_backtest(args) -> int:
    """M5 — walk-forward + pedágio de 2 lentes -> veredito da H1."""
    import backtest
    backtest.run()
    return 0


def cmd_paper(args) -> int:
    """M6 — registra a carteira forward (anti-tautologia) e liquida execuções."""
    import db
    import paper
    if not args:
        print("uso: python main.py paper <asof YYYY-MM-DD>")
        return 1
    cfg, conn = _conn()
    run_id = db.new_run(conn, {"paper": True, "asof": args[0]}, notes="paper forward")
    n = paper.record_forward(conn, cfg, args[0], run_id)
    filled = paper.settle_executions(conn, cfg)
    print(f"paper {args[0]}: {n} decisões registradas (run {run_id}); {filled} execução(ões) liquidada(s)")
    conn.close()
    return 0


_COMMANDS = {
    "status": lambda a: status(),
    "ingest": cmd_ingest,
    "adjust": cmd_adjust,
    "universe": cmd_universe,
    "backtest": cmd_backtest,
    "paper": cmd_paper,
}


def main() -> int:
    args = sys.argv[1:]
    if not args:
        return status()
    handler = _COMMANDS.get(args[0])
    if handler is None:
        print(f"comando desconhecido: {args[0]}")
        print(__doc__)
        return 1
    return handler(args[1:])


if __name__ == "__main__":
    raise SystemExit(main())