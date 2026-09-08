"""Offline source reconciliation. Populates audit staging, never event coverage."""
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'work/source-acquisition'
sys.path[:0] = [str(ROOT / 'work/stocks-predictor/stocks_predictor'), str(ROOT / 'work/stocks-predictor'), str(ROOT / 'work/runtime')]
import cash_source_audit as audit
from tools.rebuild_source_history import stage_records

database = ROOT / 'work/stocks-history-2016-2026.db'
conn = sqlite3.connect(database)
sessions = [x[0] for x in conn.execute('SELECT DISTINCT date FROM prices_raw ORDER BY date')]
calendar_hash = hashlib.sha256('\n'.join(sessions).encode()).hexdigest()
issuers = json.loads((ROOT / 'outputs/b3-historical-acquisition.json').read_text(encoding='utf-8'))
histories = {}
normalization_issues = []
raw_count = 0
for issuer in issuers:
    if issuer['status'] != 'ACQUIRED':
        continue
    code = issuer['codeCVM']
    path = RAW / f'b3-cvm{code}-cash-all.json'
    rows = json.loads(path.read_text(encoding='utf-8'))
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    histories[code] = []
    for i, row in enumerate(rows):
        item = {'cnpj': ''.join(c for c in issuer['cnpj'] if c.isdigit()), 'source_sha256': sha,
                'source_file': path.name, 'source_row': i, 'raw': row, 'eligible_for_total_return': False,
                'calendar_sha256': calendar_hash}
        try:
            item['normalized'] = audit.normalize_b3_history(row, sessions)
            histories[code].append(item['normalized'])
        except ValueError as exc:
            item['issue'] = str(exc)
            normalization_issues.append({'codeCVM': code, 'source_row': i, 'reason': str(exc)})
        raw_count += stage_records(conn, 'B3_CASH_UNVERIFIED', None, [item])

payments = []
extraction_issues = []

def provenance(filename):
    p = RAW / filename
    return {'source_file': filename, 'source_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
            'source_url': json.loads((RAW / (filename + '.source.json')).read_text(encoding='utf-8'))['url']}

# BB reports approval and monetary correction separately. Keep original values
# distinct: no updated amount is silently treated as known on the ex-date.
bb_source = provenance('ri-bbas-payments.pdf')
pages = json.loads((RAW / 'ri-bbas-payments-extracted.json').read_text(encoding='utf-8'))
pattern = re.compile(r'^\s*(JCP(?:\s*\(complementar\))?|Dividendos)\s+(\S+)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+([\d.,]+)\s+([\d.,]+)(.*)$')
for page in pages:
    for i, line in enumerate(page['text'].splitlines(), 1):
        match = pattern.match(line)
        if not match:
            if re.match(r'^\s*(?:JCP|Dividendos)\s', line) and re.search(r'\d{2}/\d{2}/\d{4}', line):
                extraction_issues.append({'source_file': bb_source['source_file'], 'page': page['page'], 'line': i, 'reason': 'UNPARSED_EVENT_LINE'})
            continue
        event, period, announcement, cum, ex, pay, total, gross, tail = match.groups()
        payments.append({**bb_source, 'locator': f"page {page['page']}, line {i}", 'ticker': 'BBAS3', 'codeCVM': '1023',
                         'security_class': 'ON', 'action': 'DIVIDENDO' if event == 'Dividendos' else 'JRS CAP PROPRIO',
                         'announcement_date': audit.br_date(announcement), 'last_cum': audit.br_date(cum),
                         'ex_date': audit.br_date(ex), 'payment_date': audit.br_date(pay),
                         'value_per_share': str(audit.br_decimal(gross)), 'monetary_update_text': tail.strip() or None,
                         'period': period})

engi_source = provenance('ri-engi-payments.xlsx')
sheets = json.loads((RAW / 'ri-engi-payments-extracted.json').read_text(encoding='utf-8'))
holding = next(s for s in sheets if s['sheet'] == 'ESA - Holding')
for row in holding['rows']:
    v = row['values']
    if not isinstance(v[3], str) or not re.match(r'^\d{4}-\d{2}-\d{2}', v[3]):
        continue
    for ticker, cls, column in [('ENGI3', 'ON', 7), ('ENGI4', 'PN', 8), ('ENGI11', 'UNT', 9)]:
        if not isinstance(v[column], (float, int)) or v[column] <= 0:
            continue
        payments.append({**engi_source, 'locator': f"ESA - Holding!D{row['row']}:J{row['row']}",
                         'ticker': ticker, 'codeCVM': '15253', 'security_class': cls, 'action': 'DIVIDENDO',
                         'approval_date': v[3][:10], 'last_cum': v[4][:10], 'ex_date': v[5][:10],
                         'payment_date': v[6][:10], 'value_per_share': str(v[column])})

