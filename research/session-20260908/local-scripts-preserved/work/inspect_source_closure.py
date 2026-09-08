from collections import Counter
import json
from pathlib import Path

ROOT = Path(r'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907')
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
base = ROOT/'work/stocks-final-review-bundle/inputs'
cash = read(base/'cash-events.json')
ev = read(base/'evidence.json')
print('CASH_MISSING_BY_TICKER', json.dumps(dict(Counter(r['ticker'] for r in cash if not r.get('payment_date')))))
print('NET_MISSING_BY_TICKER', json.dumps(dict(Counter(r['ticker'] for r in cash if r.get('net_per_share') is None))))
print('CASH_SAMPLE_MISSING', json.dumps([r for r in cash if not r.get('payment_date')][:3]))
print('REQUIRED_ACTIONS',json.dumps(ev['required_actions'],ensure_ascii=False))
print('OTHER_GAPS',json.dumps({k:v for k,v in ev.items() if k not in {'required_intervals','cash_coverage','required_actions'}},ensure_ascii=False)[:17000])
print('SOURCE_SUMMARIES', [(p.name,p.stat().st_size) for p in (ROOT/'work/h19-cash-expanded-source').iterdir() if p.is_file() and not p.name.startswith(('cvm-','b3-')) and not p.name.endswith(('.pdf','.source.json','.extracted.json','.complete-text.json'))])
print('SCRIPTS',[p.name for p in (ROOT/'work').glob('*.py') if any(k in p.name for k in ['cash','h19','corporate','reconcile'])])
