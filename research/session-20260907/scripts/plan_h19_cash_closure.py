"""Exact cash work queue for frozen H19 quarters; no new return evaluation."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
obs=read(OUT/'h18-h19-reorganization-observation.json')
trial=next(t for t in obs['trials'] if t['family']=='H19' and t['holding_months']==3)
cash=read(OUT/'VALIDACAO_PROVENTOS_AMPLIADA_STOCKS_V2.json')['cash_rows']
prior=[json.loads(line) for line in (OUT/'cash-source-matches.jsonl').read_text(encoding='utf-8').splitlines()]
by_ticker=defaultdict(list)
for r in cash:by_ticker[r['ticker']].append(r)
queue=[];counts=defaultdict(Counter)
for p in trial['periods']:
    for m in p['members']:
        for r in by_ticker[m['ticker']]:
            if not p['entry']<r['ex_date']<=p['exit']:continue
            matched=[a for a in prior if a['ticker']==m['ticker'] and a['last_cum']==r['last_cum']
                     and a['action']==r['action'] and abs(Decimal(str(a['value_per_share']))-Decimal(r['value_per_share']))<=Decimal('.00000000001')]
            known_dates=sorted(set(r['b3_supplement_payment_dates'])|{a['payment_date'] for a in matched})
            record={'asof':p['asof'],'entry':p['entry'],'exit':p['exit'],'ticker':m['ticker'],'isin':m['isin'],
                    'selected':m['selected'],'ex_date':r['ex_date'],'last_cum':r['last_cum'],
                    'action':r['action'],'value_per_share':r['value_per_share'],
                    'candidate_payment_dates':known_dates,'has_issuer_match':bool(matched),
                    'source_path':r['source_path'],'source_row':r['source_row'],
                    'candidate_dates_are_not_coverage_certification':True}
            queue.append(record)
            c=counts[m['ticker']]
            c['selected_rows' if m['selected'] else 'benchmark_only_rows']+=1
            if not known_dates:c['selected_without_date' if m['selected'] else 'benchmark_without_date']+=1
            if matched:c['issuer_matched_rows']+=1
source_set={r['source_path'] for r in queue}
result={'protocol':'H19_QUARTERLY_CASH_CLOSURE_FEASIBILITY','created_at_utc':datetime.now(timezone.utc).isoformat(),
        'fixed_quarters':sum(bool(p['members']) for p in trial['periods']),
        'cash_cells':len(queue),'selected_cash_cells':sum(r['selected'] for r in queue),
        'selected_cells_without_candidate_payment_date':sum(r['selected'] and not r['candidate_payment_dates'] for r in queue),
        'benchmark_cells_without_candidate_payment_date':sum(not r['candidate_payment_dates'] for r in queue),
        'issuer_priority':sorted([{'ticker':t,**dict(c)} for t,c in counts.items()],key=lambda r:(-r.get('selected_without_date',0),-r.get('selected_rows',0),r['ticker'])),
        'cash_queue':queue,
        'limitations':['Cash on successor instruments must be added from conversion to exit; this queue counts original instruments only.',
                       'Repeated B3 amounts may be installments; dates and counts require reconciliation.',
                       'Zero rows in a current list do not independently prove absence of dividends.',
                       'No new returns, factor variants or executable profit were observed.'],
        'source_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(source_set)}}
path=OUT/'H19_CAIXA_FILA_DE_VALIDACAO.json'
with path.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ('cash_queue','source_sha256')},ensure_ascii=False,indent=2))
