"""Schema e migração idempotente do predictor-stocks."""
import datetime
import json
import os
import pathlib
import sqlite3
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "vendor"))
from predictor_core import infra

DB_DEFAULT = pathlib.Path(__file__).parent.parent / "data" / "stocks.db"
# override p/ isolar testes/experimentos do banco de produção (mesmo padrão do
# obs.EVENTS_ENV) — honrado AQUI, no ponto de resolução do default, para que TODO
# entry point (main.py, backtest.run(), paper.main, analyst.main, ingest) respeite.
DB_PATH_ENV = "PREDICTOR_DB_PATH"

# ---------------------------------------------------------------------------
# Migrações — append-only; nunca alterar uma existente, sempre adicionar nova
# ---------------------------------------------------------------------------

MIGRATIONS: list[tuple[str, str]] = [
    ("0001_initial_schema", """
        -- preços como publicados pela B3 — append-only, imutável
        CREATE TABLE IF NOT EXISTS prices_raw (
            id          INTEGER PRIMARY KEY,
            date        TEXT    NOT NULL,          -- YYYY-MM-DD
            ticker      TEXT    NOT NULL,
            bdi_code    TEXT    NOT NULL,
            market_type TEXT    NOT NULL,
            open        REAL    NOT NULL,
            high        REAL    NOT NULL,
            low         REAL    NOT NULL,
            close       REAL    NOT NULL,
            volume_fin  REAL    NOT NULL,
            qty         INTEGER NOT NULL,
            quote_factor INTEGER NOT NULL DEFAULT 1,
            source_file TEXT    NOT NULL,
            inserted_at TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(date, ticker, source_file)
        );
        CREATE INDEX IF NOT EXISTS idx_prices_raw_ticker_date ON prices_raw(ticker, date);

        -- fatores de ajuste (proventos, splits) — append-only, com fonte obrigatória
        CREATE TABLE IF NOT EXISTS adjustments (
            id          INTEGER PRIMARY KEY,
            ticker      TEXT    NOT NULL,
            ex_date     TEXT    NOT NULL,           -- YYYY-MM-DD
            factor      REAL    NOT NULL,           -- multiplicar preços anteriores
            type        TEXT    NOT NULL,           -- 'split','grupamento','dividendo','jcp','outro'
            source      TEXT    NOT NULL,           -- 'inferred','csv_manual','yfinance_xcheck'
            notes       TEXT,
            approved_by TEXT,                       -- null = pendente aprovação humana
            inserted_at TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(ticker, ex_date, type)
        );

        -- papéis em quarentena — salto sem ajuste explicado
        CREATE TABLE IF NOT EXISTS quarantine (
            id          INTEGER PRIMARY KEY,
            ticker      TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            reason      TEXT    NOT NULL,
            raw_return  REAL,                       -- retorno overnight que disparou
            resolved_at TEXT,
            resolution  TEXT,
            inserted_at TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(ticker, date)
        );

        -- universo point-in-time materializado
        CREATE TABLE IF NOT EXISTS universe_snapshots (
            asof_date   TEXT    NOT NULL,
            ticker      TEXT    NOT NULL,
            median_vol  REAL    NOT NULL,           -- mediana vol financeiro na janela
            rank        INTEGER NOT NULL,
            inserted_at TEXT    NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (asof_date, ticker)
        );

        -- ledger de decisões — parte EVAL (universal)
        CREATE TABLE IF NOT EXISTS decisions (
            id              INTEGER PRIMARY KEY,
            run_id          TEXT    NOT NULL,
            asof            TEXT    NOT NULL,       -- data do sinal (último pregão do mês)
            ticker          TEXT    NOT NULL,
            signal_value    REAL    NOT NULL,       -- momentum 12-1
            rank            INTEGER NOT NULL,
            conviction_band TEXT    NOT NULL,       -- 'quintil_superior','resto'
            frozen_mode     INTEGER NOT NULL DEFAULT 0,  -- 1=paper forward
            inserted_at     TEXT    NOT NULL DEFAULT (datetime('now')),
            -- parte RISK — preenchida na liquidação, write-once via COALESCE
            exec_date       TEXT,
            exec_price      REAL,
            exit_date       TEXT,
            exit_price      REAL,
            cost_paid       REAL,
            realized_return_net REAL,
            holding_days    INTEGER,
            UNIQUE(run_id, asof, ticker)
        );

        -- runs — registro de cada execução do pipeline
        CREATE TABLE IF NOT EXISTS runs (
            run_id          TEXT    PRIMARY KEY,
            config_hash     TEXT    NOT NULL,
            code_version    TEXT    NOT NULL,
            started_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            params_json     TEXT    NOT NULL,
            notes           TEXT
        );
    """),
    # params_frozen_until: walk-forward congela parâmetros até esta data (design §4/§8)
    ("0002_runs_params_frozen_until", """
        ALTER TABLE runs ADD COLUMN params_frozen_until TEXT;
    """),
    # filtro à-vista na camada de leitura (universe/backtest) usa market_type como
    # predicado — sem índice, cada consulta de calendário viraria full scan da tabela
    ("0003_idx_prices_raw_market_type_date", """
        CREATE INDEX IF NOT EXISTS idx_prices_raw_mkt_date
            ON prices_raw(market_type, date);
    """),
]


def price_expr(col: str) -> str:
    """Expressão SQL do preço POR AÇÃO: coluna ÷ quote_factor (FATCOT da B3).

    COTAHIST cota papéis em lote (fator 10/100/1000/1000000) — o preço cru fica
    na escala do lote. A correção é na LEITURA (decisão do operador 2026-07-18):
    `prices_raw` permanece o espelho intocável do arquivo. CASE defende contra
    fator <= 0 hipotético (divisão por zero em SQLite viraria NULL silencioso)."""
    return f"{col} * 1.0 / (CASE WHEN quote_factor > 0 THEN quote_factor ELSE 1 END)"


def get_connection(db_path: pathlib.Path | str | None = None,
                   busy_timeout_ms: int = 5000) -> sqlite3.Connection:
    path = pathlib.Path(db_path or os.getenv(DB_PATH_ENV) or DB_DEFAULT)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = infra.connect(path, busy_timeout_ms=busy_timeout_ms)
    infra.run_migrations(conn, MIGRATIONS)
    return conn


def get_code_version() -> str:
    """Hash curto do git HEAD; 'unknown' fora de um checkout (ex.: cópia em rede limpa)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=pathlib.Path(__file__).parent, capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def new_run(conn: sqlite3.Connection, params: dict, notes: str | None = None,
            params_frozen_until: str | None = None) -> str:
    """Registra uma execução em `runs` e retorna o run_id.

    run_id = timestamp UTC + prefixo do config_hash — único, ordenável, rastreável.
    """
    cfg_hash = infra.config_hash(params)
    now = datetime.datetime.now(datetime.timezone.utc)
    # microsegundos no run_id: duas runs no mesmo segundo não podem colidir
    run_id = now.strftime("%Y%m%dT%H%M%S%f") + "-" + cfg_hash[:6]
    conn.execute(
        """INSERT INTO runs(run_id, config_hash, code_version, params_json,
                            notes, params_frozen_until)
           VALUES(?,?,?,?,?,?)""",
        (run_id, cfg_hash, get_code_version(),
         json.dumps(params, sort_keys=True, ensure_ascii=True),
         notes, params_frozen_until),
    )
    conn.commit()
    return run_id
