from pathlib import Path
import re

ROOT = Path(__file__).parent / 'stocks-predictor'

def transform(rel, function):
    path = ROOT / rel
    path.write_text(function(path.read_text(encoding='utf-8')), encoding='utf-8')

migration = '''    ("0013_verified_derivations", """
        -- New derivations only. Historical raw data, fundamentals and ledgers remain intact.
        CREATE TABLE fundamentals_pit (
            ticker TEXT NOT NULL, cnpj TEXT NOT NULL, ref_date TEXT NOT NULL,
            document_version INTEGER NOT NULL CHECK(document_version>0),
            received_at TEXT NOT NULL, available_at TEXT NOT NULL,
            source TEXT NOT NULL, source_sha256 TEXT NOT NULL,
            ativo_total REAL, passivo_total REAL, patrimonio_liquido REAL,
            lucro_liquido REAL, receita_liquida REAL, fluxo_caixa_operacional REAL,
            roe REAL, leverage REAL, net_margin REAL, accruals REAL,
            CHECK(available_at>received_at),
            UNIQUE(ticker,cnpj,ref_date,document_version,source_sha256)
        );
        CREATE INDEX idx_fundamentals_pit ON fundamentals_pit(ticker,available_at,ref_date);
        CREATE TABLE shares_pit (
            ticker TEXT NOT NULL, ref_date TEXT NOT NULL, document_id TEXT NOT NULL,
            received_at TEXT NOT NULL, available_at TEXT NOT NULL,
            shares_outstanding REAL NOT NULL CHECK(shares_outstanding>0),
            basis_date TEXT, basis_source TEXT, price_basis_source TEXT,
            source TEXT NOT NULL, source_sha256 TEXT NOT NULL,
            CHECK(available_at>received_at),
            CHECK(basis_date IS NULL OR (basis_date<=received_at AND basis_source IS NOT NULL)),
            UNIQUE(ticker,document_id,source_sha256)
        );
        CREATE INDEX idx_shares_pit ON shares_pit(ticker,available_at);
        CREATE TABLE cash_events (
            ticker TEXT NOT NULL, event_id TEXT NOT NULL, ex_date TEXT NOT NULL,
            payment_date TEXT NOT NULL, value_per_share REAL NOT NULL CHECK(value_per_share>0),
            source TEXT NOT NULL, source_sha256 TEXT NOT NULL,
            CHECK(payment_date>=ex_date), UNIQUE(ticker,event_id)
        );
        CREATE TABLE cash_event_coverage (
            ticker TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL,
            source TEXT NOT NULL, source_sha256 TEXT NOT NULL,
            CHECK(end_date>=start_date), UNIQUE(ticker,start_date,end_date)
        );
    """),
'''
transform('stocks_predictor/db.py', lambda s: s.replace('\n]\n', '\n'+migration+']\n', 1))

# Keep old parsers accessible solely by an explicit historical name. Public entrypoints
# now select the corrected derivations. This preserves forensic reproduction fixtures.
legacy_ingest = ['parse_dfp_statement_rows', 'parse_dfp_received_dates',
                 'ingest_dfp_year', 'ingest_fre_shares_year', 'ingest_fre_dividends_year']
def replace_words(text, names):
    for name in names:
        text = re.sub(r'\b'+name+r'\b', 'legacy_'+name, text)
    return text
transform('stocks_predictor/ingest_cvm.py', lambda s: replace_words(s, legacy_ingest) + '''

# Corrected public API. Legacy functions above only reproduce historical derivations.
def parse_dfp_statement_rows(rows, statement):
    from cvm_pit import statement_rows
    return statement_rows(rows, statement)


def parse_dfp_received_dates(zbytes, year):
    """Keys include document version; values are observed receipt dates."""
    from cvm_pit import dfp_received_dates
    return {key: dates[0] for key, dates in dfp_received_dates(zbytes, year).items()}


def ingest_dfp_year(conn, year, companies=None, ticker_of=None, zbytes=None):
    from cvm_pit import ingest_dfp
    return ingest_dfp(conn, year, companies, ticker_of, zbytes)


def ingest_fre_shares_year(conn, year, ticker_of=None, zbytes=None, *, basis_by_document=None):
    from cvm_pit import ingest_fre_shares
    return ingest_fre_shares(conn, year, ticker_of, zbytes, basis_by_document=basis_by_document)


def ingest_fre_dividends_year(conn, year, companies=None, ticker_of=None):
    raise ValueError("FRE payment-date/company-total proxy is not a total-return source. "
                     "Use cash_events.import_verified_events with per-ticker ex-dates and amounts.")
''')

