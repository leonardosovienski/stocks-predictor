"""Independent source arithmetic and an additive, isolated final review bundle."""
from collections import Counter
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'work/stocks-predictor'
BASE = ROOT / 'work/stocks-final-review-bundle'


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


if BASE.exists():
    raise ValueError('Use a new review directory; previous evidence is preserved')
shutil.copytree(ROOT / 'work/h19-continuous-bundle', BASE,
                ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
for name in ('retail_cash.py', 'continuous_cash.py', 'continuous_research.py'):
    shutil.copy2(REPO / 'stocks_predictor' / name, BASE / 'stocks_predictor' / name)
for name in ('test_retail_cash.py', 'test_continuous_cash.py', 'test_continuous_research.py'):
    shutil.copy2(REPO / 'tests' / name, BASE / 'tests' / name)
inputs = BASE / 'inputs'
shutil.copy2(ROOT / 'outputs/h18-h19-reorganization-observation.json', inputs)
index = read(inputs / 'quote-tape-index.json')
audit = []
for source in index['sources']:
    raw = ROOT / 'work/h19-continuous-inputs' / source['raw_excerpt']
    assert sha(raw) == source['raw_excerpt_sha256']
    shutil.copy2(raw, inputs / raw.name)
    expected = {}
    for line in raw.read_bytes().splitlines():
        assert len(line) == 245 and line[:2] == b'01'
        market = line[24:27].decode('ascii')
        symbol = line[12:24].decode('ascii').strip()
        ticker = symbol[:-1] if market == '020' and symbol.endswith('F') else symbol
        d = line[2:10].decode('ascii')
        day = d[:4] + '-' + d[4:6] + '-' + d[6:]
        divisor = D(int(line[210:217])) * 100
        key = (day, ticker, market)
        assert key not in expected
        expected[key] = {'isin': line[230:242].decode('ascii'),
            'open': D(int(line[56:69])) / divisor,
            'close': D(int(line[108:121])) / divisor,
            'volume_fin': D(int(line[170:188])) / 100,
            'quantity': int(line[152:170]), 'quote_factor': int(line[210:217])}
    count = 0
    for line in (inputs / source['quotes']).read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        original = expected.pop((row['date'], row['ticker'], row['market_type']))
        assert original['isin'] == row['isin']
        for field in ('open', 'close', 'volume_fin', 'quantity', 'quote_factor'):
            assert original[field] == D(str(row[field])), (source['quotes'], row, field)
        assert original['quantity'] > 0 and original['volume_fin'] > 0
        count += 1
    assert not expected
    audit.append({'file': source['quotes'], 'raw_sha256': source['raw_excerpt_sha256'],
                  'records_equal_to_raw': count, 'economic_numeric_fields_per_record': 5})
write(inputs / 'SHA256.json', {p.name: sha(p) for p in sorted(inputs.iterdir())
                             if p.is_file() and p.name != 'SHA256.json'})
source_files = read(BASE / 'SOURCE_FILES.json')
for source in source_files['copied']:
    assert sha(BASE / source['packaged_path']) == source['sha256']
evidence = read(inputs / 'evidence.json')
cash = read(inputs / 'cash-events.json')
collisions = []
for portfolio, plans in index['plans'].items():
    for plan in plans:
        names = {m['ticker'] for m in plan['members']}
        for action in evidence['required_actions']:
            if action['ticker'] in names and plan['asof'] < action['ex_date'] <= plan['entry']:
                collisions.append({'portfolio': portfolio, 'asof': plan['asof'], 'entry': plan['entry'],
                    'ticker': action['ticker'], 'event_id': action['event_id'],
                    'status': 'REQUIRES_REVIEWED_ORDER_TRANSFORMATION'})
monthly = Counter(r['ex_date'][:4] for r in cash if not r.get('payment_date'))
audit_result = {'scope': 'SOURCE_AND_CAPABILITY_REVIEW_NO_RETURN_CALCULATION',
    'quote_sources': audit, 'total_quote_records_equal_to_raw': sum(r['records_equal_to_raw'] for r in audit),
    'primary_raw_copies_verified': len(source_files['copied']),
    'primary_raw_copies_missing_in_existing_registry': source_files['unresolved_raw_copies'],
    'frozen_protocol_sha256': sha(inputs / 'protocol.json'),
    'frozen_selection_sha256': sha(inputs / 'h18-h19-reorganization-observation.json'),
    'source_quote_availability_is_not_a_fill_or_capacity_certificate': True,
    'cash_event_rows': len(cash), 'cash_rows_without_payment_date': sum(monthly.values()),
    'missing_payment_by_ex_year': dict(sorted(monthly.items())),
    'required_cash_intervals': len(evidence['required_intervals']),
    'certified_cash_intervals': len(evidence['cash_coverage']),
    'required_action_records': len(evidence['required_actions']),
    'integrated_action_records': len(read(inputs / 'corporate-actions.json')),
    'entry_day_action_capability_gaps': collisions,
    'new_historical_return_evaluations': 0}
write(ROOT / 'outputs/STOCKS_REVISAO_FINAL_FONTES.json', audit_result)
print(json.dumps({k: v for k, v in audit_result.items() if k not in ('quote_sources', 'entry_day_action_capability_gaps')},
                 ensure_ascii=False))
print(json.dumps({'entry_action_conflicts': len(collisions), 'conflicts': collisions}, ensure_ascii=False))
