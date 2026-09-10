"""Finite operational acceptance through fresh CLI processes, including installed wheels."""
import argparse
from contextlib import redirect_stdout
from datetime import date, timedelta
import hashlib
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import zipfile


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installed', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--rows', type=int, default=250000)
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--worker', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.installed:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import stocks_predictor
    from stocks_predictor import cotahist, operations
    if args.installed:
        origin = Path(stocks_predictor.__file__).resolve()
        if not origin.is_relative_to(Path(sys.prefix).resolve()):
            raise ValueError('wheel must be imported from its installed environment')
    if args.worker is not None:
        output = io.StringIO()
        started, cpu = time.perf_counter(), time.process_time()
        with redirect_stdout(output):
            status = operations.main(args.worker)
        print(json.dumps({'exit_code': status, 'result': json.loads(output.getvalue()) if output.getvalue() else None,
                          'seconds': time.perf_counter() - started, 'cpu_seconds': time.process_time() - cpu,
                          'peak_process_rss_bytes': peak_rss()}))
        return status
    if args.output is None or args.rows <= 0 or bool(args.archive) != bool(args.receipt):
        parser.error('new --output, positive --rows, and paired --archive/--receipt required')
    args.output.mkdir(exist_ok=False)
    archive = args.archive or args.output / 'synthetic.zip'
    if args.archive:
        receipt = json.loads(args.receipt.read_text(encoding='utf-8'))
        source_sha, url, observed = receipt['sha256'], receipt['url'], receipt['completed_at_utc']
        dataset, version = 'COTAHIST_A2026', 'observed-20260910T152027Z'
    else:
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as zipped:
            member = zipfile.ZipInfo('COTAHIST.TXT', date_time=(2024, 1, 1, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            with zipped.open(member, 'w') as stream:
                for i in range(args.rows):
                    day = (date(2024, 1, 1) + timedelta(days=i // 1000)).isoformat()
                    line = cotahist._pack(day, f'T{i % 1000:04d}', '02', '010', 10, 11, 9, 10, 100, 1000, 1)
                    stream.write((line + '\n').encode('latin-1'))
        with archive.open('rb') as stream:
            source_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
        url, observed = 'https://example.invalid/synthetic.zip', '2026-09-10T10:00:00Z'
        dataset, version = 'synthetic-capacity-fixture', 'v1'
    measurements = []

    def command(*arguments):
        process = subprocess.run([sys.executable, '-I', str(Path(__file__).resolve()),
                                  *(['--installed'] if args.installed else []), '--worker', *map(str, arguments)],
                                 capture_output=True, text=True, timeout=600)
        if process.returncode:
            raise RuntimeError(process.stderr + process.stdout)
        result = json.loads(process.stdout)
        measurements.append({'command': list(map(str, arguments)), **result})
        print(json.dumps({'command': arguments[0], 'seconds': result['seconds']}), flush=True)
        return result['result']

    db = args.output / 'research.sqlite'
    command('init', '--db', db)
    ingest = ['ingest', '--db', db, '--archive', archive, '--publisher', 'B3' if args.archive else 'SYNTHETIC',
              '--dataset', dataset, '--version', version, '--source-url', url, '--observed-at', observed,
              '--sha256', source_sha, '--scratch-dir', args.output]
    first = command(*ingest)
    replay = command(*ingest)
    original = command('inspect', '--db', db)
    command('snapshot', '--db', db, '--destination', args.output / 'backup')
    command('restore', '--snapshot', args.output / 'backup', '--destination', args.output / 'restored')
    recovered = command('inspect', '--db', args.output / 'restored/research.sqlite')
    if (first['inserted'] != args.rows or replay['inserted'] != 0 or original != recovered
            or original['stored_rows'] != args.rows):
        raise ValueError('operational row count, replay or restored identity mismatch')
    profile = args.output / 'profile.json'
    profile.write_text('{"capital_brl":"5000"}\n', encoding='utf-8')
    personal = command('profile', '--input', profile)
    if personal['status'] != 'INCOMPLETE_PERSONAL_SCENARIO' or personal['capital_enabled']:
        raise ValueError('unknown personal inputs must remain unknown')
    outcomes = args.output / 'outcomes.json'
    outcomes.write_text('[]\n', encoding='utf-8')
    dated = command('evidence', '--input', outcomes, '--asof', '2026-09-10T00:00:00Z')
    if dated['status'] != 'INSUFFICIENT_EVIDENCE' or dated['capital_enabled']:
        raise ValueError('absent evidence must not pass an economic gate')
    report = {'status': 'PASS', 'python': sys.version, 'platform': platform.platform(),
              'package_code_sha256_lf': {path.name: hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
                                         for path in Path(stocks_predictor.__file__).parent.glob('*.py')},
              'installed_wheel': args.installed, 'source_sha256': source_sha,
              'archive_bytes': archive.stat().st_size, 'rows': args.rows, 'inspection': original,
              'measurements': measurements, 'capital_enabled': False,
              'scope': 'Finite local batch capacity and CLI recovery. RSS is peak of each fresh CLI process; no live-trading or profit validation.'}
    with (args.output / 'validation.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': report['status'], 'rows': args.rows, 'source_sha256': source_sha}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
