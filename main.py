"""predictor-stocks — ponto de entrada.

Uso:
    python main.py            # status do projeto (somente leitura)

Os comandos de pipeline nascem com os marcos:
    M1: python main.py ingest <ano>     (bloqueado: layout oficial COTAHIST)
    M2: python main.py adjust
    M5: python main.py backtest
    M6: python main.py paper
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "vendor")]

# console Windows usa cp850 por default — acentos viram mojibake sem isto
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


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
    print(f"  universo       : top {cfg['universe']['top_n']} por liquidez, "
          f"janela {cfg['universe']['lookback_trading_days']} pregões")
    print(f"  fator          : {cfg['factor']['name']} "
          f"({cfg['factor']['lookback_days']}-{cfg['factor']['skip_days']})")
    print(f"  carteira       : {cfg['portfolio']['quantile']}, "
          f"{cfg['portfolio']['direction']}")
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

    print("\nmarcos           : M0 completo — M1 bloqueado (layout COTAHIST oficial)")
    print("testes           : python -m pytest tests/ -v")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        return status()
    cmd = args[0]
    blocked = {"ingest": "M1", "adjust": "M2", "backtest": "M5", "paper": "M6"}
    if cmd in blocked:
        print(f"comando '{cmd}' pertence ao marco {blocked[cmd]} — ainda não implementado.")
        print("Ver HANDOFF.md (próximos passos) e docs/DESIGN.md (§10, portões).")
        return 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
