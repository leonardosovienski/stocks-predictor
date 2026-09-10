"""Local, versioned research store with explicit ownership and recoverable snapshots.

No legacy schema migration, automatic source selection, network or order execution.
SQLite WAL is for one host on a local filesystem. Direct file owners can bypass
SQL guards; these are integrity controls, not an authentication boundary.
"""
from contextlib import closing, contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import time
from typing import Iterator
from urllib.parse import urlsplit

from . import source_catalog

APPLICATION_ID = 0x53544B50
SCHEMA_VERSION = 1
PRICE_COLUMNS = ('date,ticker,bdi_code,market_type,open,high,low,close,'
                 'volume_fin,qty,quote_factor,source_file')
SCHEMA = (
    source_catalog.SCHEMA.replace(' IF NOT EXISTS', ''),
    '''CREATE TABLE prices_raw (
        date TEXT NOT NULL, ticker TEXT NOT NULL, bdi_code TEXT NOT NULL,
        market_type TEXT NOT NULL, open REAL NOT NULL, high REAL NOT NULL,
        low REAL NOT NULL, close REAL NOT NULL, volume_fin REAL NOT NULL,
        qty INTEGER NOT NULL, quote_factor INTEGER NOT NULL CHECK(quote_factor>0),
        source_file TEXT NOT NULL REFERENCES source_versions(source_id),
        UNIQUE(date,ticker,source_file))''',
    'CREATE INDEX idx_prices_source ON prices_raw(source_file,date,ticker)',
    *(f"CREATE TRIGGER {table}_no_{action.lower()} BEFORE {action} ON {table} "
      "BEGIN SELECT RAISE(ABORT,'append-only research store'); END"
      for table in ('prices_raw', 'source_versions') for action in ('UPDATE', 'DELETE')),
)


