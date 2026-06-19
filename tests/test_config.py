"""Testes do carregador de config (mini-parser stdlib) e dos helpers de runs."""
import pathlib

import pytest

ROOT = pathlib.Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# parse_simple_yaml — o subconjunto suportado
# ---------------------------------------------------------------------------

def test_parse_sections_and_scalars():
    from config import parse_simple_yaml
    cfg = parse_simple_yaml(
        'universe:\n'
        '  top_n: 60          # comentário\n'
        '  freq: monthly\n'
        'execution:\n'
        '  fee: 0.0003\n'
        '  start: "2018-01-01"\n'
        '  enabled: true\n'
    )
    assert cfg["universe"]["top_n"] == 60
    assert cfg["universe"]["freq"] == "monthly"
    assert cfg["execution"]["fee"] == 0.0003
    assert cfg["execution"]["start"] == "2018-01-01"  # aspas → string, não data-mágica
    assert cfg["execution"]["enabled"] is True


def test_parse_comment_inside_quotes_preserved():
    from config import parse_simple_yaml
    cfg = parse_simple_yaml('section:\n  note: "valor com # dentro"\n')
    assert cfg["section"]["note"] == "valor com # dentro"


def test_parse_rejects_lists():
    from config import parse_simple_yaml
    with pytest.raises(ValueError):
        parse_simple_yaml("section:\n  - item\n")


def test_parse_rejects_deep_nesting():
    from config import parse_simple_yaml
    with pytest.raises(ValueError):
        parse_simple_yaml("a:\n  b:\n")  # chave indentada sem valor = nível 3


# ---------------------------------------------------------------------------
# load_config — o config.yaml real do projeto
# ---------------------------------------------------------------------------

def test_load_real_config_h1_frozen_params():
    """Os parâmetros H1-FROZEN do config devem bater com o design §5–§9 um a um."""
    from config import load_config
    cfg = load_config()
    assert cfg["universe"]["top_n"] == 60
    assert cfg["universe"]["lookback_trading_days"] == 126
    assert cfg["universe"]["min_history_days"] == 252
    assert cfg["factor"]["lookback_days"] == 252
    assert cfg["factor"]["skip_days"] == 21
    assert cfg["portfolio"]["quantile"] == "top_quintile"
    assert cfg["portfolio"]["direction"] == "long_only"
    assert cfg["execution"]["b3_fee_pct"] == 0.0003
    assert cfg["execution"]["spread_slippage_pct"] == 0.0015
    assert cfg["backtest"]["warmup_end"] == "2017-12-31"
    assert cfg["backtest"]["test_start"] == "2018-01-01"
    assert cfg["bootstrap"]["block_length"] == 21
    assert cfg["jump_detector"]["threshold_abs"] == 0.30


def test_config_hash_stable_across_loads():
    from config import load_config, config_hash
    h1 = config_hash(load_config())
    h2 = config_hash(load_config())
    assert h1 == h2


# ---------------------------------------------------------------------------
# db.new_run — reprodutibilidade por run_id + config_hash
# ---------------------------------------------------------------------------

def test_new_run_creates_row(tmp_path):
    import db
    conn = db.get_connection(tmp_path / "stocks.db")
    run_id = db.new_run(conn, {"top_n": 60}, notes="teste",
                        params_frozen_until="2018-01-01")
    row = conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
    assert row is not None
    assert row["config_hash"]
    assert row["code_version"]
    assert row["params_frozen_until"] == "2018-01-01"
    assert '"top_n": 60' in row["params_json"]
    conn.close()


def test_new_run_same_params_same_config_hash(tmp_path):
    import db
    conn = db.get_connection(tmp_path / "stocks.db")
    r1 = db.new_run(conn, {"a": 1})
    r2 = db.new_run(conn, {"a": 1})
    rows = conn.execute(
        "SELECT run_id, config_hash FROM runs WHERE run_id IN (?,?)", (r1, r2)
    ).fetchall()
    assert len(rows) == 2, "run_ids devem ser únicos mesmo com params iguais"
    assert rows[0]["config_hash"] == rows[1]["config_hash"]
    conn.close()


