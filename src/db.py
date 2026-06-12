"""Schema e migração idempotente do predictor-stocks."""
import pathlib
import sqlite3
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "vendor"))
from predictor_core import infra

DB_DEFAULT = pathlib.Path(__file__).parent.parent / "data" / "stocks.db"

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
]


def get_connection(db_path: pathlib.Path | str | None = None,
                   busy_timeout_ms: int = 5000) -> sqlite3.Connection:
    path = pathlib.Path(db_path) if db_path else DB_DEFAULT
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = infra.connect(path, busy_timeout_ms=busy_timeout_ms)
    infra.run_migrations(conn, MIGRATIONS)
    return conn