def file_sha256(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _timeout(seconds: float) -> float:
    if isinstance(seconds, bool) or not math.isfinite(seconds) or not 0 < seconds <= 3600:
        raise ValueError('timeout must be finite, positive and at most 3600 seconds')
    return seconds


def _validate_schema(conn: sqlite3.Connection) -> None:
    if (conn.execute('PRAGMA application_id').fetchone()[0] != APPLICATION_ID
            or conn.execute('PRAGMA user_version').fetchone()[0] != SCHEMA_VERSION):
        raise ValueError('not a supported managed research store')
    actual = {''.join(row[0].split()) for row in conn.execute(
        "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'")}
    expected = {''.join(statement.split()) for statement in SCHEMA}
    if actual != expected:
        raise ValueError('managed store schema differs from its version')


def _open(path: Path, *, writable: bool = False, timeout: float = 5) -> sqlite3.Connection:
    _timeout(timeout)
    if (path.parent / 'INCOMPLETE.json').exists():
        raise ValueError('store directory is incomplete')
    if not path.is_file():
        raise FileNotFoundError(path)
    mode = 'rw' if writable else 'ro'
    conn = sqlite3.connect(path.resolve().as_uri() + '?mode=' + mode, uri=True, timeout=timeout)
    try:
        _validate_schema(conn)
        conn.execute('PRAGMA foreign_keys=ON')
        if writable:
            if conn.execute('PRAGMA journal_mode').fetchone()[0] != 'wal':
                raise ValueError('writable managed stores require WAL mode')
            conn.execute('PRAGMA synchronous=FULL')
        else:
            conn.execute('PRAGMA query_only=ON')
        return conn
    except BaseException:
        conn.close()
        raise


@contextmanager
def writer(path: Path, *, timeout: float = 5) -> Iterator[sqlite3.Connection]:
    """Serialize writers before reads; avoid deferred-transaction upgrade races."""
    with closing(_open(path, writable=True, timeout=timeout)) as conn:
        conn.execute('BEGIN IMMEDIATE')
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise


def initialize(path: Path) -> dict:
    """Reserve a new file exclusively. Failed/aborted creation cannot be reused silently."""
    with path.open('xb'):
        pass
    with closing(sqlite3.connect(path)) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=FULL')
        with conn:
            conn.execute('BEGIN IMMEDIATE')
            conn.execute(f'PRAGMA application_id={APPLICATION_ID}')
            conn.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
            for statement in SCHEMA:
                conn.execute(statement)
    return inspect(path)


def ingest(path: Path, archive: Path, *, publisher: str, dataset: str, version: str,
           source_url: str, observed_at: str, expected_sha256: str, scratch_dir: Path,
           all_markets: bool = False, timeout: float = 5) -> dict:
    if type(all_markets) is not bool:
        raise ValueError('all_markets must be boolean')
    parsed = urlsplit(source_url)
    if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('source_url requires an HTTP(S) URL without credentials')
    # This operational boundary requires an acquisition hash. The catalog checks
    # the actual temporary snapshot, not an earlier independent read of the source.
    if not expected_sha256:
        raise ValueError('expected_sha256 is required')
    with writer(path, timeout=timeout) as conn:
        result = source_catalog.ingest_version(
            conn, archive, publisher=publisher, dataset=dataset, version=version,
            source_url=source_url, observed_at=observed_at, scratch_dir=scratch_dir,
            avista_only=not all_markets, expected_sha256=expected_sha256)
    return {'status': 'PASS', **result, 'capital_enabled': False}


def _inspect(conn: sqlite3.Connection) -> dict:
    _validate_schema(conn)
    if conn.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
        raise ValueError('SQLite integrity check failed')
    if conn.execute('PRAGMA foreign_key_check').fetchall():
        raise ValueError('source references are invalid')
    sources = []
    columns = [row[1] for row in conn.execute('PRAGMA table_info(source_versions)')]
    for version in conn.execute('SELECT * FROM source_versions ORDER BY source_id'):
        source = dict(zip(columns, version))
        count, tickers, first, last = conn.execute(
            'SELECT COUNT(*),COUNT(DISTINCT ticker),MIN(date),MAX(date) FROM prices_raw WHERE source_file=?',
            (source['source_id'],)).fetchone()
        digest = hashlib.sha256()
        for row in conn.execute(f'SELECT {PRICE_COLUMNS} FROM prices_raw WHERE source_file=? ORDER BY date,ticker',
                                (source['source_id'],)):
            digest.update(json.dumps(row, separators=(',', ':'), allow_nan=False).encode('utf-8'))
        sources.append({**source, 'rows': count, 'tickers': tickers, 'date_min': first,
                        'date_max': last, 'rows_sha256': digest.hexdigest()})
    return {'status': 'PASS', 'schema_version': SCHEMA_VERSION, 'sources': sources,
            'stored_rows': sum(row['rows'] for row in sources),
            'scope': 'Physical source versions; never an automatically merged price series.',
            'historical_publication_certified': False, 'capital_enabled': False}


def inspect(path: Path) -> dict:
    with closing(_open(path)) as conn:
        # One consistent read snapshot for integrity, catalog, counts and row hashes.
        conn.execute('BEGIN')
        return _inspect(conn)


def _reserve_directory(destination: Path) -> None:
    destination.mkdir(exist_ok=False)
    _write_json(destination / 'INCOMPLETE.json', {'status': 'INCOMPLETE'})


def _write_json(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def snapshot(path: Path, destination: Path, *, timeout: float = 60) -> dict:
    """Online backup includes committed WAL; incomplete artifacts remain labelled."""
    _timeout(timeout)
    with closing(_open(path)) as source:
        _reserve_directory(destination)
        partial = destination / 'snapshot.sqlite.partial'
        started = time.monotonic()

        def progress(status: int, remaining: int, total: int) -> None:
            if time.monotonic() - started > timeout:
                raise TimeoutError('online backup exceeded deadline')

        with closing(sqlite3.connect(partial)) as target:
            source.backup(target, pages=256, progress=progress, sleep=0.01)
            target.execute('PRAGMA journal_mode=DELETE')
            report = _inspect(target)
        with partial.open('r+b') as stream:
            os.fsync(stream.fileno())
        complete = destination / 'snapshot.sqlite'
        partial.rename(complete)
        manifest = {'format': 'stocks-snapshot-v1', 'sha256': file_sha256(complete),
                    'created_at': datetime.now(timezone.utc).isoformat(), 'inspection': report}
        _write_json(destination / 'manifest.json', manifest)
        (destination / 'INCOMPLETE.json').unlink()
    return {'status': 'PASS', **manifest}


def restore(snapshot_dir: Path, destination: Path) -> dict:
    """Copy verified snapshot bytes to a new directory; no replacement of live banks."""
    if (snapshot_dir / 'INCOMPLETE.json').exists():
        raise ValueError('snapshot is incomplete')
    manifest = json.loads((snapshot_dir / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('format') != 'stocks-snapshot-v1':
        raise ValueError('unsupported snapshot format')
    _reserve_directory(destination)
    partial = destination / 'research.sqlite.partial'
    digest = hashlib.sha256()
    with (snapshot_dir / 'snapshot.sqlite').open('rb') as source, partial.open('xb') as target:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
            target.write(chunk)
        target.flush()
        os.fsync(target.fileno())
    if digest.hexdigest() != manifest['sha256']:
        raise ValueError('snapshot SHA-256 mismatch')
    with closing(sqlite3.connect(partial.resolve().as_uri() + '?mode=ro', uri=True)) as conn:
        report = _inspect(conn)
    if report != manifest['inspection']:
        raise ValueError('restored content differs from snapshot manifest')
    with closing(sqlite3.connect(partial)) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=FULL')
    complete = destination / 'research.sqlite'
    partial.rename(complete)
    receipt = {'status': 'PASS', 'source_snapshot_sha256': digest.hexdigest(), 'inspection': report}
    _write_json(destination / 'receipt.json', receipt)
    (destination / 'INCOMPLETE.json').unlink()
    return receipt
