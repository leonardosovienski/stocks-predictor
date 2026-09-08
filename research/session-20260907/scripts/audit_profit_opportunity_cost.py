"""Gross Selic reference over identical dates, not a taxed retail investment."""
from datetime import date,datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'work/profit-opportunity-source';OUT.mkdir(exist_ok=True)
intent={'purpose':'Compare fixed diagnostic equity outcomes with gross SGS11 on identical dates, with no selection or parameter change.',
        'convention':'Compound official daily percent values for start <= rate_date < end; compare calendar time. No product fees, taxes, exact intraday settlement, or retail investability implied.',
        'registered_at_utc':datetime.now(timezone.utc).isoformat()}
with (OUT/'intent.json').open('x',encoding='utf-8') as f:json.dump(intent,f,indent=2)
url='https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&dataInicial=01/01/2018&dataFinal=30/04/2026'
with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=45) as r:data=r.read()
source=json.loads(data)
with (OUT/'selic-sgs11.json').open('xb') as f:f.write(data)
meta={'url':url,'sha256':hashlib.sha256(data).hexdigest(),'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
      'metadata_url':'https://dadosabertos.bcb.gov.br/dataset/11-taxa-de-juros---selic','unit':'percent_per_day'}
with (OUT/'selic-sgs11.source.json').open('x',encoding='utf-8') as f:json.dump(meta,f,indent=2)
rates={datetime.strptime(r['data'],'%d/%m/%Y').date().isoformat():float(r['valor'])/100 for r in source}
if len(rates)!=len(source) or not rates:raise ValueError('Ambiguous/empty SGS observations')
obs=json.loads((ROOT/'outputs/VALIDACAO_LUCRO_STOCKS.json').read_text(encoding='utf-8'))
results=[]
for t in obs['trials']:
    s=t['modes']['open']['summary'];a,b=s['start'],s['end']
    values=[r for d,r in sorted(rates.items()) if a<=d<b]
    if min(rates)>a or max(rates)<b:raise ValueError('Truncated rate coverage')
    wealth=math.prod(1+r for r in values);years=(date.fromisoformat(b)-date.fromisoformat(a)).days/365.25
    results.append({'family':t['family'],'holding_months':t['holding_months'],'start':a,'end':b,
                    'selic_daily_records':len(values),'selic_gross_terminal_multiple':wealth,
                    'selic_gross_annualized':wealth**(1/years)-1,
                    'strategy_price_entitlements_after_flat72_annualized':s['synthetic_strategy_after_flat_72bp']['annualized_geometric_return']})
out={'reference':meta,'intent':intent,'comparisons':results,'not_a_like_for_like_net_total_return_comparison':True,
     'interpretation':'Opportunity-cost warning only: equities omit ordinary dividends and all taxes; Selic is an untaxed reference, not a traded product. Do not conclude a final net ranking from this comparison.'}
with (ROOT/'outputs/VALIDACAO_CUSTO_OPORTUNIDADE_STOCKS.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(results,indent=2))
