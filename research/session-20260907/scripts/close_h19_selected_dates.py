"""Close the 16 outstanding selected payment dates against explicit evidence.

Read-only source audit. No return, portfolio selection, tax-net inference or DB writes.
Run against the fixed delivered V2 registry; do not mutate V2.
"""
from collections import Counter
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'work/h19-cash-expanded-source'
OLD=ROOT/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V2.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=read(OLD); result=deepcopy(before)
rows=result['cash_queue']; changes=[]; evidence_files=set()

def source(name,page,needles):
    pdf=BASE/name; metadata=read(pdf.with_suffix('.pdf.source.json'))
    assert sha(pdf)==metadata['sha256']
    p=next(p for p in read(pdf.with_suffix('.extracted.json')) if p['page']==page)
    normalized=' '.join(p['text'].split())
    for needle in needles:
        assert needle in normalized,(name,page,needle)
    evidence_files.update([name,pdf.with_suffix('.pdf.source.json').name,pdf.with_suffix('.extracted.json').name])
    return dict(file=name,page=page,sha256=sha(pdf),url=metadata['url'],checked_fragments=needles)

def resolve(ticker,ex,pay,sources,method,note,amount=None,**extra):
    found=[r for r in rows if r['ticker']==ticker and r['ex_date']==ex
           and (amount is None or Decimal(r['value_per_share'])==Decimal(amount))]
    assert len(found)==1,(ticker,ex,amount,len(found))
    row=found[0]
    assert row['selected'] and not row['candidate_payment_dates']
    assert row['last_cum']<row['ex_date']<=pay
    fact={k:row[k] for k in ('ticker','isin','ex_date','last_cum','action','value_per_share')}
    fact.update(payment_date=pay,payment_date_reviewed=True,review_method=method,
        sources=sources,source_review_scope=note,interval_complete=False,net_per_share=None,**extra)
    row.update(payment_date_reviewed=True,reviewed_payment=fact,candidate_payment_dates=[pay])
    result['facts'].append(fact)
    changes.append(dict(ticker=ticker,ex_date=ex,value_per_share=row['value_per_share'],payment_date=pay,
                        sources=sources,method=method,note=note))

resolve('VLID3','2018-12-17','2019-01-10',[
    source('cvm-notice-0006.pdf',1,['0,588235294','14 de dezembro de 2018','10 de janeiro de 2019'])],
    'EXACT_NOTICE_DATE_AMOUNT','Recovered previously failed PDF; declared gross amount and payment, not a complete-history certificate.')
resolve('CSMG3','2019-03-11','2019-06-10',[
    source('cvm-notice-0019.pdf',1,['0,7297139697','08.03.2019']),
    source('copasa-2019-agm.pdf',2,['92.231.328,84','28/02/2019','08/03/2019','10/06/2019'])],
    'DECLARATION_AND_AGM_PAYMENT','AGM fixes payment for the same total, approval and record date. Its quarter-year label says 2019 in a passage about 2018; keep that typo explicit.')
resolve('BRML3','2019-05-02','2019-05-31',[
    source('brml-2019-agm.pdf',3,['70.228.000,34']),
    source('brml-2019-2q-financials.pdf',62,['Dividendos mínimo obrigatórios (iv) 70.228 31/05/2019',
                                            'Dividendos mínimos obrigatórios aprovados em 30 de abril de 2019'])],
    'AGM_AND_SUBSEQUENT_FINANCIAL_STATEMENT','Issuer financial statement hosted by its financial-publication distributor. Date refers specifically to mandatory dividends approved at the 30 April AGM; unrelated JCP rows are not used. Per-share amount stays from B3, not from the rounded aggregate table.')
resolve('TUPY3','2019-05-22','2019-06-18',[
    source('cvm-notice-0025.pdf',1,['18 de junho de 2019','0,1733973'])],
    'ORIGINAL_PORTUGUESE_NOTICE','Original Portuguese states June 18. Attached English version incorrectly says March 28, which precedes this entitlement. Preserve the translation conflict; use the original language.')

updates=[('2021-02-23','2021-03-03','0.43586362186','0.43453097234','0.00133264952','cvm-notice-0045.pdf','03.03.2021'),
         ('2024-08-22','2024-08-30','0.15456771254','0.15186078881','0.00270692373','cvm-notice-0116.pdf','30.08.2024'),
         ('2024-08-22','2024-08-30','0.32008713184','0.31448148860','0.00560564324','cvm-notice-0116.pdf','30.08.2024')]
for ex,pay,updated,original,increment,name,spelling in updates:
    assert Decimal(updated)-Decimal(original)==Decimal(increment)
    resolve('BBAS3',ex,pay,[source(name,1,[updated.replace('.',','),original.replace('.',','),spelling])],
        'EXACT_FINAL_UPDATED_MINUS_NOMINAL','Monetary adjustment is the final payment-date total minus the nominal distribution, with Decimal arithmetic. Keep increment separate; do not credit updated total plus increment. No tax treatment inferred.',
        amount=increment,nominal_per_share=original,final_updated_per_share=updated)