# ---------------------------------------------------------------------------
# net.sha256_file
# ---------------------------------------------------------------------------

def test_sha256_file_known_value(tmp_path):
    from predictor_core.net import sha256_file
    f = tmp_path / "x.txt"
    f.write_bytes(b"abc")
    # sha256("abc") — vetor de teste conhecido (FIPS 180-2)
    assert sha256_file(f) == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


# ---------------------------------------------------------------------------
# docs/DESIGN.md presente no repo (o HANDOFF referencia §§ dele)
# ---------------------------------------------------------------------------

def test_main_status_runs():
    """python main.py deve rodar limpo (exit 0) e mostrar o config_hash."""
    import subprocess
    import sys as _sys
    out = subprocess.run(
        [_sys.executable, str(ROOT / "main.py")],
        capture_output=True, text=True, timeout=60, encoding="utf-8",
    )
    assert out.returncode == 0, f"main.py falhou:\n{out.stderr}"
    assert "config_hash" in out.stdout


def test_main_backtest_command_runs(tmp_path):
    """backtest roda (M5 implementado) e sai 0 mesmo com banco vazio (inconclusivo).

    ISOLADO: aponta para um banco temporário vazio via $STOCKS_DB_PATH em vez do
    banco de produção. Antes, este teste lia data/stocks.db (estado mutável) e
    estourava o timeout assim que dados reais (COTAHIST 2024+) eram ingeridos —
    acoplamento a estado externo que dava falsa confiança. Eventos de telemetria
    vão para um JSONL temporário para não sujar a árvore de trabalho.
    """
    import os
    import subprocess
    import sys as _sys
    env = {
        **os.environ,
        "STOCKS_DB_PATH": str(tmp_path / "empty.db"),
        "PREDICTOR_EVENTS_PATH": str(tmp_path / "events.jsonl"),
    }
    out = subprocess.run(
        [_sys.executable, str(ROOT / "main.py"), "backtest"],
        capture_output=True, text=True, timeout=60, encoding="utf-8", env=env,
    )
    assert out.returncode == 0, f"main.py backtest falhou:\n{out.stderr}"
    assert "M5" not in out.stdout                       # não é mais 'bloqueado'


def test_main_unknown_command_exits_nonzero():
    import subprocess
    import sys as _sys
    out = subprocess.run(
        [_sys.executable, str(ROOT / "main.py"), "naoexiste"],
        capture_output=True, text=True, timeout=60, encoding="utf-8",
    )
    assert out.returncode != 0


def test_design_doc_in_repo():
    design = ROOT / "docs" / "DESIGN.md"
    assert design.exists(), "docs/DESIGN.md ausente — o HANDOFF referencia seções dele"
    content = design.read_text(encoding="utf-8")
    assert "H1" in content and "COTAHIST" in content


# ---------------------------------------------------------------------------
# frozen_config_hash — o lacre da H1 por MÁQUINA (não por comentário [H1-FROZEN])
# ---------------------------------------------------------------------------

def test_frozen_config_hash_golden():
    """Golden: qualquer mudança em param H1-FROZEN quebra este lacre."""
    from config import load_config, frozen_config_hash
    assert frozen_config_hash(load_config()) == "4a4e8d57e1224191"


def test_frozen_hash_ignores_operational_params():
    import copy
    from config import load_config, frozen_config_hash
    cfg = load_config()
    base = frozen_config_hash(cfg)
    op = copy.deepcopy(cfg)
    op["data"]["db_path"] = "outro.db"
    op["bootstrap"]["seed"] = 999
    op["bootstrap"]["method"] = "stationary"
    assert frozen_config_hash(op) == base, "param operacional não pode mover o lacre"


def test_frozen_hash_breaks_on_frozen_param():
    import copy
    from config import load_config, frozen_config_hash
    cfg = load_config()
    base = frozen_config_hash(cfg)
    fr = copy.deepcopy(cfg)
    fr["universe"]["top_n"] = 61
    assert frozen_config_hash(fr) != base, "mexer num param frozen DEVE mover o lacre"
