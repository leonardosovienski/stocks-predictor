"""stocks-predictor — ponto de entrada legado do domínio cross-sectional.

Uso:
    python main.py                          # status do projeto (somente leitura)
    python main.py ingest <COTAHIST.ZIP>    # M1: parse posicional -> prices_raw
    python main.py adjust                    # M2: detector de saltos -> quarentena
    python main.py universe <YYYY-MM-DD>     # M3: materializa o universo point-in-time
    python main.py backtest                  # M5: walk-forward + pedágio -> veredito H1
    python main.py attest-power              # H2+: controle positivo + atestado + trials
    python main.py backtest-h2               # H2: walk-forward baixa-vol + pedágio + DSR
    python main.py backtest-h4               # H4: sizing 1/vol + pedágio + DSR + drawdown
    python main.py backtest-h5               # H5: reversão 21d + pedágio + DSR
    python main.py paper <YYYY-MM-DD>        # M6: registra carteira forward + liquida exec
    python main.py analyst [rótulo]          # §9b: briefing consultivo read-only (reports/ai/)
    python main.py splits-review [saída.csv] # M2: exporta candidatos a split p/ revisão humana
    python main.py splits-import <csv>       # M2: grava em adjustments só as linhas aprovadas
"""
import os
import pathlib
import sys
from contextlib import closing

