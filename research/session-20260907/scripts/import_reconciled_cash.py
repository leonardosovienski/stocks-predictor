"""Promote only fully reconciled CASH intervals in the disposable research copy.

This certifies agreement of the two complete issuer-level cash lists. It does
not certify non-cash corporate actions, point-in-time forecasts, net taxes or
whole-universe eligibility. No return series or strategy is evaluated.
"""
from collections import defaultdict
from decimal import Decimal
import csv
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'work/source-acquisition'
sys.path[:0] = [str(ROOT / 'work/stocks-predictor/stocks_predictor'), str(ROOT / 'work/runtime')]
import cash_events
import cash_source_audit as audit

conn = sqlite3.connect(ROOT / 'work/stocks-history-2016-2026.db')
sessions = [x[0] for x in conn.execute('SELECT DISTINCT date FROM prices_raw ORDER BY date')]
matches = [json.loads(s) for s in (ROOT / 'outputs/cash-source-matches.jsonl').read_text(encoding='utf-8').splitlines()]
specs = [('15253', 'ENGI3', 'ON', '2026-08-27'), ('15253', 'ENGI4', 'PN', '2026-08-27'),
         ('15253', 'ENGI11', 'UNT', '2026-08-27'), ('23264', 'ABEV3', 'ON', '2026-06-22')]
events, coverage, evidence = [], [], []
prior_ri = json.loads((ROOT / 'outputs/cash-source-reconciliation.json').read_text(encoding='utf-8'))['extraction_issues']
for code, ticker, cls, end in specs:
    start = '2016-01-04'
    raw = json.loads((RAW / f'b3-cvm{code}-cash-all.json').read_text(encoding='utf-8'))
    selected = []
    for row in raw:
        if row['typeStock'] != cls:
            continue
        cum = audit.br_date(row['lastDatePriorEx'])
        if cum < start:
            if cum >= '2015-12-21':
                boundary_proof = [p for p in prior_ri if p.get('ticker') == ticker
                    and p.get('approval_date') == audit.br_date(row['dateApproval'])
                    and p.get('payment_date') and cum <= p['payment_date'] < start
                    and Decimal(p['value_per_share']) == audit.br_decimal(row['valueCash']) / audit.br_decimal(row['quotedPerShares'])]
                if len(boundary_proof) != 1:
                    raise ValueError('unverified event adjacent to left calendar boundary')
            continue
        if cum >= end:
            continue
        selected.append(audit.normalize_b3_history(row, sessions))
    matched = [r for r in matches if r['ticker'] == ticker and start <= r['ex_date'] <= end]
    def key(row):
        return row['security_class'], row['action'], row.get('b3_approval_date', row.get('approval_date')), row['last_cum'], row['ex_date']
    expected = {}
    for row in selected:
        if key(row) in expected:
            raise ValueError('ambiguous B3 event identity')
        expected[key(row)] = Decimal(row['value_per_share'])
    observed = defaultdict(Decimal)
    for row in matched:
        observed[key(row)] += Decimal(row['value_per_share'])
    if not expected or set(expected) != set(observed) or any(abs(expected[k] - observed[k]) > Decimal('0.00000000001') for k in expected):
        raise ValueError(f'incomplete two-source cash reconciliation for {ticker}')
    source = f"B3 CVM {code} full paginated cash history + {matched[0]['source_url']}; source manifests in delivery; reconciliation 2026-09-07"
    coverage.append({'ticker': ticker, 'start_date': start, 'end_date': end, 'source': source})
    for row in matched:
        economic_key = [code, *key(row), row.get('installment_number', 0)]
        event_id = 'B3-RI:' + hashlib.sha256(json.dumps(economic_key).encode()).hexdigest()[:32]
        events.append({'ticker': ticker, 'event_id': event_id, 'ex_date': row['ex_date'], 'payment_date': row['payment_date'],
                       'value_per_share': row['value_per_share'], 'source': f"{source}; {row['locator']}"})
    evidence.append({'ticker': ticker, 'start_date': start, 'end_date': end, 'b3_entitlements': len(expected),
                     'receivables': len(matched), 'all_entitlements_reconciled': True})

buffer = io.StringIO(newline='')
writer = csv.DictWriter(buffer, fieldnames=['ticker', 'event_id', 'ex_date', 'payment_date', 'value_per_share', 'source'], lineterminator='\n')
writer.writeheader()
writer.writerows(events)
payload = buffer.getvalue().encode('utf-8')
inserted = cash_events.import_verified_events(conn, payload, coverage)
conn.commit()
assert cash_events.import_verified_events(conn, payload, coverage) == 0
conn.commit()
conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
conn.close()
(ROOT / 'outputs/reconciled-cash-events.csv').write_bytes(payload)
(ROOT / 'outputs/reconciled-cash-coverage.json').write_text(json.dumps(coverage, ensure_ascii=False, indent=2), encoding='utf-8')
report = {'inserted': inserted, 'receivables': len(events), 'intervals': evidence, 'idempotent_reimport': True,
          'whole_universe_coverage': False, 'noncash_actions_certified': False, 'performance_observed': False,
          'excluded_abev_event': {'ex_date': '2026-06-23', 'reason': 'Conflicting payment dates: RI workbook 2026-12-30; B3 supplement 2026-12-31'},
          'database_sha256': hashlib.sha256((ROOT / 'work/stocks-history-2016-2026.db').read_bytes()).hexdigest()}
(ROOT / 'outputs/reconciled-cash-import.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
