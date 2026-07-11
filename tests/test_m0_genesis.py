"""M0 — testes de aceitação da Gênese.

Critérios: estrutura criada, migração roda, suíte verde.
"""
import pathlib
import sqlite3

ROOT = pathlib.Path(__file__).parent.parent  # paths em conftest.py


# ---------------------------------------------------------------------------
# vendor/predictor_core
# ---------------------------------------------------------------------------

def test_vendor_version_file_exists():
    version_file = ROOT / "vendor" / "predictor_core" / "VERSION"
    assert version_file.exists(), "VERSION não encontrado no vendor"
    content = version_file.read_text().strip()
    assert content, "VERSION está vazio"


def test_vendor_version_readable():
    import re

    from predictor_core import __version__
    assert __version__, "predictor_core.__version__ está vazio"
    # O carimbo do vendor é <semver>-<procedência>-<YYYYMMDD> (ex.: 0.7.0-vendored-20260616,
    # 0.8.0-redteam-20260625). O teste valida o FORMATO da provenância, não uma palavra fixa:
    # acoplar ao keyword 'vendored' quebrava quando o sync carimbou '-redteam-'. O que importa
    # é existir procedência datada, não qual a palavra.
    assert re.match(r"^\d+\.\d+\.\d+-[a-z0-9]+-\d{8}$", __version__), (
        f"__version__ deve ter carimbo de procedência <semver>-<tag>-<YYYYMMDD>: {__version__!r}")


def test_vendor_modules_importable():
    from predictor_core import net, obs, infra, stats  # noqa: F401


# ---------------------------------------------------------------------------
# infra — connect + WAL
# ---------------------------------------------------------------------------

def test_infra_connect_creates_db(tmp_path):
    from predictor_core import infra
    db = tmp_path / "test.db"
    conn = infra.connect(db)
    row = conn.execute("PRAGMA journal_mode").fetchone()
    assert row[0] == "wal", "WAL não ativado"
    conn.close()


def test_infra_migrations_idempotent(tmp_path):
    from predictor_core import infra
    db = tmp_path / "test.db"
    migrations = [
        ("001_foo", "CREATE TABLE IF NOT EXISTS foo (id INTEGER PRIMARY KEY);"),
    ]
    conn = infra.connect(db)
    infra.run_migrations(conn, migrations)
    infra.run_migrations(conn, migrations)  # segunda vez não deve falhar
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "foo" in tables
    assert "_migrations" in tables
    conn.close()


def test_infra_config_hash_deterministic():
    from predictor_core import infra
    params = {"top_n": 60, "quantile": "quintil", "cost": 0.0036}
    h1 = infra.config_hash(params)
    h2 = infra.config_hash(params)
    assert h1 == h2, "config_hash não é determinístico"
    assert len(h1) == 16


# ---------------------------------------------------------------------------
# db.py — schema completo
# ---------------------------------------------------------------------------

def test_db_get_connection_creates_schema(tmp_path):
    import db
    conn = db.get_connection(tmp_path / "stocks.db")
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    expected = {
        "prices_raw", "adjustments", "quarantine",
        "universe_snapshots", "decisions", "runs", "_migrations",
    }
    missing = expected - tables
    assert not missing, f"tabelas ausentes: {missing}"
    conn.close()


def test_db_schema_idempotent(tmp_path):
    import db
    path = tmp_path / "stocks.db"
    db.get_connection(path).close()
    db.get_connection(path).close()  # segunda abertura não deve falhar


def test_db_runs_has_params_frozen_until(tmp_path):
    """Coluna nomeada explicitamente no design §4 — congelamento de params do walk-forward."""
    import db
    conn = db.get_connection(tmp_path / "stocks.db")
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(runs)")}
    assert "params_frozen_until" in cols, f"colunas de runs: {cols}"
    conn.close()


def test_db_migration_upgrade_path(tmp_path):
    """Banco criado só com a migração 0001 deve receber a 0002 ao reconectar (append-only)."""
    import db
    from predictor_core import infra
    path = tmp_path / "stocks.db"
    conn = infra.connect(path)
    infra.run_migrations(conn, db.MIGRATIONS[:1])  # estado antigo: só 0001
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(runs)")}
    assert "params_frozen_until" not in cols
    conn.close()
    conn = db.get_connection(path)  # reconectar aplica o restante
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(runs)")}
    assert "params_frozen_until" in cols, "migração 0002 não foi aplicada no upgrade"
    conn.close()


def test_db_prices_raw_unique_constraint(tmp_path):
    import db
    conn = db.get_connection(tmp_path / "stocks.db")
    conn.execute("""
        INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,low,close,
                               volume_fin,qty,source_file)
        VALUES('2024-01-02','PETR4','02','010',28.5,29.0,28.0,28.8,1e7,350000,'COTAHIST_A2024.TXT')
    """)
    conn.commit()
    raised = False
    try:
        conn.execute("""
            INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,low,close,
                                   volume_fin,qty,source_file)
            VALUES('2024-01-02','PETR4','02','010',28.5,29.0,28.0,28.8,1e7,350000,'COTAHIST_A2024.TXT')
        """)
        conn.commit()
    except sqlite3.IntegrityError:
        raised = True
    assert raised, "UNIQUE(date,ticker,source_file) não está sendo aplicado"
    conn.close()