ROOT = pathlib.Path(__file__).parent
# O código de domínio continua com imports planos por compatibilidade histórica,
# mas Core/Ops vêm do ambiente/package manager. vendor/ não participa do runtime.
sys.path.insert(0, str(ROOT / "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _db_path(cfg):
    """Path do banco: override de teste (db.DB_PATH_ENV) > config. A mesma env é
    honrada dentro de db.get_connection para os entry points que não passam path."""
    import db
    override = os.getenv(db.DB_PATH_ENV)
    return pathlib.Path(override) if override else ROOT / cfg["data"]["db_path"]


def _conn():
    import config as cfg_mod
    import db
    cfg = cfg_mod.load_config()
    return cfg, db.get_connection(_db_path(cfg))


def status() -> int:
    from predictor_core import __version__ as core_version
    import config as cfg_mod
    import db

    print("=" * 60)
    print("stocks-predictor — status")
    print("=" * 60)
    print(f"\ncore compartilhado: {core_version}")
    print(f"code_version      : {db.get_code_version()}")

    cfg = cfg_mod.load_config()
    print(f"config_hash       : {cfg_mod.config_hash(cfg)}")
    print(f"frozen_hash (H1)  : {cfg_mod.frozen_config_hash(cfg)}")
    print(f"frozen_hash (H2)  : {cfg_mod.h2_frozen_config_hash(cfg)}")
    print(f"frozen_hash (H4)  : {cfg_mod.h4_frozen_config_hash(cfg)}")
    print(f"frozen_hash (H5)  : {cfg_mod.h5_frozen_config_hash(cfg)}")
    print(f"  universo       : top {cfg['universe']['top_n']} por liquidez, "
          f"janela {cfg['universe']['lookback_trading_days']} pregões")
    print(f"  fator          : {cfg['factor']['name']} "
          f"({cfg['factor']['lookback_days']}-{cfg['factor']['skip_days']})")
    print(f"  carteira       : {cfg['portfolio']['quantile']}, {cfg['portfolio']['direction']}")
    print(f"  custo roundtrip: ~{2 * (cfg['execution']['b3_fee_pct'] + cfg['execution']['spread_slippage_pct']) * 100:.2f}%")

    db_path = _db_path(cfg)
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

    import trials_gate
    reg_trials = trials_gate.trials_path_from(cfg)
    if reg_trials.exists():
        import json
        ts = json.loads(reg_trials.read_text(encoding="utf-8"))
        print(f"\ntrials (DSR)     : {len(ts)} tentativa(s) registrada(s) — "
              + ", ".join(t["name"] for t in ts))
    else:
        print("\ntrials (DSR)     : registro ainda não criado (rode attest-power)")

    print("\nmarcos           : M1–M6 completos. H1/H2/H4/H5 julgadas — nenhuma "
          "comprovada (ver HANDOFF).")
    print("testes           : uv run pytest -q")
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
    with closing(conn):
        thr = float(cfg.get("jump_detector", {}).get("threshold_abs", 0.30))
        n = adjust.scan_and_quarantine(conn, thr)
        print(f"quarentena: {n} salto(s) sem ajuste registrado (|r| > {thr:.0%})")
    return 0


def cmd_universe(args) -> int:
    """M3 — materializa o universo point-in-time num asof."""
    import universe
    if not args:
        print("uso: python main.py universe <asof YYYY-MM-DD>")
        return 1
    cfg, conn = _conn()
    with closing(conn):
        u = cfg["universe"]
        uni = universe.materialize_snapshot(
            conn, args[0], u["top_n"], u["lookback_trading_days"], u["min_history_days"])
        extra = "..." if len(uni) > 10 else ""
        print(f"universo em {args[0]}: {len(uni)} papéis — {', '.join(uni[:10])}{extra}")
    return 0


def cmd_backtest(args) -> int:
    """M5 — walk-forward + pedágio de 2 lentes -> veredito da H1 + relatório."""
    import backtest
    import db
    cfg, conn = _conn()
    with closing(conn):
        # params = o CONFIG REAL: runs.config_hash tem que identificar os parâmetros
        # que a rodada usou (reprodutível por run_id+config_hash, §11) — nunca um
        # marcador constante.
        run_id = db.new_run(conn, cfg, notes="veredito H1 (backtest)")
        backtest.run(cfg=cfg, conn=conn, write_report=True, run_id=run_id)
    return 0


def cmd_attest_power(args) -> int:
    """H2+ — controle positivo do pedágio (harness) + atestado + trials baseline.

    Prova que o judge REAL detecta edge plantado e rejeita ruído; grava o
    atestado irmão do trials.json e registra as tentativas (H1 retroativa +
    H2 pendente). Sem isso, nenhum veredito da H2 é interpretável."""
    import config as cfg_mod
    import trials_gate
    cfg = cfg_mod.load_config()
    rec = trials_gate.attest(cfg)
    print(f"controle positivo OK (sensibilidade + especificidade) — "
          f"atestado emitido em {rec['passed_at']} (metric={rec['metric']})")
    reg = trials_gate.register_baseline_trials(cfg)
    names = [t["name"] for t in reg.load()]
    print(f"trials registradas em {reg.path}: {', '.join(names)}")
    return 0


def cmd_backtest_h2(args) -> int:
    """H2 — walk-forward baixa-vol + pedágio + DSR -> veredito da H2 + relatório."""
    import backtest
    import db
    import trials_gate
    cfg, conn = _conn()
    with closing(conn):
        # trava de poder: a criação das trials exige o atestado do harness
        trials_gate.register_baseline_trials(cfg)
        run_id = db.new_run(conn, cfg, notes="veredito H2 (baixa volatilidade)")
        backtest.run_h2(cfg=cfg, conn=conn, write_report=True, run_id=run_id)
    return 0


def cmd_backtest_h4(args) -> int:
    """H4 — sizing 1/vol + pedágio + DSR (N=3) + drawdown -> veredito da H4."""
    import backtest
    import db
    import trials_gate
    from config import H4_FROZEN_KEYS
    cfg, conn = _conn()
    with closing(conn):
        # trava de poder: criação de trial exige o atestado do harness
        trials_gate.register_baseline_trials(cfg)
        trials_gate.register_hypothesis(
            cfg, "h4-invvol-sizing-252", H4_FROZEN_KEYS,
            "pré-registro 2026-07-18 (HANDOFF); sharpe preenchido pela rodada única")
        run_id = db.new_run(conn, cfg, notes="veredito H4 (sizing volatility targeting)")
        backtest.run_h4(cfg=cfg, conn=conn, write_report=True, run_id=run_id)
    return 0


def cmd_backtest_h5(args) -> int:
    """H5 — reversão 21d + pedágio + DSR (N=4) -> veredito da H5."""
    import backtest
    import db
    import trials_gate
    from config import H5_FROZEN_KEYS
    cfg, conn = _conn()
    with closing(conn):
        # trava de poder: criação de trial exige o atestado do harness
        trials_gate.register_baseline_trials(cfg)
        trials_gate.register_hypothesis(
            cfg, "h5-strev-21", H5_FROZEN_KEYS,
            "pré-registro 2026-07-18 (HANDOFF); sharpe preenchido pela rodada única")
        run_id = db.new_run(conn, cfg, notes="veredito H5 (reversão de curto prazo)")
        backtest.run_h5(cfg=cfg, conn=conn, write_report=True, run_id=run_id)
    return 0


def cmd_paper(args) -> int:
    """M6 — registra a carteira forward (anti-tautologia) e liquida execuções."""
    import db
    import paper
    if not args:
        print("uso: python main.py paper <asof YYYY-MM-DD>")
        return 1
    cfg, conn = _conn()
    with closing(conn):
        run_id = db.new_run(conn, {"command": "paper", "asof": args[0], "config": cfg},
                            notes="paper forward")
        n = paper.record_forward(conn, cfg, args[0], run_id)
        filled = paper.settle_executions(conn, cfg)
        print(f"paper {args[0]}: {n} decisões registradas (run {run_id}); "
              f"{filled} execução(ões) liquidada(s)")
    return 0


def _anchor(path_str: str) -> pathlib.Path:
    """Path relativo é ancorado na raiz do repo (comandos rodam de qualquer cwd)."""
    p = pathlib.Path(path_str)
    return p if p.is_absolute() else ROOT / p


def cmd_splits_review(args) -> int:
    """M2 — exporta candidatos a split/grupamento (quarentena c/ proporção redonda) p/ CSV."""
    import adjust
    cfg, conn = _conn()
    with closing(conn):
        out = _anchor(args[0] if args else "reports/splits_candidates.csv")
        out.parent.mkdir(parents=True, exist_ok=True)
        n = adjust.export_candidates_csv(conn, out)
        print(f"{n} candidato(s) exportado(s) para {out} — preencha source/approved_by e "
              f"rode 'splits-import {out}'")
    return 0


def cmd_splits_import(args) -> int:
    """M2 — grava em `adjustments` só as linhas do CSV com source+approved_by preenchidos."""
    import adjust
    if not args:
        print("uso: python main.py splits-import <caminho_do_csv_revisado>")
        return 1
    cfg, conn = _conn()
    with closing(conn):
        n = adjust.import_approved_adjustments(conn, _anchor(args[0]))
        print(f"{n} ajuste(s) aprovado(s) gravado(s) em adjustments a partir de {args[0]}")
    return 0


def cmd_analyst(args) -> int:
    """Analista somente-leitura (§9b) — briefing consultivo em reports/ai/."""
    import analyst
    cfg, conn = _conn()
    with closing(conn):
        stamp = args[0] if args else "adhoc"
        path = analyst.write_brief(conn, stamp=stamp)
        print(f"briefing consultivo (read-only): {path}")
    return 0


_COMMANDS = {
    "status": lambda a: status(),
    "ingest": cmd_ingest,
    "adjust": cmd_adjust,
    "universe": cmd_universe,
    "backtest": cmd_backtest,
    "attest-power": cmd_attest_power,
    "backtest-h2": cmd_backtest_h2,
    "backtest-h4": cmd_backtest_h4,
    "backtest-h5": cmd_backtest_h5,
    "paper": cmd_paper,
    "analyst": cmd_analyst,
    "splits-review": cmd_splits_review,
    "splits-import": cmd_splits_import,
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
