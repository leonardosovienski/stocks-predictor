"""Generate candidates only; a nearby date never becomes an approved payment."""
from collections import Counter
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import re
import unicodedata

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'work/h19-cash-expanded-source'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def norm(s):return ' '.join(unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower().split())
months={v:i+1 for i,v in enumerate('janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro'.split())}
pattern=re.compile(r'\b(\d{1,2})\s*(?:de\s+('+ '|'.join(months) +r')\s*(?:de\s*)?|([/.-])(\d{1,2})\3)(\d{4})\b')
def dates(text):
    result=[]
    for m in pattern.finditer(text):
        try:day=date(int(m[5]),months[m[2]] if m[2] else int(m[4]),int(m[1])).isoformat()
        except ValueError:continue
        result.append((day,m.start(),m.end()))
    return result
queue=read(ROOT/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V3.json')['cash_queue']
docs=read(BASE/'ipe-complete-notices.json')
index={}
for d in docs:
    p=BASE/d['local_file']; textfile=p.with_suffix('.extracted.json')
    if not textfile.exists():textfile=p.with_suffix('.complete-text.json')
    if not textfile.exists():continue
    pages=[(p['page'],norm(p['text'])) for p in read(textfile)]
    for r in d['matching_cash_requirements']:
        index.setdefault((r['ticker'],r['ex_date']),[]).append((d,pages))
results=[];all_dates=set();selected_passages=[]
for row in queue:
    if row['payment_date_reviewed']:continue
    value=Decimal(row['value_per_share']);quantum=Decimal(1).scaleb(value.normalize().as_tuple().exponent)
    candidates=set(row['candidate_payment_dates']);passages=[]
    for d,pages in index.get((row['ticker'],row['ex_date']),[]):
        for page,text in pages:
            hits=[]
            for m in re.finditer(r'(?<![\d.,])\d+[.,]\d+(?!\d|[.,]\d)',text):
                raw=m.group();v=Decimal(raw.replace(',','.'))
                if abs(v-value) < quantum:hits.append(m)
            if not hits:continue
            ds=dates(text)
            pay_dates=[]
            for day,start,end in ds:
                if day<row['ex_date']:continue
                nearby=text[max(0,start-230):min(len(text),end+100)]
                if re.search(r'pagamento|pagos|pago|creditados|credito|payment|paid',nearby):
                    candidates.add(day);pay_dates.append(day)
            passages.append({'file':d['local_file'],'page':page,'date_candidates':sorted(set(pay_dates)),
                'amount_passages':[text[max(0,m.start()-90):m.end()+220] for m in hits],
                'payment_passages':[text[max(0,m.start()-80):m.end()+250] for m in re.finditer('pagamento|payment',text)]})
    entry={k:row[k] for k in ('ticker','isin','ex_date','last_cum','action','value_per_share','selected','source_path','source_row')}
    raw=read(Path(row['source_path']))[row['source_row']]
    entry.update(approval_date=raw['dateApproval'],candidate_dates=sorted(candidates),matches=passages)
    results.append(entry)
    all_dates.update(day for day in candidates if '2018-01-01'<=day<='2026-09-07')
    if row['selected']:selected_passages.append(entry)
(BASE/'complete-payment-candidates.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
(BASE/'selected-final-candidate-passages.json').write_text(json.dumps(selected_passages,ensure_ascii=False,indent=2),encoding='utf-8')
jobs=[]
for day in sorted(all_dates):
    name='b3-credit-'+day.replace('-','')+'.pdf'
    if not (BASE/name).exists():jobs.append([name,f'https://arquivos.b3.com.br/bdi/download/bdi/{day}/BDI_05_{day.replace("-", "")}.pdf'])
(ROOT/'work/h19-credit-candidates-batch.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
print(json.dumps({'unreviewed_rows':len(results),'exact_amount_documents_found_for':sum(bool(r['matches']) for r in results),
    'with_any_candidate':sum(bool(r['candidate_dates']) for r in results),'candidate_credit_days':len(all_dates),
    'credit_documents_to_download':len(jobs),'by_year':dict(Counter(d[:4] for d in all_dates))},indent=2))
