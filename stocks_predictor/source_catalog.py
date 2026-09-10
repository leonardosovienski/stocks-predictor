"""Content-addressed, atomic ingestion of explicitly versioned COTAHIST sources.

The catalog describes observations, not historical publication availability.
Legacy filename identities are preserved. New versions never overwrite them.
"""
from collections.abc import Iterable
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import zipfile

from . import cotahist

SCHEMA = """CREATE TABLE IF NOT EXISTS source_versions (
    source_id TEXT PRIMARY KEY,
    publisher TEXT NOT NULL,
    dataset TEXT NOT NULL,
    version TEXT NOT NULL,
    policy TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    source_url TEXT NOT NULL,
    original_name TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    UNIQUE(publisher, dataset, version, policy)
)"""


def utc_timestamp(value: str) -> str:
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError('timestamp requires an explicit UTC offset')
    return stamp.astimezone(timezone.utc).isoformat()


def strict_lines(lines: Iterable[bytes]) -> Iterable[str]:
    """Reject malformed quote records; never silently certify skipped content."""
    for raw in lines:
        line = raw.decode('latin-1')
        if line.startswith('01'):
            cotahist.parse_line(line)  # raises before the loader can skip it
        yield line


def ingest_version(
    conn: sqlite3.Connection, archive: Path, *, publisher: str, dataset: str,
    version: str, source_url: str, observed_at: str, scratch_dir: Path,
    avista_only: bool = True, expected_sha256: str | None = None,
) -> dict:
    """Snapshot and hash bytes before parsing; catalog and prices share one transaction.

    Caller transactions are preserved. A changed payload under a declared version
    fails even if the changed bytes would be excluded by the spot filter. Replays
    retain the first observation and return the number of genuinely new prices.
    """
    values = (publisher, dataset, version, source_url)
    if any(not isinstance(x, str) or not x.strip() or x != x.strip() for x in values):
        raise ValueError('explicit nonempty publisher, dataset, version and URL required')
    observed_at = utc_timestamp(observed_at)
    if type(avista_only) is not bool:
        raise ValueError('avista_only must be boolean')
    if expected_sha256 is not None and not re.fullmatch('[0-9a-f]{64}', expected_sha256):
        raise ValueError('expected_sha256 must be a lowercase SHA-256')
    policy = 'cotahist-strict-v1/' + ('spot-02-010' if avista_only else 'all-markets')
    # Explicit scratch location prevents modifying a source tree or the global runtime.
    with tempfile.TemporaryFile(dir=scratch_dir) as snapshot:
        digest = hashlib.sha256()
        with archive.open('rb') as source:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
                snapshot.write(chunk)
        content_sha = digest.hexdigest()
        if expected_sha256 is not None and content_sha != expected_sha256:
            raise ValueError('source snapshot differs from expected SHA-256')
        identity = json.dumps([publisher, dataset, version, policy, content_sha], separators=(',', ':'))
        source_id = 'sha256:' + hashlib.sha256(identity.encode('utf-8')).hexdigest()
        snapshot.seek(0)
        with zipfile.ZipFile(snapshot) as zipped:
            candidates = [n for n in zipped.namelist() if n.upper().endswith('.TXT')]
            preferred = [n for n in candidates if 'COTAHIST' in n.upper()]
            chosen = preferred or candidates
            if len(chosen) != 1:
                raise ValueError('source must contain one unambiguous COTAHIST text member')
            own_transaction = not conn.in_transaction
            conn.execute('SAVEPOINT stocks_source_version')
            try:
                conn.execute(SCHEMA)
                prior = conn.execute(
                    'SELECT sha256 FROM source_versions WHERE publisher=? AND dataset=? AND version=? AND policy=?',
                    (publisher, dataset, version, policy),
                ).fetchone()
                if prior is not None and prior[0] != content_sha:
                    raise ValueError('declared source version has conflicting content')
                conn.execute(
                    'INSERT INTO source_versions VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(source_id) DO NOTHING',
                    (source_id, publisher, dataset, version, policy, content_sha,
                     source_url, archive.name, observed_at),
                )
                with zipped.open(chosen[0]) as stream:
                    inserted = cotahist.load_prices(conn, strict_lines(stream), source_id, avista_only)
                conn.execute('RELEASE stocks_source_version')
            except BaseException:
                if own_transaction:
                    conn.rollback()
                elif conn.in_transaction:
                    conn.execute('ROLLBACK TO stocks_source_version')
                    conn.execute('RELEASE stocks_source_version')
                raise
    return {'source_id': source_id, 'sha256': content_sha, 'inserted': inserted,
            'policy': policy, 'historical_publication_certified': False}