resolve('NEOE3','2021-07-02','2021-12-21',[
    source('cvm-notice-0054.pdf',1,['0,1406397677','01/07/2021','21 de dezembro de 2021'])],
    'FINAL_PAYMENT_NOTICE','Replaces the initial end-of-year deadline with the payment date explicitly announced in December.')
resolve('BRML3','2022-05-02','2022-05-31',[
    source('brml-2022-payment.pdf',1,['31 de maio de 2022','0,05361046637835','29 de abril de 2022'])],
    'EXACT_NOTICE_ROUNDED_B3_VALUE','B3 0.05361046638 rounds the longer precision in the issuer notice. Retain the B3 gross and source precision difference.')
assert abs(Decimal('0.05361046638')-Decimal('0.05361046637835'))<Decimal('0.000000000005')
resolve('NTCO3','2024-03-20','2024-04-19',[
    source('cvm-notice-0133.pdf',1,['19 de março de 2024','20 de março 2024','19 de abril de 2024']),
    source('cvm-notice-0134.pdf',2,['0,707658'])],
    'ORIGINAL_DATE_AND_CORRECTED_ROUNDED_AMOUNT','Final notice displays six decimals; B3 amount differs by less than half that displayed precision. Date is reconciled; the six-decimal notice alone does not certify all eleven decimals.')
assert abs(Decimal('0.70765824985')-Decimal('0.707658'))<Decimal('0.0000005')
resolve('NTCO3','2024-04-09','2024-12-03',[
    source('cvm-followup-0071.pdf',1,['08 de abril de 2024','09 de abril de 2024','03 de dezembro de 2024']),
    source('cvm-followup-0072.pdf',1,['0,0324159 3478'])],
    'PAYMENT_AND_FINAL_EXACT_AMOUNT','Final amount is split by PDF text whitespace and confirmed in both language versions. Earlier notice net 0.0284370 is inconsistent with its gross and stated 15% rate; do not import that net figure.')

for ticker,ex,pay,value,name,payment_phrase in [
    ('ALOS3','2025-02-21','2025-03-07','0,091350145','cvm-followup-0079.pdf','07 de março de 2025'),
    ('ALOS3','2025-05-23','2025-06-03','0,101814360','cvm-followup-0080.pdf','03 de junho de 2025'),
    ('ALOS3','2025-04-23','2025-05-06','0,101692470','cvm-notice-0146.pdf','06 de maio de 2025')]:
    resolve(ticker,ex,pay,[source(name,1,[value,payment_phrase])],
        'FINAL_PER_SHARE_PAYMENT_NOTICE','Final payment and value confirmed in the issuer notice; insignificant trailing zeroes do not change the amount.')
resolve('COGN3','2025-04-29','2025-05-30',[
    source('b3-credit-20250530.pdf',4,['BRCOGNACNOR2 106 DIVIDENDO 28/04/2025 0,06672034907 30/05/2025'])],
    'B3_CREDIT_TABLE','B3 credit table provides exact ISIN, action, approval, value and credit date. This closes the initial deadline-only source.')
resolve('EZTC3','2025-08-15','2025-08-29',[
    source('b3-credit-20250829.pdf',4,['BREZTCACNOR0 129 DIVIDENDO 07/08/2025 0,30466792494 29/08/2025'])],
    'B3_CREDIT_TABLE','B3 credit table provides exact ISIN, action, approval, value and credit date. This closes the initial deadline-only source.')

assert len(changes)==16
assert len(rows)==len(before['cash_queue'])==778
for old,new in zip(before['cash_queue'],rows):
    for field in ('asof','entry','exit','ticker','isin','selected','ex_date','last_cum','action','value_per_share','source_row','source_path'):
        assert old[field]==new[field],('Frozen cash identity changed',field)
assert all(r['candidate_payment_dates'] for r in rows if r['selected'])
count=Counter()
for r in rows:
    count['queue_rows']+=1; count['selected_rows']+=r['selected']
    count['reviewed_payment_rows']+=r['payment_date_reviewed']
    count['selected_reviewed_payment_rows']+=r['selected'] and r['payment_date_reviewed']
    count['without_candidate_date']+=not r['candidate_payment_dates']
    count['selected_without_candidate_date']+=r['selected'] and not r['candidate_payment_dates']
result.update(schema='H19_REVIEWED_PAYMENT_DATES_3',summary=dict(count),
    incremental_review=dict(source_v2_sha256=sha(OLD),closed_selected_rows=changes,
        source_files=sorted(evidence_files),selected_payment_dates_not_equal_complete_cash_history=True,
        no_new_returns=True,selection_unchanged=True),
    full_cash_coverage_verified=False,new_historical_return_evaluations=0)
target=ROOT/'outputs/H19_CAIXA_PAGAMENTOS_REVISADOS_V3.json'
target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'summary':dict(count),'closed':len(changes),'output_sha256':sha(target)},indent=2))