abev_source = provenance('ri-abev-payments.xlsx')
sheets = json.loads((RAW / 'ri-abev-payments-extracted.json').read_text(encoding='utf-8'))
ambev = next(s for s in sheets if s['sheet'] == 'Ambev S.A.')
abev_groups = defaultdict(list)
for row in ambev['rows']:
    v = row['values']
    if not isinstance(v[0], str) or not re.match(r'^\d{4}-\d{2}-\d{2}', v[0]):
        continue
    if not isinstance(v[2], (float, int)) or v[2] <= 0:
        continue
    action = 'DIVIDENDO' if v[6] == 'DIVIDENDOS' else 'JRS CAP PROPRIO' if str(v[6]).startswith('JUROS') else None
    payment = {**abev_source, 'locator': f"Ambev S.A.!A{row['row']}:G{row['row']}", 'ticker': 'ABEV3',
               'codeCVM': '23264', 'security_class': 'ON', 'action': action, 'approval_date': v[0][:10],
               'payment_date': v[1][:10], 'value_per_share': str(v[2]), 'net_per_share_reported': v[3]}
    abev_groups[payment['approval_date'], action].append(payment)

installments = []
for (approval, action), group in abev_groups.items():
    total = sum(Decimal(p['value_per_share']) for p in group)
    candidates = [r for r in histories['23264'] if r['approval_date'] == approval and r['action'] == action
                  and abs(Decimal(r['value_per_share']) - total) <= Decimal('0.00000000001')]
    if len(candidates) != 1:
        for payment in group:
            extraction_issues.append({**payment, 'reason': f'NO_UNIQUE_B3_ENTITLEMENT_MATCH ({len(candidates)})'})
        continue
    for payment in group:
        payment.update(last_cum=candidates[0]['last_cum'], ex_date=candidates[0]['ex_date'])
    if len(group) == 1:
        payments.extend(group)
    else:
        installments.extend(audit.match_installments(group, histories['23264'], sessions))

matched, rejected = list(installments), []
for item in installments:
    stage_records(conn, 'RI_B3_CASH_MATCH', None, [item])
for payment in payments:
    try:
        item = audit.match_payment(payment, histories[payment['codeCVM']], sessions)
        matched.append(item)
        stage_records(conn, 'RI_B3_CASH_MATCH', None, [item])
    except ValueError as exc:
        rejected.append({**payment, 'reason': str(exc)})
        stage_records(conn, 'RI_CASH_REJECTED', None, [{**payment, 'reason': str(exc)}])
conn.commit()
conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
staged_total = conn.execute("SELECT COUNT(*) FROM research_source_documents WHERE kind='B3_CASH_UNVERIFIED'").fetchone()[0]
conn.close()
(ROOT / 'outputs/cash-source-matches.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False, sort_keys=True) + '\n' for x in matched), encoding='utf-8')
report = {'raw_b3_records_staged': staged_total, 'new_raw_b3_records_inserted': raw_count, 'b3_records_in_calendar': sum(map(len, histories.values())),
          'calendar_start': sessions[0], 'calendar_end': sessions[-1], 'calendar_sha256': calendar_hash,
          'matched_payments': len(matched), 'matched_by_ticker': dict(Counter(x['ticker'] for x in matched)),
          'rejected_payments': rejected, 'extraction_issues': extraction_issues,
          'b3_normalization_issue_counts': dict(Counter(x['reason'] for x in normalization_issues)),
          'b3_normalization_issues': normalization_issues, 'complete_event_coverage': False,
          'missing_fields_fabricated': False, 'performance_observed': False,
          'output_database_sha256': hashlib.sha256(database.read_bytes()).hexdigest()}
(ROOT / 'outputs/cash-source-reconciliation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k not in ('rejected_payments', 'extraction_issues', 'b3_normalization_issues')}, indent=2))
