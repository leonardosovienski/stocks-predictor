from datetime import datetime
import json
from pathlib import Path
from explore_b3_events import fetch

ROOT=Path(__file__).resolve().parent.parent
RAW=ROOT/'work/source-acquisition'
summary=[]
for ticker in ('BBAS3','ABEV3','ENGI11'):
    first=json.loads((RAW/f'b3-{ticker}-cash-1.json').read_text(encoding='utf-8'))
    detail=json.loads((RAW/f'b3-{ticker}-detail.json').read_text(encoding='utf-8'))
    params=json.loads((RAW/f'b3-{ticker}-cash-1.source.json').read_text(encoding='utf-8'))['params']
    rows=list(first['results'])
    for page in range(2,first['page']['totalPages']+1):
        r=fetch('GetListedCashDividends',{**params,'pageNumber':page},f'b3-{ticker}-cash-{page}')
        if r['page']['totalRecords']!=first['page']['totalRecords']:
            raise ValueError('pagination changed while fetching; retry from a new snapshot')
        rows.extend(r['results'])
    assert len(rows)==first['page']['totalRecords']
    combined=RAW/f'b3-{ticker}-cash-all.json'
    combined.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    dates=[datetime.strptime(r['lastDatePriorEx'],'%d/%m/%Y').date().isoformat() for r in rows if r.get('lastDatePriorEx')]
    supplement=json.loads((RAW/f'b3-{ticker}-supplement.json').read_text(encoding='utf-8'))[0]
    event_dates=[datetime.strptime(r['lastDatePrior'],'%d/%m/%Y').date().isoformat() for r in supplement.get('cashDividends',[]) if r.get('lastDatePrior')]
    item={'ticker':ticker,'records':len(rows),'types':sorted({r['typeStock'] for r in rows}),
          'first_right_date':min(dates),'last_right_date':max(dates),'history_has_payment_date':any('paymentDate' in r for r in rows),
          'supplement_cash_events':len(event_dates),'supplement_first_right_date':min(event_dates,default=None),
          'supplement_last_right_date':max(event_dates,default=None),'performance_observed':False}
    summary.append(item)
    print(json.dumps(item),flush=True)
(ROOT/'outputs/b3-historical-coverage-sample.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
