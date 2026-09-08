"""Append exact B3 credit joins and four explicit selected-source reviews."""
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'work/h19-cash-expanded-source'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=ROOT/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V3.json'
registry=read(old);credits=read(BASE/'complete-credit-reconciliation.json')
def identity(r):return r['ticker'],r['ex_date'],r['action'],r['value_per_share'],r['source_row']
lookup={identity(r):r for r in registry['cash_queue']}
changes=[]
def apply(row,pay,sources,method,**extra):
    assert not row['payment_date_reviewed']
    row['reviewed_payment']={k:row[k] for k in ('ticker','isin','ex_date','last_cum','action','value_per_share')}
    row['reviewed_payment'].update(payment_date=pay,sources=sources,method=method,net_amount_reviewed=False,**extra)
    row['payment_date_reviewed']=True
    row['candidate_payment_dates']=sorted(set(row['candidate_payment_dates'])|{pay})
    changes.append({'identity':identity(row),'payment_date':pay,'method':method})
for match in credits['exact_unique_queue_matches']:
    row=lookup[identity(match['row'])];e=match['evidence']
    assert sha(BASE/e['source_file'])==e['source_sha256']
    apply(row,e['payment_date'],[e],'EXACT_B3_ISIN_TYPE_APPROVAL_AMOUNT_CREDIT')
def page_source(name,page,fragments):
    path=BASE/name;meta=read(path.with_suffix('.pdf.source.json'))
    assert sha(path)==meta['sha256']
    texts=read(path.with_suffix('.extracted.json'))
    text=' '.join(next(p['text'] for p in texts if p['page']==page).split())
    for f in fragments:assert f in text,(name,f)
    return {'source_file':name,'source_sha256':meta['sha256'],'url':meta['url'],'page':page,'verified_fragments':fragments}
manual=[
 ('COGN3','2025-12-26','0.0661459121','2026-02-13','cvm-notice-0140.pdf',3,
  ['0,06614591210','13 de fevereiro de 2026'],{'amount_is_declared_estimate':True,'not_bank_credit_confirmation':True}),
 ('COGN3','2025-12-26','0.04858806025','2028-12-20','cvm-notice-0140.pdf',3,
  ['0,04858806025','20 de dezembro de 2028'],{'amount_is_declared_estimate':True,'future_payment_not_available_during_history':True}),
 ('AZZA3','2025-12-22','1.5847435','2025-12-30','cvm-notice-0153.pdf',1,
  ['1,58474350000','30 de dezembro de 2025','19 de dezembro de 2025'],{}),
 ('BBAS3','2026-02-24','0.00518759764','2026-03-05','cvm-notice-0158.pdf',1,
  ['0,21630429188','0,22149188952','05.03.2026'],{'nominal_per_share':'0.21630429188','final_updated_per_share':'0.22149188952','no_duplicate_updated_total_credit':True})]
assert Decimal('0.22149188952')-Decimal('0.21630429188')==Decimal('0.00518759764')
for ticker,ex,value,pay,name,page,fragments,extra in manual:
    rows=[r for r in registry['cash_queue'] if r['ticker']==ticker and r['ex_date']==ex and Decimal(r['value_per_share'])==Decimal(value)]
    assert len(rows)==1
    apply(rows[0],pay,[page_source(name,page,fragments)],'EXPLICIT_PRIMARY_NOTICE_REVIEW',**extra)
counts=Counter()
for r in registry['cash_queue']:
    counts['queue_rows']+=1;counts['selected_rows']+=r['selected']
    counts['reviewed_payment_rows']+=r['payment_date_reviewed']
    counts['selected_reviewed_payment_rows']+=r['selected'] and r['payment_date_reviewed']
    counts['without_candidate_date']+=not r['candidate_payment_dates']
    counts['selected_without_candidate_date']+=r['selected'] and not r['candidate_payment_dates']
registry.update(schema='H19_REVIEWED_PAYMENT_DATES_4',summary=dict(counts),
    v4_increment={'baseline_sha256':sha(old),'credit_reconciliation_sha256':sha(BASE/'complete-credit-reconciliation.json'),
                  'changes':changes,'cash_coverage_not_certified':True,'new_return_evaluations':0})
target=ROOT/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V4.json'
target.write_text(json.dumps(registry,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'summary':dict(counts),'new_reviews':len(changes),'sha256':sha(target)},indent=2))