def test_db_decisions_write_once_semantics(tmp_path):
    """exec_price deve ser write-once: UPDATE com COALESCE não sobrescreve valor já preenchido."""
    import db
    conn = db.get_connection(tmp_path / "stocks.db")
    conn.execute("""
        INSERT INTO decisions(run_id,asof,ticker,signal_value,rank,conviction_band)
        VALUES('run_001','2024-01-31','PETR4',0.32,1,'quintil_superior')
    """)
    conn.commit()
    # preencher exec_price pela primeira vez
    conn.execute("""
        UPDATE decisions SET exec_price = COALESCE(exec_price, 29.10)
        WHERE run_id='run_001' AND asof='2024-01-31' AND ticker='PETR4'
    """)
    conn.commit()
    row = conn.execute("SELECT exec_price FROM decisions WHERE run_id='run_001'").fetchone()
    assert row[0] == 29.10
    # tentar sobrescrever com COALESCE — deve manter o original
    conn.execute("""
        UPDATE decisions SET exec_price = COALESCE(exec_price, 99.99)
        WHERE run_id='run_001' AND asof='2024-01-31' AND ticker='PETR4'
    """)
    conn.commit()
    row = conn.execute("SELECT exec_price FROM decisions WHERE run_id='run_001'").fetchone()
    assert row[0] == 29.10, "COALESCE sobrescreveu valor já preenchido — write-once quebrado"
    conn.close()


# ---------------------------------------------------------------------------
# stats — ci_mean e block_bootstrap
# ---------------------------------------------------------------------------

def test_stats_ci_mean_coverage():
    from predictor_core.stats import ci_mean
    import random
    rng = random.Random(0)
    data = [rng.gauss(5.0, 1.0) for _ in range(200)]
    lo, hi = ci_mean(data, confidence=0.95)
    assert lo < 5.0 < hi, f"IC 95% não cobre a verdade 5.0: [{lo:.3f}, {hi:.3f}]"


def test_stats_block_bootstrap_moving_reproducible():
    from predictor_core.stats import block_bootstrap_ci, sharpe
    returns = [0.001 * (i % 7 - 3) for i in range(200)]
    lo1, hi1, _ = block_bootstrap_ci(returns, sharpe, seed=42)
    lo2, hi2, _ = block_bootstrap_ci(returns, sharpe, seed=42)
    assert lo1 == lo2 and hi1 == hi2, "bootstrap não é reprodutível com mesma seed"


def test_stats_block_bootstrap_wider_than_iid_for_autocorrelated():
    """Para série AR(1) com autocorrelação alta, block bootstrap deve ter IC mais largo que iid."""
    from predictor_core.stats import block_bootstrap_ci, ci_mean
    import random
    rng = random.Random(99)
    # AR(1) com phi=0.7
    series = [0.0]
    for _ in range(499):
        series.append(0.7 * series[-1] + rng.gauss(0, 0.01))
    mean_stat = lambda s: sum(s) / len(s)
    lo_iid, hi_iid = ci_mean(series, confidence=0.95, seed=42)
    lo_blk, hi_blk, _ = block_bootstrap_ci(series, mean_stat, block_length=21, seed=42)
    width_iid = hi_iid - lo_iid
    width_blk = hi_blk - lo_blk
    assert width_blk > width_iid, (
        f"block bootstrap deveria ser mais largo que iid para AR(1): "
        f"block={width_blk:.6f}, iid={width_iid:.6f}"
    )


def test_stats_sharpe_sign():
    from predictor_core.stats import sharpe
    pos = [0.001] * 100
    neg = [-0.001] * 100
    assert sharpe(pos) > 0
    assert sharpe(neg) < 0


# ---------------------------------------------------------------------------
# config.yaml
# ---------------------------------------------------------------------------

def test_config_yaml_parseable():
    config_path = ROOT / "config.yaml"
    assert config_path.exists(), "config.yaml não encontrado"
    content = config_path.read_text(encoding="utf-8")
    assert "H1-FROZEN" in content, "parâmetros H1-FROZEN não encontrados no config"
    assert "top_n: 60" in content
    assert "test_start" in content


# ---------------------------------------------------------------------------
# HANDOFF.md
# ---------------------------------------------------------------------------

def test_handoff_exists_with_h1():
    handoff = ROOT / "HANDOFF.md"
    assert handoff.exists(), "HANDOFF.md não encontrado"
    content = handoff.read_text(encoding="utf-8")
    assert "H1" in content, "H1 não encontrada no HANDOFF.md"
    assert "Sharpe" in content, "critério Sharpe não encontrado no HANDOFF.md"
    assert "2018-01" in content, "janela de teste não encontrada no HANDOFF.md"