legacy_factor = ['accruals_signals', 'earnings_yield_signals', 'book_to_market_signals',
                 '_value_signals', '_shares_with_ref_date', '_shares_on_price_base']
transform('stocks_predictor/factor.py', lambda s: replace_words(s, legacy_factor) + '''

# Current factors consume verified versioned derivations only, never the legacy table.
def accruals_signals(conn, tickers, asof, disclosure_embargo_days=90):
    from cvm_pit import fundamental_values
    return fundamental_values(conn, tickers, asof, "accruals")


def earnings_yield_signals(conn, tickers, asof, disclosure_embargo_days=90):
    from cvm_pit import value_signals
    return value_signals(conn, tickers, asof, "lucro_liquido")


def book_to_market_signals(conn, tickers, asof, disclosure_embargo_days=90):
    from cvm_pit import value_signals
    return value_signals(conn, tickers, asof, "patrimonio_liquido")


def _shares_on_price_base(conn, ticker, shares, basis_date, asof):
    from cvm_pit import shares_on_price_base
    return shares_on_price_base(conn, ticker, shares, basis_date, asof)
''')
transform('stocks_predictor/adjust.py', lambda s: replace_words(s, ['total_return_series']) + '''


def total_return_series(conn, ticker, *, asof=None):
    """Verified ex-date cash events, with explicit coverage and split-consistent units."""
    from cash_events import total_return_series as verified_series
    return verified_series(conn, ticker, asof=asof)
''')

def backtest_changes(s):
    s = replace_words(s, ['walk_forward'])
    s = s.replace('series_fn=adjust.total_return_series)', 'series_fn=adjust.legacy_total_return_series)')
    for num in (17,18,19):
        start = s.index(f'def run_h{num}(')
        end = s.index('\ndef ', start+1)
        s = s[:start] + f'''def run_h{num}(cfg=None, conn=None, write_report=False, run_id=None, trials_path=None):
    """Protected: corrected measurement needs a new preregistration before observation."""
    raise ValueError("H{num} PAUSED: CVM/execution methodology changed; validate the rebuilt "
                     "dataset and preregister the corrected instrument before observing performance.")


''' + s[end+1:]
    return s + '''


def walk_forward(conn, cfg, signal_fn=None, take="top", portfolio_fn=None, series_fn=None):
    """Corrected instrument. Historical hypothesis runners explicitly use legacy_walk_forward."""
    from simulation import walk_forward as simulate
    return simulate(conn, cfg, signal_fn, take, portfolio_fn, series_fn)
'''
transform('stocks_predictor/backtest.py', backtest_changes)

# Retain tests of historical behavior under explicit legacy names, then add independent
# regression tests of the fixed public paths. No historical expected value is rewritten.
for path in (ROOT/'tests').glob('test_*.py'):
    if path.name == 'test_dfp_readiness_audit.py':
        continue
    s = path.read_text(encoding='utf-8')
    before = s
    for module,names in [('ingest_cvm',legacy_ingest), ('factor',legacy_factor),
                          ('adjust',['total_return_series'])]:
        for name in names:
            s = s.replace(module+'.'+name+'(', module+'.legacy_'+name+'(')
    # Old instrument expectations (including its documented inert embargo) remain replay tests.
    s = s.replace('backtest.walk_forward(', 'backtest.legacy_walk_forward(')
    for num in (17,18,19):
        pattern = rf'def test_run_h{num}_smoke\(.*?\n(?=def )'
        replacement = f'''def test_run_h{num}_blocked_before_protected_performance(tmp_path):
    import pytest
    conn = _synthetic_conn(tmp_path)
    before = conn.total_changes
    with pytest.raises(ValueError, match="H{num} PAUSED"):
        backtest.run_h{num}(conn=conn, trials_path=tmp_path / "trials.json")
    assert conn.total_changes == before
    assert not (tmp_path / "trials.json").exists()
    conn.close()


'''
        s = re.sub(pattern,replacement,s,flags=re.S)
    if s != before:
        path.write_text('# Historical regression fixtures use explicit legacy APIs; see test_repairs_*.py for current paths.\n'+s,encoding='utf-8')

transform('tools/audit_dfp_readiness.py', lambda s: s.replace('ingest_cvm.parse_dfp_received_dates(', 'ingest_cvm.legacy_parse_dfp_received_dates(').replace('ingest_cvm.parse_dfp_statement_rows(', 'ingest_cvm.legacy_parse_dfp_statement_rows(').replace('The current ingestion path', 'The archived ingestion path'))
transform('stocks_predictor/cvm_pit.py', lambda s: s.replace('    reader = csv.DictReader([], fieldnames=[])  # accept rows or an existing DictReader\n    del reader\n',''))
print('Integrated versioned derivations and protected historical APIs.')
