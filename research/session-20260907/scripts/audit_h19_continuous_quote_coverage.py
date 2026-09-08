"""Check every frozen potential holding session, without computing returns."""
from collections import Counter
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'work/h19-continuous-inputs'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
index=read(BASE/'quote-tape-index.json');quotes={}
for source in index['sources']:
    for line in (BASE/source['quotes']).read_text(encoding='utf-8').splitlines():
        r=json.loads(line);quotes[(r['date'],r['ticker'],r['market_type'])]=r
audit=read(ROOT/'outputs/H19_CAIXA_EXECUCAO_V3.json')
intervals=[i['interval'] for i in audit['issues'] if i['kind']=='CASH_COVERAGE']
terms=read(ROOT/'work/value-event-terms/reorganizations.json')['events']
missing=[];seen=set();n=0
for ticker,isin,start,end in intervals:
    removed=any(e['ticker']==ticker and e['isin']==isin and e['ex_date']==end and e['removes_original'] for e in terms)
    for day in index['sessions']:
        if not start<=day<=end or (removed and day==end):continue
        key=(ticker,isin,day)
        if key in seen:continue
        seen.add(key);n+=1
        row=quotes.get((day,ticker,'010'))
        if not row or row['isin']!=isin:missing.append({'ticker':ticker,'isin':isin,'day':day,'side':'daily_standard'})
endpoint_gaps=[]
for label,plans in index['plans'].items():
    for plan in plans:
        for member in plan['members']:
            for day,market in [(plan['asof'],'010'),(plan['entry'],'010'),(plan['entry'],'020')]:
                if market=='020' and member['lot']==1:continue
                r=quotes.get((day,member['ticker'],market))
                if not r or r['isin']!=member['isin']:
                    endpoint_gaps.append({'portfolio':label,'ticker':member['ticker'],'day':day,'market':market})
result={'required_unique_holding_days':n,'missing_holding_quotes':missing,'endpoint_gaps':endpoint_gaps,
    'summary':{'holding_days':n,'missing':len(missing),'missing_by_ticker':dict(Counter(r['ticker'] for r in missing)),
               'endpoint_gaps':len(endpoint_gaps)},'new_return_evaluations':0}
(BASE/'quote-coverage.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result['summary'],indent=2));print(json.dumps(endpoint_gaps[:15]))
