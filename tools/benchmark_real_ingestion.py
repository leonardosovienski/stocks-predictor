"""Compare ingestion revisions on preserved real text sources in fresh subprocesses."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import platform
import sqlite3
import statistics
import subprocess
import sys
import time
import types

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = '''CREATE TABLE prices_raw(date TEXT, ticker TEXT, bdi_code TEXT,
market_type TEXT, open REAL, high REAL, low REAL, close REAL, volume_fin REAL,
qty INTEGER, quote_factor INTEGER, source_file TEXT, UNIQUE(date,ticker,source_file))'''


def peak_rss():
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
                'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
                'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        psapi = ctypes.WinDLL('psapi', use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        info = Counters()
        info.cb = ctypes.sizeof(info)
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(info), info.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return info.PeakWorkingSetSize
    import resource
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == 'darwin' else value * 1024


def worker(source, revision):
    code = subprocess.check_output(['git', 'show', revision + ':stocks_predictor/cotahist.py'], cwd=ROOT)
    module = types.ModuleType('benchmark_cotahist')
    exec(compile(code, 'cotahist.py', 'exec'), module.__dict__)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    count, quotes, spot = 0, 0, 0
    with source.open(encoding='latin-1') as stream:
        for line in stream:
            count += 1
            if line.startswith('01'):
                quotes += 1
                rec = module.parse_line(line)
                spot += bool(rec and module.is_avista(rec))
    # Keep inspection outside the timed interval; each worker is a fresh process.
    rss_before = peak_rss()
    with closing(sqlite3.connect(':memory:')) as conn, source.open(encoding='latin-1') as stream:
        conn.execute(SCHEMA)
        cpu, wall = time.process_time(), time.perf_counter()
        reported = module.load_prices(conn, stream, 'preserved-real-source')
        elapsed, cpu_elapsed = time.perf_counter() - wall, time.process_time() - cpu
        rss_after = peak_rss()
        rows_sha = hashlib.sha256()
        rows = 0
        for row in conn.execute('SELECT * FROM prices_raw ORDER BY date,ticker,source_file'):
            rows += 1
            rows_sha.update(json.dumps(row, separators=(',', ':')).encode('utf-8'))
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_sha:
        raise ValueError('benchmark input changed')
    return {'source': str(source), 'source_sha256': source_sha,
            'code_sha256': hashlib.sha256(code).hexdigest(), 'revision': revision,
            'lines': count, 'quote_records': quotes, 'spot_records': spot,
            'reported_inserts': reported, 'stored_rows': rows, 'stored_rows_sha256': rows_sha.hexdigest(),
            'seconds': elapsed, 'cpu_seconds': cpu_elapsed, 'peak_rss_before_bytes': rss_before,
            'peak_rss_after_ingestion_bytes': rss_after}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, action='append', required=True)
    parser.add_argument('--before', required=True)
    parser.add_argument('--after', default='HEAD')
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.source[0], args.before)))
        return
    if args.repeats < 1 or args.output is None or args.output.exists():
        parser.error('positive repeats and a new output file required')
    revisions = [subprocess.check_output(['git', 'rev-parse', ref], cwd=ROOT, text=True).strip()
                 for ref in (args.before, args.after)]
    results = []
    for source in args.source:
        measurements = []
        for _ in range(args.repeats):
            for revision in revisions:
                raw = subprocess.check_output([sys.executable, __file__, '--worker', '--source', str(source),
                                               '--before', revision], cwd=ROOT, text=True)
                measurements.append(json.loads(raw))
        identities = {(m['source_sha256'], m['stored_rows_sha256'], m['stored_rows']) for m in measurements}
        if len(identities) != 1:
            raise ValueError('different economic input/output rows across revisions')
        summary = {rev: {key: statistics.median(m[key] for m in measurements if m['revision'] == rev)
                        for key in ('seconds', 'cpu_seconds', 'peak_rss_after_ingestion_bytes')}
                   for rev in revisions}
        results.append({'source': str(source), 'measurements': measurements, 'medians': summary})
    receipt = {'status': 'PASS', 'platform': platform.platform(), 'python': sys.version,
               'results': results, 'scope': 'Preserved real text extracts, no tracing; process peak RSS includes Python and SQLite, not separate allocator attribution. No production throughput or concurrency guarantee.'}
    with args.output.open('x', encoding='utf-8') as handle:
        json.dump(receipt, handle, indent=2)
    print(json.dumps({'status': 'PASS', 'output': str(args.output), 'medians': [r['medians'] for r in results]}, indent=2))


if __name__ == '__main__':
    main()
