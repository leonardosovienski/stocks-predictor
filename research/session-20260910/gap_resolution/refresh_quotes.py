"""Verify a new annual capture against frozen BOVA prices and official sessions."""
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from stocks_predictor.cotahist import parse_line

root = Path('C:/STOCKS/work/gap-resolution-r6-20260910')
path = root/'raw/COTAHIST_A2026.ZIP'
receipt = json.loads(path.with_suffix('.ZIP.receipt.json').read_text(encoding='utf-8'))
if hashlib.sha256(path.read_bytes()).hexdigest() != receipt['sha256']:
    raise ValueError('Capture hash mismatch')
records = {}
sessions = set()
with zipfile.ZipFile(path) as archive:
    if len(archive.namelist()) != 1:
        raise ValueError('Unexpected archive members')
    with archive.open(archive.namelist()[0]) as stream:
        for line in stream:
            if line[:2] != b'01' or line[24:27] != b'010':
                continue
            raw = line[2:10].decode('ascii')
            day = date.fromisoformat(f'{raw[:4]}-{raw[4:6]}-{raw[6:]}').isoformat()
            if not day.startswith('2026') or day >= '2026-09-10':
                raise ValueError('Archive contains a wrong-year or unfinished-session record')
            sessions.add(day)
            if line[12:24].strip() != b'BOVA11':
                continue
            row = parse_line(line.decode('latin-1'))
            row.update(isin=line[230:242].decode('ascii').strip(), currency=line[52:56].decode('ascii').strip())
            if day in records:
                raise ValueError('Duplicate target date')
            records[day] = row
old_path = Path('C:/STOCKS/work/h21-source-closure-20260909/normalized-v2/quotes-2018-20260908.json')
old = [r for r in json.loads(old_path.read_text(encoding='utf-8'))['records'] if r['date'].startswith('2026')]
changed = [r['date'] for r in old if records.get(r['date']) != r]
cal_path = Path('C:/STOCKS/work/h21-source-closure-20260909/calendar-2026.json')
closures = set(json.loads(cal_path.read_text(encoding='utf-8'))['closed_equity_dates'])
expected = set()
day = date(2026,1,1)
while day <= date(2026,9,9):
    if day.weekday() < 5 and day.isoformat() not in closures:
        expected.add(day.isoformat())
    day += timedelta(days=1)
report = {'checked_at_utc':datetime.now(timezone.utc).isoformat(), 'source_sha256':receipt['sha256'],
          'prior_overlap_rows':len(old), 'changed_prior_dates':changed, 'new_dates':sorted(set(records)-{r['date'] for r in old}),
          'latest_complete_target_date':max(records), 'bova_records':len(records),
          'missing_official_sessions':sorted(expected-set(records)), 'unexpected_spot_sessions':sorted(sessions-expected),
          'missing_spot_sessions':sorted(expected-sessions), 'profit_evaluation':False,
          'source_snapshot_acquired_at_utc':receipt['completed_at_utc'], 'contemporaneous_historical_publication_certified':False}
with (root/'quote-refresh.json').open('x',encoding='utf-8') as output:
    json.dump({'report':report, 'records':[records[k] for k in sorted(records)]},output,indent=2)
print(json.dumps(report,indent=2))
if changed or report['missing_official_sessions'] or report['unexpected_spot_sessions'] or report['missing_spot_sessions']:
    raise SystemExit(2)
