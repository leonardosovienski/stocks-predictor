"""Schema e migração idempotente do predictor-stocks."""
import datetime
import json
import os
import pathlib
import sqlite3
import subprocess

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
    # domínio RJ (predictor-rj): reaproveita prices_raw/adjustments/quarantine
    # deste banco (mesmo COTAHIST, mesmo quote_factor, mesma disciplina de
    # aprovação humana) — tabelas novas, nenhuma existente é tocada.
    ("0004_rj_domain_schema", """
        -- universo PRIMEIRO, rally depois: uma linha por empresa que entrou
        -- em RJ com ação negociada na B3 — nunca filtrado por ter tido rally.
        CREATE TABLE IF NOT EXISTS rj_universe (
            ticker              TEXT    PRIMARY KEY,
            company_name        TEXT    NOT NULL,
            rj_request_date     TEXT    NOT NULL,
            rj_process_number   TEXT,
            plan_presented_date TEXT,
            plan_approved_date  TEXT,
            rj_end_date         TEXT,
            delisted_date       TEXT,
            source              TEXT    NOT NULL,
            approved_by         TEXT,
            notes               TEXT,
            inserted_at         TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- episódios: fundo -> outcome. is_primary=1 é a unidade estatística
        -- principal (empresa->episódios); demais entram como secundário.
        CREATE TABLE IF NOT EXISTS rj_episodes (
            id                  INTEGER PRIMARY KEY,
            ticker              TEXT    NOT NULL REFERENCES rj_universe(ticker),
            trough_date         TEXT    NOT NULL,
            trough_price        REAL    NOT NULL,
            is_primary          INTEGER NOT NULL DEFAULT 1,
            outcome             TEXT,
            rally_pct           REAL,
            rally_date          TEXT,
            trading_days_to_rally INTEGER,
            censored            INTEGER NOT NULL DEFAULT 0,
            inserted_at         TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(ticker, trough_date)
        );

        -- eventos discretos (fato relevante, entrada de investidor >=5%).
        -- known_at != event_date: um evento só existe para decisão simulada
        -- em D se known_at <= D (anti-lookahead informacional).
        CREATE TABLE IF NOT EXISTS rj_events (
            id          INTEGER PRIMARY KEY,
            ticker      TEXT    NOT NULL REFERENCES rj_universe(ticker),
            event_date  TEXT    NOT NULL,
            published_at TEXT,
            known_at    TEXT    NOT NULL,
            event_type  TEXT    NOT NULL,
            source      TEXT    NOT NULL,
            approved_by TEXT,
            notes       TEXT,
            inserted_at TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_rj_events_ticker_known ON rj_events(ticker, known_at);

        -- scores por família, um valor por episódio
        CREATE TABLE IF NOT EXISTS rj_family_scores (
            episode_id  INTEGER NOT NULL REFERENCES rj_episodes(id),
            family      TEXT    NOT NULL,
            value       REAL,
            computed_at TEXT    NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (episode_id, family)
        );
    """),
    # retratos datados da lista pública de emissores em RJ (ingest_rj_universe)
    # — anti-viés de sobrevivência DO UNIVERSO: a lista da B3 é um retrato de
    # hoje; sem snapshots, quem saiu (falência/encerramento/deslistagem)
    # desaparece do universo histórico — o viés proibido pelo protocolo §3.
    ("0005_rj_universe_snapshots", """
        CREATE TABLE IF NOT EXISTS rj_universe_snapshots (
            snapshot_date TEXT    NOT NULL,
            source        TEXT    NOT NULL,
            ticker        TEXT    NOT NULL,
            company_name  TEXT    NOT NULL,
            payload_hash  TEXT    NOT NULL,
            raw_payload   TEXT,
            inserted_at   TEXT    NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (snapshot_date, source, ticker)
        );
    """),
    ("0006_rj_secondary_outcome", """
        ALTER TABLE rj_episodes ADD COLUMN secondary_outcome TEXT;
        ALTER TABLE rj_episodes ADD COLUMN secondary_rally_pct REAL;
        ALTER TABLE rj_episodes ADD COLUMN secondary_rally_date TEXT;
        ALTER TABLE rj_episodes ADD COLUMN secondary_trading_days_to_rally INTEGER;
        ALTER TABLE rj_episodes ADD COLUMN secondary_censored INTEGER;
    """),
    ("0007_fundamentals", """
        -- Demonstrações financeiras padronizadas (DFP/ITR da CVM) — insumo
        -- da futura H7 (fator de qualidade: ROE/alavancagem). Domínio
        -- INDEPENDENTE de ações/RJ (não referencia prices_raw/rj_*); um
        -- ticker+ref_date por linha, append-only via UNIQUE(ticker,ref_date).
        CREATE TABLE IF NOT EXISTS fundamentals (
            id                  INTEGER PRIMARY KEY,
            ticker              TEXT    NOT NULL,
            ref_date            TEXT    NOT NULL,      -- DT_REFER (fim do exercício/trimestre)
            ativo_total         REAL,
            passivo_total       REAL,
            patrimonio_liquido  REAL,
            lucro_liquido       REAL,
            roe                 REAL,                  -- lucro_liquido / patrimonio_liquido
            leverage            REAL,                  -- passivo_total / ativo_total
            source              TEXT    NOT NULL,       -- 'CVM DFP <ano>' / 'CVM ITR <ano>'
            inserted_at         TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(ticker, ref_date, source)
        );
        CREATE INDEX IF NOT EXISTS idx_fundamentals_ticker_ref
            ON fundamentals(ticker, ref_date);
    """),
    ("0008_rj_company_censoring", """
        -- Empresas aprovadas sem nenhum candidato a fundo não podem sumir do
        -- denominador. A observação é separada de rj_episodes porque não existe
        -- trough_date legítima para usar como episódio.
        CREATE TABLE IF NOT EXISTS rj_company_observations (
            ticker              TEXT NOT NULL REFERENCES rj_universe(ticker),
            asof                TEXT NOT NULL,
            rj_request_date     TEXT NOT NULL,
            observed_trading_days INTEGER NOT NULL,
            censoring_horizon_trading_days INTEGER NOT NULL,
            status              TEXT NOT NULL CHECK(status IN ('censored','no_candidate_control')),
            inserted_at         TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (ticker, asof)
        );
    """),
    ("0009_dividends", """
        -- Proventos (dividendos/JCP) para a série de retorno TOTAL (preço +
        -- reinvestimento) — corrige o viés só-preço declarado em H1-H10.
        -- Fonte: FRE da CVM (fre_cia_aberta_distribuicao_dividendos_classe_acao),
        -- não a data-ex real (não capturada por este dataset) — ver
        -- ingest_cvm.ingest_fre_dividends_year para as duas aproximações
        -- declaradas (valor por ação via divisão pelo total de ações em
        -- circulação; ex_date = data de PAGAMENTO como proxy conservador,
        -- não a data-ex real). Domínio INDEPENDENTE de ações (não referencia
        -- prices_raw/adjustments); um ticker+ex_date+source por linha,
        -- append-only via UNIQUE.
        CREATE TABLE IF NOT EXISTS dividends (
            id                  INTEGER PRIMARY KEY,
            ticker              TEXT    NOT NULL,
            ex_date             TEXT    NOT NULL,   -- proxy: Data_Pagamento_Dividendo
            value_per_share     REAL    NOT NULL,
            source              TEXT    NOT NULL,   -- 'CVM FRE <ano>'
            inserted_at         TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(ticker, ex_date, source)
        );
        CREATE INDEX IF NOT EXISTS idx_dividends_ticker_exdate
            ON dividends(ticker, ex_date);
    """),
    ("0010_fundamentals_revenue", """
        -- Receita líquida (DRE, já baixada/parseada desde a H7 mas nunca
        -- extraída) — insumo da H12 (margem líquida) e H13 (crescimento de
        -- receita YoY), pré-registradas 2026-09-04. Append-only: nova coluna
        -- em `fundamentals`, migração 0007 intocada. `net_margin` gravado
        -- (mesmo padrão de roe/leverage, calculado uma vez na ingestão);
        -- crescimento YoY é calculado no sinal (precisa comparar 2 linhas),
        -- não faz sentido como coluna de uma linha só.
        ALTER TABLE fundamentals ADD COLUMN receita_liquida REAL;
        ALTER TABLE fundamentals ADD COLUMN net_margin REAL;
    """),
    ("0011_fundamentals_cashflow_shares", """
        -- Insumos de H17 (accruals) e H18/H19 (valor), pré-registradas
        -- 2026-09-04. Append-only: colunas novas em `fundamentals`,
        -- migrações 0007/0010 intocadas.
        --
        -- `fluxo_caixa_operacional`: conta 6.01 da DFC-MI consolidada
        -- (`dfp_cia_aberta_DFC_MI_con_YYYY.csv`) — arquivo que já vem DENTRO
        -- do zip DFP baixado desde a H7, mas que nunca foi aberto. É a
        -- primeira DEMONSTRAÇÃO nova ingerida desde o M2 (BPA/BPP/DRE):
        -- fluxo de caixa não é derivável de nenhuma das três.
        -- `accruals` gravado (mesmo padrão de roe/leverage/net_margin,
        -- calculado uma vez na ingestão).
        --
        -- `shares_outstanding`: quantidade total de ações do FRE. O parser
        -- já existia (`ingest_cvm.parse_fre_capital_total_rows`, usado para
        -- converter montante de provento em valor-por-ação) mas o valor era
        -- transitório, nunca persistido. Sem ele não há capitalização de
        -- mercado, logo não há múltiplo — é a peça que faltava para
        -- qualquer hipótese de VALOR.
        ALTER TABLE fundamentals ADD COLUMN fluxo_caixa_operacional REAL;
        ALTER TABLE fundamentals ADD COLUMN accruals REAL;
        ALTER TABLE fundamentals ADD COLUMN shares_outstanding REAL;
    """),
    ("0012_fundamentals_known_at", """
        -- `known_at`: data em que o documento FICOU PÚBLICO, OBSERVADA, não
        -- estimada. Vem do `DT_RECEB` do arquivo principal do FRE
        -- (`fre_cia_aberta_{ano}.csv`), casado por `ID_Documento` -> `ID_DOC`,
        -- então é por companhia E por versão do documento.
        --
        -- Por que existe (achado da ingestão real 2026-09-05, ver HANDOFF): o
        -- embargo fixo de 90 dias sobre `ref_date` erra em direções OPOSTAS
        -- antes e depois de 2023, porque `DT_REFER` do FRE é rótulo de
        -- exercício e não data do dado — no FRE 2023 a referência
        -- (2023-12-31) é POSTERIOR à entrega (2023-05-30). Somar dias a esse
        -- campo não produz nada interpretável.
        --
        -- Append-only: coluna nova, migrações 0007/0010/0011 intocadas.
        -- NULL = desconhecido, e o consumidor (`factor._fundamental_signals`)
        -- cai no embargo por `ref_date` — as linhas da DFP não têm known_at
        -- e continuam se comportando EXATAMENTE como antes, preservando
        -- H7/H9/H12/H13/H17 já julgadas ou pré-registradas.
        ALTER TABLE fundamentals ADD COLUMN known_at TEXT;
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
