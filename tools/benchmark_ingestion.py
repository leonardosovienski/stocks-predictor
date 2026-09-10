"""Fixed synthetic ingestion benchmark; no market evaluation or production DB."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import statistics
import subprocess
import time
import tracemalloc
import types

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = '''CREATE TABLE prices_raw(date TEXT, ticker TEXT, bdi_code TEXT,
    market_type TEXT, open REAL, high REAL, low REAL, close REAL,
    volume_fin REAL, qty INTEGER, quote_factor INTEGER, source_file TEXT,
    UNIQUE(date,ticker,source_file))'''


def benchmark(revision=None, count=100_000, repeats=3):
    relative = 'stocks_predictor/cotahist.py'
    source = (subprocess.check_output(['git', 'show', f'{revision}:{relative}'], cwd=ROOT)
              if revision else (ROOT / relative).read_bytes())
    module = types.ModuleType('stocks_benchmark_cotahist')
    exec(compile(source, relative, 'exec'), module.__dict__)
    spot = module._pack('2024-01-02', 'T', '02', '010', 10, 11, 9, 10, 100, 1000, 1)
    option = module._pack('2024-01-02', 'T', '78', '070', 1, 2, 1, 1, 10, 10, 1)
    results = []
    for _ in range(repeats):
        source_digest = hashlib.sha256()

        def records():
            for i in range(count):
                template = spot if i % 20 == 0 else option
                line = template[:12] + f'T{i:011d}' + template[24:]
                source_digest.update(line.encode('ascii'))
                yield line

        with closing(sqlite3.connect(':memory:')) as conn:
            conn.execute(SCHEMA)
            tracemalloc.start()
            started = time.perf_counter()
            inserted = module.load_prices(conn, records(), 'fixed-synthetic.txt')
            elapsed = time.perf_counter() - started
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            output = hashlib.sha256()
            for row in conn.execute('SELECT * FROM prices_raw ORDER BY date,ticker,source_file'):
                output.update(json.dumps(row, separators=(',', ':')).encode('ascii'))
            expected = (count + 19) // 20
            if inserted != expected:
                raise AssertionError((inserted, expected))
        results.append({'seconds_with_tracemalloc': elapsed, 'peak_python_bytes': peak,
                        'inserted': inserted, 'input_sha256': source_digest.hexdigest(),
                        'stored_rows_sha256': output.hexdigest()})
    return {'revision': revision or 'working-tree', 'source_sha256': hashlib.sha256(source).hexdigest(),
            'records': count, 'spot_fraction': 0.05, 'repeats': results,
            'median_seconds_with_tracemalloc': statistics.median(r['seconds_with_tracemalloc'] for r in results),
            'median_peak_python_bytes': statistics.median(r['peak_python_bytes'] for r in results),
            'scope': 'Synthetic fixed input; Python heap excludes SQLite native memory; tracing affects timing.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision')
    parser.add_argument('--count', type=int, default=100_000)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.count < 1 or args.repeats < 1:
        parser.error('count and repeats must be positive')
    if args.output.exists():
        parser.error('output already exists; use a new receipt')
    result = benchmark(args.revision, args.count, args.repeats)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))
